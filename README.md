
<h1 align="center">  
  A4MD-insitu-ensemble-simulator
</h1>

## About

An experimental simulator for workflow ensembles of simulations and in situ analyses

## Prerequisites

- SimGrid
- Wrench
- yaml-cpp

## Installation

```
mkdir build
cd build

cmake .. \
-DSimGrid_PATH=<SimGrid_ROOT> \
-DWRENCH_PATH=<WRENCH_ROOT> \
-DYAMLCPP_PATH=<yamlcpp_ROOT>

make
make install
```

## Run
```
./insitu-ensemble-simulator <number of compute nodes> <yaml config file> <xml platform file>
```
