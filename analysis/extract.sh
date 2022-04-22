#!/usr/bin/env bash
scenarios=( "ideal" "transit" "increasing0.25" "increasing0.5" "increasing0.75" "decreasing0.25" "decreasing0.5" "decreasing0.75" )
echo "variation,variable,scenario,time"
for d in $(ls -dq log/*/); do
    for scenario in "${scenarios[@]}"
    do
        dir_name=$(basename $d)
        parts=(${dir_name//_/ })
        variation=${parts[0]}
        variable=${parts[1]}
        time=$(cat ${d}/${scenario}.err | grep 'End time of the simulation' | sed 's/^.*\: //')
        echo "${variation},${variable},${scenario},${time}" 
    done
done