#!/usr/bin/env python
"""
  author: akshshar@cisco.com

  audit_helper.py

  Audit Helper library for Python on IOS-XR

  Copyright (c) 2018 by Cisco Systems, Inc.
  All rights reserved.

"""

from ztp_helper import ZtpHelpers
import subprocess, posixpath
import datetime, os, re
import glob
import yaml
from lxml import etree
import pdb
import xmltodict as xd
import ast, json
from pprint import pprint
import logging, logging.handlers


class AuditHelpers(ZtpHelpers):

    def __init__(self, 
                 compliance_xsd=None,
                 compliance_cfg=None):

        self.setup_syslog()
        self.setup_debug_logger()
        self.debug = False

        if compliance_xsd is None:
            self.syslogger.info("No Compliance xsd file - compliance_xsd provided, aborting")
            return None


        if compliance_cfg is None:
            self.syslogger.info("No Compliance config file - compliance_cfg provided, aborting")
            return None

 
        self.compliance_xsd = compliance_xsd
        self.compliance_xsd_dict = {}
        self.compliance_cfg = compliance_cfg
        self.compliance_cfg_dict = {}
        self.compliance_xsd_dict = self.xsd_to_dict()
        self.compliance_cfg_dict = self.yaml_to_dict()

        self.calendar_months = {'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04',
                                'May':'05', 'Jun':'06', 'Jul':'07', 'Aug':'08',
                                'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}



    def toggle_debug(self, enable):
        """Enable/disable debug logging
           :param enable: Enable/Disable flag 
           :type enable: int
        """
        if enable:
            self.debug = True
            self.logger.propagate = True
        else:
            self.debug = False
            self.logger.propagate = False


    def setup_debug_logger(self):
        """Setup the debug logger to throw debugs to stdout/stderr 
        """

        logger = logging.getLogger('DebugZTPLogger')
        logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        self.logger = logger


    def setup_syslog(self):
        """Setup up the Syslog logger for remote or local operation
        """


        logger = logging.getLogger('ZTPLogger')
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter('Python: { "loggerName":"%(name)s", "asciTime":"%(asctime)s", "pathName":"%(pathname)s", "logRecordCreationTime":"%(created)f", "functionName":"%(funcName)s", "levelNo":"%(levelno)s", "lineNo":"%(lineno)d", "time":"%(msecs)d", "levelName":"%(levelname)s", "message":"%(message)s"}')

        MAX_SIZE = 1024*1024
        LOG_PATH = "/tmp/ztp_python.log"
        handler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=MAX_SIZE, backupCount=1)
        handler.formatter = formatter
        logger.addHandler(handler)

        self.syslogger = logger



    def run_bash(self, cmd=None):
        """User defined method in Child Class
           Wrapper method for basic subprocess.Popen to execute 
           bash commands on IOS-XR.
           :param cmd: bash command to be executed in XR linux shell. 
           :type cmd: str 
           
           :return: Return a dictionary with status and output
                    { 'status': '0 or non-zero', 
                      'output': 'output from bash cmd' }
           :rtype: dict
        """

        print "cmd is"
        print cmd

        ## In XR the default shell is bash, hence the name
        if cmd is not None:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            out, err = process.communicate()
        else:
            self.syslogger.info("No bash command provided")


        status = process.returncode

        return {"status" : status, "output" : out}



    def validate_xml(xml_path, xsd_path):

        try:
            xmlschema_doc = etree.parse(xsd_path)
            xmlschema = etree.XMLSchema(xmlschema_doc)
            xml_doc = etree.parse(xml_path)
            result = xmlschema.validate(xml_doc)
        except Exception as e:
            self.syslogger.info("Failed to parse generated XML against compliance xml schema")
            self.syslogger.info("Error is %s" % e) 
        return result

   
    def xsd_to_dict(self):
        xsd_dict = {}
        try:
            with open(self.compliance_xsd,'r') as f:
                xsd_dict_raw = xd.parse(f)
                xsd_dict = ast.literal_eval(json.dumps(xsd_dict_raw))
        except Exception as e:
            self.syslogger.info("Failed to parse compliance xsd file")
            self.syslogger.info("Error is %s" % e)
            return {}

        if self.debug:
            self.logger.debug(xsd_dict)

        return xsd_dict

    def yaml_to_dict(self):
        yaml_dict = {}
        try:
            with open(self.compliance_cfg, 'r') as stream:
                try:
                    yaml_dict = yaml.load(stream)
                except yaml.YAMLError as e:
                    self.syslogger.info("Failed to parse YAML file, Error: %s" % e)
        except Exception as e:
            self.syslogger.info("Failed to open compliance config YAML file")
            self.syslogger.info("Error is %s" % e)
            
        if self.debug:
            self.logger.debug(yaml_dict)

        return yaml_dict


    def gather_general_data(self):
        general_fields= []
        general_fields_dict = {}

        for element in self.compliance_xsd_dict["xs:schema"]["xs:element"]:
            try:
                if "xs:complexType" in element.keys():
                    if element["@name"] == "GENERAL":
                        general_fields_dict = element["xs:complexType"]["xs:all"]["xs:element"]
                for field in general_fields_dict:
                   general_fields.append(field["@ref"])
            except Exception as e:
                self.syslogger.info("Failed to gather General fields from the compliance file")
                self.syslogger.info("Error is: "+e)

        general_data_dict = {}

        for field in general_fields:
            value = self.get_general_field(field)
            general_data_dict[field] = value
       
        return general_data_dict 


    def get_checksum(self, filename):
        try:
            result = self.run_bash(cmd="md5sum "+filename)
            if not result["status"]:
                return result["output"].split(' ')[0]
            else:
                return ""
        except Exception as e:
            self.syslogger.info("Failed to md5 checksum of file "+filename)
            self.syslogger.info("Error is: "+e) 
            return "" 

    def get_file_content(self, filename):
        try:
            with open(filename, 'r') as f:
                file_content = [x.strip() for x in f.readlines()] 
            file_content = filter(None, file_content)
            return json.dumps(file_content)
        except Exception as e:
            self.syslogger.info("Failed to md5 checksum of file "+filename)                
            self.syslogger.info("Error is: "+e) 
            return []


    def run_cmd_on_element(self, element_type, element_name, cmd=None):
        if cmd is None:
            if element_type == 'file':
                cmd = "ls -la"
            elif element_type == 'dir':
                cmd = "ls -ld"
        try:
            result = self.run_bash(cmd=cmd+" "+ element_name)
            if not result["status"]:
                return result["output"]
            else:
                return ""
        except Exception as e:
            self.syslogger.info("Failed to run cmd: "+cmd+" on "+element_type+" "+element_name)                
            self.syslogger.info("Error is: "+e) 
            return "" 


    def integrity_field_handler(self, field):
        field_dict = {
                'CHK': self.get_checksum,
                'DIR': self.run_cmd_on_element,
                'FILE': self.run_cmd_on_element,
                'CON': self.get_file_content,
                }
        return field_dict[field]


    def transfer_admin_to_host(self, src=None, dest=None):
        if src is None:
            self.syslogger.info("No source on admin LXC specified, bailing out")
            return 1
       
        if dest is None:
            self.syslogger.info("No destination on host specified, bailing out")
            return 1

        print "Inside here!!!!"
        print src
        print dest

        try:
            result = self.run_bash(cmd="scp "+src+" root@10.0.2.16:"+dest)
            print result
            return result["status"]
        except Exception as e:
            self.syslogger.info("Failed to transfer file to host")
            self.syslogger.info("Error is: "+e)
            return 1

   

    def gather_integrity_data(self, domain):
        
        integrity_data = {}

        integrity_data["@domain"] = domain
        integrity_data["DIRECTORIES"] = {} 
        integrity_data["FILES"] = {}



        integrity_data["DIRECTORIES"]["DIRECTORY"] = []

        directories_dict = {}
        directories_dict["CMD-LIST"] = {}
        directories_dict["CMD-LIST"]["CMD"] = []



        integrity_data["FILES"]["FILE"] = []

        files_dict = {}
        files_dict["CMD-LIST"] = {}
        files_dict["CMD-LIST"]["CMD"] = []
        

        for key, value in self.compliance_cfg_dict.iteritems():

            if key == "DIR":
                for item in value:
                    directories_dict['NAME'] = item["NAME"]
                    try:
                        cmd_list = item["CMD"]
                    except:
                        cmd_list = ["ls -ld"]

                    #directories_dict["CMD-LIST"]["CMD"] = list(cmd_list) 
                    
                    handler = self.integrity_field_handler("DIR")
                    for cmd in cmd_list:    
                        handler_argument= {"element_type" : "dir",
                                           "element_name" : item["NAME"],
                                           "cmd" : cmd}
                        cmd_dict = { "REQUEST" : cmd, 
                                     "RESPONSE" : handler(**handler_argument)}

                        directories_dict["CMD-LIST"]["CMD"].append(cmd_dict)
                    
                    integrity_data["DIRECTORIES"]["DIRECTORY"].append(directories_dict)


            if key == "FILE":
                for item in value:
                    files_dict['NAME'] = item["NAME"]
                    try:
                        cmd_list = item["CMD"]
                    except:
                        cmd_list = ["ls -la"]

                    #files_dict["CMD-LIST"]["CMD"] = list(cmd_list)

                    handler = self.integrity_field_handler("FILE")
                    for cmd in cmd_list:
                        handler_argument= {"element_type" : "file",
                                           "element_name" : item["NAME"],
                                           "cmd" : cmd}
                        cmd_dict = { "REQUEST" : cmd,
                                     "RESPONSE" : handler(**handler_argument)}

                        files_dict["CMD-LIST"]["CMD"].append(cmd_dict)

                    try:
                        if item["CON"]:
                            handler = self.integrity_field_handler("CON")
                            handler_argument= {"filename" : item["NAME"]}
                            files_dict["CONTENT"] = handler(**handler_argument)
                    except:
                        if self.debug:
                            self.logger.debug("File content for file: "+item["NAME"]+ "not requested")

                    
                    try:
                        if item["CHK"]:
                            handler = self.integrity_field_handler("CHK")
                            handler_argument= {"filename" : item["NAME"]}
                            files_dict["CHECKSUM"] = handler(**handler_argument)
                    except:
                        if self.debug:
                            self.logger.debug("Checksum for file: "+item["NAME"]+ "not requested")

                    integrity_data["FILES"]["FILE"].append(files_dict)

        return integrity_data


    def create_xml_dump(self, domain):

        dict_dump = {}

        dict_dump["INTEGRITY"] = self.gather_integrity_data(domain)

        dict_dump['@version'] = '1.0.0'
        dict_dump['@xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
        dict_dump['@xsi:noNamespaceSchemaLocation'] = 'compliance.xsd'


        final_dict = {'COMPLIANCE-DUMP' : dict_dump}

        return xd.unparse(final_dict, pretty=True)
       

    def validate_xml_dump(self, domain):
        
        xmlschema_doc = etree.parse(self.compliance_xsd)
        xmlschema = etree.XMLSchema(xmlschema_doc)

        xml_dump = self.create_xml_dump(domain)

        output_file = "/misc/scratch/"+domain+".xml"

        with open(output_file, 'w') as f:
            f.writelines(xml_dump)

        # Validate the output XML and return the validation result
        xml_doc = etree.parse(output_file)

        self.logger.info(xml_dump)
        result = xmlschema.validate(xml_doc)


        return result
 
