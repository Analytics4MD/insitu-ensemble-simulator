#!/usr/bin/env bash
scenarios=( "ideal" "transit" "increasing0.25" "increasing0.5" "increasing0.75" "decreasing0.25" "decreasing0.5" "decreasing0.75" )
# scenarios=( "ideal" "transit" "increasing0.5" "decreasing0.5" )
heuristics=( "model" "even" )

function generate_statistics {
    echo "simulation,analysis,data,node,scenario,heuristic,time,model,model-bw,ideal-normalization,model-normalization"
    for d in $(ls -dq log_new/*/); do
        for scenario in "${scenarios[@]}"
        do
            dir_name=$(basename $d)
            parts=(${dir_name//./ })
            config=${parts[0]}
            trial=${parts[1]}
            parts=(${config//_/ })
            simulation=${parts[0]}
            analysis=${parts[1]}
            data=${parts[2]}
            node=${parts[3]}
            for node_heuristic in "${heuristics[@]}"
            do
                for core_heuristic in "${heuristics[@]}"
                do
                    time=$(cat ${d}/${scenario}_${node_heuristic}_${core_heuristic}.err | grep 'End time of the simulation' | sed 's/^.*\: //')
                    model=$(cat ${d}/${scenario}_${node_heuristic}_${core_heuristic}.conf | grep 'makespan:' | sed 's/^.*\: //')
                    model_bw=$(cat ${d}/${scenario}_${node_heuristic}_${core_heuristic}.conf | grep 'makespan_bw:' | sed 's/^.*\: //')
                    # echo ${model_bw}
                    base_scenario=$(cat ${d}/ideal_${node_heuristic}_${core_heuristic}.err | grep 'End time of the simulation' | sed 's/^.*\: //')
                    base_heuristic=$(cat ${d}/${scenario}_model_model.err | grep 'End time of the simulation' | sed 's/^.*\: //')
                    ratio_scenario=$(echo ${time}/${base_scenario} | bc -l)
                    ratio_heuristic=$(echo ${time}/${base_heuristic} | bc -l)
                    echo "${simulation},${analysis},${data},${node},${scenario},${node_heuristic}-${core_heuristic},${time},${model},${model_bw},${ratio_scenario},${ratio_heuristic}" 
                done
            done
        done
    done
}

function recompute_allocations {
    for d in $(ls -dq log/*/); do
        echo ${d}
        cp ../solver/scheduler.py ${d}
        cd ${d} 
        python3 scheduler.py config.yml
        cd ../..
    done
}

function generate_bw {
    echo "simulation,analysis,data,node,trial,scenario,heuristic,type,time,simulator-normalization"
    for d in $(ls -dq log_bw/*/); do
        for scenario in "${scenarios[@]}"
        do
            dir_name=$(basename $d)
            parts=(${dir_name//./ })
            config=${parts[0]}
            trial=${parts[1]}
            parts=(${config//_/ })
            simulation=${parts[0]}
            analysis=${parts[1]}
            data=${parts[2]}
            node=${parts[3]}
            for node_heuristic in "${heuristics[@]}"
            do
                for core_heuristic in "${heuristics[@]}"
                do
                    time=$(cat ${d}/${scenario}_${node_heuristic}_${core_heuristic}.err | grep 'End time of the simulation' | sed 's/^.*\: //')
                    model=$(cat ${d}/${scenario}_${node_heuristic}_${core_heuristic}.conf | grep 'makespan:' | sed 's/^.*\: //')
                    model_1=$(cat ${d}/${scenario}_${node_heuristic}_${core_heuristic}.conf | grep 'makespan_1:' | sed 's/^.*\: //')
                    model_2=$(cat ${d}/${scenario}_${node_heuristic}_${core_heuristic}.conf | grep 'makespan_2:' | sed 's/^.*\: //')
                    model_3=$(cat ${d}/${scenario}_${node_heuristic}_${core_heuristic}.conf | grep 'makespan_3:' | sed 's/^.*\: //')
                    ratio_model=$(echo ${time}/${model} | bc -l)
                    ratio_model_1=$(echo ${time}/${model_1} | bc -l)
                    ratio_model_2=$(echo ${time}/${model_2} | bc -l)
                    ratio_model_3=$(echo ${time}/${model_3} | bc -l)
                    echo "${simulation},${analysis},${data},${node},${trial},${scenario},${node_heuristic}-${core_heuristic},Simulator,${time},1.0" 
                    echo "${simulation},${analysis},${data},${node},${trial},${scenario},${node_heuristic}-${core_heuristic},Model(B),${model},${ratio_model}" 
                    echo "${simulation},${analysis},${data},${node},${trial},${scenario},${node_heuristic}-${core_heuristic},Model(B1),${model_1},${ratio_model_1}"
                    echo "${simulation},${analysis},${data},${node},${trial},${scenario},${node_heuristic}-${core_heuristic},Model(B2),${model_2},${ratio_model_2}" 
                    echo "${simulation},${analysis},${data},${node},${trial},${scenario},${node_heuristic}-${core_heuristic},Model(B3),${model_3},${ratio_model_3}" 
                done
            done
        done
    done
}

# recompute_allocations
# generate_statistics 
generate_bw