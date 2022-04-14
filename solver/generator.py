#!/usr/bin/env python3
import yaml
import math
import random
from lxml import etree 
from io import StringIO

config_file = 'initial.yml'
platform_file = 'test.xml'
num_nodes = 2
num_sims = 1
num_steps = 1
compute_speed = 36.8
compute_speed_str = str(compute_speed) + 'Gf'
num_cores = 32
num_cores_str = str(num_cores)
read_bandwidth = 1000
read_bandwidth_str = str(read_bandwidth) + 'GBps'
write_bandwidth = 1000
write_bandwidth_str = str(write_bandwidth) + 'GBps'
disk_capacity = 50000
disk_capacity_str = str(disk_capacity) + 'GiB'
memory_capacity = 128
memory_capacity_str = str(memory_capacity) + 'GB'
mount_point = '/'
shared_bandwidth = 6
shared_bandwidth_str = str(shared_bandwidth) + 'GBps'
shared_latency = 0
shared_latency_str = str(shared_latency) + 'us'
loopback_bandwidth = 1000
loopback_bandwidth_str = str(loopback_bandwidth) + 'GBps'
loopback_latency = 0
loopback_latency_str = str(loopback_latency) + 'us' 

def config_generator(config_file):
    config = {}
    config['nodes'] = num_nodes
    config['cores'] = num_cores
    config['memory'] = memory_capacity
    config['bandwidth'] = shared_bandwidth
    config['speed'] = compute_speed
    config['steps'] = num_steps
    config['simulations'] = {}
    
    for i in range(1, num_sims+1):
        sim = 'sim' + str(i)
        config['simulations'][sim] = {}
        config['simulations'][sim]['flop'] = round(random.uniform(100, 1000), 3)
        config['simulations'][sim]['data'] = round(random.uniform(1, 10), 2)
        config['simulations'][sim]['mem'] = round(random.uniform(10, 60), 1)
        config['simulations'][sim]['coupling'] = {}
        config['simulations'][sim]['time_seq'] = config['simulations'][sim]['flop'] / config['speed']

        num_analyses = random.randint(1, 1)
        for j in range(1, num_analyses+1):
            ana = 'ana' + str(j)
            config['simulations'][sim]['coupling'][ana] = {}
            ana_config = config['simulations'][sim]['coupling'][ana]
            ana_config['flop'] = round(random.uniform(100, 1000), 3)
            ana_config['mem'] = round(random.uniform(10, 60), 1)
            ana_config['time_seq'] = ana_config['flop'] / config['speed']

    with open(config_file, 'w') as file:
        yaml.dump(config, file)

def platform_generator(platform_file):
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
    platform_generator(platform_file)
