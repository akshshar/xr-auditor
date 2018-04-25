# -*- coding: utf-8 -*-
#!/usr/bin/env python

from lib.audit_helper import AuditHelpers
from lib.audit_helper import VALID_DOMAINS
from pprint import pprint
import pdb
import subprocess
import sys, os
import shutil, copy
import datetime
import xmltodict as xd
import json
from ctypes import cdll
libc = cdll.LoadLibrary('libc.so.6')
_setns = libc.setns
CLONE_NEWNET = 0x40000000

class IosxrAuditMain(AuditHelpers):
    def __init__(self,
                 server_cfg=None,
                 *args, **kwargs):

        super(IosxrAuditMain, self).__init__(*args, **kwargs) 

        if server_cfg is None:
            self.syslogger.info("No path to server config yaml file provided, aborting")
            self.exit = True
        else:
            self.server_cfg_dict = self.yaml_to_dict(server_cfg)
            if not self.server_cfg_dict:
                self.exit = True

        self.compliance_xmlname_parameters = { "router_hostname" : self.get_hostname_string,
                                               "router_mgmt_ip" : self.get_mgmt_ip_dashed}

        try:
            # Extract the absolute path for server private key
            self.id_rsa_file = self.server_cfg_dict["ID_RSA_FILE_PATH"]
            self.id_rsa_file = IosxrAuditMain.current_dir()+"/"+self.id_rsa_file

            # Extract the Remote user for Server connection over SSH
            self.remote_user = self.server_cfg_dict["USER"]

            # Extract the directory on the remote server where the final compliance
            # file should be placed.
            self.remote_directory = self.server_cfg_dict["REMOTE_DIRECTORY"]
             

            # Extract the remote Server's domain name or IP address

            self.server_connection = self.server_cfg_dict["SERVER_HOST"]["CONNECTION"]
            
            if "CONNECTION_TYPE" in self.server_cfg_dict["SERVER_HOST"]:
                self.server_connection_type = self.server_cfg_dict["SERVER_HOST"]["CONNECTION_TYPE"]
            else:
                self.server_connection_type = "IP"

               
            # Extract the Domain Name Server to configure if CONNECTION_TYPE = "DOMAIN_NAME"
            if self.server_connection_type == "DOMAIN_NAME":
                if "DOMAIN_NAME_SERVER" in self.server_cfg_dict["SERVER_HOST"]:
                    self.dns = self.server_cfg_dict["SERVER_HOST"]["DOMAIN_NAME_SERVER"]
                else:
                    self.syslogger.info("No DNS server specified when server connection type is DOMAIN_NAME, aborting")
                    self.exit = True
            else:
                self.dns = ""


            # Extract the naming pattern for the final compliance XML file

            if "COMPLIANCE_XMLNAME_PARAMS_ORDERED" in self.server_cfg_dict:
                xmlname_params = self.server_cfg_dict["COMPLIANCE_XMLNAME_PARAMS_ORDERED"]
            else:
                xmlname_params = ['router_hostname', 'router_mgmt_ip']
       
            xmlname_string = ""
            for param in xmlname_params:
                if param in self.compliance_xmlname_parameters:
                    value = self.compliance_xmlname_parameters[param]()
                    xmlname_string = xmlname_string+"_"+value 
                else:
                    self.syslogger.info("Specified Parameter for Compliance XML filename: "+param+" is not supported")
                    self.exit = True
                
            self.compliance_xmlname = "compliance_audit"+xmlname_string+".xml"
        except Exception as e:
            self.syslogger.info("Failed to extract server configuration parameters from supplied server config file")
            self.syslogger.info("Error is: "+str(e))
            self.exit = True


    def get_hostname_string(self):
        hostname = self.get_host()
        if not hostname:
            return ""
        else:
            return str(hostname)

    def get_mgmt_ip_dashed(self):
        mgmt_ip = self.get_mgmt_ip()
        if mgmt_ip == "":
            return ""
        else:
            return ('_'.join(mgmt_ip.split('.'))).split('/')[0]

        
    def collate_xml(self, domain_dict=None, output_xml_dir=None):

        if domain_dict is None:
            self.syslogger.info("Input dictionary with details on output_xml_dir/domain not provided, bailing out")
            return {}

        if output_xml_dir is None:
            self.syslogger.info("output_xml_dir for collector not provided, bailing out")
            return {}

        collated_xml_dict = {}
        xml_dict = {}
        integrity_list = []

        for element in domain_dict:
            if domain_dict[element]["domain"] in VALID_DOMAINS:
                xml_file = domain_dict[element]["input_xml_dir"]+"/"+domain_dict[element]["domain"]+".xml"
                xml_dict = self.xml_to_dict(xml_file)
                integrity_list.append(xml_dict["COMPLIANCE-DUMP"]["INTEGRITY-SET"]["INTEGRITY"])
                if domain_dict[element]["domain"] == "XR-LXC":
                    collated_xml_dict = copy.deepcopy(xml_dict)
            else:
                self.syslogger.info("Invalid domain specified: "+str(domain))
                return {}

        collated_xml_dict["COMPLIANCE-DUMP"]["INTEGRITY-SET"].pop("INTEGRITY", None)
        collated_xml_dict["COMPLIANCE-DUMP"]["INTEGRITY-SET"]["INTEGRITY"] = integrity_list

        collated_xml_dump = xd.unparse(collated_xml_dict, pretty=True)

        if self.debug:
            self.logger.debug(collated_xml_dump)

        output_file = output_xml_dir+"/"+ self.compliance_xmlname

        with open(output_file, 'w') as f:
            f.writelines(collated_xml_dump)

        return output_file


    def send_to_server(self, filename, vrf="global-vrf"):
        with open(self.get_netns_path(nsname=self.vrf)) as fd:
            self.setns(fd, CLONE_NEWNET)
            if filename is None:
                self.syslogger.info("No filename specified, bailing out")
                return False

            fname = os.path.basename(self.compliance_xmlname)

            cmd =  "cat "+filename+" | ssh -i "+ os.path.abspath(self.id_rsa_file)
            cmd =  cmd + " -o StrictHostKeyChecking=no "
            cmd =  cmd + self.remote_user+"@"+self.server_connection
            cmd =  cmd + " \"cat > "+self.remote_directory+"/"+fname+"\""

            try:
                result = self.run_bash(cmd, vrf=vrf)
                return result["status"]
            except Exception as e:
                self.syslogger.info("Failed to transfer file to remote host")
                self.syslogger.info("Error is: "+str(e))
                return False
    

    @classmethod
    def current_dir(cls):
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            cls.bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            cls.bundle_dir = os.path.dirname(os.path.abspath(__file__))
        
        return cls.bundle_dir



if __name__ == "__main__":

    # Create an Object of the child class, syslog parameters are optional. 
    # If nothing is specified, then logging will happen to local log rotated file.


    audit_obj = IosxrAuditMain(server_cfg=IosxrAuditMain.current_dir()+"/userfiles/server.cfg.yml",
                               syslog_server="11.11.11.2", syslog_port=514,
                               domain = "COLLECTOR",
                               compliance_xsd=IosxrAuditMain.current_dir()+"/userfiles/compliance.xsd",
                               compliance_cfg=IosxrAuditMain.current_dir()+"/userfiles/compliance.cfg.yml")

    if audit_obj.exit:
        audit_obj.syslogger.info("Exit flag is set, aborting")
        sys.exit(1)

    audit_obj.toggle_debug(0)
    if audit_obj.debug:
        for root, directories, filenames in os.walk(IosxrAuditMain.current_dir()):
            for directory in directories:
                audit_obj.logger.debug(os.path.join(root, directory))
            for filename in filenames:
                audit_obj.logger.debug(os.path.join(root,filename))

    audit_obj.toggle_debug(0)

    try:
        installer_cfg = audit_obj.yaml_to_dict(IosxrAuditMain.current_dir()+"/userfiles/installer.cfg.yml")
        output_xml_dir = installer_cfg["COLLECTOR"]["output_xml_dir"]
    except Exception as e:
        audit_obj.syslogger.info("Failed to extract output_xml_dir for the COLLECTOR domain,"
                                 "defaulting to /misc/app_host")
        output_xml_dir = "/misc/app_host"


    try:
        installer_cfg = audit_obj.yaml_to_dict(IosxrAuditMain.current_dir()+"/userfiles/installer.cfg.yml")
        input_xml_dir_xr = installer_cfg["XR"]["output_xml_dir"]
    except Exception as e:
        audit_obj.syslogger.info("Failed to extract output_xml_dir for the XR domain,"
                                 "defaulting to /misc/app_host")
        input_xml_dir_xr = "/misc/app_host"


    try:
        installer_cfg = audit_obj.yaml_to_dict(IosxrAuditMain.current_dir()+"/userfiles/installer.cfg.yml")
        input_xml_dir_admin = installer_cfg["ADMIN"]["output_xml_dir_xr"]
    except Exception as e:
        audit_obj.syslogger.info("Failed to extract output_xml_dir for the ADMIN domain,"
                                 "defaulting to /misc/app_host")
        input_xml_dir_admin = "/misc/app_host"

    try:
        installer_cfg = audit_obj.yaml_to_dict(IosxrAuditMain.current_dir()+"/userfiles/installer.cfg.yml")
        input_xml_dir_host = installer_cfg["HOST"]["output_xml_dir"]
    except Exception as e:
        audit_obj.syslogger.info("Failed to extract output_xml_dir for the HOST domain,"
                                 "defaulting to /misc/app_host")
        input_xml_dir_host = "/misc/app_host"




    domain_dict = {"xr" : { "domain": "XR-LXC", 
                            "input_xml_dir": input_xml_dir_xr}, 
                   "admin": {"domain": "ADMIN-LXC",
                             "input_xml_dir": input_xml_dir_admin}, 
                   "host" : {"domain": "HOST", 
                             "input_xml_dir": input_xml_dir_host}
                  }

    xml_file = audit_obj.collate_xml(domain_dict, output_xml_dir)


    if audit_obj.validate_xml_dump(xml_file):
        audit_obj.syslogger.info('Valid XML! :)')
        audit_obj.syslogger.info('Successfully created output XML: '+str(xml_file))

        # Attempt to send to remote server only on the active RP

        # Am I the active RP?
        check_active_rp = audit_obj.is_active_rp()

        if check_active_rp["status"] == "success":
            if check_active_rp["output"]:
                if not audit_obj.send_to_server(xml_file, vrf="global-vrf"):
                    audit_obj.syslogger.info("Successfully transferred audit result to Remote Server, over SSH")
                    sys.exit(0)
                else:
                    audit_obj.syslogger.info("Failed to send audit result to Remote Server")
                    sys.exit(1)
            else:
                audit_obj.syslogger.info("Not running on active RP, bailing out")
                sys.exit(0)
        else:
            audit_obj.syslogger.info("Failed to check current RP node's state")
            sys.exit(1)
    else:
        audit_obj.syslogger.info('Output XML Not valid! :(')
        sys.exit(1)

