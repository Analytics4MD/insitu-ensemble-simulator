#!/usr/bin/env python3
import yaml
from sympy import solveset, S, Eq
from sympy.abc import x
import signal
import math
import random

config_file = 'initial.yml'
num_sims = 3

if __name__ == "__main__":
    config = {}
    

    config['nodes'] = 10
    config['cores'] = 32
    config['memory'] = 128
    config['bandwidth'] = 6
    config['speed'] = 36.8
    config['steps'] = 1
    config['simulations'] = {}
    

    for i in range(1, num_sims+1):
        sim = 'sim' + str(i)
        config['simulations'][sim] = {}
        config['simulations'][sim]['flop'] = round(random.uniform(100, 1000), 3)
        config['simulations'][sim]['data'] = round(random.uniform(1, 10), 2)
        config['simulations'][sim]['mem'] = round(random.uniform(10, 60), 1)
        config['simulations'][sim]['coupling'] = {}
        config['simulations'][sim]['time_seq'] = config['simulations'][sim]['flop'] / config['speed']

        num_analyses = random.randint(0, 10)
        for j in range(1, num_analyses+1):
            ana = 'ana' + str(j)
            config['simulations'][sim]['coupling'][ana] = {}
            ana_config = config['simulations'][sim]['coupling'][ana]
            ana_config['flop'] = round(random.uniform(100, 1000), 3)
            ana_config['mem'] = round(random.uniform(10, 60), 1)
            ana_config['time_seq'] = ana_config['flop'] / config['speed']

    with open(config_file, 'w') as file:
        yaml.dump(config, file)

