#!/usr/bin/env python3
from lxml import etree 
from io import StringIO

if __name__ == "__main__":
    platform_file = 'test.xml'
    doctype_string = '<!DOCTYPE platform SYSTEM "https://simgrid.org/simgrid.dtd">'
    xml_header = '<?xml version="1.0"?>'
    xhtml = xml_header + doctype_string + '<platform version="4.1"></platform>'
    tree = etree.parse(StringIO(xhtml))
    platform = tree.getroot()
    etree.SubElement(platform, 'zone', id='AS0', routing='Full')
    zone = platform[0]
    etree.SubElement(zone, 'host', id='UserHost', speed='36.8Gf', core='1')
    print(zone.tag)
    print(etree.tostring(tree, pretty_print=True).decode("utf-8"))
    with open(platform_file, 'wb') as doc:
        # doc.write(etree.tostring(tree, pretty_print = True, xml_declaration=True, encoding='utf-8'))
        tree.write(doc, pretty_print=True, xml_declaration=True, encoding='utf-8')