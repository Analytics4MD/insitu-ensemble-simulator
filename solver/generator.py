#!/usr/bin/env python3
import yaml
import math
import random
from lxml import etree 
from io import StringIO
import sys

# Name of generated config file
config_file = sys.argv[1]
# Name of generated platform file
platform_file = sys.argv[2]

# Ensemble settings
num_nodes = 2
num_simulations = 1
# num_analyses_per_simulation = random.randint(1, 3)
num_analyses_per_simulation = 2

# Applications' profile
num_steps = 100
# sim_flop = round(random.uniform(500, 1000), 3)
sim_flop = 5000.00 
# data_size = round(random.uniform(1, 10), 2)
data_size = 4
diff_flop = 0.5

# Plaform configurations
compute_speed = 36.8
num_cores = 128
read_bandwidth = 100
write_bandwidth = 100
disk_capacity = 50000
memory_capacity = 128
shared_bandwidth = 6
shared_latency = 0
loopback_bandwidth = 1000
loopback_latency = 0

compute_speed_str = str(compute_speed) + 'Gf'
num_cores_str = str(num_cores)
read_bandwidth_str = str(read_bandwidth) + 'GBps'
write_bandwidth_str = str(write_bandwidth) + 'GBps'
disk_capacity_str = str(disk_capacity) + 'GiB'
memory_capacity_str = str(memory_capacity) + 'GB'
mount_point = '/'
shared_bandwidth_str = str(shared_bandwidth) + 'GBps'
shared_latency_str = str(shared_latency) + 'us'
loopback_bandwidth_str = str(loopback_bandwidth) + 'GBps'
loopback_latency_str = str(loopback_latency) + 'us'

def config_generator(config_file):
    """
    Generate YAML file that contains general structure of ensemble
        
    Args:
        config_file: Name of output yaml config file

    Returns: 

    """ 
    config = {}
    config['nodes'] = num_nodes
    config['cores'] = num_cores
    config['memory'] = memory_capacity
    config['bandwidth'] = shared_bandwidth
    config['speed'] = compute_speed
    config['steps'] = num_steps
    config['simulations'] = {}
    
    for i in range(1, num_simulations + 1):
        sim = 'sim' + str(i)
        config['simulations'][sim] = {}
        config['simulations'][sim]['flop'] = sim_flop
        config['simulations'][sim]['data'] = data_size
        # config['simulations'][sim]['mem'] = round(random.uniform(10, 60), 1)
        config['simulations'][sim]['coupling'] = {}
        config['simulations'][sim]['time_seq'] = config['simulations'][sim]['flop'] / config['speed']

        for j in range(1, num_analyses_per_simulation + 1):
            ana = 'ana' + str(j)
            config['simulations'][sim]['coupling'][ana] = {}
            ana_config = config['simulations'][sim]['coupling'][ana]
            ana_config['flop'] = round(random.uniform((1-diff_flop)*sim_flop, (1+diff_flop)*sim_flop), 3)
            # ana_config['mem'] = round(random.uniform(10, 60), 1)
            ana_config['time_seq'] = ana_config['flop'] / config['speed']

    with open(config_file, 'w') as file:
        yaml.dump(config, file)

def platform_generator(platform_file):
    """
    Generate XML platform file
        
    Args:
        platform_file: Name of output xml platform file

    Returns: 

    """ 
    doctype_string = '<!DOCTYPE platform SYSTEM "https://simgrid.org/simgrid.dtd">'
    xml_header = '<?xml version="1.0"?>'
    xhtml = xml_header + doctype_string + '<platform version="4.1"></platform>'
    tree = etree.parse(StringIO(xhtml))
    platform = tree.getroot()
    etree.SubElement(platform, 'zone', id='AS0', routing='Full')
    zone = platform[0]
    track = 0
    etree.SubElement(zone, 'host', id='UserHost', speed=compute_speed_str, core='1')
    track += 1
    for i in range(1,num_nodes+1):
        etree.SubElement(zone, 'host', id='ComputeHost' + str(i), speed=compute_speed_str, core=num_cores_str)
        host = zone[track]
        etree.SubElement(host, 'disk', id='local_disk', read_bw=read_bandwidth_str, write_bw=write_bandwidth_str)
        disk = host[0]
        etree.SubElement(disk, 'prop', id='size', value=disk_capacity_str)
        etree.SubElement(disk, 'prop', id='mount', value=mount_point)
        etree.SubElement(host, 'prop', id='ram', value=memory_capacity_str)
        track += 1

    etree.SubElement(zone, 'link', id='shared_network', bandwidth=shared_bandwidth_str, latency=shared_latency_str)
    etree.SubElement(zone, 'link', id='loopback_network', bandwidth=loopback_bandwidth_str, latency=loopback_latency_str)
    track += 2
    for i in range(1,num_nodes+1):
        etree.SubElement(zone, 'route', src='UserHost', dst='ComputeHost' + str(i))
        route = zone[track]
        etree.SubElement(route, 'link_ctn', id='shared_network')
        track += 1
    
    for i in range(1,num_nodes+1):
        etree.SubElement(zone, 'route', src='ComputeHost' + str(i), dst='ComputeHost' + str(i))
        etree.SubElement(zone[track], 'link_ctn', id='loopback_network')
        track += 1
        for j in range(i+1, num_nodes+1):
            etree.SubElement(zone, 'route', src='ComputeHost' + str(i), dst='ComputeHost' + str(j))
            etree.SubElement(zone[track], 'link_ctn', id='shared_network')
            track += 1

    # Write platform file
    with open(platform_file, 'wb') as doc:
        # doc.write(etree.tostring(tree, pretty_print = True, xml_declaration=True, encoding='utf-8'))
        tree.write(doc, pretty_print=True, xml_declaration=True, encoding='utf-8')

if __name__ == "__main__":
    # Generate config file
    platform_generator(platform_file)
    # Generate platform file
    config_generator(config_file)
