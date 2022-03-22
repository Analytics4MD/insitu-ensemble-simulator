
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

#include "Controller.h"

WRENCH_LOG_CATEGORY(controller, "Log category for Controller");

namespace wrench {

    /**
     * @brief Constructor
     *
     * @param compute_service: a set of compute services available to run actions
     * @param storage_service: a set of storage services available to store files
     * @param hostname: the name of the host on which to start the WMS
     */
    Controller::Controller(const std::vector<std::shared_ptr<BareMetalComputeService>> &compute_services,
                           const std::vector<std::shared_ptr<SimpleStorageService>> &storage_services,
                           const std::string &hostname) :
            ExecutionController(hostname,"controller"),
            compute_services(compute_services), storage_services(storage_services) {
        WRENCH_INFO("Number of compute services: %d", this->compute_services.size());
        WRENCH_INFO("Number of storage services: %d", this->storage_services.size());
    }

    /**
     * @brief main method of the Controller
     *
     * @return 0 on completion
     *
     * @throw std::runtime_error
     */
    int Controller::main() {

        /* Set the logging output to GREEN */
        TerminalOutput::setThisProcessLoggingColor(TerminalOutput::COLOR_GREEN);
        WRENCH_INFO("Controller starting");

        /* Input parameters */
        // conint num_simulations = 1;
        // std::vector<int> num_analyses_per_simulation = {1};
        std::vector<std::vector<int>> allocation_map = {{0,0,1,2}}; 
        std::vector<std::tuple<int, int>> cosched_allocations = {{0,1},{2,2},{3,3}};
        // int num_nodes = 2;
        double data_size = 1 * GBYTE;
        double compute_flops = 100 * GFLOP;
        double compute_mem = 50 * MBYTE;
        double analysis_flops = 100 * GFLOP;
        double analysis_mem = 50 * MBYTE;

        /* Create a job manager so that we can create/submit jobs */
        auto job_manager = this->createJobManager();

        int num_simulations = allocation_map.size();
        int num_jobs = 0;

        /* Define fine-grained stages for ensemble members */
        for (int i = 1; i <= num_simulations; i++) {
            int simulation_allocation = allocation_map[i-1][0];
            std::vector<std::shared_ptr<wrench::CompoundJob>> data_write_jobs;

            int simulation_node_start = std::get<0>(cosched_allocations[simulation_allocation]);
            int simulation_node_end = std::get<1>(cosched_allocations[simulation_allocation]);
            int simulation_num_nodes = simulation_node_end - simulation_node_start + 1;
            double simulation_data_size = data_size / simulation_num_nodes;

            WRENCH_INFO("Simulation %d is co-scheduled on co-scheduling allocation %d from node %d to node %d, each node writes %.2lf bytes", i, simulation_allocation, simulation_node_start, simulation_node_end, simulation_data_size);
            for (int node = simulation_node_start; node <= simulation_node_end; node++) {
                auto simulation_storage = this->storage_services[node];
                auto simulation_compute = this->compute_services[node];

                /* Computing stage */
                // WRENCH_INFO("Creating a compound job %s with a file read action followed by a compute action", job->getName().c_str());
                auto compute_job = job_manager->createCompoundJob("member_" + std::to_string(i) + "_compute_job_" + std::to_string(node));
                compute_job->addComputeAction("compute", compute_flops, compute_mem, 1, 3, wrench::ParallelModel::AMDAHL(0.8));            
                job_manager->submitJob(compute_job, simulation_compute);

                /* Writing stage */
                auto output_data = wrench::Simulation::addFile("member_" + std::to_string(i) + "_output_data_" + std::to_string(node), simulation_data_size);
                auto data_write_job = job_manager->createCompoundJob("member_" + std::to_string(i) + "_data_write_job_" + std::to_string(node));
                data_write_job->addFileWriteAction("data_write", output_data, wrench::FileLocation::LOCATION(simulation_storage));
                data_write_job->addParentJob(compute_job);
                job_manager->submitJob(data_write_job, simulation_compute);
                data_write_jobs.push_back(data_write_job);
                
                num_jobs += 2;
            }
            std::vector<std::shared_ptr<wrench::CompoundJob>> data_read_jobs;
            for (int j = 1; j <= (allocation_map[i-1]).size()-1; j++) {
                
                int analysis_allocation = allocation_map[i-1][j];
                int analysis_node_start = std::get<0>(cosched_allocations[analysis_allocation]);
                int analysis_node_end = std::get<1>(cosched_allocations[analysis_allocation]);
                int analysis_num_nodes = (analysis_node_end - analysis_node_start + 1);
                double analysis_data_size = data_size / analysis_num_nodes;

                int analysis_storage_node = simulation_node_start;
                WRENCH_INFO("Analysis %d (simulation %d) is co-scheduled on co-scheduling allocation %d from node %d to node %d, each node reads %.2lf bytes", j, i, analysis_allocation, analysis_node_start, analysis_node_end, analysis_data_size);
                for (int node = analysis_node_start; node <= analysis_node_end; node++) {
                    if (analysis_storage_node > simulation_node_end) 
                        analysis_storage_node = simulation_node_start; 
                    auto analysis_storage = this->storage_services[analysis_storage_node];
                    auto analysis_compute = this->compute_services[node];

                    /* Reading stage */
                    auto input_data = wrench::Simulation::addFile("member_" + std::to_string(i) + "_" + std::to_string(j) + "_input_data_" + std::to_string(node), analysis_data_size);
                    analysis_storage->createFile(input_data, wrench::FileLocation::LOCATION(analysis_storage));
                    auto data_read_job = job_manager->createCompoundJob("member_" + std::to_string(i) + "_" + std::to_string(j) + "_data_read_job_" + std::to_string(node));
                    data_read_job->addFileReadAction("data_read", input_data, wrench::FileLocation::LOCATION(analysis_storage));
                    for (auto data_write_job : data_write_jobs) {
                        data_read_job->addParentJob(data_write_job);
                    }
                    data_read_jobs.push_back(data_read_job);
                    job_manager->submitJob(data_read_job, analysis_compute);

                    /* Analyzing stage */
                    auto analysis_job = job_manager->createCompoundJob("member_" + std::to_string(i) + "_" + std::to_string(j) + "_analysis_job_" + std::to_string(node));
                    analysis_job->addComputeAction("analysis", analysis_flops, analysis_mem, 1, 3, wrench::ParallelModel::AMDAHL(0.8));
                    analysis_job->addParentJob(data_read_job);
                    job_manager->submitJob(analysis_job, analysis_compute);

                    analysis_storage_node++;
                    num_jobs += 2;
                }
            }
            
            // WRENCH_INFO("Submitting job %s to the bare-metal compute service", job->getName().c_str());
        }

        /* Submite jobs */
        // for (int i = 1; i <= num_nodes; i++) {
        //     job_manager->submitJob(jobs[i-1], this->bare_metal_compute_service);
        //     WRENCH_INFO("Submitting job %s to the bare-metal compute service", jobs[i-1]->getName().c_str());
        // }

        for (int i = 1; i <= num_jobs; i++) {
            // WRENCH_INFO("Waiting for an execution event...");
            this->waitForAndProcessNextEvent();
        }

        WRENCH_INFO("Execution complete!");

        WRENCH_INFO("Controller terminating");
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
            WRENCH_INFO("  - Compound job %s completed: Action %s ran on host %s (physical: %s), used %lu cores for computation, and %.2lf bytes of RAM, started at time %.2lf and finished at time %.2lf",
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
