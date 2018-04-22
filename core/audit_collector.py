# -*- coding: utf-8 -*-
#!/usr/bin/env python

from lib.audit_helper import AuditHelpers
from pprint import pprint
import pdb
import subprocess
import sys, os
import shutil
import datetime
import xmltodict as xd

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

        self.compliance_xmlname_parameters = { "router_hostname" : self.get_host,
                                               "router_mgmt_ip" : self.get_mgmt_ip}

        pdb.set_trace()
        try:
            # Extract the absolute path for server private key
            self.id_rsa_file = self.server_cfg_dict["ID_RSA_FILE_PATH"]
            self.id_rsa_file = IosxrAuditMain.current_dir()+"/"+self.id_rsa_file

            # Extract the Remote user for Server connection over SSH
            self.remote_user = self.server_cfg_dict["USER"]


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



    def collate_xml(self, domain_list, xml_directory="/misc/app_host"):
        collated_xml_dict = {}
        xml_dict = {}
        integrity_list = []

        for domain in domain_list:
            if domain in VALID_DOMAINS:
                xml_file = "/misc/app_host/"+domain+".xml"
                xml_dict = self.xml_to_dict(xml_file)
                integrity_list.append(xml_dict["COMPLIANCE-DUMP"]["INTEGRITY-SET"]["INTEGRITY"])
                if domain == "XR-LXC":
                    collated_xml_dict = copy.deepcopy(xml_dict)
            else:
                self.syslogger.info("Invalid domain specified: "+str(domain))
                return {}

        collated_xml_dict["COMPLIANCE-DUMP"]["INTEGRITY-SET"].pop("INTEGRITY", None)
        collated_xml_dict["COMPLIANCE-DUMP"]["INTEGRITY-SET"]["INTEGRITY"] = integrity_list

        collated_xml_dump = xd.unparse(collated_xml_dict, pretty=True)

        self.logger.info(collated_xml_dump)

        output_file = xml_directory+"/"+ self.compliance_xmlname

        with open(output_file, 'w') as f:
            f.writelines(collated_xml_dump)

        return output_file

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

    #audit_obj.toggle_debug(0)

    domain_list = ["XR-LXC", "ADMIN-LXC", "HOST"]
    xml_file = audit_obj.collate_xml(domain_list)


    if audit_obj.validate_xml_dump(xml_file):
        audit_obj.syslogger.info('Valid XML! :)')
        audit_obj.syslogger.info('Successfully created output XML: '+str(xml_file))
        sys.exit(0)
    else:
        audit_obj.syslogger.info('Output XML Not valid! :(')
        sys.exit(1)

