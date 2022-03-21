
/**
 * Copyright (c) 2017-2018. The WRENCH Team.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */


#ifndef CONTROLLER_H
#define CONTROLLER_H

#include <wrench-dev.h>

namespace wrench {

    /**
     *  @brief A Workflow Management System (WMS) implementation
     */
    class Controller : public ExecutionController {

    public:
        // Constructor
        Controller(
                  const std::vector<std::shared_ptr<BareMetalComputeService>> &compute_services,
                  const std::vector<std::shared_ptr<SimpleStorageService>> &storage_services,
                  const std::string &hostname);

    protected:

        // Overridden methods
        void processEventCompoundJobCompletion(std::shared_ptr<CompoundJobCompletedEvent>) override;
        void processEventCompoundJobFailure(std::shared_ptr<CompoundJobFailedEvent>) override;

    private:
        // main() method of the WMS
        int main() override;

        const std::vector<std::shared_ptr<BareMetalComputeService>> compute_services;
        const std::vector<std::shared_ptr<SimpleStorageService>> storage_services;

    };
}
#endif //CONTROLLER_H
