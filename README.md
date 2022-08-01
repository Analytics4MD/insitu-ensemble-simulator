
<h1 align="center">  
  A4MD-insitu-ensemble-simulator
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

## Run
```
./insitu-ensemble-simulator <yaml config file> <xml platform file>
```
