
/**
 * Copyright (c) 2017-2021. The WRENCH Team.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

/**
 ** An execution controller to execute a workflow
 **/

#define GFLOP (1000.0 * 1000.0 * 1000.0)
#define MBYTE (1000.0 * 1000.0)
#define GBYTE (1000.0 * 1000.0 * 1000.0)

#include <iostream>

#include <yaml-cpp/yaml.h>

#include "Controller.h"

WRENCH_LOG_CATEGORY(controller, "Log category for Controller");

namespace wrench {

    /**
     * @brief Constructor
     *
     * @param compute_service: a set of compute services available to run actions
     * @param storage_service: a set of storage services available to store files
     * @param hostname: the name of the host on which to start the WMS
     * @param num_steps: the number of iterations
     */
    Controller::Controller(const std::vector<std::shared_ptr<BareMetalComputeService>> &compute_services,
                           const std::vector<std::shared_ptr<SimpleStorageService>> &storage_services,
                           const std::string &hostname,
                           const std::string &config_file) :
            ExecutionController(hostname,"controller"),
            compute_services(compute_services), 
            storage_services(storage_services),
            config_file(config_file) {
        WRENCH_INFO("Number of compute services: %lu", this->compute_services.size());
        WRENCH_INFO("Number of storage services: %lu", this->storage_services.size());
        WRENCH_INFO("YAML configuration file: %s", this->config_file.c_str());
    }

    /**
     * @brief main method of the Controller
     *
     * @return 0 on completion
     *
     * @throw std::runtime_error
     */
    int Controller::main() {
        std::cerr << "Controller starting" << std::endl;

        /* Set the logging output to GREEN */
        TerminalOutput::setThisProcessLoggingColor(TerminalOutput::COLOR_GREEN);
        

        /* Pre-defined input parameters */
        double compute_mem = 0;
        double analysis_mem = 0;

        /* Amdahl alpha fraction. Setting this to 1 mean the task is perfectly parallel */
        double amdahl_fraction = 1.0;

        /* Create a job manager so that we can create/submit jobs */
        auto job_manager = this->createJobManager();

        /* Load YAML configuration file */
        YAML::Node config = YAML::LoadFile(this->config_file);
        int num_simulations = config["simulations"].size();
        WRENCH_INFO("Number of simulations : %lu", config["simulations"].size());
        int num_steps = config["steps"].as<int>();
        WRENCH_INFO("Number of steps: %d", num_steps);
        
        /* Count number of Wrench compoud jobs */
        int num_jobs = 0;
        /* Loop over simulations */
        for(YAML::const_iterator i=config["simulations"].begin(); i!=config["simulations"].end(); ++i) {
            std::string simulation_name = i->first.as<std::string>(); 
            std::string simulation_allocation = i->second["alloc"].as<std::string>();
            int simulation_node_start = config["allocations"][simulation_allocation]["start"].as<int>(); 
            int simulation_node_end = config["allocations"][simulation_allocation]["end"].as<int>();
            int simulation_num_nodes = simulation_node_end - simulation_node_start + 1;
            double data_size = i->second["data"].as<double>() * GBYTE;
            double simulation_data_size = data_size / simulation_num_nodes;
            int simulation_core = i->second["core_per_node"].as<int>();
            double simulation_flop = i->second["flop"].as<double>() * GFLOP / simulation_num_nodes;
            int num_analyses = i->second["coupling"].size();
            WRENCH_DEBUG("Simulation %s is co-scheduled on co-scheduling allocation %s from node %d to node %d, each node writes %.2lf bytes", simulation_name.c_str(), simulation_allocation.c_str(), simulation_node_start, simulation_node_end, simulation_data_size);
            WRENCH_DEBUG("Number of analyses coupled with simulation %s : %d", simulation_name.c_str(), num_analyses);

            std::vector<std::shared_ptr<wrench::CompoundJob>> data_write_jobs;
            data_write_jobs.reserve(simulation_num_nodes);
            std::vector<std::shared_ptr<wrench::CompoundJob>> data_read_jobs;
            std::vector<std::vector<std::shared_ptr<wrench::CompoundJob>>> analysis_jobs(num_analyses);
            for (int step = 1; step <= num_steps; step++) {
                
                for (int node = simulation_node_start; node <= simulation_node_end; node++) {
                    auto simulation_storage = this->storage_services[node];
                    auto simulation_compute = this->compute_services[node];
                    
                    /* Computing stage */
                    // WRENCH_INFO("Creating a compound job %s with a file read action followed by a compute action", job->getName().c_str());
                    auto compute_job = job_manager->createCompoundJob("member_" + simulation_name + "_compute_job_step_" + std::to_string(step) + "_node_" + std::to_string(node));
                    compute_job->addComputeAction("compute", simulation_flop, compute_mem, simulation_core, simulation_core, wrench::ParallelModel::AMDAHL(amdahl_fraction));     
                    /* Computing stage succeeds writing stage of the previous step */
                    if (step > 1)
                        compute_job->addParentJob(data_write_jobs[node-simulation_node_start]);       
                    job_manager->submitJob(compute_job, simulation_compute);

                    /* Writing stage */
                    auto output_data = wrench::Simulation::addFile("member_" + simulation_name + "_output_data_step_" + std::to_string(step) + "_node_" + std::to_string(node), simulation_data_size);
                    auto data_write_job = job_manager->createCompoundJob("member_" + simulation_name + "_data_write_job_step_" + std::to_string(step) + "_node_" + std::to_string(node));
                    data_write_job->addFileWriteAction("data_write", output_data, wrench::FileLocation::LOCATION(simulation_storage));
                    /* Writing stage succeeds computing stage */
                    data_write_job->addParentJob(compute_job);
                    /* Writing stage succeeds reading stage of the previous iteration */
                    for (auto & data_read_job : data_read_jobs) {
                        data_write_job->addParentJob(data_read_job);
                    }
                    job_manager->submitJob(data_write_job, simulation_compute);
                    if (step > 1)
                        data_write_jobs[node - simulation_node_start] = data_write_job;
                    else
                        data_write_jobs.push_back(data_write_job);
                    
                    num_jobs += 2;
                }
                
                data_read_jobs.clear();
                // Analysis index
                int k = 0;
                /* Loop over coupled analyses of the simulation */
                for(YAML::const_iterator j=i->second["coupling"].begin(); j!=i->second["coupling"].end(); ++j) {
                    
                    std::string analysis_name = j->first.as<std::string>();
                    // std::cout << analysis_name << std::endl;
                    std::string analysis_allocation = j->second["alloc"].as<std::string>();
                    int analysis_node_start = config["allocations"][analysis_allocation]["start"].as<int>(); 
                    int analysis_node_end = config["allocations"][analysis_allocation]["end"].as<int>(); 
                    int analysis_num_nodes = (analysis_node_end - analysis_node_start + 1);
                    //
                    double analysis_total_data_size = simulation_data_size * simulation_num_nodes / analysis_num_nodes;
                    int analysis_core = j->second["core_per_node"].as<int>();
                    double analysis_flop = j->second["flop"].as<double>() * GFLOP / analysis_num_nodes;        

                    WRENCH_DEBUG("Analysis %s (simulation %s) is co-scheduled on co-scheduling allocation %s from node %d to node %d, each node reads %.2lf bytes", analysis_name.c_str(), simulation_name.c_str(), analysis_allocation.c_str(), analysis_node_start, analysis_node_end, analysis_total_data_size);

                    for (int node = analysis_node_start; node <= analysis_node_end; node++) {
                        auto analysis_compute = this->compute_services[node];

                        /* Reading stage */
                        auto data_read_job = job_manager->createCompoundJob("member_" + simulation_name + "_" + analysis_name + "_data_read_job_step_" + std::to_string(step) + "_node_" + std::to_string(node));
                        /* Use createFile to create artificial files to read */
                        // if (analysis_allocation == simulation_allocation) {
                        //     /* The analysis is co-scheduled with the coupled simulation */
                        //     double analysis_data_size = simulation_data_size;
                        //     auto input_data = wrench::Simulation::addFile("member_" + simulation_name + "_" + analysis_name + "_input_data_step_" + std::to_string(step) + "_node_" + std::to_string(node), analysis_data_size);
                        //     auto analysis_storage = this->storage_services[node];
                        //     wrench::Simulation::createFile(input_data, wrench::FileLocation::LOCATION(analysis_storage));
                        //     data_read_job->addFileReadAction("data_read", input_data, wrench::FileLocation::LOCATION(analysis_storage));
                        // } else {
                        //     /* The analysis is not co-scheduled with the coupled simulation */
                        //     double analysis_data_size = simulation_data_size / analysis_num_nodes;
                        //     for (int simulation_storage_node = simulation_node_start; simulation_storage_node <= simulation_node_end; simulation_storage_node++) {
                        //         auto input_data = wrench::Simulation::addFile("member_" + simulation_name + "_" + analysis_name + "_input_data_step_" + std::to_string(step) + "_node_" + std::to_string(node) + "_" + std::to_string(simulation_storage_node), analysis_data_size);
                        //         auto analysis_storage = this->storage_services[simulation_storage_node];
                        //         wrench::Simulation::createFile(input_data, wrench::FileLocation::LOCATION(analysis_storage));
                        //         data_read_job->addFileReadAction("data_read_" + std::to_string(simulation_storage_node), input_data, wrench::FileLocation::LOCATION(analysis_storage));
                        //     }
                        // }

                        /* Use num_bytes_to_read API to determine the partial number of bytes to read */
                        if (analysis_allocation == simulation_allocation) {
                            /* The analysis is co-scheduled with the coupled simulation */
                            double analysis_data_size = simulation_data_size;
                            auto input_data = wrench::Simulation::getFileByID("member_" + simulation_name + "_output_data_step_" + std::to_string(step) + "_node_" + std::to_string(node));
                            auto analysis_storage = this->storage_services[node];
                            data_read_job->addFileReadAction("data_read", input_data, wrench::FileLocation::LOCATION(analysis_storage));
                        } else {
                            /* The analysis is not co-scheduled with the coupled simulation */
                            double analysis_data_size = simulation_data_size / analysis_num_nodes;
                            for (int simulation_storage_node = simulation_node_start; simulation_storage_node <= simulation_node_end; simulation_storage_node++) {
                                auto input_data = wrench::Simulation::getFileByID("member_" + simulation_name + "_output_data_step_" + std::to_string(step) + "_node_" + std::to_string(simulation_storage_node));
                                auto analysis_storage = this->storage_services[simulation_storage_node];
                                data_read_job->addFileReadAction("data_read_" + std::to_string(simulation_storage_node), input_data, wrench::FileLocation::LOCATION(analysis_storage), analysis_data_size);
                            }
                        }

                        /* Reading stage succeeds the analyzing stage of the previous iteration */
                        if (step > 1)
                            data_read_job->addParentJob(analysis_jobs[k][node - analysis_node_start]);
                        /* Reading stage succeeds writing stages */
                        for (auto & data_write_job : data_write_jobs) {
                            data_read_job->addParentJob(data_write_job);
                        }
                        data_read_jobs.push_back(data_read_job);
                        job_manager->submitJob(data_read_job, analysis_compute);

                        /* Analyzing stage */
                        auto analysis_job = job_manager->createCompoundJob("member_" + simulation_name + "_" + analysis_name + "_analysis_job_step_" + std::to_string(step) + "_node_" + std::to_string(node));
                        analysis_job->addComputeAction("analysis", analysis_flop, analysis_mem, analysis_core, analysis_core, wrench::ParallelModel::AMDAHL(amdahl_fraction));
                        /* Analyzing stage succeeds reading stage */
                        analysis_job->addParentJob(data_read_job);
                        if (step > 1) 
                            analysis_jobs[k][node - analysis_node_start] = analysis_job;
                        else
                            analysis_jobs[k].push_back(analysis_job);
                        job_manager->submitJob(analysis_job, analysis_compute);

                        num_jobs += 2;
                    }
                    ++k;
                }
            }
        }
        int num_jobs_per_ten_percent = num_jobs / 10;
        for (int i = 1; i <= num_jobs; i++) {
            // WRENCH_INFO("Waiting for an execution event...");
            /*  Wait for an execution event and handle returned event */
            // this->waitForAndProcessNextEvent();

            /* Wait for next event without handling */
            auto event = this->waitForNextEvent();
            if (auto job_completion_event = std::dynamic_pointer_cast<wrench::CompoundJobCompletedEvent>(event)) {
                auto completed_job = job_completion_event->job;
                for (auto const &action: completed_job->getActions()) {
                    fprintf(stdout, "%s, %s, %s, %s, %lu, %.2lf, %.4lf, %.4lf\n",
                        completed_job->getName().c_str(),
                        action->getName().c_str(),
                        action->getExecutionHistory().top().execution_host.c_str(),
                        action->getExecutionHistory().top().physical_execution_host.c_str(),
                        action->getExecutionHistory().top().num_cores_allocated,
                        action->getExecutionHistory().top().ram_allocated,
                        action->getExecutionHistory().top().start_date,
                        action->getExecutionHistory().top().end_date
                        );
                    if (i == num_jobs) {
                        fprintf(stderr, "End time of the simulation: %.4lf\n", action->getExecutionHistory().top().end_date);
                    }
                    if (i == 1) {
                        fprintf(stderr, "Start time of the simulation: %.4lf\n", action->getExecutionHistory().top().start_date);
                    }
                }
            } else {
                throw std::runtime_error("Unexpected event: " + event->toString());
            }
            if ((num_jobs_per_ten_percent > 0) && (i % num_jobs_per_ten_percent == 0)) {
                fprintf(stderr, "%.2lf%% done\n", (double)i / num_jobs * 100);
            }
        }

        std::cerr << "Execution complete!" << std::endl;

        std::cerr << "Controller terminating" << std::endl;
        return 0;
    }

    /**
     * @brief Process a compound job completion event
     *
     * @param event: the event
     */
    void Controller::processEventCompoundJobCompletion(std::shared_ptr<CompoundJobCompletedEvent> event) {
        TerminalOutput::setThisProcessLoggingColor(TerminalOutput::COLOR_BLUE);
        /* Retrieve the job that this event is for */
        auto job = event->job;
        /* Print info about all actions in the job */
        // WRENCH_INFO("It had %lu actions:", job->getActions().size());
        for (auto const &action : job->getActions()) {
            WRENCH_INFO("  - Compound job %s completed: Action %s ran on host %s (physical: %s), used %lu cores for computation, and %.2lf bytes of RAM, started at time %.4lf and finished at time %.4lf",
                        job->getName().c_str(),
                        action->getName().c_str(),
                        action->getExecutionHistory().top().execution_host.c_str(),
                        action->getExecutionHistory().top().physical_execution_host.c_str(),
                        action->getExecutionHistory().top().num_cores_allocated,
                        action->getExecutionHistory().top().ram_allocated,
                        action->getExecutionHistory().top().start_date,
                        action->getExecutionHistory().top().end_date
                        );
        }
        TerminalOutput::setThisProcessLoggingColor(TerminalOutput::COLOR_GREEN);
    }

    /**
     * @brief Process a standard job failure event
     *
     * @param event: the event
     */
    void Controller::processEventCompoundJobFailure(std::shared_ptr<CompoundJobFailedEvent> event) {
        auto job = event->job;
        WRENCH_INFO("Compound job %s has failed!", job->getName().c_str());
        throw std::runtime_error("This should not happen in this example");
    }

}
