#!/usr/bin/env python

from lib.ztp_extended_helper import ZtpExtHelpers
from pprint import pprint
import pdb
import subprocess
import sys, os
frozen = 'not'

def run_bash(cmd=None):
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
            print("No bash command provided")


        status = process.returncode

        return {"status" : status, "output" : out}

if __name__ == "__main__":

    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        frozen = 'ever so'
        bundle_dir = sys._MEIPASS
    else:
        # we are running in a normal Python environment
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    print( 'we are',frozen,'frozen')
    print( 'bundle dir is', bundle_dir )
    print( 'sys.argv[0] is', sys.argv[0] )
    print( 'sys.executable is', sys.executable )
    print( 'os.getcwd is', os.getcwd() )

    file_list=os.listdir(bundle_dir)
    print (file_list)

    # Create an Object of the child class, syslog parameters are optional. 
    # If nothing is specified, then logging will happen to local log rotated file.

    ztp_obj = ZtpExtHelpers(syslog_file="/root/ztp_python.log", syslog_server="11.11.11.2", syslog_port=514)

    with open('/misc/app_host/test_fil2', 'a') as fd:
        fd.write('Hello World')

    pprint(ztp_obj.admincmd(root_lr_user="root", cmd = "show environment power"))
    pprint(ztp_obj.adminscp(root_lr_user="root", src="/misc/app_host/test_fil2", dest="/misc/scratch/test_file2"))
    pprint(ztp_obj.hostscp(root_lr_user="root", src="/misc/app_host/test_fil2", dest="/root/test_file2host"))

    with open(bundle_dir+'/id_rsa_server') as f:
        lines = f.readlines()

    print lines

    run_bash("cat /misc/scratch/try | ip netns exec global-vrf ssh -i "+bundle_dir+"/id_rsa_server -o StrictHostKeyChecking=no cisco@11.11.11.2 \"cat >> file_sent_by_main_apr8\"")

    #run_bash("cat /misc/scratch/try | ip netns exec global-vrf ssh -i "+bundle_dir+"/id_rsa_server -o StrictHostKeyChecking=no cisco@11.11.11.2")

    
