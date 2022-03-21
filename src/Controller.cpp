
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
            compute_services(compute_services), storage_services(storage_services) {}

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
        int num_nodes = 2;
        double data_size = 1 * GBYTE;
        double compute_flops = 100 * GFLOP;
        double compute_mem = 50 * MBYTE;
        double analysis_flops = 100 * GFLOP;
        double analysis_mem = 50 * MBYTE;

        

        /* Create a job manager so that we can create/submit jobs */
        auto job_manager = this->createJobManager();

        std::vector<std::shared_ptr<wrench::CompoundJob>> jobs;
        for (int i = 1; i <= num_nodes; i++) {
            auto job = job_manager->createCompoundJob("job_" + std::to_string(i));
            WRENCH_INFO("Creating a compound job %s with a file read action followed by a compute action", job->getName().c_str());

            /* Create a input, output data */        
            auto input_data = wrench::Simulation::addFile("input_data_" + std::to_string(i), data_size);
            auto output_data = wrench::Simulation::addFile("output_data_" + std::to_string(i), data_size);
            this->storage_services[i-1]->createFile(input_data, wrench::FileLocation::LOCATION(this->storage_services[i-1]));

            /* Writing stage */
            auto data_write = job->addFileWriteAction("data_write_" + std::to_string(i), output_data, wrench::FileLocation::LOCATION(this->storage_services[i-1]));
            /* Computing stage */
            auto compute = job->addComputeAction("compute_" + std::to_string(i), compute_flops, compute_mem, 1, 3, wrench::ParallelModel::AMDAHL(0.8));
            /* Reading stage */
            auto data_read = job->addFileReadAction("data_read_" + std::to_string(i), input_data, wrench::FileLocation::LOCATION(this->storage_services[i-1]));
            /* Analyzing stage */
            auto analysis = job->addComputeAction("analysis_" + std::to_string(i), analysis_flops, analysis_mem, 1, 3, wrench::ParallelModel::AMDAHL(0.8));
            /* Dependencies among fine-grained stages */
            job->addActionDependency(compute, data_write);
            job->addActionDependency(data_write, data_read);
            job->addActionDependency(data_read, analysis);
            
            job_manager->submitJob(job, this->compute_services[i-1]);
            WRENCH_INFO("Submitting job %s to the bare-metal compute service", job->getName().c_str());

            jobs.push_back(job);

        }

        /* Submite jobs */
        // for (int i = 1; i <= num_nodes; i++) {
        //     job_manager->submitJob(jobs[i-1], this->bare_metal_compute_service);
        //     WRENCH_INFO("Submitting job %s to the bare-metal compute service", jobs[i-1]->getName().c_str());
        // }

        for (int i = 1; i <= num_nodes; i++) {
            WRENCH_INFO("Waiting for an execution event...");
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
        /* Retrieve the job that this event is for */
        auto job = event->job;
        /* Print info about all actions in the job */
        WRENCH_INFO("Notified that compound job %s has completed:", job->getName().c_str());
        WRENCH_INFO("It had %lu actions:", job->getActions().size());
        for (auto const &action : job->getActions()) {
            WRENCH_INFO("  - Action %s ran on host %s (physical: %s)",
                        action->getName().c_str(),
                        action->getExecutionHistory().top().execution_host.c_str(),
                        action->getExecutionHistory().top().physical_execution_host.c_str());
            WRENCH_INFO("     - it used %lu cores for computation, and %.2lf bytes of RAM",
                        action->getExecutionHistory().top().num_cores_allocated,
                        action->getExecutionHistory().top().ram_allocated);
            WRENCH_INFO("     - it started at time %.2lf and finished at time %.2lf",
                        action->getExecutionHistory().top().start_date,
                        action->getExecutionHistory().top().end_date);
        }
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
