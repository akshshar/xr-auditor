#!/usr/bin/env python

from lxml import etree
import pdb
import xmltodict as xd
import ast, json
from pprint import pprint
import sys
def validate(xml_path, xsd_path):

    xmlschema_doc = etree.parse(xsd_path)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    xml_doc = etree.parse(xml_path)
    result = xmlschema.validate(xml_doc)

    return result


def dumpxsd(xsd_path):
    xmlschema_doc = etree.parse(xsd_path)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    print xmlschema

if validate("XR-LXC.xml", "compliance.xsd"):
    print('Valid! :)')
else:
    print('Not valid! :(')


with open('XR-LXC.xml','r') as f:
    xsd_dict_raw = xd.parse(f)
    xsd_dict = ast.literal_eval(json.dumps(xsd_dict_raw)) 


print pprint(xsd_dict)

sys.exit(0)
general_fields= []

for element in xsd_dict["xs:schema"]["xs:element"]:
    try:
        if "xs:complexType" in element.keys():
            if element["@name"] == "GENERAL":
                general_fields_dict = element["xs:complexType"]["xs:sequence"]["xs:element"]
                for field in general_fields_dict:
                   general_fields.append(field["@ref"]) 
    except:
        continue


pdb.set_trace()
print general_fields 
