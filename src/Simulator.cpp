
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

#include <yaml-cpp/yaml.h>

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
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <yaml config file> <xml platform file> [--log=controller.threshold=info | --wrench-full-log]" << std::endl;
        exit(1);
    }

    /* Instantiating the simulated platform */
    std::cerr << "Instantiating simulated platform..." << std::endl;
    simulation->instantiatePlatform(argv[2]);

    std::string config_file(argv[1]);
    YAML::Node config = YAML::LoadFile(config_file);
    int num_nodes = config["nodes"].as<int>();

    std::cerr << "Instantiating compute and storage services..." << std::endl;
    std::vector<std::shared_ptr<wrench::BareMetalComputeService>> compute_services;
    std::vector<std::shared_ptr<wrench::SimpleStorageService>> storage_services;
    for (int i = 1; i <= num_nodes; i++) {
        std::string host_name = "ComputeHost" + std::to_string(i);
        /* Instantiate a storage service on the platform */            
        auto storage_service = simulation->add(new wrench::SimpleStorageService(
            host_name, {"/"}, 
            {{wrench::SimpleStorageServiceProperty::BUFFER_SIZE, "infinity"}}, 
            // {},
            {
            {wrench::SimpleStorageServiceMessagePayload::FILE_WRITE_ANSWER_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_WRITE_REQUEST_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_READ_ANSWER_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_READ_REQUEST_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_LOOKUP_ANSWER_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_LOOKUP_REQUEST_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_COPY_ANSWER_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_COPY_REQUEST_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_DELETE_ANSWER_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_DELETE_REQUEST_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FILE_NOT_FOUND_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FREE_SPACE_ANSWER_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::FREE_SPACE_REQUEST_MESSAGE_PAYLOAD, 0},
            {wrench::SimpleStorageServiceMessagePayload::NOT_ENOUGH_STORAGE_SPACE_MESSAGE_PAYLOAD, 0}
            }
            ));
        storage_services.push_back(storage_service);

        /* Instantiate a bare-metal compute service on the platform */
        auto compute_service = simulation->add(new wrench::BareMetalComputeService(
            host_name, {host_name}, "", {}, {}));
        compute_services.push_back(compute_service);
    }

    /* Instantiate an execution controller */
    std::cerr << "Instantiating execution controller..." << std::endl;
    auto wms = simulation->add(
        new wrench::Controller(compute_services, storage_services, "UserHost", config_file));

    /* Launch the simulation */
    std::cerr << "Launching the Simulation..." << std::endl;
    try {
        simulation->launch();
    } catch (std::runtime_error &e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }
    std::cerr << "Simulation done!" << std::endl;

    // /* Simulation results can be examined via simulation->getOutput(), which provides access to traces
    //  * of events. In the code below, we print the  retrieve the trace of all task completion events, print how
    //  * many such events there are, and print some information for the first such event. */
    // auto trace = simulation->getOutput().getTrace<wrench::SimulationTimestampTaskCompletion>();
    // for (auto const &item: trace) {
    //     std::cerr << "Task " << item->getContent()->getTask()->getID() << " completed at time " << item->getDate() << " on host " << item->getContent()->getTask()->getExecutionHost() << std::endl;
    // }
    // simulation->getOutput().enableBandwidthTimestamps(true);
    // simulation->getOutput().dumpLinkUsageJSON("link_usage.json");
    // simulation->getOutput().dumpDiskOperationsJSON("disk_operations.json");

    return 0;
}
