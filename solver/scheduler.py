#!/usr/bin/env python3
import yaml
from sympy import solveset, S, Eq
from sympy.abc import x

if __name__ == "__main__":
    config_file = '../data/config.yml'
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    
    speed = config['speed']
    cores = config['cores']
    bandwidth = config['bandwidth']
    print(speed, bandwidth, cores)
    func_props = []
    time_sum = 0
    for sim in config['non-co-scheduling']:
        # print(sim)
        data_size = config['simulations'][sim]['data']
        for ana in config['non-co-scheduling'][sim]:
            ana_config = config['simulations'][sim]['coupling'][ana]
            time_seq = ana_config['flop']/speed
            time_sum += time_seq
            func_props.append((time_seq, data_size))
    
    equation = - 1/bandwidth
    for func_prop in func_props:
        print(func_prop)
        equation += func_prop[0]/(bandwidth * time_sum + x - cores * func_prop[1])
    print(solveset(equation, x, domain=S.Reals))