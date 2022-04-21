#!/usr/bin/env bash
echo "Generating configuration and platform files ..."
python3 generator.py config.yml platform.xml
echo "Computing the solution ..."
python3 scheduler.py config.yml

scenarios=( "ideal" "transit" "increasing0.25" "increasing0.5" "increasing0.75" "decreasing0.25" "decreasing0.5" "decreasing0.75" )
for scenario in "${scenarios[@]}"
do
    echo "Simulating ${scenario} case ..."
    ./insitu-ensemble-simulator ${scenario}.conf platform.xml 1> ${scenario}.log 2> ${scenario}.err &
done