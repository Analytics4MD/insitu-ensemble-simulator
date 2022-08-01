#!/usr/bin/env python3
import yaml
from sympy import solveset, S, Eq
from sympy.abc import x
import signal
import math
import random
import itertools
import sys

def heuristic_round(number):
    return round(number) 

# Load yaml config file
config_file = sys.argv[1]
output_file = 'result.yml'

with open(config_file, 'r') as file:
    config = yaml.safe_load(file)
simulations_config = config['simulations']
# Computational power per core (GFLOPs)
speed = config['speed']
# Number of cores per node
cores = config['cores']
# Memory bandwidth per node (GB/s)
bandwidth_global = config['bandwidth']
# Number of nodes
nodes = config['nodes']
# Memory capacity per node (GB)
mem = config['memory']
print('Number of nodes : {}'.format(nodes))
print('Number of cores per node : {}'.format(cores))
print('Memory bandwidth per node (GB/s) : {}'.format(bandwidth_global))
print('Computational power per core (GFLOPs) : {}'.format(speed))
print('Memory capacity per node (GB) : {}'.format(mem))

def sublist(l):  
    result = []  
    for i in range(0, len(l)+1):
        for subset in itertools.combinations(l, i):
            result.append(subset)
    return result

# ac = []
# for sim in simulations_config:
#     for ana in simulations_config[sim]['coupling']:
#         ac.append(sim + '_' + ana)
# sub_ac = sublist(ac)
# print(sub_ac) 
track = 0


def schedule(output_file, heuristic="increasing"):
    """
    Continuously co-schedules simulations and analyses following given heuristic.
        
    Args:
        output_file:
        heuristic: either 'increasing', 'decreasing', 'random', or 'brute-force'
    
    Returns: 
        True if it is feasible to continue co-scheduling
        False otherwise.

    """ 

    # with open(config_file, 'r') as file:
    #     config = yaml.safe_load(file)
    global track
    print(f'track: {track}')    
    # simulations_config = config['simulations']
    if 'unfeasible' not in config:
        config['unfeasible'] = []
        config['non-co-scheduling'] = {}
        for sim in simulations_config:
            config['non-co-scheduling'][sim] = []
    # print(simulations_config.keys())
    # if not config['unfeasible']:
    #     config['unfeasible'] = list(simulations_config.keys())
    else:
        if heuristic == 'brute-force': 
            # global track
            if track == len(sub_ac):
                print('sim0 has no feasible scheduling')
                return False
            # print(track, sub_ac[track])
            for sim in simulations_config:
                config['non-co-scheduling'][sim] = []
            for sim_ana in sub_ac[track]:
                sim, ana = sim_ana.split('_')
                config['non-co-scheduling'][sim].append(ana)
            
        else:
            if not config['unfeasible'] or config['unfeasible'] == ['sim0']:
                picked_sim = None
                picked_ana = None
                if heuristic == "increasing":
                    picked_flop = float('inf')
                elif heuristic == 'decreasing':
                    picked_flop = float('-inf')
                else:
                    picked_anas = []
                for sim in simulations_config:
                    for ana in simulations_config[sim]['coupling']:
                        if ana not in config['non-co-scheduling'][sim]:
                            ana_flop = simulations_config[sim]['coupling'][ana]['flop']
                            if heuristic == "increasing":
                                if ana_flop <= picked_flop:
                                    picked_sim = sim
                                    picked_ana = ana
                                    picked_flop = ana_flop
                            elif heuristic == "decreasing":
                                if ana_flop >= picked_flop:
                                    picked_sim = sim
                                    picked_ana = ana
                                    picked_flop = ana_flop
                            else:
                                picked_anas.append((sim, ana))
                
                if heuristic == "increasing" or heuristic == "decreasing":
                    if not picked_sim:
                        print(f'sim0 has no feasible scheduling')
                        return False
                else:
                    if not picked_anas:
                        print(f'sim0 has no feasible scheduling')
                        return False
                    (picked_sim, picked_ana) = random.choice(picked_anas)
                
                config['non-co-scheduling'][picked_sim].append(picked_ana)
            
            for sim in config['unfeasible']:
                if sim != 'sim0':
                    simulations_config[sim]['alloc'] = sim
                    if heuristic == 'increasing':
                        sorted_ana = sorted(simulations_config[sim]['coupling'].items(), key=lambda item: item[1]['flop'])
                    elif heuristic == 'decreasing':
                        sorted_ana = sorted(simulations_config[sim]['coupling'].items(), key=lambda item: item[1]['flop'], reverse=True)
                    else:
                        sorted_ana = list(simulations_config[sim]['coupling'].items())
                    # print(sorted_ana)
                    if not config['non-co-scheduling'][sim]:
                        config['non-co-scheduling'][sim] = []
                    subset_ana = [k for k, v in sorted_ana if k not in config['non-co-scheduling'][sim]]
                    if not subset_ana:
                        print(f'{sim} has no feasible scheduling')
                        return False
                    if heuristic == "random":
                        new_ana = random.choice(subset_ana)
                    else:
                        new_ana = subset_ana[0]
                    config['non-co-scheduling'][sim].append(new_ana)
    
    track += 1
    
    if output_file:
        with open(output_file, 'w') as file:
            yaml.dump(config, file)

    return True

def near_allocate(output_file):
    scheduling_config = config['non-co-scheduling']
    config['allocations'] = {}
    allocation_config = config['allocations']
    time_sum = 0
    time_nc_sum = 0
    
    for sim in simulations_config:
        allocation_config[sim] = {}
        time_s_seq = simulations_config[sim]['time_seq']
        time_sum += time_s_seq
        time_c_sum = time_s_seq
        simulations_config[sim]['alloc'] = sim
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            time_a_seq = ana_config['time_seq']
            if ana in scheduling_config[sim]:
                ana_config['alloc'] = 'sim0'
                time_nc_sum += time_a_seq
            else:
                ana_config['alloc'] = sim
                time_c_sum += time_a_seq
            time_sum += time_a_seq
        allocation_config[sim]['time_sum'] = time_c_sum
        print(time_c_sum)
    print(f'time_sum = {time_sum}')
    print(f'time_nc_sum = {time_nc_sum}')

    allocation_config['sim0'] = {}
    allocation_config['sim0']['time_sum'] = time_nc_sum
    allocation_config['sim0']['node'] = time_nc_sum * nodes / time_sum
    num_int_nodes = 0
    if allocation_config['sim0']['node'].is_integer():
        num_int_nodes += 1
    sum_node_rd = math.floor(allocation_config['sim0']['node'])
    for sim in simulations_config:
        time_s_seq = simulations_config[sim]['time_seq']
        time_c_sum = allocation_config[sim]['time_sum']
        simulations_config[sim]['core'] = time_s_seq * cores / time_c_sum
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            time_a_seq = ana_config['time_seq'] 
            if ana in scheduling_config[sim]:
                ana_config['core'] = time_a_seq * cores / time_nc_sum
            else:
                ana_config['core'] = time_a_seq * cores / time_c_sum
        node = time_c_sum * nodes / time_sum
        if node.is_integer():
            num_int_nodes += 1
        sum_node_rd += math.floor(node)
        allocation_config[sim]['node'] = node

    sorted_alloc = sorted(allocation_config.keys(), key=lambda item: allocation_config[item]['time_sum'])
    print(sorted_alloc)
    threshold = len(sorted_alloc) - num_int_nodes - nodes + sum_node_rd
    print(threshold)
    track = len(sorted_alloc) - 1
    for alloc in sorted_alloc:
        node = allocation_config[alloc]['node']
        if node.is_integer():
            round_node = int(node)
        else:
            if node < 1: 
                round_node = math.ceil(node)
            else:
                if threshold > 0:
                    if track > 0:
                        round_node = math.floor(node)
                        threshold -= 1
                    else:
                        round_node = math.floor(node) - threshold + 1
                        threshold = 0
                else:
                    round_node = math.ceil(node)
        allocation_config[alloc]['node'] = round_node
        allocation_config[alloc]['original_node'] = node
        track -= 1
    if threshold > 0:
        print(f'Not sufficient resource for node allocation')
        config['unfeasible'] = []
        return False

    for sim in simulations_config:
        c_dict = {}
        num_int_cores = 0
        c_dict[sim + '_'] = simulations_config[sim]['time_seq']
        core = simulations_config[sim]['core']
        if core.is_integer():
            num_int_cores += 1
        sum_core_rd = math.floor(core)
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            if ana not in scheduling_config[sim]:
                c_dict[sim + '_' + ana] = ana_config['time_seq']
                core = ana_config['core']
                if core.is_integer():
                    num_int_cores += 1
                sum_core_rd += math.floor(core)

        sorted_c_dict = sorted(c_dict.items(), key=lambda item: item[1])
        threshold = len(sorted_c_dict) - num_int_cores - cores + sum_core_rd
        print(threshold)
        track = len(sorted_c_dict) - 1
        for sim_ana, time_seq in sorted_c_dict:
            sim, ana = sim_ana.split('_')
            if ana:
                core_config = simulations_config[sim]['coupling'][ana]
            else:
                core_config = simulations_config[sim]
            core = core_config['core']
            if core.is_integer():
                round_core = int(core)
            else:
                if core < 1: 
                    round_core = math.ceil(core)
                else:
                    if threshold > 0:
                        if track > 0:
                            round_core = math.floor(core)
                            threshold -= 1
                        else:
                            round_core = math.floor(core) - threshold + 1
                            threshold = 0
                    else:
                        round_core = math.ceil(core)
            core_config['core'] = round_core
            core_config['original_core'] = core
            track -= 1
        if threshold > 0:
            print(f'Not sufficient resource for core allocation of {sim}')
            config['unfeasible'] = []
            return False
    
    nc_dict = {}
    num_int_cores = 0
    sum_core_rd = 0
    for sim in scheduling_config:
        for ana in scheduling_config[sim]:
            nc_dict[sim + '_' + ana] = simulations_config[sim]['coupling'][ana]['time_seq']
            core = simulations_config[sim]['coupling'][ana]['core']
            if core.is_integer():
                num_int_cores += 1
            sum_core_rd += math.floor(core)
    sorted_nc_dict = sorted(nc_dict.items(), key=lambda item: item[1])
    print(sorted_nc_dict)
    threshold = len(sorted_nc_dict) - num_int_cores - cores + sum_core_rd
    print(threshold)
    track = len(sorted_nc_dict) - 1
    for sim_ana, time_seq in sorted_nc_dict:
        sim, ana = sim_ana.split('_')
        core = simulations_config[sim]['coupling'][ana]['core']
        if core.is_integer():
            round_core = int(core)
        else:
            if core < 1: 
                round_core = math.ceil(core)
            else:
                if threshold > 0:
                    if track > 0:
                        round_core = math.floor(core)
                        threshold -= 1
                    else:
                        round_core = math.floor(core) - threshold + 1
                        threshold = 0
                else:
                    round_core = math.ceil(core)
        simulations_config[sim]['coupling'][ana]['core'] = round_core
        simulations_config[sim]['coupling'][ana]['original_core'] = core
        track -= 1
    if threshold > 0:
        print(f'Not sufficient resource for core allocation of sim0')
        config['unfeasible'] = []
        return False

    if output_file:
        with open(output_file, 'w') as out_file:
            yaml.dump(config, out_file)
    
    return True
        


def allocate(output_file, round_up=True, node_heuristic='model', core_heuristic='model'):
    """
    Compute the resource allocation for each simulation and analysis.
        
    Args:
        output_file:
        round_up:
        node_heuristic:
        core_heuristic:

    Returns: 
        True if it is feasible to compute integer resource allocation
        Otherwise, False.

    """ 

    # with open(config_file, 'r') as file:
    #     config = yaml.safe_load(file)

    # simulations_config = config['simulations']

    # # Computational power per core (GFLOPs)
    # speed = config['speed']
    # # Number of cores per node
    # cores = config['cores']
    # # Memory bandwidth per node (GB/s)
    # bandwidth = config['bandwidth']
    # # Number of nodes
    # nodes = config['nodes']
    # # print('Number of nodes : {}'.format(nodes))
    # # print('Number of cores per node : {}'.format(cores))
    # # print('Memory bandwidth per node (GB/s) : {}'.format(bandwidth))
    # # print('Computational power per core (GFLOPs) : {}'.format(speed))

    ideal_sched = True
    # if 'non-co-scheduling' not in config:
    #     ideal_sched = True
        # config['non-co-scheduling'] = {}
        # for sim in simulations_config:
        #     config['non-co-scheduling'][sim] = []

    scheduling_config = config['non-co-scheduling']
    # print(scheduling_config)
    for sim in scheduling_config:
        if len(scheduling_config[sim]):
            ideal_sched = False
            break 
    
    
    # t(P^NC)
    time_nc_sum = 0
    # t(S)
    time_s_sum = 0
    # t(P^C)
    time_c_sum = 0
    num_nc_anas = 0
    # Compute t(S), t(P^C), t(P^NC)
    for sim in scheduling_config:
        num_nc_anas += len(scheduling_config[sim])
        time_s_seq = simulations_config[sim]['time_seq']
        time_s_sum += time_s_seq
        simulations_config[sim]['alloc'] = sim

        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            time_a_seq = ana_config['time_seq'] 
            if ana in scheduling_config[sim]:
                ana_config['alloc'] = 'sim0'
                time_nc_sum += time_a_seq
            else:
                ana_config['alloc'] = sim
                time_c_sum += time_a_seq

    bandwidth = bandwidth_global
    num_sims = len(simulations_config.keys())
    round_nc_nodes = 0
    config['allocations'] = {}
    config['allocations']['sim0'] = {}
    if not ideal_sched:
        print('not ideal scheduling')
        bandwidths = {}
        bandwidths[1] = bandwidth / num_nc_anas
        bandwidths[2] = bandwidth * (time_s_sum + time_c_sum + time_nc_sum) / (time_nc_sum * nodes)
        bandwidths[3] = bandwidth * (time_s_sum + time_c_sum + time_nc_sum) / (time_nc_sum * nodes * num_nc_anas)
        # bandwidth = bandwidth_global * (time_s_sum + time_c_sum + time_nc_sum) / (time_nc_sum * nodes * num_nc_anas) 
        # Solve Equation 25
        equation = - 1/bandwidth
        for sim in scheduling_config:
            data_size = simulations_config[sim]['data']
            for ana in scheduling_config[sim]:
                ana_config = simulations_config[sim]['coupling'][ana]
                equation += ana_config['time_seq']/(bandwidth * time_nc_sum + x - cores * data_size)
        u_sol = solveset(equation, x, domain=S.Reals)
        # print(u_sol)
        lu = list(u_sol.args)
        u = float(lu[-1])
        # print("U = {}".format(u))
        if node_heuristic == 'model':
            # Compute n^{NC}
            time_sum = time_s_sum + time_c_sum + time_nc_sum
            nc_nodes = nodes * (bandwidth * time_nc_sum + u) / (bandwidth * time_sum + u)
            config['allocations']['sim0']['node_nr'] = nc_nodes
            round_nc_nodes = math.ceil(nc_nodes)
            if nc_nodes > nodes-1:
                print(f'Cannot round up num_nodes for non-co-scheduling to {nodes}')
                round_nc_nodes = math.floor(nc_nodes)
            else:
                if nc_nodes < 1:
                    print(f'Cannot round down num_nodes for non-co-scheduling to 0')
                else:
                    diff_up = max((time_s_sum + time_c_sum) / (nodes - math.ceil(nc_nodes)), (bandwidth * time_nc_sum + u) / (bandwidth * math.ceil(nc_nodes)))
                    # print(f'diff_up = {diff_up}')
                    diff_down = max((time_s_sum + time_c_sum) / (nodes - math.floor(nc_nodes)), (bandwidth * time_nc_sum + u) / (bandwidth * math.floor(nc_nodes)))
                    # print(f'diff_down = {diff_down}')
                    if diff_down < diff_up:
                        round_nc_nodes = math.floor(nc_nodes)
            
            # # Heuristic to round n^{NC}
            # if round_up:
            #     round_nc_nodes = math.ceil(nc_nodes)
            # else:
            #     if nc_nodes < 1:
            #         print(f'Cannot round down num_nodes for non-co-scheduling to 0')
            #         config['unfeasible'] = []
            #         with open(output_file, 'w') as file:
            #             yaml.dump(config, file)
            #         return False 
            #     round_nc_nodes = math.floor(nc_nodes)
            # print(f'nc_nodes = {nc_nodes}')
        else:
            even_nodes = nodes / (num_sims + 1)
            # print(f'even_nodes = {even_nodes}')
            round_nc_nodes = nodes - math.floor(even_nodes) * num_sims

        # print(f'round_nc_nodes = {round_nc_nodes}')
        if nodes - round_nc_nodes < num_sims:
            # We probably might want to return False here
            print(f'Number of nodes for co-scheduling cannot be less than the number of simulations')
            round_nc_nodes = nodes - num_sims

        # Resource allocation for P^NC
        if core_heuristic == 'model':
            nc_seq_dict = {}
            sum_core_rd = 0
            num_int_cores = 0
            for sim in scheduling_config:
                data_size = simulations_config[sim]['data']
                for ana in scheduling_config[sim]:
                    ana_config = simulations_config[sim]['coupling'][ana]
                    core = bandwidth * cores * ana_config['time_seq']/(bandwidth * time_nc_sum + u - cores * data_size)
                    nc_seq_dict[sim + '_' + ana] = ana_config['time_seq']
                    if core.is_integer():
                        num_int_cores += 1
                    sum_core_rd += math.floor(core)
                    ana_config['core_per_node'] = core
                    time_a = ana_config['time_seq'] / (round_nc_nodes * core)
                    time_a +=  data_size / (round_nc_nodes * bandwidth)
                    # ana_config['time_nr'] = time_a 
            
            # Heuristic to round c^{NC}: Round up c_A of analyses A with greater t(A)  
            # Sort by analysis sequential time
            sorted_nc_seq_dict = sorted(nc_seq_dict.items(), key=lambda item: item[1])
            # print(nc_seq_dict)
            # print(sorted_nc_seq_dict)
            threshold = len(sorted_nc_seq_dict) - num_int_cores - cores + sum_core_rd
            # print('Number of analyses whose cores are round up : {}'.format(threshold))
            # sum_cores = 0
            for sim_ana, time_seq in sorted_nc_seq_dict:
                sim, ana = sim_ana.split('_')
                ana_config = simulations_config[sim]['coupling'][ana]
                core = ana_config['core_per_node']
                if core.is_integer():
                    round_core = int(core)
                else:
                    if core < 1: 
                        round_core = math.ceil(core)
                    else:
                        if threshold > 0:
                            round_core = math.floor(core)
                            threshold -= 1
                        else:
                            round_core = math.ceil(core)
                # sum_cores += round_core
                ana_config['core_per_node'] = round_core
                ana_config['core_per_node_nr'] = core
                # Compute execution time
                time_a = ana_config['time_seq'] / (round_nc_nodes * round_core)
                ana_config['time'] = time_a + data_size / (round_nc_nodes * bandwidth)
                for k in bandwidths: 
                    # bandwidth_bw = bandwidth * (time_s_sum + time_c_sum + time_nc_sum) / (time_nc_sum * nodes * num_nc_anas)
                    ana_config['time_' + str(k)] = time_a + data_size / (round_nc_nodes * bandwidths[k] )
                # print(sim, ana, core, round_core, time_a)
            # print(f'Sum of cores : {sum_cores}')
            if threshold > 0:
                print(f'Not sufficient resource for core allocation in non-co-scheduling')
                config['unfeasible'] = []
                # with open(output_file, 'w') as file:
                #     yaml.dump(config, file)
                return False
        else:
            num_nc_anas = 0
            for sim in scheduling_config:
                num_nc_anas += len(scheduling_config[sim])
            even_cores = math.floor(cores / num_nc_anas)
            num_anas_ru = cores - even_cores * num_nc_anas
            num_anas_rd = num_nc_anas - num_anas_ru
            for sim in scheduling_config:
                data_size = simulations_config[sim]['data']
                for ana in scheduling_config[sim]:
                    ana_config = simulations_config[sim]['coupling'][ana]
                    if num_anas_rd > 0:
                        ana_config['core_per_node'] = even_cores
                        num_anas_rd -= 1
                    else: 
                        ana_config['core_per_node'] = even_cores + 1
                    time_a = ana_config['time_seq'] / (round_nc_nodes * ana_config['core_per_node'])
                    ana_config['time'] = time_a + data_size / (round_nc_nodes * bandwidth)
                    for k in bandwidths:
                        # bandwidth_bw = bandwidth * (time_s_sum + time_c_sum + time_nc_sum) / (time_nc_sum * nodes * num_nc_anas)
                        ana_config['time_' + str(k)] = time_a + data_size / (round_nc_nodes * bandwidths[k] )

            

    print('Number of nodes for non-co-scheduling : {}'.format(round_nc_nodes))
    # round_nc_nodes = nc_nodes
    # Compute n^{C}
    c_nodes = nodes - round_nc_nodes
    print('Number of nodes for co-scheduling : {} '.format(c_nodes))
    if c_nodes < 1:
        print(f'Cannot assign zero node for co-scheduling')
        config['unfeasible'] = []
        # with open(output_file, 'w') as file:
        #     yaml.dump(config, file)
        return False
        
    # Co-scheduling
    
    if node_heuristic == 'model':
        c_seq_dict = {}
        sum_c_nodes_rd = 0
        num_int_nodes = 0
        for sim in simulations_config:
            # print(sim)
            numerator = simulations_config[sim]['time_seq']
            for ana in simulations_config[sim]['coupling']:
                ana_config = simulations_config[sim]['coupling'][ana]
                if ana not in scheduling_config[sim]:
                    numerator += ana_config['time_seq']
            c_seq_dict[sim] = numerator
            simulations_config[sim]['time_sum'] = numerator
            # Node allocation
            node = numerator * c_nodes / (time_s_sum + time_c_sum)
            if node.is_integer():
                num_int_nodes += 1
            sum_c_nodes_rd += math.floor(node)
            config['allocations'][sim] = {}
            config['allocations'][sim]['node'] = node

        sorted_c_seq_dict = sorted(c_seq_dict.items(), key=lambda item: item[1])
        # print(c_seq_dict)
        # print(sorted_c_seq_dict)
        threshold = len(sorted_c_seq_dict) - num_int_nodes - c_nodes + sum_c_nodes_rd
        # print(threshold)
        # sum_nodes = 0
        for sim, numerator in sorted_c_seq_dict:
            node = config['allocations'][sim]['node']
            if node.is_integer():
                round_node = int(node)
            else: 
                if node < 1:
                    round_node = math.ceil(node)
                else:
                    if threshold > 0:
                        round_node = math.floor(node)
                        threshold -= 1
                    else:
                        round_node = math.ceil(node)
            # sum_nodes += round_node
            config['allocations'][sim]['node'] = round_node
            config['allocations'][sim]['node_nr'] = node
            # config['allocations'][sim]['node_nr'] = node
            # print(sim, node, round_node)  
        # print('Sum of nodes: {}'.format(sum_nodes))
        if threshold > 0:
            print(f'Not sufficient resource for node allocation in co-scheduling')
            config['unfeasible'] = []
            # with open(output_file, 'w') as file:
            #     yaml.dump(config, file)
            return False
    else:
        # node_heuristic == 'even'
        even_nodes = math.floor(c_nodes / num_sims)
        num_allocs_ru = c_nodes - even_nodes * num_sims
        num_allocs_rd = num_sims - num_allocs_ru
        for sim in simulations_config:
            config['allocations'][sim] = {}
            if num_allocs_rd > 0:
                config['allocations'][sim]['node'] = even_nodes
                num_allocs_rd -= 1
            else:
                config['allocations'][sim]['node'] = even_nodes + 1

    if core_heuristic == 'model':
        for sim in simulations_config:
            num_int_cores = 0
            numerator = simulations_config[sim]['time_sum']
            core = simulations_config[sim]['time_seq'] * cores / numerator
            simulations_config[sim]['core_per_node'] = core
            if core.is_integer():
                num_int_cores += 1
            sim_seq_dict = {}
            sim_seq_dict[sim + '_'] = (simulations_config[sim]['time_seq'],core)
            # Core allocation
            sum_sim_rd = math.floor(core)
            for ana in simulations_config[sim]['coupling']:
                ana_config = simulations_config[sim]['coupling'][ana]
                if ana not in scheduling_config[sim]:
                    core = ana_config['time_seq'] * cores / numerator
                    if core.is_integer():
                        num_int_cores += 1
                    sum_sim_rd += math.floor(core)
                    ana_config['core_per_node'] = core
                    sim_seq_dict[sim + '_' + ana] = (ana_config['time_seq'],core)
                    
            # print(sim_seq_dict.items())
            sorted_sim_seq_dict = sorted(sim_seq_dict.items(), key=lambda item: item[1][0])
            # print(sorted_sim_seq_dict)
            sub_threshold = len(sorted_sim_seq_dict) - num_int_cores - cores + sum_sim_rd 
            # print(sub_threshold)
            # sum_sub_cores = 0
            for sim_ana, time_seq in sorted_sim_seq_dict:
                sim, ana = sim_ana.split('_')
                # print(sim, ana)
                core = time_seq[1]
                if not ana:
                    core_per_node = simulations_config[sim] 
                    # core = simulations_config[sim]['core_per_node']
                else:
                    core_per_node = simulations_config[sim]['coupling'][ana]
                    # core = simulations_config[sim]['coupling'][ana]['core_per_node']
                if core.is_integer():
                    round_core = int(core)
                else:
                    if core < 1:
                        round_core = math.ceil(core)
                    else:
                        if sub_threshold > 0:
                            round_core = math.floor(core)
                            sub_threshold -= 1
                        else:   
                            round_core = math.ceil(core)
                # print(sub_threshold)
                
                # sum_sub_cores += round_core
                core_per_node['core_per_node'] = round_core
                core_per_node['core_per_node_nr'] = core
                core_per_node['time'] = core_per_node['time_seq'] / (config['allocations'][core_per_node['alloc']]['node'] * round_core)
                # core_per_node['time_nrc'] = core_per_node['time_seq'] / (config['allocations'][core_per_node['alloc']]['node'] * core)
                # core_per_node['time_nrnc'] = core_per_node['time_seq'] / (config['allocations'][core_per_node['alloc']]['node_nr'] * core)
            # print(f'Sum of cores of allocation {sim}: {sum_sub_cores}')
            if sub_threshold > 0:
                print(f'Not sufficient resource for core allocations in co-scheduling')
                config['unfeasible'] = []
                # with open(output_file, 'w') as file:
                #     yaml.dump(config, file)
                return False
    else:
        # core_heuristic == 'even'
        for sim in simulations_config:
            num_comps = 1 + len(simulations_config[sim]['coupling'].keys()) - len(scheduling_config[sim])
            # print(f'num_comps of {sim} = {num_comps}')
            even_cores = math.floor(cores / num_comps)
            num_comps_ru = cores - even_cores * num_comps
            num_comps_rd = num_comps - num_comps_ru - 1
            simulations_config[sim]['core_per_node'] = even_cores
            simulations_config[sim]['time'] = simulations_config[sim]['time_seq'] / (config['allocations'][sim]['node'] * even_cores)
            for ana in simulations_config[sim]['coupling']:
                ana_config = simulations_config[sim]['coupling'][ana]
                if ana not in scheduling_config[sim]:
                    if num_comps_rd > 0:
                        ana_config['core_per_node'] = even_cores
                        num_comps_rd -= 1
                    else:
                        ana_config['core_per_node'] = even_cores + 1
                    ana_config['time'] = ana_config['time_seq'] / (config['allocations'][ana_config['alloc']]['node'] * ana_config['core_per_node'])

    start_node = 0
    for sim in simulations_config:
        allocation_config = config['allocations'][sim]
        round_node = allocation_config['node']
        if round_node > 0:
            allocation_config['start'] = start_node
            start_node += round_node
            allocation_config['end'] = start_node - 1

    # Need to fix start and end node when rounding heristic is finalized
    # config['allocations']['sim0'] = {}
    config['allocations']['sim0']['node'] = round_nc_nodes
    if round_nc_nodes > 0:
        config['allocations']['sim0']['start'] = start_node
        config['allocations']['sim0']['end'] = start_node + round_nc_nodes - 1

    # # Execution time and makespan
    makespan = float('-inf')
    makespans = {k:float('-inf') for k in [1,2,3]}
    for sim in simulations_config:
    #     time_s = simulations_config[sim]['time_seq'] / (config['allocations'][sim]['node'] * simulations_config[sim]['core_per_node'])
        time_s = simulations_config[sim]['time']
    #     data_size = simulations_config[sim]['data']
        if time_s > makespan:
            makespan = time_s
        for k in makespans:
            if time_s > makespans[k]:
                makespans[k] = time_s
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
    #         ana_alloc = ana_config['alloc']
    #         time_a = ana_config['time_seq'] / (config['allocations'][ana_alloc]['node'] * ana_config['core_per_node'])
    #         if ana_alloc == 'sim0':
    #             time_a +=  data_size / (config['allocations'][ana_alloc]['node'] * bandwidth)
            time_a = ana_config['time']
            if time_a > makespan:
                makespan = time_a
            for k in makespans:
                if 'time_' + str(k) in ana_config:
                    time_a = ana_config['time_' + str(k)]
                if time_a > makespans[k]:
                    makespans[k] = time_a
            
    config['makespan'] = makespan * config['steps']
    for k in makespans:
        config['makespan_' + str(k)] = makespans[k] * config['steps']

    # print(simulations_config)
    if output_file:
        with open(output_file, 'w') as out_file:
            yaml.dump(config, out_file)
    
    return True

def feasible(output_file): 
    """
    Returns: list of co-scheduling allocations that cannot be sustained

    Check whether a resource allocation is feasible
        
    Parameter config_file:
    Parameter output_file:
    """ 

    # with open(config_file, 'r') as file:
    #     config = yaml.safe_load(file)
    # simulations_config = config['simulations']
    scheduling_config = config['non-co-scheduling']
    allocations_config = config['allocations']
    # mem = config['memory']

    # Check if the configuration is feasible  
    uf_allocs = []
    mem_remain_nc = allocations_config['sim0']['node'] * mem
    for sim in simulations_config:
        
        sim_alloc = simulations_config[sim]['alloc']
        node = allocations_config[sim_alloc]['node']
        mem_remain_c = mem * node - simulations_config[sim]['mem']
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            if ana_config['alloc'] == sim_alloc:
                mem_remain_c -= ana_config['mem']
            else:
                mem_remain_nc -= ana_config['mem']
        if mem_remain_c < 0:
            uf_allocs.append(sim)
    if mem_remain_nc < 0:
        uf_allocs.append('sim0')

    config['unfeasible'] = uf_allocs
    if output_file:
        with open(output_file, 'w') as file:
            yaml.dump(config, file)
    
    print(uf_allocs)
    return uf_allocs, config['makespan']

def heuristic(heuristic='increasing'):
    """
    Perform co-scheduling various heuristics. From schedule -> allocate -> feasible
        
    Parameter heuristic: either 'increasing' or 'decreasing' or 'random' or 'brute-force'
    """

    k = 1
    output_fn = 'log.schedule' + str(k)  
    min_makespan = float('inf')
    count = 1
    while True :
        # print(f'schedule : {input_fn} -> {output_fn}')
        if not schedule(None, heuristic):
            print(f'Not able to schedule further')
            break

        output_fn = 'log.allocate' + str(k)
        # print(f'allocate {method}: {input_fn} -> {output_fn}')
        if allocate(None):
            # print(f'feasible: ')
            unfeasible, makespan = feasible(None)
            if not unfeasible:
                print(f'Schedule is feasible, makespan: {makespan}')
                with open('log.' + heuristic + str(count), 'w') as file:
                    yaml.dump(config, file)
                count += 1
                if makespan < min_makespan:
                    min_makespan = makespan
                # break

        k += 1
        output_fn = 'log.schedule' + str(k)
        print('\n')

    print(f'Minimal makespan: {min_makespan}')  

def test(cosched_config):
    """
    Test
    """
    config['non-co-scheduling'] = cosched_config

    if allocate(None, None):
        # print(f'feasible: ')
        unfeasible, makespan = feasible(None, None)
        if not unfeasible:
            print(f'Schedule is feasible, makespan: {makespan}')
            with open('log.test', 'w') as file:
                yaml.dump(config, file)

def coschedule(scenario='ideal', ratio=None, heuristics=['model'], near=False):
    """
    Generate full configurations for a co-scheduling scenario
        
    Args:
        scenario:
        ratio:
        heuristics:
        near:

    Returns: 

    """ 

    config['non-co-scheduling'] = {}
    for sim in simulations_config:
        config['non-co-scheduling'][sim] = []
    if scenario != 'ideal':
        if (scenario == 'increasing' or scenario == 'decreasing') and ratio is None:
            print(f'Please specify the ratio for {scenario}')
            return    
        anas = []
        for sim in simulations_config:
            for ana in simulations_config[sim]['coupling']:
                ana_config = simulations_config[sim]['coupling'][ana]
                anas.append((sim, ana))
        # print(anas)
        if scenario == 'transit':
            picked_anas = anas
        if scenario == 'increasing':
            k = int(len(anas) * float(ratio))
            picked_anas = sorted(anas, key=lambda x: simulations_config[x[0]]['coupling'][x[1]]['flop'])[:k]
            
        if scenario == 'decreasing':
            k = int(len(anas) * float(ratio))
            picked_anas = sorted(anas, key=lambda x: simulations_config[x[0]]['coupling'][x[1]]['flop'], reverse=True)[:k]
        
        for sim,ana in picked_anas:
            config['non-co-scheduling'][sim].append(ana)

    output_file = scenario
    if ratio: 
        output_file += ratio
    # heuristics = ['model','even']
    for node_heuristic in heuristics:
        for core_heuristic in heuristics:
            print(f'node_heuristic = {node_heuristic}, core_heuristic = {core_heuristic}')
            if allocate(f'{output_file}_{node_heuristic}_{core_heuristic}.conf', node_heuristic=node_heuristic, core_heuristic=core_heuristic):
                print('Feasible to allocate')
                print(f'Makespan: {config["makespan"]}')
                # with open(output_file, 'w') as file:
                #     yaml.dump(config, file)
            if near:
                output_file += 'near'
                if near_allocate(output_file + '.conf'):
                    print(f'Feasible to near allocate')

def schedule():
    """
    Schedule various co-scheduling scenarios
        
    Args: 

    Returns: 

    """ 
    scenarios = ['ideal', 'increasing', 'decreasing', 'transit']
    ratios = [0.25, 0.5, 0.75]
    heuristics = ['model', 'even']
    for scenario in scenarios:
        if scenario in ['increasing', 'decreasing']:
            for ratio in ratios:
                print(f'{scenario} {ratio}')
                coschedule(scenario, ratio, heuristics=heuristics)
        else:
            print(f'{scenario}')
            coschedule(scenario, heuristics=heuristics)
    print('\n')

if __name__ == "__main__":
    # schedule
    if len(sys.argv) == 3:
        coschedule(sys.argv[2])
    elif len(sys.argv) == 4:
        coschedule(sys.argv[2], sys.argv[3])
    else:
        print('python3 scheduler.py <config yaml> <scenario> <ratio> (optional)>')
        sys.exit()
    
