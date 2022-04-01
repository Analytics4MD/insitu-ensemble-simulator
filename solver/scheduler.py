#!/usr/bin/env python3
import yaml
from sympy import solveset, S, Eq
from sympy.abc import x
import signal
import math

def round_up(number):
    return round(number+0.5)

def round_down(number):
    return round(number-0.5)

def heuristic_round(number):
    return round(number) 

# Load yaml config file
config_file = '../data/config.yml'
with open(config_file, 'r') as file:
    config = yaml.safe_load(file)

simulations_config = config['simulations']
scheduling_config = config['non-co-scheduling']
# allocations_config = config['allocations']

# Computational power per core (GFLOPs)
speed = config['speed']
# Number of cores per node
cores = config['cores']
# Memory bandwidth per node (GB/s)
bandwidth = config['bandwidth']
# Number of nodes
nodes = config['nodes']
print('Number of nodes : {}'.format(nodes))
print('Number of cores per node : {}'.format(cores))
print('Memory bandwidth per node (GB/s) : {}'.format(bandwidth))
print('Computational power per core (GFLOPs) : {}'.format(speed))

if __name__ == "__main__":

    func_props = {}
    # t(P^NC)
    time_nc_sum = 0
    # t(S)
    time_s_sum = 0
    # t(P^C)
    time_c_sum = 0
    
    # Compute t(S), t(P^C), t(P^NC)
    for sim in scheduling_config:
        # print(sim)
        time_s_seq = simulations_config[sim]['flop']/speed
        time_s_sum += time_s_seq
        simulations_config[sim]['time_seq'] = time_s_seq
        data_size = simulations_config[sim]['data']
        simulations_config[sim]['alloc'] = sim
        # print(config['non-co-scheduling'][sim])
        # print(config['simulations'][sim]['coupling'])

        temp = {}
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            time_a_seq = ana_config['flop']/speed
            ana_config['time_seq'] = time_a_seq
            if ana in scheduling_config[sim]:
                ana_config['alloc'] = 'sim0'
                time_nc_sum += time_a_seq
                temp[ana] = (time_a_seq, data_size)
            else:
                ana_config['alloc'] = sim
                time_c_sum += time_a_seq
        
        func_props[sim] = temp
    
    # print(func_props)
    # print(simulations_config)

    # Solve Equation 25
    equation = - 1/bandwidth
    for sim in scheduling_config:
        data_size = simulations_config[sim]['data']
        for ana in scheduling_config[sim]:
            ana_config = simulations_config[sim]['coupling'][ana]
            equation += ana_config['time_seq']/(bandwidth * time_nc_sum + x - cores * data_size)
    u_sol = solveset(equation, x, domain=S.Reals)
    print(u_sol)
    lu = list(u_sol.args)
    u = float(lu[-1])
    # print(type(u))
    print("U = {}".format(u))

    # Compute n^{NC}
    time_sum = time_s_sum + time_c_sum + time_nc_sum
    nc_nodes = nodes * (bandwidth * time_nc_sum + u) / (bandwidth * time_sum + u)
    
    # Heuristic to round n^{NC}
    round_nc_nodes = math.floor(nc_nodes)
    print('Number of nodes for non-co-scheduling : {} {}'.format(nc_nodes, round_nc_nodes))
    # round_nc_nodes = nc_nodes

    # Resource allocation for P^NC
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
            ana_config['time_nr'] = time_a 
    
    # Heuristic to round c^{NC}: Round up c_A of analyses A with greater t(A)  
    # Sort by analysis sequential time
    sorted_nc_seq_dict = sorted(nc_seq_dict.items(), key=lambda item: item[1])
    print(nc_seq_dict)
    print(sorted_nc_seq_dict)
    threshold = len(sorted_nc_seq_dict) - num_int_cores - cores + sum_core_rd
    print('Number of analyses whose cores are round up : {}'.format(threshold))
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
        ana_config['core_per_node'] = round_core
        # Compute execution time
        time_a = ana_config['time_seq'] / (round_nc_nodes * round_core)
        time_a +=  data_size / (round_nc_nodes * bandwidth)
        ana_config['time'] = time_a
        print(sim, ana, core, round_core, time_a)

    # Compute n^{C}
    c_nodes = nodes - round_nc_nodes
    print('Number of nodes for co-scheduling : {} '.format(c_nodes))
    
    # Co-scheduling
    config['allocations'] = {}
    start_node = 0
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

        # Node allocation
        node = numerator * c_nodes / (time_s_sum + time_c_sum)
        if node.is_integer():
            num_int_nodes += 1
        sum_c_nodes_rd += math.floor(node)
        config['allocations'][sim] = {}
        config['allocations'][sim]['node'] = node

    sorted_c_seq_dict = sorted(c_seq_dict.items(), key=lambda item: item[1])
    print(c_seq_dict)
    print(sorted_c_seq_dict)
    threshold = len(sorted_c_seq_dict) - num_int_nodes - c_nodes + sum_c_nodes_rd
    print(threshold)
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
        
        config['allocations'][sim]['node'] = round_node
        config['allocations'][sim]['node_nr'] = node
        print(sim, node, round_node)  

        num_int_cores = 0
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
                
        print(sim_seq_dict.items())
        sorted_sim_seq_dict = sorted(sim_seq_dict.items(), key=lambda item: item[1][0])
        print(sorted_sim_seq_dict)
        sub_threshold = len(sorted_sim_seq_dict) - num_int_cores - cores + sum_sim_rd 
        print(sub_threshold)
        for sim_ana, time_seq in sorted_sim_seq_dict:
            sim, ana = sim_ana.split('_')
            print(sim, ana)
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
            
            core_per_node['core_per_node'] = round_core
            core_per_node['time'] = core_per_node['time_seq'] / (config['allocations'][core_per_node['alloc']]['node'] * round_core)
            core_per_node['time_nrc'] = core_per_node['time_seq'] / (config['allocations'][core_per_node['alloc']]['node'] * core)
            core_per_node['time_nrnc'] = core_per_node['time_seq'] / (config['allocations'][core_per_node['alloc']]['node_nr'] * core)


    start_node = 0
    for sim in simulations_config:
        allocation_config = config['allocations'][sim]
        round_node = allocation_config['node']
        allocation_config['start'] = start_node
        start_node += round_node
        allocation_config['end'] = start_node - 1

    # Need to fix start and end node when rounding heristic is finalized
    config['allocations']['sim0'] = {}
    config['allocations']['sim0']['node'] = round_nc_nodes
    config['allocations']['sim0']['start'] = start_node
    config['allocations']['sim0']['end'] = start_node + round_nc_nodes - 1
    # print(config['allocations']) 
        

    

    # # Execution time and makespan
    makespan = float('-inf')
    for sim in simulations_config:
    #     time_s = simulations_config[sim]['time_seq'] / (config['allocations'][sim]['node'] * simulations_config[sim]['core_per_node'])
        time_s = simulations_config[sim]['time']
    #     data_size = simulations_config[sim]['data']
        if time_s > makespan:
            makespan = time_s
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
    #         ana_alloc = ana_config['alloc']
    #         time_a = ana_config['time_seq'] / (config['allocations'][ana_alloc]['node'] * ana_config['core_per_node'])
    #         if ana_alloc == 'sim0':
    #             time_a +=  data_size / (config['allocations'][ana_alloc]['node'] * bandwidth)
            time_a = ana_config['time']
            if time_a > makespan:
                makespan = time_a
    config['makespan'] = makespan * config['steps']

    # print(simulations_config)
    with open('result.yml', 'w') as output_file:
        yaml.dump(config, output_file)

    