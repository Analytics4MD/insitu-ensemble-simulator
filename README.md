
<h1 align="center">  
  insitu-ensemble-simulator
</h1>

## About

An experimental simulator for workflow ensembles of simulations and in situ analyses

## Prerequisites

- [SimGrid](https://simgrid.org/)
- [WRENCH](https://wrench-project.org/)
- [yaml-cpp](https://github.com/jbeder/yaml-cpp)
- [SymPy](https://www.sympy.org)
- [lxml](https://lxml.de)

## Installation

Please disable SMPI feature `-Denable_smpi=off` when installing SimGrid to avoid trouble later

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
This command will generate an executable `insitu-ensemble-simulator` for the simulator.

## Run
Generate platform file and general ensemble's structure
```
python3 solver/generator.py <name of output config file (yml)> <name of output platform file (xml)>
```
Specify co-scheduling mapping and compute resource allocation according to a particular scenario, e.g. ideal, transit
```
python3 solver/scheduler.py <config file> <scenario>
```
Run the simulation
```
./insitu-ensemble-simulator <config file> <platform file>
```
