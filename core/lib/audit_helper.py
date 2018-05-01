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
import json
from pprint import pprint
import logging, logging.handlers
from ctypes import cdll
import copy

libc = cdll.LoadLibrary('libc.so.6')
_setns = libc.setns
CLONE_NEWNET = 0x40000000

VALID_DOMAINS = ["XR-LXC",
                 "ADMIN-LXC",
                 "HOST",
                 "COLLECTOR",
                 "INSTALLER"]

XML_PREFIX_DOMAINS = ["XR-LXC",
                      "ADMIN-LXC",
                      "HOST"]

COMPLIANCE_PREFIX = "compliance_audit"



class AuditHelpers(ZtpHelpers):

    def __init__(self,
                 request_version=False,
                 syslog_server=None, 
                 syslog_port=None, 
                 syslog_file=None,
                 domain=None,
                 compliance_xsd=None,
                 compliance_cfg=None):

        self.exit = False
        self.version = {}
        self.request_version = request_version

        if self.request_version:
            if compliance_xsd is None:
                self.exit = True
            else:
                self.compliance_xsd = compliance_xsd
            self.version = self.xsd_to_dict(version=True)
            return None

        if domain is None:
            self.syslogger.info("No domain specified, aborting.\n"
                                "Specify one of "+', '.join(VALID_DOMAINS))
            self.exit = True 
        else:
            if domain in VALID_DOMAINS:
                self.domain = domain
            else:
                self.syslogger.info("Domain: "+str(domain)+" specified is invalid, aborting.\n"
                                    "Specify one of "+', '.join(VALID_DOMAINS))
                self.exit = True 

        if ( self.domain == "XR-LXC" or
             self.domain == "COLLECTOR" ):
            super(AuditHelpers, self).__init__(syslog_server, syslog_port, syslog_file)
        elif self.domain == "INSTALLER":
            super(AuditHelpers, self).__init__(syslog_server, syslog_port, syslog_file)

            standby_status = self.is_ha_setup()
            if standby_status["status"] == "success":
                if not standby_status["output"]:
                    self.syslogger.info("Standby RP not present")
                    self.ha_setup = False
                else:
                    self.syslogger.info("Standby RP is present")
                    self.ha_setup = True
            else:
                self.syslogger.info("Failed to get standby status, bailing out")
                self.exit = True


            # Am I the active RP?
            check_active_rp = self.is_active_rp()

            if check_active_rp["status"] == "success":
                if check_active_rp["output"]:
                    self.active_rp = True
                    self.syslogger.info("Running on active RP")
                else:
                    self.active_rp = False
                    self.syslogger.info("Not running on active RP")
            else:
                self.syslogger.info("Failed to check current RP node's state")
                self.exit =  True


            # Fetch and store the xrnns ip addresses of XR LXC on active and standby
            xrnns_ips = self.get_xr_ip()

            if xrnns_ips["status"] == "success":
                self.active_xr_ip = xrnns_ips["output"]["active_xr_ip"]
                self.standby_xr_ip = xrnns_ips["output"]["standby_xr_ip"]
            else:
                self.syslogger.info("Failed to fetch the xrnns ips of the XR LXCs on active/standby RPs")
                self.exit =  True

            self.exit = False
            return None 
        else:
            self.setup_syslog_child()
            self.setup_debug_logger_child()
            self.debug = False


        if compliance_xsd is None:
            self.syslogger.info("No Compliance xsd file - compliance_xsd provided, aborting")
            self.exit = True
        else:
            self.compliance_xsd = compliance_xsd

        if compliance_cfg is None:
            self.syslogger.info("No path to Compliance config yaml file provided, aborting")
            self.exit = True 
        else:
            self.compliance_cfg = compliance_cfg


        self.compliance_xsd_dict = {}
        self.compliance_cfg_dict = {}

        self.compliance_xsd_dict = self.xsd_to_dict()
        if not self.compliance_xsd_dict:
            self.exit = True

        self.compliance_cfg_dict = self.yaml_to_dict(self.compliance_cfg)
        if not self.compliance_cfg_dict:
            self.exit = True        

        self.calendar_months = {'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04',
                                'May':'05', 'Jun':'06', 'Jul':'07', 'Aug':'08',
                                'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}



       
    def setup_debug_logger_child(self):
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


    def setup_syslog_child(self):
        """Setup up the Syslog logger to log to a logrotated local file 
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


    def get_host(self):
        try:
            result = self.xrcmd({"exec_cmd" : "show running-config hostname"})

            if result["status"] == "success":
                return result["output"][0].split(' ')[1]
            else:
                return []
        except Exception as e:
            self.syslogger.info("Failed to fetch hostname (Not configured?), Error: %s" %e) 
            return []


    def get_product(self):
        try:
            result = self.run_bash("source /pkg/etc/ztp.config && get_ztp_product_id")
            if not result["status"]:
                return result["output"]
            else:
                self.syslogger.info("Failed to fetch product name, output:" + result["output"]+ ", error:"+result["error"])
                return ""
        except Exception as e:
            self.syslogger.info("Failed to fetch product name, Error: %s" % e) 
            return ""


    def get_vendor(self):
        return "Cisco"

    def get_os(self):
        return "IOS-XR"

    def get_date(self):

        try:
            if self.compliance_xsd_dict["xs:schema"]["xs:attribute"]['@name'] == 'DATE':
                pattern = self.compliance_xsd_dict["xs:schema"]["xs:attribute"]['xs:simpleType']['xs:restriction']['xs:pattern']['@value']
        except Exception as e:
            sys.syslogger.info("Failed to fetch pattern for DATE from compliance xsd, Error:"+str(e))
            sys.syslogger.info("Using default pattern: CCYYMMDD-HH:MI TZ")
 
        try:
            result = self.xrcmd({"exec_cmd" : "show clock"})

            if result["status"] == "success":
                HH = result["output"][0].split(' ')[0].split(':')[0] 
                MI = result["output"][0].split(' ')[0].split(':')[1]
                CCYY = result["output"][0].split(' ')[-1]
                MM = self.calendar_months[result["output"][0].split(' ')[3]]
                DD = result["output"][0].split(' ')[4]
                TZ = result["output"][0].split(' ')[1]
  
                date = CCYY+MM+DD+"-"+HH+":"+MI+' '+TZ
 
                if re.match(pattern, date):
                    return date
                else:
                    sys.syslogger.info("Failed to match requested pattern, please change format as needed")
                    sys.syslogger.info("Using default pattern: CCYYMMDD-HH:MI TZ")
            else:
                return ""
        except Exception as e:
            self.syslogger.info("Failed to fetch product name, Error: %s" % e)
            return ""
        

    def get_version(self):
        try:
            result = self.xrcmd({"exec_cmd" : "show version"})

            if result["status"] == "success":
                return result["output"][0].split(' ')[-1] 
            else:
                return ""
        except Exception as e:
            self.syslogger.info("Failed to fetch hostname, Error: %s" % e)
            return ""


    def get_mgmt_ip(self):
        try:
            # Get the name of the current node
            cmd = "/sbin/ip netns exec xrnns /pkg/bin/node_list_generation -f MY"

            result = self.run_bash(cmd)

            if not result["status"]:
                my_node_name = result["output"]
            else:
                self.syslogger.info("Failed to get current node name, output: "+result["output"]+", error: "+result["error"])
                return ""

            result = self.xrcmd({"exec_cmd" : "show interface MgmtEth"+my_node_name+"/0"})

            if result["status"] == "success":
                return result["output"][3].split(' ')[-1]
            else:
                return ""
        except Exception as e:
            self.syslogger.info("Failed to fetch hostname, Error: %s" % e)
            return ""

        
    def get_general_field(self, field):
        field_dict = {
                'HOST': self.get_host, 
                'DATE': self.get_date, 
                'VENDOR': self.get_vendor,
                'PRODUCT': self.get_product,
                'OS': self.get_os, 
                'VERSION': self.get_version, 
                'IPADDR' : self.get_mgmt_ip
                }
        return field_dict[field]()


    def is_active_rp(self):
        '''method to check if the node executing this script is the active RP
        '''

        try:
            # Get the current active RP node-name
            exec_cmd = "show redundancy summary"
            show_red_summary = self.xrcmd({"exec_cmd" : exec_cmd})

            if show_red_summary["status"] == "error":
                self.syslogger.info("Failed to get show redundancy summary output from XR")
                return {"status" : "error", "output" : "", "warning" : "Failed to get show redundancy summary output"}

            else:
                try:
                    current_active_rp = show_red_summary["output"][2].split()[0]
                except Exception as e:
                    self.syslogger.info("Failed to get Active RP from show redundancy summary output")
                    return {"status" : "error", "output" : "", "warning" : "Failed to get Active RP, error: " + str(e)}


            # get the name of the current node
            cmd = "/sbin/ip netns exec xrnns /pkg/bin/node_list_generation -f MY"

            result = self.run_bash(cmd)

            if not result["status"]:
                my_node_name = result["output"]
            else:
                self.syslogger.info("Failed to get current node name, output: "+result["output"]+", error: "+result["error"])
                return {"status" : "error", "output" : "", "warning" : "Failed to get current node name"}

            if current_active_rp == my_node_name:
                return {"status" : "success", "output" : True, "warning" : ""}    
            else:
                return {"status" : "success", "output" : False, "warning" : ""} 
        except Exception as e:
            self.syslogger.info("Failed to check if current node is Active RP")
            return {"status" : "error", "output" : "", "warning" : "Failed to check if current node is Active RP, error: " + str(e)}



    def admincmd(self, cmd=None):
        """Issue an admin exec cmd and obtain the output
           :param cmd: Dictionary representing the XR exec cmd
                       and response to potential prompts
                       { 'exec_cmd': '', 'prompt_response': '' }
           :type cmd: string 
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if cmd is None:
            return {"status" : "error", "output" : "No command specified"}

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}

        status = "success"


        if self.debug:
            self.logger.debug("Received admin exec command request: \"%s\"" % cmd)

        cmd = "export AAA_USER="+self.root_lr_user+" && source /pkg/bin/ztp_helper.sh && echo -ne \""+cmd+"\\n \" | xrcmd \"admin\""

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = process.communicate()


        if process.returncode:
            status = "error"
            output = "Failed to get command output"
        else:
            output_list = []
            output = ""

            for line in out.splitlines():
                fixed_line= line.replace("\n", " ").strip()
                output_list.append(fixed_line)
                if "syntax error: expecting" in fixed_line:
                    status = "error"
                output = filter(None, output_list)    # Removing empty items

        if self.debug:
            self.logger.debug("Exec command output is %s" % output)

        return {"status" : status, "output" : output}


    def adminscp(self, src=None, dest=None):
        """Transfer a file from XR LXC to admin LXC
           :param src: Path of src file in XR to be 
                       transferred to admin shell
           :type src: string
           :param src: Path of destination file in admin shell 
           :type src: string
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}


        if dest is None:
            return {"status" : "error", "output" : "dest file path in admin shell not specified"}


        if self.debug:
            self.logger.debug("Received scp request to transfer file from XR LXC to admin LXC")


        result = self.admincmd(cmd="run scp root@"+self.active_xr_ip+":"+src+" "+dest)

        return {"status" : result["status"], "output" : result["output"]}



    def active_adminscp(self, src=None, dest=None):

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}


        if dest is None:
            return {"status" : "error", "output" : "dest file path in admin shell not specified"}


        if self.debug:
            self.logger.debug("Inside active_adminscp")

        # Get the active Admin LXC's xrnns ip
        result = self.get_admin_ip()

        if result["status"] == "success":
            active_admin_ip = result["output"]["active_admin_ip"]
        else:
            self.syslogger.info("Failed to get active RP's  admin xrnns ip")
            return {"status" : "error", "output" : ""}


        # First transfer the file to temp location in Admin LXC

        filename = posixpath.basename(src)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tempfile = "audit_aadscp_"+filename+"_"+timestamp

        result = self.adminscp(src=src, dest="/misc/scratch/"+tempfile)


        if result["status"] == "error":
            return {"status" : result["status"], "output" : result["output"]}
        else:
            result = self.admincmd(cmd="run scp /misc/scratch/"+tempfile+" root@"+active_admin_ip+":"+dest)

            # Remove tempfile from Admin shell

            self.admincmd(cmd="run rm -f /misc/scratch/"+tempfile)
            return {"status" : result["status"], "output" : result["output"]}

        

    def active_adminruncmd(self, cmd=None):

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if cmd is None:
            return {"status" : "error", "output" : "linux cmd not specified"}


        if self.debug:
            self.logger.debug("Received bash cmd: %s to run in shell of active RP's admin LXC" % cmd)


       # Get the active RP's admin LXC's xrnns ip:

        result = self.get_admin_ip()

        if result["status"] == "success":
            active_admin_ip = result["output"]["active_admin_ip"]
        else:
            self.syslogger.info("Failed to get the active admin xrnns ip")
            return {"status" : "error", "output" : ""}


        # Now run this command via the admin shell of the active RP

        result = self.admincmd(cmd="run ssh root@"+active_admin_ip+" "+cmd)

        return {"status" : result["status"], "output" : result["output"]}



    def hostcmd(self, cmd=None):
        """Issue a cmd in the host linux shell and obtain the output
           :param cmd: Dictionary representing the XR exec cmd
                       and response to potential prompts
                       { 'exec_cmd': '', 'prompt_response': '' }
           :type cmd: string 
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if cmd is None:
            return {"status" : "error", "output" : "No command specified"}

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if self.debug:
            self.logger.debug("Received host command request: \"%s\"" % cmd)


        result = self.admincmd(cmd="run ssh root@10.0.2.16 "+cmd)

        return {"status" : result["status"], "output" : result["output"]}



    def hostscp(self, src=None, dest=None):
        """Transfer a file from XR LXC to underlying host shell
           :param src: Path of src file in XR to be 
                       transferred to host shell
           :type src: string
           :param src: Path of destination file in host shell 
           :type src: string
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}


        if dest is None:
            return {"status" : "error", "output" : "dest file path in host shell not specified"}


        if self.debug:
            self.logger.debug("Received scp request to transfer file from XR LXC to host shell")


        # First transfer the file to temp location in Admin LXC 

        filename = posixpath.basename(src)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tempfile = "audit_hscp_"+filename+"_"+timestamp
 
        result = self.adminscp(src=src, dest="/misc/scratch/"+tempfile)


        if result["status"] == "error":
            return {"status" : result["status"], "output" : result["output"]}
        else:
            result = self.admincmd(cmd="run scp /misc/scratch/"+tempfile+" root@10.0.2.16:"+dest)

            # Remove tempfile from Admin shell

            self.admincmd(cmd="run rm -f /misc/scratch/"+tempfile)
            return {"status" : result["status"], "output" : result["output"]}


    def get_xr_ip(self):

        try:
            # First determine the currently allocated ip address for IOS-XR lxc in xrnns namespace
            # Show commands using Parent class helper method: xrcmd

            result = self.xrcmd({"exec_cmd" : "show platform vm"})

            # We first extract the XR-LXC IP from active and standby(if available) RPs:

            active_ip = ""
            standby_ip = ""

            for line in result["output"][2:]:
                row = filter(None, line.split(" "))
                if row[1] == "RP":
                    if "ACTIVE" in row[2]:
                        active_ip = row[6]
                    if "STANDBY" in row[2]:
                        standby_ip = row[6]

            return {"status" : "success",
                    "output" : {"active_xr_ip" : active_ip,
                                "standby_xr_ip" : standby_ip}
                   }

        except Exception as e:
            self.syslogger.info("Failed to fetch the  xr xrnns ips, Error:" +str(e))
            return {"status" : "error", "output" : str(e)}



    def get_admin_ip(self):
        active_admin_ip = ""
        standby_admin_ip = ""

        # First fetch the XR LXC xrnns ips for active and standby
 
        #result = self.get_xr_ip()

        #if result["status"] == "success":

        #split_active_ip = result["output"]["active_xr_ip"].split('.')
        split_active_ip = self.active_xr_ip.split('.')
        split_active_ip[3] = '1'
        active_admin_ip = '.'.join(split_active_ip)
 
        # if result["output"]["standby_xr_ip"] is not "":
        if self.standby_xr_ip is not "":
            #split_standby_ip = result["output"]["standby_xr_ip"].split('.') 
            split_standby_ip = self.standby_xr_ip.split('.')
            split_standby_ip[3] = '1'
            standby_admin_ip = '.'.join(split_standby_ip)


        return {"status" : "success",
                "output" : {"active_admin_ip" : active_admin_ip,
                            "standby_admin_ip" : standby_admin_ip}
               }



    def standby_adminruncmd(self, cmd=None):

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if cmd is None:
            return {"status" : "error", "output" : "linux cmd not specified"}


        if self.debug:
            self.logger.debug("Received bash cmd: %s to run in shell of standby RP's admin LXC" % cmd)


       # Get the standby RP's admin LXC's xrnns ip:
    
        result = self.get_admin_ip()

        if result["status"] == "success":
            standby_admin_ip = result["output"]["standby_admin_ip"]
            if standby_admin_ip == "":
               self.syslogger.info("Did not receive a standby admin IP (no standby RP?), bailing out")
               return {"status" : "error", "output" : ""}
        else:
            self.syslogger.info("Failed to get the standby admin xrnns ip")
            return {"status" : "error", "output" : ""}


        # Now try to run this command via the admin LXC of the active RP

        result = self.admincmd(cmd="run ssh root@"+standby_admin_ip+" "+cmd)

        return {"status" : result["status"], "output" : result["output"]}





    def standby_adminscp(self, src=None, dest=None):
        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}


        if dest is None:
            return {"status" : "error", "output" : "dest file path in standby admin shell not specified"}


        if self.debug:
            self.logger.debug("Received scp request to transfer file from XR LXC to standby admin shell")


       # Get the standby RP's admin LXC's xrnns ip:

        result = self.get_admin_ip()

        if result["status"] == "success":
            standby_admin_ip = result["output"]["standby_admin_ip"]
            if standby_admin_ip == "":
               self.syslogger.info("Did not receive a standby admin IP (no standby RP?), bailing out")
               return {"status" : "error", "output" : ""}
        else:
            self.syslogger.info("Failed to get the standby admin xrnns ip")
            return {"status" : "error", "output" : ""}


        # First transfer the file to temp location in active Admin LXC 

        filename = posixpath.basename(src)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tempfile = "audit_sadscp_"+filename+"_"+timestamp

        result = self.adminscp(src=src, dest="/misc/scratch/"+tempfile)


        if result["status"] == "error":
            return {"status" : result["status"], "output" : result["output"]}
        else:
            result = self.admincmd(cmd="run scp /misc/scratch/"+tempfile+" root@"+standby_admin_ip+":"+dest)

            # Remove tempfile from Admin shell

            self.admincmd(cmd="run rm -f /misc/scratch/"+tempfile)
            return {"status" : result["status"], "output" : result["output"]}



    def standby_xrruncmd(self, cmd=None):
        """Issue a cmd in the standby xr linux shell and obtain the output
           :param cmd: String representing the linux cmd to run
           :type cmd: string 
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if cmd is None:
            return {"status" : "error", "output" : "No command specified"}


        if self.debug:
            self.logger.debug("Received standby xr run command request: \"%s\"" % cmd)


        # First fetch the XR LXC xrnns ips for active and standby

        #result = self.get_xr_ip()

        if self.ha_setup:
            if self.standby_xr_ip is not "":
                cmd_run = self.run_bash("ssh root@"+self.standby_xr_ip+" "+cmd)
                if not cmd_run["status"]:
                    return {"status" : "success", "output" : cmd_run["output"]}
                else:
                    self.syslogger.info("Failed to run command on standby XR LXC shell")
                    return {"status" : "error", "output" : cmd_run["output"]}
            else:
                self.syslogger.info("No standby xr ip, (no standby RP?)")
                return {"status" : "error", "output" : result["output"]}

        else:
            self.syslogger.info("Not an HA setup, no standby - Bailing out")
            return {"status" : "error", "output" : result["output"]}


    def standby_xrscp(self, src=None, dest=None):
        """Transfer a file from XR LXC to underlying host shell
           :param src: Path of src file in XR to be 
                       transferred to host shell
           :type src: string
           :param src: Path of destination file in host shell of standby RP 
           :type src: string
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}

        if dest is None:
            return {"status" : "error", "output" : "dest file path in standby RP XR LXC shell not specified"}


        if self.debug:
            self.logger.debug("Received scp request to transfer file from XR LXC in active to XR LXC on standby")

        # First fetch the XR LXC xrnns ips for active and standby

        if self.ha_setup:
            if self.standby_xr_ip is not "":
                cmd_run = self.run_bash("scp "+src+" root@"+self.standby_xr_ip+":"+dest)
                if not cmd_run["status"]:
                    return {"status" : "success", "output" : cmd_run["output"]}
                else:
                    self.syslogger.info("Failed to transfer file to standby XR LXC, output:"+cmd_run["output"]+", error:"+cmd_run["error"])
                    return {"status" : "error", "output" : cmd_run["error"]}
            else:
                self.syslogger.info("No standby xr ip, (no standby RP?)")
                return {"status" : "error", "output" : result["output"]}

        else:
            self.syslogger.info("Failed to fetch the  xr xrnns ips")
            return {"status" : "error", "output" : result["output"]}



    def active_hostcmd(self, cmd=None):
        """Issue a cmd in the host linux shell and obtain the output
           :param cmd: Dictionary representing the XR exec cmd
                       and response to potential prompts
                       { 'exec_cmd': '', 'prompt_response': '' }
           :type cmd: string 
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if cmd is None:
            return {"status" : "error", "output" : "No command specified"}

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if self.debug:
            self.logger.debug("Received host command request: \"%s\"" % cmd)


        result = self.active_adminruncmd(cmd="ssh root@10.0.2.16 "+cmd)

        return {"status" : result["status"], "output" : result["output"]}



    def active_hostscp(self, src=None, dest=None):
        """Transfer a file from XR LXC to underlying host shell
           :param src: Path of src file in XR to be 
                       transferred to host shell
           :type src: string
           :param src: Path of destination file in host shell of standby RP 
           :type src: string
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}


        if dest is None:
            return {"status" : "error", "output" : "dest file path in host shell not specified"}


        if self.debug:
            self.logger.debug("Received scp request to transfer file from XR LXC to host shell")


        # First transfer the file to temp location in active Admin LXC 

        filename = posixpath.basename(src)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tempfile = "audit_ahscp_"+filename+"_"+timestamp

        result = self.active_adminscp(src=src, dest="/misc/scratch/"+tempfile)


        if result["status"] == "error":
            return {"status" : result["status"], "output" : result["output"]}
        else:
            result = self.active_adminruncmd(cmd="scp /misc/scratch/"+tempfile+" root@10.0.2.16:"+dest)

            # Remove tempfile from activey Admin shell

            self.active_adminruncmd(cmd="rm -f /misc/scratch/"+tempfile)
            return {"status" : result["status"], "output" : result["output"]}



    def standby_hostcmd(self, cmd=None):
        """Issue a cmd in the host linux shell and obtain the output
           :param cmd: Dictionary representing the XR exec cmd
                       and response to potential prompts
                       { 'exec_cmd': '', 'prompt_response': '' }
           :type cmd: string 
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if cmd is None:
            return {"status" : "error", "output" : "No command specified"}

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if self.debug:
            self.logger.debug("Received host command request: \"%s\"" % cmd)


        result = self.standby_adminruncmd(cmd="ssh root@10.0.2.16 "+cmd)

        return {"status" : result["status"], "output" : result["output"]}



    def standby_hostscp(self, src=None, dest=None):
        """Transfer a file from XR LXC to underlying host shell
           :param src: Path of src file in XR to be 
                       transferred to host shell
           :type src: string
           :param src: Path of destination file in host shell of standby RP 
           :type src: string
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        #if root_lr_user is None:
        #    return {"status" : "error", "output" : "root-lr user not specified"}


        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}


        if dest is None:
            return {"status" : "error", "output" : "dest file path in host shell not specified"}


        if self.debug:
            self.logger.debug("Received scp request to transfer file from XR LXC to host shell")


        # First transfer the file to temp location in standby Admin LXC 

        filename = posixpath.basename(src)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tempfile = "audit_shscp_"+filename+"_"+timestamp

        result = self.standby_adminscp(src=src, dest="/misc/scratch/"+tempfile)


        if result["status"] == "error":
            return {"status" : result["status"], "output" : result["output"]}
        else:
            result = self.standby_adminruncmd(cmd="scp /misc/scratch/"+tempfile+" root@10.0.2.16:"+dest)

            # Remove tempfile from Standby Admin shell

            self.standby_adminruncmd(cmd="rm -f /misc/scratch/"+tempfile)
            return {"status" : result["status"], "output" : result["output"]}





    def run_bash(self, cmd=None, vrf="xrnns", pid=1):
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

        with open(self.get_netns_path(nsname=vrf,nspid=pid)) as fd:
            self.setns(fd, CLONE_NEWNET)

            if self.debug:
                self.logger.debug("bash cmd being run: "+cmd)
            ## In XR the default shell is bash, hence the name
            if cmd is not None:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                out, err = process.communicate()
                if self.debug:
                    self.logger.debug("output: "+out)
                    self.logger.debug("error: "+err)
            else:
                self.syslogger.info("No bash command provided")
                return {"status" : 1, "output" : "", "error" : "No bash command provided"}

            status = process.returncode

            return {"status" : status, "output" : out, "error" : err}



    def get_peer_rp_ip(self):
        """User defined method in Child Class
           IOS-XR internally use a private IP address space
           to reference linecards and RPs.
 
           This method uses XR internal binaries to fetch the
           internal IP address of the Peer RP in an HA setup.
           :param url: Complete url for config to be downloaded 
           :param caption: Any reason to be specified when applying 
                           config. Will show up in the output of:
                          "show configuration commit list detail" 
           :type url: str 
           :type caption: str 
           :return: Return a dictionary with status and the peer RP IP 
                    { 'status': 'error/success', 
                      'peer_rp_ip': 'IP address of Peer RP' }
           :rtype: dict
        """
        cmd = "ip netns exec xrnns /pkg/bin/node_list_generation -f MY"
        bash_out = self.run_bash(cmd)
        if not bash_out["status"]:
            my_name = bash_out["output"]
        else:
            self.syslogger.info("Failed to get My Node Name")
            return {"status" : "error", "peer_rp_ip" : ""}

        cmd = "ip netns exec xrnns /pkg/bin/node_conversion -N " + str(my_name)
        bash_out = self.run_bash(cmd)
        if not bash_out["status"]:
            my_node_name = bash_out["output"].replace('\n', '')
        else:
            self.syslogger.info("Failed to convert My Node Name")
            return {"status" : "error", "peer_rp_ip" : ""}


        cmd = "ip netns exec xrnns /pkg/bin/node_list_generation -f ALL"
        bash_out = self.run_bash(cmd)

        if not bash_out["status"]:
            node_name_list = bash_out["output"].split()
        else:
            self.syslogger.info("Failed to get Node Name List")
            return {"status" : "error", "peer_rp_ip" : ""}

        
        for node in node_name_list:
            if "RP" in node:
                if my_node_name != node:
                    cmd="ip netns exec xrnns /pkg/bin/admin_nodeip_from_nodename -n " + str(node)
                    bash_out = self.run_bash(cmd)
       
                    if not bash_out["status"]:
                        return {"status" : "success", "peer_rp_ip" : bash_out["output"]}
                    else:
                        self.syslogger.info("Failed to get Peer RP IP")
                        return {"status" : "error", "peer_rp_ip" : ""}

        self.syslogger.info("There is no standby RP!")            
        return {"status" : "error", "peer_rp_ip" : ""}
 


    def scp_to_standby(self, src_file_path=None, dest_file_path=None):
        """User defined method in Child Class
           Used to scp files from active to standby RP.
           
           leverages the get_peer_rp_ip() method above.
           Useful to keep active and standby in sync with files 
           in the linux environment.
           :param src_file_path: Source file location on Active RP 
           :param dest_file_path: Destination file location on Standby RP 
           :type src_file_path: str 
           :type dest_file_path: str 
           :return: Return a dictionary with status based on scp result. 
                    { 'status': 'error/success' }
           :rtype: dict
        """

        if any([src_file_path, dest_file_path]) is None:
            self.syslogger.info("Incorrect File path\(s\)") 
            return {"status" : "error"}

        standby_ip = self.get_peer_rp_ip()

        if standby_ip["status"] == "error":
            return {"status" : "error"}
        else:
            self.syslogger.info("Transferring file "+str(src_file_path)+" from Active RP to standby location: " +str(dest_file_path))
            cmd = "ip netns exec xrnns scp "+str(src_file_path)+ " root@" + str(standby_ip["peer_rp_ip"]) + ":" + str(dest_file_path)
            bash_out = self.run_bash(cmd)

            if bash_out["status"]:
                self.syslogger.info("Failed to transfer file to standby")
                return {"status" : "error"}
            else:
                return {"status" : "success"}


            
    def execute_cmd_on_standby(self, cmd=None): 
        """User defined method in Child Class
           Used to execute bash commands on the standby RP
           and fetch the output over SSH.
           Leverages get_peer_rp_ip() and run_bash() methods above.
           :param cmd: bash command to execute on Standby RP 
           :type cmd: str 
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 
                      'output': 'empty/output from bash cmd on standby' }
           :rtype: dict
        """

        if cmd is None:
            self.syslogger.info("No command specified")
            return {"status" : "error", "output" : ""}
        else:
            with tempfile.NamedTemporaryFile(delete=True) as f:
                f.write("#!/bin/bash\n%s" % cmd)
                f.flush()
                f.seek(0,0)
                standby_ip = self.get_peer_rp_ip()
                if standby_ip["status"] == "error":
                    return {"status" : "error", "output" : ""}
                standby_cmd = "ip netns exec xrnns ssh root@"+str(standby_ip["peer_rp_ip"])+ " " + "\"$(< "+str(f.name)+")\"" 
               
                bash_out = self.run_bash(standby_cmd)

                if bash_out["status"]:
                    self.syslogger.info("Failed to execute command on standby")
                    return {"status" : "error", "output" : ""}
                else:
                    return {"status" : "success", "output": bash_out["output"]}



    def is_ha_setup(self):

        try:
            # Get the current active RP node-name
            exec_cmd = "show redundancy summary"
            show_red_summary = self.xrcmd({"exec_cmd" : exec_cmd})

            if show_red_summary["status"] == "error":
                self.syslogger.info("Failed to get show redundancy summary output from XR")
                return {"status" : "error", "output" : "", "warning" : "Failed to get show redundancy summary output"}
            else:
                try:
                    if "N/A" in show_red_summary["output"][2].split()[1]:
                        return {"status" : "success", "output": False} 
                    else:
                        return {"status" : "success", "output": True} 
                except Exception as e:
                    self.syslogger.info("Failed to extract standby status from show redundancy summary output")
                    return {"status" : "error", "output" : "Failed to get Active RP, error: " + str(e)}
        except Exception as e:
            self.syslogger.info("Failed to extract standby status from show redundancy summary output")
            return {"status" : "error", "output" : "Failed to get Active RP, error: " + str(e)}


    def cron_job(self, standby=False, folder="/etc/cron.d", croncmd=None, croncmd_fname=None, cronfile=None, action="add"):
        """Pretty useful method to cleanly add or delete cronjobs 
           on the active and/or standby RP.
           Leverages execute_cmd_on_standby(), scp_to_standby() methods defined above
           :param folder: folder to place the final cron file. By default this is set to /etc/cron.d (Activates by default)
           :param croncmd: croncmd to be added to crontab on Active RP 
           :param croncmd_fname: user can specify a custom name for the file to create under
                                 the folder . If not specified, then the name is randomly generated
                                 in the following form:
                                 /<folder>/audit_cron_timestamp
                                 where timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
 
 
           :param cronfile: Absolute Path to user specified cronfile to blindly place and activate. 
                            Name of the target file under /<folder> will be the same as original filename.
                            If both croncmd and cronfile are provided at the same time, then
                            cronfile will be preferred.
           :param standby: Flag to indicate if the cronjob should be synced to standby RP
                           Default: False 
           :param action: String Flag to indicate whether the croncmd should be added or deleted
                          Default: "add"
                          Available options: "add" | "delete"
           :type croncmd: str 
           :type standby: bool 
           :type active: str
           :return: Return a dictionary with status
                    { 'status': 'error/success' }
           :rtype: dict
        """

        if action == "add":

            if croncmd is None and cronfile is None:
                self.syslogger.info("No cron job specified, specify either a croncmd or a cronfile")
                return {"status" : "error"}

            # By default cronfile is selected if provided. NO CHECKS will be made on the cronfile, make
            # sure the supplied cronfile is correct.


            if cronfile is not None:
                audit_cronfile = folder + "/"+ os.path.basename(cronfile)
                try:
                    shutil.copy(cronfile, audit_cronfile)
                    self.syslogger.info("Successfully added cronfile "+str(cronfile)+" to "+folder)
                    # Set valid permissions on the cron file
                    if not self.run_bash("chmod 0644 "+ audit_cronfile)["status"]:
                        self.syslogger.info("Successfully set permissions on cronfile " + audit_cronfile)
                    else:
                        self.syslogger.info("Failed to set permissions on the cronfile")
                        return {"status" : "error"}
                    if standby:
                        if self.scp_to_standby(audit_cronfile, audit_cronfile)["status"]:
                            self.syslogger.info("Cronfile "+ audit_cronfile+" synced to standby RP!")
                        else:
                            self.syslogger.info("Failed to sync cronfile "+audit_cronfile+" on standby: "+ str(result["output"]))
                            return {"status" : "error"} 
                except Exception as e:
                    self.syslogger.info("Failed to copy supplied cronfile "+audit_cronfile+" to "+folder)
                    self.syslogger.info("Error is "+ str(e))
                    return {"status" : "error"} 
            else:
                # Let's create a file with the required croncmd 

                if croncmd_fname is None:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    audit_cronfile = folder+"/audit_cron_"+timestamp
                else:
                    audit_cronfile = folder+"/"+str(croncmd_fname)

                try:
                    with open(audit_cronfile, "w") as fd:
                        fd.write(str(croncmd) + '\n')        
                    self.syslogger.info("Successfully wrote croncmd "+str(croncmd)+" to file"+audit_cronfile) 

                    # Set valid permissions on the cron file
                    if not self.run_bash("chmod 0644 "+ audit_cronfile)["status"] == "success":
                        self.syslogger.info("Successfully set permissions on cronfile " + audit_cronfile)
                    else:
                        self.syslogger.info("Failed to set permissions on the cronfile")
                        return {"status" : "error"}

                    if standby:
                        if self.scp_to_standby(audit_cronfile, audit_cronfile)["status"] == "success":
                            self.syslogger.info("Cronfile "+ audit_cronfile+" synced to standby RP!")
                        else:
                            self.syslogger.info("Failed to sync cronfile "+audit_cronfile+" on standby: "+ str(result["output"]))
                            return {"status" : "error"}

                except Exception as e:
                    self.syslogger.info("Failed to write supplied croncmd "+str(croncmd)+" to file "+audit_cronfile)
                    self.syslogger.info("Error is "+ str(e))
                    return {"status" : "error"}


        elif action == "delete":
            # Delete any audit_cron_timestamp files under /<folder> if no specific file is specified.
            # if cronfile is specified, remove cronfile
            # if croncmd_fname is specified, remove /<folder>/croncmd_fname
            # Else Delete any audit_cron_timestamp files under /<folder> if no specific file/filename is specified. 

            audit_cronfiles = []
            if cronfile is not None:
                audit_cronfiles.append(folder+"/"+str(os.path.basename(cronfile)))
            elif croncmd_fname is not None:
                audit_cronfiles.append(folder+"/"+str(croncmd_fname))
            else:
                # Remove all audit_cron_* files under <folder> 
                for f in os.listdir(folder):
                    if re.search("audit_cron_", f):
                        audit_cronfiles.append(os.path.join(folder, f))

       
            for audit_cronfile in audit_cronfiles:
                try:
                    for filename in glob.glob(audit_cronfile):
                        os.remove(filename)
                    self.syslogger.info("Successfully removed cronfile "+ audit_cronfile)

                    if standby:
                        if self.execute_cmd_on_standby("rm "+ audit_cronfile)["status"] == "success":
                            self.syslogger.info("Successfully removed cronfile"+audit_cronfile+" on standby")
                        else:
                            self.syslogger.info("Failed to remove cronfile"+audit_cronfile+" on standby")
                            return {"status" : "error"}
                except Exception as e:
                    self.syslogger.info("Failed to remove cronfile "+ audit_cronfile)
                    self.syslogger.info("Error is "+ str(e))
                    return {"status" : "error"}

        return {"status" : "success"}                        


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


    def xsd_to_dict(self, version=False):
        xsd_dict = {}
        try:
            with open(self.compliance_xsd,'r') as f:
                xsd_dict_raw = xd.parse(f)
                xsd_dict = json.loads(json.dumps(xsd_dict_raw))
            if version:
                version = "v"+ str(xsd_dict["xs:schema"]["@version"])
                return {"version" : version} 
        except Exception as e:
            if version:
                return {}
            self.syslogger.info("Failed to parse compliance xsd file")
            self.syslogger.info("Error is %s" % e)
            return {}

        if self.debug:
            self.logger.debug(xsd_dict)

        return xsd_dict



    def xml_to_dict(self, xml_file):
        xml_dict = {}
        try:
            with open(xml_file,'r') as f:
                xml_dict_raw = xd.parse(f)
                xml_dict = json.loads(json.dumps(xml_dict_raw))
        except Exception as e:
            self.syslogger.info("Failed to parse compliance xml file")
            self.syslogger.info("Error is %s" % e)
            return {}

        if self.debug:
            self.logger.debug(xml_dict)

        return xml_dict


    def yaml_to_dict(self, yaml_file):
        yaml_dict = {}
        try:
            with open(yaml_file, 'r') as stream:
                try:
                    yaml_dict = yaml.load(stream)
                except yaml.YAMLError as e:
                    self.syslogger.info("Failed to parse YAML file, Error: %s" % e)
        except Exception as e:
            self.syslogger.info("Failed to open YAML file")
            self.syslogger.info("Error is %s" % e)
            
        if self.debug:
            self.logger.debug(yaml_dict)

        return yaml_dict



    def gather_general_data(self):
        general_fields_dict = {}

        for element in self.compliance_xsd_dict["xs:schema"]["xs:element"]:
            try:
                if "xs:complexType" in element.keys():
                    if element["@name"] == "GENERAL":
                        general_fields_dict = element["xs:complexType"]["xs:all"]["xs:element"]
            except Exception as e:
                self.syslogger.info("Failed to gather General fields from the compliance file")
                self.syslogger.info("Error is: "+str(e))

        general_data_dict = {}

        for field in general_fields_dict:
            value = self.get_general_field(field["@ref"])
            general_data_dict[field["@ref"]] = str(value)
       
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
            self.syslogger.info("Error is: "+str(e)) 
            return "" 

    def get_file_content(self, filename):
        try:
            with open(filename, 'r') as f:
                file_content = [x.strip() for x in f.readlines()] 
            file_content = filter(None, file_content)
            return json.dumps(file_content)
        except Exception as e:
            self.syslogger.info("Failed to md5 checksum of file "+filename)                
            self.syslogger.info("Error is: "+str(e)) 
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
            self.syslogger.info("Error is: "+str(e)) 
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


        try:
            result = self.run_bash(cmd="scp "+src+" root@10.0.2.16:"+dest, vrf="", pid=1)
            return result["status"]
        except Exception as e:
            self.syslogger.info("Failed to transfer file to host")
            self.syslogger.info("Error is: "+str(e))
            return 1


    def gather_integrity_data(self):
        
        integrity_data = {}

        integrity_data["@domain"] = self.domain
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
                    directories_dict["CMD-LIST"]["CMD"]= []
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
                    
                    integrity_data["DIRECTORIES"]["DIRECTORY"].append(copy.deepcopy(directories_dict))


            if key == "FILE":
                for item in value:
                    
                    files_dict['NAME'] = item["NAME"]
                    files_dict["CMD-LIST"]["CMD"] = []
                    files_dict.pop("CONTENT", None)
                    files_dict.pop("CHECKSUM", None)

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

                    integrity_data["FILES"]["FILE"].append(copy.deepcopy(files_dict))

        return integrity_data


    def create_xml_dump(self, output_xml_dir=None):

        if output_xml_dir is None:
            self.syslogger.info("No output directory specified, bailing out")
            return ""

        dict_dump = {}

        dict_dump["INTEGRITY-SET"] = {}
        dict_dump["INTEGRITY-SET"]["INTEGRITY"] = self.gather_integrity_data()
 
        if self.domain == "XR-LXC":
            dict_dump["GENERAL"] = self.gather_general_data()


        dict_dump['@version'] = '1.0.0'
        dict_dump['@xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
        dict_dump['@xsi:noNamespaceSchemaLocation'] = 'compliance.xsd'


        final_dict = {'COMPLIANCE-DUMP' : dict_dump}

        xml_dump = xd.unparse(final_dict, pretty=True)


        output_file = output_xml_dir + "/"+ self.domain+".xml"
        with open(output_file, 'w') as f:
            f.writelines(xml_dump)
          
        return output_file



    def validate_xml_dump(self, xml_file):
        
        xmlschema_doc = etree.parse(self.compliance_xsd)

        #print "\n\n######################################\n\n"
        #print etree.tostring(xmlschema_doc.getroot(), encoding='utf8',method='xml')

        xmlschema = etree.XMLSchema(xmlschema_doc)

        # Validate the output XML and return the validation result
        xml_doc = etree.parse(xml_file)

        #print "\n\n######################################\n\n"

        #print etree.tostring(xml_doc.getroot(), encoding='utf8',method='xml')

        #print "\n\n######################################\n\n"

        result = xmlschema.validate(xml_doc)


        return result
 
