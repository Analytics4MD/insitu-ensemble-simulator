#!/usr/bin/env python3
import yaml
from sympy import solveset, S, Eq
from sympy.abc import x
import signal

def heuristic_round(number):
    return round(number)

if __name__ == "__main__":
    # Load yaml config file
    config_file = '../data/config.yml'
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    
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

    simulations_config = config['simulations']
    scheduling_config = config['non-co-scheduling']
    # allocations_config = config['allocations']

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
    print('Number of nodes for non-co-scheduling : {}'.format(nc_nodes))

    # Resource allocation for P^NC
    for sim in scheduling_config:
        data_size = simulations_config[sim]['data']
        for ana in scheduling_config[sim]:
            ana_config = simulations_config[sim]['coupling'][ana]
            core = bandwidth * cores * ana_config['time_seq']/(bandwidth * time_nc_sum + u - cores * data_size)
            ana_config['core_per_node'] = core

    # Heuristic to round n^{NC}
    round_nc_nodes = heuristic_round(nc_nodes)
    # round_nc_nodes = nc_nodes
    
    c_nodes = nodes - round_nc_nodes
    print('Number of nodes for co-scheduling : {} '.format(c_nodes))
    
    # Co-scheduling
    config['allocations'] = {}
    start_node = 0
    for sim in simulations_config:
        # print(sim)
        numerator = simulations_config[sim]['time_seq']
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            if ana not in scheduling_config[sim]:
                numerator += ana_config['time_seq']
    
        # Node allocation
        node = numerator * c_nodes / (time_s_sum + time_c_sum)
        config['allocations'][sim] = {}
        allocation_config = config['allocations'][sim] 
        config['allocations'][sim]['node'] = node
        allocation_config['start'] = start_node
        start_node += node
        allocation_config['end'] = start_node
        
        core = simulations_config[sim]['time_seq'] * cores / numerator
        simulations_config[sim]['core_per_node'] = core

        # Core allocation
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            if ana not in scheduling_config[sim]:
                core = ana_config['time_seq'] * cores / numerator
                ana_config['core_per_node'] = core

    # Need to fix start and end node when rounding heristic is finalized
    config['allocations']['sim0'] = {}
    config['allocations']['sim0']['node'] = round_nc_nodes
    config['allocations']['sim0']['start'] = start_node
    config['allocations']['sim0']['end'] = start_node + round_nc_nodes
    # print(config['allocations'])

    # Execution time and makespan
    makespan = float('-inf')
    for sim in simulations_config:
        time_s = simulations_config[sim]['time_seq'] / (config['allocations'][sim]['node'] * simulations_config[sim]['core_per_node'])
        simulations_config[sim]['time'] = time_s
        data_size = simulations_config[sim]['data']
        if time_s > makespan:
            makespan = time_s
        for ana in simulations_config[sim]['coupling']:
            ana_config = simulations_config[sim]['coupling'][ana]
            ana_alloc = ana_config['alloc']
            time_a = ana_config['time_seq'] / (config['allocations'][ana_alloc]['node'] * ana_config['core_per_node'])
            if ana_alloc == 'sim0':
                time_a +=  data_size / (config['allocations'][ana_alloc]['node'] * bandwidth)
            ana_config['time'] = time_a
            if time_a > makespan:
                makespan = time_a
    config['makespan'] = makespan * config['steps']

    # print(simulations_config)
    with open('result.yml', 'w') as output_file:
        yaml.dump(config, output_file)

    