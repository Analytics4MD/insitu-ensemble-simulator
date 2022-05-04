#!/usr/bin/env bash
echo "Generating configuration and platform files ..."
python3 generator.py config.yml platform.xml
echo "Computing the solution ..."
python3 scheduler.py config.yml

scenarios=( "ideal" "transit" "increasing0.25" "increasing0.5" "increasing0.75" "decreasing0.25" "decreasing0.5" "decreasing0.75" )
# scenarios=( "increasing0.5" )
heuristics=( "model_model" "model_even" "even_model" "even_even" )
# heuristics=( "model_model" )
for scenario in "${scenarios[@]}"
do
    # mv ${scenario}.err ${scenario}_model_model.err
    # mv ${scenario}.log ${scenario}_model_model.log
    # rm ${scenario}.conf
    for heuristic in "${heuristics[@]}"
    do
        # cp ${scenario}_${heuristic}.conf ${scenario}_${heuristic}.conf.bak
        # mv ${scenario}_${heuristic}.log ${scenario}_${heuristic}.log.bak
        # mv ${scenario}_${heuristic}.err ${scenario}_${heuristic}.err.bak
        echo "Simulating ${scenario} case ..."
        ./insitu-ensemble-simulator ${scenario}_${heuristic}.conf platform.xml 1> ${scenario}_${heuristic}.log 2> ${scenario}_${heuristic}.err &
    done
done