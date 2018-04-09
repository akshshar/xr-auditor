#!/usr/bin/env python
"""
  author: akshshar@cisco.com

  ztp_extended_helper.py

  ZTP extended helper for Python

  Copyright (c) 2018 by Cisco Systems, Inc.
  All rights reserved.

"""

from ztp_helper import ZtpHelpers
import subprocess, posixpath
import datetime

class ZtpExtHelpers(ZtpHelpers):

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

        print "cmd is"
        print cmd
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
        tempfile = "ztp_"+filename+"_"+timestamp
 
        result = self.adminscp(root_lr_user="root", src=src, dest="/misc/scratch/"+tempfile)


        if result["status"] == "error":
            return {"status" : result["status"], "output" : result["output"]}
        else:
            result = self.admincmd(root_lr_user="root", 
                                   cmd="run scp /misc/scratch/"+tempfile+" root@10.0.2.16:"+dest)

            # Remove tempfile from Admin shell

            self.admincmd(root_lr_user="root", cmd="run rm -f /misc/scratch/"+tempfile)
            return {"status" : result["status"], "output" : result["output"]}
