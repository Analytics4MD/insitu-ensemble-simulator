
/**
 * Copyright (c) 2017-2021. The WRENCH Team.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

/**
 ** This is the main function for a WRENCH simulator. The simulator takes
 ** a input an XML platform description file. It generates a workflow with
 ** a simple diamond structure, instantiates a few services on the platform, and
 ** starts an execution controller to execute the workflow using these services
 ** using a simple greedy algorithm.
 **/

#include <iostream>
#include <wrench-dev.h>

#include "Controller.h"

/**
 * @brief The Simulator's main function
 *
 * @param argc: argument count
 * @param argv: argument array
 * @return 0 on success, non-zero otherwise
 */
int main(int argc, char **argv) {

    /* Create a WRENCH simulation object */
    auto simulation = wrench::Simulation::createSimulation();

    /* Initialize the simulation */
    simulation->init(&argc, argv);

    /* Parsing of the command-line arguments */
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <number of compute nodes> <number of steps> <yaml config file> <xml platform file> [--log=controller.threshold=info | --wrench-full-log]" << std::endl;
        exit(1);
    }

    /* Instantiating the simulated platform */
    std::cerr << "Instantiating simulated platform..." << std::endl;
    simulation->instantiatePlatform(argv[4]);

    int num_nodes = std::atoi(argv[1]);
    int num_steps = std::atoi(argv[2]);
    std::string config_file(argv[3]);


    std::cerr << "Instantiating compute and storage services..." << std::endl;
    std::vector<std::shared_ptr<wrench::BareMetalComputeService>> compute_services;
    std::vector<std::shared_ptr<wrench::SimpleStorageService>> storage_services;
    for (int i = 1; i <= num_nodes; i++) {
        std::string host_name = "ComputeHost" + std::to_string(i);
        /* Instantiate a storage service on the platform */            
        auto storage_service = simulation->add(new wrench::SimpleStorageService(
            host_name, {"/"}, {}, {}));
        storage_services.push_back(storage_service);

        /* Instantiate a bare-metal compute service on the platform */
        auto compute_service = simulation->add(new wrench::BareMetalComputeService(
            host_name, {host_name}, "", {}, {}));
        compute_services.push_back(compute_service);
    }

    /* Instantiate an execution controller */
    std::cerr << "Instantiating execution controller..." << std::endl;
    auto wms = simulation->add(
        new wrench::Controller(compute_services, storage_services, "UserHost", num_steps, config_file));

    /* Launch the simulation */
    std::cerr << "Launching the Simulation..." << std::endl;
    try {
        simulation->launch();
    } catch (std::runtime_error &e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }
    std::cerr << "Simulation done!" << std::endl;

    return 0;
}
