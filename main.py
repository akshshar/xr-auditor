#!/usr/bin/env python

from lib.audit_helper import AuditHelpers
from pprint import pprint
import pdb
import subprocess
import sys, os
import shutil
import datetime

class IosxrAuditMain(AuditHelpers):

    def _current_dir(self):
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        return bundle_dir

 
    def _copy_file(self, src=None, dest=None):
        try:
            shutil.copy2(src, dest)
            # eg. src and dest are the same file
            return True
        except shutil.Error as e:
            self.logger.info("Failed to copy file, Error: %s" % e)
            # eg. source or destination doesn't exist
            return False 
        except IOError as e:
            self.logger.info('Failed to copy file, Error: %s' % e.strerror)
            return False



    def setup_xr_audit(self, srcfolder=None, dstfolder="/misc/scratch",appName="audit_xr.bin", cronName="audit_xr.cron"):
                
        if srcfolder is None:
            srcfolder = self._current_dir();

        if self._copy_file(srcfolder+"/xr/"+appName, dstfolder+"/"+appName):
            self.logger.info("XR LXC audit app successfully copied")
        else:
            return False

        # Now Create the cron job in XR to periodically execute the XR LXC audit app

        with open(self._current_dir() + '/xr/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_xr_"+timestamp


        cron_cleanup = self.cron_job(folder="/etc/cron.d", action="delete")

        if cron_cleanup["status"] == "success":
            self.syslogger.info("Successfully cleaned up existing audit cron jobs")
            cron_setup = self.cron_job(folder="/etc/cron.d", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add") 
        
            if cron_setup["status"] == "error":
                self.syslogger.info("Unable to set up cron Job")
                return False
        else:
            self.syslogger.info("Failed to clean existing audit cron jobs")
            return False

        return True



    def setup_admin_audit(self, srcfolder=None, root_lr_user=None, dstfolder="/misc/scratch", appName="audit_admin.bin", cronName="audit_admin.cron"):

        if srcfolder is None:
            srcfolder = self._current_dir();

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}


        transfer_to_admin = self.adminscp(root_lr_user=root_lr_user, src=srcfolder+"/admin/"+appName, dest=dstfolder+"/"+appName)

        if transfer_to_admin["status"] == "success":
            self.logger.info("Admin LXC audit app successfully copied: %s" % transfer_to_admin["output"])
        else:
            self.logger.info("Failed to copy Admin LXC audit app, Error: %s" % transfer_to_admin["output"])
            return False

        # Now Create the cron job in Admin LXC to periodically execute the Admin LXC audit app
       

        with open(self._current_dir() + '/admin/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_admin_"+timestamp


        cron_cleanup = self.cron_job(folder="/misc/app_host", action="delete")

        if cron_cleanup["status"] == "success":
            self.syslogger.info("Successfully cleaned up existing audit cron jobs")
            cron_setup = self.cron_job(folder="/misc/app_host", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.syslogger.info("Unable to create admin LXC cron Job in /misc/app_host")
                return False

        else:
            self.syslogger.info("Failed to clean existing audit cron jobs")
            return False

        # Finally copy the created cron file into admin LXC /etc/cron.d to activate it

        transfer_to_admin = self.adminscp(root_lr_user=root_lr_user, src="/misc/app_host/"+cron_fname, dest="/etc/cron.d/"+cron_fname)

        if transfer_to_admin["status"] == "success":
            self.logger.info("Admin LXC audit cron file successfully copied")
        else:
            self.logger.info("Failed to copy Admin LXC audit cron file, Error: %s" % transfer_to_admin["output"])
            return False


        return True



    def setup_host_audit(self, srcfolder=None, root_lr_user=None, dstfolder="/misc/scratch", appName="audit_host.bin", cronName="audit_host.cron"):

        if srcfolder is None:
            srcfolder = self._current_dir();

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}


        transfer_to_host = self.hostscp(root_lr_user=root_lr_user, src=srcfolder+"/host/"+appName, dest=dstfolder+"/"+appName)

        if transfer_to_host["status"] == "success":
            self.logger.info("Host app successfully copied: %s" % transfer_to_host["output"])
        else:
            self.logger.info("Failed to copy host audit app, Error: %s" % transfer_to_host["output"])
            return False

        # Now Create the cron job in host layer to periodically execute the host audit app
       

        with open(self._current_dir() + '/host/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_host"+timestamp


        cron_cleanup = self.cron_job(folder="/misc/app_host", action="delete")

        if cron_cleanup["status"] == "success":
            self.syslogger.info("Successfully cleaned up existing audit cron jobs")
            cron_setup = self.cron_job(folder="/misc/app_host", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.syslogger.info("Unable to create host LXC cron Job in /misc/app_host")
                return False

        else:
            self.syslogger.info("Failed to clean existing audit cron jobs")
            return False

        # Finally copy the created cron file into host's /etc/cron.d to activate it

        transfer_to_host = self.hostscp(root_lr_user=root_lr_user, src="/misc/app_host/"+cron_fname, dest="/etc/cron.d/"+cron_fname)

        if transfer_to_host["status"] == "success":
            self.logger.info("Host audit cron file successfully copied and activated %s" % transfer_to_host["output"])
        else:
            self.logger.info("Failed to copy and activate Host audit cron file, Error: %s" % transfer_to_host["output"])
            return False


        return True



    def setup_collector(self, srcfolder=None, dstfolder="/misc/app_host",appName="collector.bin", cronName="audit_collector.cron"):

        if srcfolder is None:
            srcfolder = self._current_dir();

        if self._copy_file(srcfolder+"/"+appName, dstfolder+"/"+appName):
            self.logger.info("Host audit app successfully copied")
        else:
            return False

        # Create the cron job in XR to periodically collect the combined logs from XR LXC, Admin LXC and host 

        with open(self._current_dir() + '/collector/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_collector_"+timestamp


        cron_setup = self.cron_job(folder="/etc/cron.d", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

        if cron_setup["status"] == "error":
            self.syslogger.info("Unable to set up cron Job")
            return False

        return True




if __name__ == "__main__":

    # Create an Object of the child class, syslog parameters are optional. 
    # If nothing is specified, then logging will happen to local log rotated file.

    audit_obj = IosxrAuditMain(syslog_file="/root/audit_python.log", syslog_server="11.11.11.2", syslog_port=514)

    audit_obj.setup_xr_audit()

    audit_obj.setup_admin_audit(root_lr_user="root")

    audit_obj.setup_host_audit(root_lr_user="root")

    audit_obj.setup_collector()


    #with open(bundle_dir+'/id_rsa_server') as f:
    #    lines = f.readlines()

    #print lines

    #run_bash("cat /misc/scratch/try | ip netns exec global-vrf ssh -i "+bundle_dir+"/id_rsa_server -o StrictHostKeyChecking=no cisco@11.11.11.2 \"cat >> file_sent_by_main_apr8\"")

    #run_bash("cat /misc/scratch/try | ip netns exec global-vrf ssh -i "+bundle_dir+"/id_rsa_server -o StrictHostKeyChecking=no cisco@11.11.11.2")

    
