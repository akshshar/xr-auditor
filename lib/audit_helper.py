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

class AuditHelpers(ZtpHelpers):

    def admincmd(self, root_lr_user=None, cmd=None):
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

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}

        status = "success"


        if self.debug:
            self.logger.debug("Received admin exec command request: \"%s\"" % cmd)

        cmd = "export AAA_USER="+root_lr_user+" && source /pkg/bin/ztp_helper.sh && echo -ne \""+cmd+"\\n \" | xrcmd \"admin\""

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


    def adminscp(self, root_lr_user=None, src=None, dest=None):
        """Transfer a file from XR LXC to admin LXC
           :param root_lr_user: username in root-lr group in XR
           :type root_lr_user: string
           :param src: Path of src file in XR to be 
                       transferred to admin shell
           :type src: string
           :param src: Path of destination file in admin shell 
           :type src: string
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}


        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}


        if dest is None:
            return {"status" : "error", "output" : "dest file path in admin shell not specified"}

        status = "success"


        if self.debug:
            self.logger.debug("Received scp request to transfer file from XR LXC to admin LXC")


        # First determine the currently allocated ip address for IOS-XR lxc in xrnns namespace
        # This IP is used in the admin shell to scp from XR LXC.

        # Show commands using Parent class helper method: xrcmd

        show_plat_vm = self.xrcmd({"exec_cmd" : "show platform vm"})

        print show_plat_vm["output"]

        for line in show_plat_vm["output"]:
            if '0/RP' in line:
                xr_lxc_ip = line.split(' ')[-1]

        result = self.admincmd(root_lr_user="root", cmd="run scp root@"+xr_lxc_ip+":"+src+" "+dest)

        return {"status" : result["status"], "output" : result["output"]}



    def hostcmd(self, root_lr_user=None, cmd=None):
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

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}

        status = "success"


        if self.debug:
            self.logger.debug("Received host command request: \"%s\"" % cmd)


        result = self.admincmd(root_lr_user="root", cmd="run ssh root@10.0.2.16 "+cmd)

        return {"status" : result["status"], "output" : result["output"]}



    def hostscp(self, root_lr_user=None, src=None, dest=None):
        """Transfer a file from XR LXC to underlying host shell
           :param root_lr_user: username in root-lr group in XR
           :type root_lr_user: string
           :param src: Path of src file in XR to be 
                       transferred to host shell
           :type src: string
           :param src: Path of destination file in host shell 
           :type src: string
           :return: Return a dictionary with status and output
                    { 'status': 'error/success', 'output': '' }
           :rtype: string
        """

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}


        if src is None:
            return {"status" : "error", "output" : "src file path in XR not specified"}


        if dest is None:
            return {"status" : "error", "output" : "dest file path in admin shell not specified"}


        if self.debug:
            self.logger.debug("Received scp request to transfer file from XR LXC to host shell")


        # First transfer the file to temp location in Admin LXC 

        filename = posixpath.basename(src)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        tempfile = "audit_"+filename+"_"+timestamp
 
        result = self.adminscp(root_lr_user="root", src=src, dest="/misc/scratch/"+tempfile)


        if result["status"] == "error":
            return {"status" : result["status"], "output" : result["output"]}
        else:
            result = self.admincmd(root_lr_user="root", 
                                   cmd="run scp /misc/scratch/"+tempfile+" root@10.0.2.16:"+dest)

            # Remove tempfile from Admin shell

            self.admincmd(root_lr_user="root", cmd="run rm -f /misc/scratch/"+tempfile)
            return {"status" : result["status"], "output" : result["output"]}



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
        ## In XR the default shell is bash, hence the name
        if cmd is not None:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            out, err = process.communicate()
        else:
            self.syslogger.info("No bash command provided")


        status = process.returncode

        return {"status" : status, "output" : out}



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
        rp_count = 0
        show_platform = self.xrcmd({"exec_cmd" : "show platform"})

        if show_platform["status"] == "success":
            try:
                for line in show_platform["output"]:
                    if '/CPU' in line.split()[0]:
                        node_info =  line.split()
                        node_name = node_info[0]
                        if 'RP' in node_name:
                            rp_count = rp_count + 1


                if rp_count in (1,2):
                    return {"status": "success", "rp_count": rp_count}
                else:
                    return {"status": "error", "rp_count": rp_count, "error": "Invalid RP count"}

            except Exception as e:
                if self.debug:
                    self.logger.debug("Error while fetching the RP count")
                    self.logger.debug(e)
                    return {"status": "error", "error": e }

        else:
            if self.debug:
                self.logger.debug("Failed to get the output of show platform")
            return {"status": "error", "output": "Failed to get the output of show platform"}



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
                        print f
        
            for audit_cronfile in audit_cronfiles:
                try:
                    os.remove(audit_cronfile)
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



