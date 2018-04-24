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

    @classmethod
    def current_dir(self):
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
            srcfolder = IosxrAuditMain.current_dir();


        clean_up_filename = self.run_bash(cmd="\"mv "+dstfolder+"/"+appName+" "+dstfolder+"/"+appName+".running && rm "+dstfolder+"/"+appName+".running 2>/dev/null\"")
        print clean_up_filename

        if self._copy_file(srcfolder+"/xr/"+appName, dstfolder+"/"+appName):
            self.logger.info("XR LXC audit app successfully copied")
        else:
            return False

        # Now Create the cron job in XR to periodically execute the XR LXC audit app

        with open(IosxrAuditMain.current_dir() + '/xr/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_xr_"+timestamp


        cron_cleanup = self.cron_job(folder="/etc/cron.d", croncmd_fname="audit_cron_xr*", action="delete")

        if cron_cleanup["status"] == "success":
            self.logger.info("Successfully cleaned up old XR audit cron jobs")
            cron_setup = self.cron_job(folder="/etc/cron.d", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add") 
        
            if cron_setup["status"] == "error":
                self.logger.info("Unable to set up cron Job")
                return False
            
            self.logger.info("XR LXC audit cron job successfully set up")
        else:
            self.logger.info("Failed to clean existing audit cron jobs")
            return False

        return True



    def setup_admin_audit(self, srcfolder=None, root_lr_user=None, dstfolder="/misc/scratch", appName="audit_admin.bin", cronName="audit_admin.cron"):

        if srcfolder is None:
            srcfolder = IosxrAuditMain.current_dir();

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}


        clean_up_filename = self.admincmd(root_lr_user=root_lr_user, cmd="run \"mv "+dstfolder+"/"+appName+" "+dstfolder+"/"+appName+".running && rm "+dstfolder+"/"+appName+".running 2>/dev/null\"")
        print clean_up_filename
        transfer_to_admin = self.adminscp(root_lr_user=root_lr_user, src=srcfolder+"/admin/"+appName, dest=dstfolder+"/"+appName)

        if transfer_to_admin["status"] == "success":
            self.logger.info("Admin LXC audit app successfully copied") 
            if self.debug:
                self.logger.debug(transfer_to_admin["output"])
        else:
            self.logger.info("Failed to copy Admin LXC audit app, Error:")
            self.logger.info(transfer_to_admin["output"])
            return False

        # Now Create the cron job in Admin LXC to periodically execute the Admin LXC audit app
       

        with open(IosxrAuditMain.current_dir() + '/admin/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_admin_"+timestamp


        cron_cleanup = self.cron_job(folder="/misc/app_host", action="delete")

        if cron_cleanup["status"] == "success":
            self.logger.info("Successfully cleaned up temp admin audit cron jobs")

            # Clean up stale cron jobs in the admin /etc/cron.d

            admin_cron_cleanup = self.admincmd(root_lr_user=root_lr_user, cmd="run rm -f /etc/cron.d/audit_cron_admin_*")

            if admin_cron_cleanup["status"] == "success":
                self.logger.info("Successfully cleaned up old admin audit cron jobs")
                check_admin_cron_cleanup = self.admincmd(root_lr_user=root_lr_user, cmd="run ls /etc/cron.d/")

                if "audit_cron_admin" in check_admin_cron_cleanup["output"]:
                    self.logger.info("Failed to clean up stale cron jobs in admin shell under /etc/cron.d")
                    return False

            else:
                self.logger.info("Failed to initiate admin shell cron cleanup")
                return False


            # Set up the temp admin audit cron job before transfer to admin shell
                
            cron_setup = self.cron_job(folder="/misc/app_host", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.logger.info("Unable to create admin LXC cron Job in /misc/app_host")
                return False
        else:
            self.logger.info("Failed to clean existing audit cron jobs")
            return False

        # Finally copy the created cron file into admin LXC /etc/cron.d to activate it

        transfer_to_admin = self.adminscp(root_lr_user=root_lr_user, src="/misc/app_host/"+cron_fname, dest="/etc/cron.d/"+cron_fname)

        if transfer_to_admin["status"] == "success":
            self.logger.info("Admin LXC audit cron file successfully copied and activated")
            if self.debug:
                self.logger.debug(transfer_to_admin["output"])
        else:
            self.logger.info("Failed to copy Admin LXC audit cron file, Error: %s" % transfer_to_admin["output"])
            return False


        return True



    def setup_host_audit(self, srcfolder=None, root_lr_user=None, dstfolder="/misc/scratch", appName="audit_host.bin", cronName="audit_host.cron"):

        if srcfolder is None:
            srcfolder = IosxrAuditMain.current_dir();

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}


        clean_up_filename = self.hostcmd(root_lr_user=root_lr_user, cmd="\"mv "+dstfolder+"/"+appName+" "+dstfolder+"/"+appName+".running && rm "+dstfolder+"/"+appName+".running 2>/dev/null\"")
        print clean_up_filename
        transfer_to_host = self.hostscp(root_lr_user=root_lr_user, src=srcfolder+"/host/"+appName, dest=dstfolder+"/"+appName)

        if transfer_to_host["status"] == "success":
            self.logger.info("Host audit app successfully copied")
            if self.debug:
                self.logger.debug(transfer_to_host["output"])
        else:
            self.logger.info("Failed to copy Host audit app, Error:")
            self.logger.info(transfer_to_host["output"])
            return False


        # Now Create the cron job in host layer to periodically execute the host audit app
       

        with open(IosxrAuditMain.current_dir() + '/host/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_host_"+timestamp


        cron_cleanup = self.cron_job(folder="/misc/app_host", action="delete")

        if cron_cleanup["status"] == "success":
            self.logger.info("Successfully cleaned up temp host audit cron jobs")

            # Clean up stale cron jobs in the host /etc/cron.d

            host_cron_cleanup = self.hostcmd(root_lr_user=root_lr_user, cmd="rm -f /etc/cron.d/audit_cron_host_*")

            if host_cron_cleanup["status"] == "success":
                self.logger.info("Successfully cleaned up old host audit cron jobs")
                check_host_cron_cleanup = self.hostcmd(root_lr_user=root_lr_user, cmd="ls /etc/cron.d/")

                if "audit_cron_host" in check_host_cron_cleanup["output"]:
                    self.logger.info("Failed to clean up stale cron jobs in host shell under /etc/cron.d")
                    return False

            else:
                self.logger.info("Failed to initiate host shell cron cleanup")
                return False


            cron_setup = self.cron_job(folder="/misc/app_host", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.logger.info("Unable to create temp host audit cron job in /misc/app_host")
                return False

        else:
            self.logger.info("Failed to clean existing audit cron jobs")
            return False

        # Finally copy the created cron file into host's /etc/cron.d to activate it

        transfer_to_host = self.hostscp(root_lr_user=root_lr_user, src="/misc/app_host/"+cron_fname, dest="/etc/cron.d/"+cron_fname)

        if transfer_to_host["status"] == "success":
            self.logger.info("Host audit cron file successfully copied and activated")
            if self.debug:
                self.logger.debug(transfer_to_host["output"])
        else:
            self.logger.info("Failed to copy and activate Host audit cron file, Error: %s" % transfer_to_host["output"])
            return False


        return True



    def setup_standby_xr_audit(self, srcfolder=None, dstfolder="/misc/scratch", appName="audit_xr.bin", cronName="audit_xr.cron"):

        if srcfolder is None:
            srcfolder = IosxrAuditMain.current_dir();

        # Check if standby RP is present
        standby_status = self.is_ha_setup()

        if standby_status["status"] == "success":
            if not standby_status["output"]:
                self.syslogger.info("Standby RP not present, bailing out")
                return False
        else:
            self.syslogger.info("Failed to get standby status, bailing out")
            return False 


        clean_up_filename = self.standby_xrruncmd(cmd="\"mv "+dstfolder+"/"+appName+" "+dstfolder+"/"+appName+".running && rm "+dstfolder+"/"+appName+".running 2>/dev/null\"")
        print clean_up_filename        
        transfer_to_standby_xr = self.standby_xrscp(src=srcfolder+"/xr/"+appName, dest=dstfolder+"/"+appName)

        if transfer_to_standby_xr["status"] == "success":
            self.logger.info("XR LXC audit app successfully copied to standby XR LXC")
            if self.debug:
                self.logger.debug(transfer_to_standby_xr["output"])
        else:
            self.logger.info("Failed to copy to XR LXC audit app to Standby XR LXC, Error:")
            self.logger.info(transfer_to_standby_xr["output"])
            return False

        # Now Create the cron job in Standby XR LXC to periodically execute the XR LXC audit app


        with open(IosxrAuditMain.current_dir() + '/xr/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_xr_"+timestamp


        cron_cleanup = self.cron_job(folder="/misc/app_host", action="delete")

        if cron_cleanup["status"] == "success":
            self.logger.info("Successfully cleaned up temp standby XR LXC audit cron jobs")

            # Clean up stale cron jobs in the standby XR LXC /etc/cron.d

            standby_xr_cron_cleanup = self.standby_xrruncmd(cmd="rm -f /etc/cron.d/audit_cron_xr_\*")

            if standby_xr_cron_cleanup["status"] == "success":
                self.logger.info("Successfully cleaned up old standby XR LXC audit cron jobs")
                check_standby_xr_cron_cleanup = self.standby_xrruncmd(cmd="ls /etc/cron.d/")

                if "audit_cron_xr" in check_standby_xr_cron_cleanup["output"]:
                    self.logger.info("Failed to clean up stale cron jobs in standby XR LXC shell under /etc/cron.d")
                    return False

            else:
                self.logger.info("Failed to initiate standby XR LXC shell cron cleanup")
                return False


            # Set up the temp XR audit cron job before transfer to standby XR LXC shell

            cron_setup = self.cron_job(folder="/misc/app_host", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.logger.info("Unable to create standby XR LXC cron Job in /misc/app_host")
                return False
        else:
            self.logger.info("Failed to clean existing audit cron jobs")
            return False

        # Finally copy the created cron file into standby XR LXC /etc/cron.d to activate it

        transfer_to_standby_xr = self.standby_xrscp(src="/misc/app_host/"+cron_fname, dest="/etc/cron.d/"+cron_fname)

        if transfer_to_standby_xr["status"] == "success":
            self.logger.info("Standby XR LXC audit cron file successfully copied and activated")
            if self.debug:
                self.logger.debug(transfer_to_standby_xr["output"])
        else:
            self.logger.info("Failed to copy standby XR LXC audit cron file, Error: %s" % transfer_to_standby_xr["output"])
            return False

        return True




    def setup_standby_admin_audit(self, srcfolder=None, root_lr_user=None, dstfolder="/misc/scratch", appName="audit_admin.bin", cronName="audit_admin.cron"):

        if srcfolder is None:
            srcfolder = IosxrAuditMain.current_dir();

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}


        # Check if standby RP is present
        standby_status = self.is_ha_setup()

        if standby_status["status"] == "success":
            if not standby_status["output"]:
                self.syslogger.info("Standby RP not present, bailing out")
                return False
        else:
            self.syslogger.info("Failed to get standby status, bailing out")
            return False


        clean_up_filename = self.standby_adminruncmd(root_lr_user=root_lr_user,cmd="\"mv "+dstfolder+"/"+appName+" "+dstfolder+"/"+appName+".running && rm "+dstfolder+"/"+appName+".running 2>/dev/null\"")
        print clean_up_filename
        transfer_to_standby_admin = self.standby_adminscp(root_lr_user=root_lr_user, src=srcfolder+"/admin/"+appName, dest=dstfolder+"/"+appName)

        if transfer_to_standby_admin["status"] == "success":
            self.logger.info("Admin LXC audit app successfully copied to Standby Admin LXC")
            if self.debug:
                self.logger.debug(transfer_to_standby_admin["output"])
        else:
            self.logger.info("Failed to copy Admin LXC audit app to standby Admin LXC, Error:")
            self.logger.info(transfer_to_standby_admin["output"])
            return False

        # Now Create the cron job in standby Admin LXC to periodically execute the Admin LXC audit app


        with open(IosxrAuditMain.current_dir() + '/admin/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_admin_"+timestamp


        cron_cleanup = self.cron_job(folder="/misc/app_host", action="delete")

        if cron_cleanup["status"] == "success":
            self.logger.info("Successfully cleaned up temp admin audit cron jobs")

            # Clean up stale cron jobs in the standby admin /etc/cron.d

            standby_admin_cron_cleanup = self.standby_adminruncmd(root_lr_user=root_lr_user, cmd="rm -f /etc/cron.d/audit_cron_admin_\*")

            if standby_admin_cron_cleanup["status"] == "success":
                self.logger.info("Successfully cleaned up old admin audit cron jobs")
                check_standby_admin_cron_cleanup = self.standby_adminruncmd(root_lr_user=root_lr_user, cmd="ls /etc/cron.d/")

                if "audit_cron_admin" in check_standby_admin_cron_cleanup["output"]:
                    self.logger.info("Failed to clean up stale cron jobs in standby admin LXC shell under /etc/cron.d")
                    return False

            else:
                self.logger.info("Failed to initiate Standby admin LXCshell cron cleanup")
                return False


            # Set up the temp admin audit cron job before transfer to Standby Admin LXCshell

            cron_setup = self.cron_job(folder="/misc/app_host", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.logger.info("Unable to create standby admin LXC cron Job in /misc/app_host")
                return False
        else:
            self.logger.info("Failed to clean existing audit cron jobs")
            return False

        # Finally copy the created cron file into admin LXC /etc/cron.d to activate it

        transfer_to_standby_admin = self.standby_adminscp(root_lr_user=root_lr_user, src="/misc/app_host/"+cron_fname, dest="/etc/cron.d/"+cron_fname)

        if transfer_to_standby_admin["status"] == "success":
            self.logger.info("Standby Admin LXC audit cron file successfully copied and activated")
            if self.debug:
                self.logger.debug(transfer_to_standby_admin["output"])
        else:
            self.logger.info("Failed to copy Standby Admin LXC audit cron file, Error: %s" % transfer_to_standby_admin["output"])
            return False

        return True



    def setup_standby_host_audit(self, srcfolder=None, root_lr_user=None, dstfolder="/misc/scratch", appName="audit_host.bin", cronName="audit_host.cron"):

        if srcfolder is None:
            srcfolder = IosxrAuditMain.current_dir();

        if root_lr_user is None:
            return {"status" : "error", "output" : "root-lr user not specified"}


        # Check if standby RP is present
        standby_status = self.is_ha_setup()

        if standby_status["status"] == "success":
            if not standby_status["output"]:
                self.syslogger.info("Standby RP not present, bailing out")
                return False
        else:
            self.syslogger.info("Failed to get standby status, bailing out")
            return False


        clean_up_filename = self.standby_hostcmd(root_lr_user=root_lr_user,cmd="\"mv "+dstfolder+"/"+appName+" "+dstfolder+"/"+appName+".running && rm "+dstfolder+"/"+appName+".running 2>/dev/null\"")
        print clean_up_filename
        transfer_to_standby_host = self.standby_hostscp(root_lr_user=root_lr_user, src=srcfolder+"/host/"+appName, dest=dstfolder+"/"+appName)

        if transfer_to_standby_host["status"] == "success":
            self.logger.info("Host audit app successfully copied to Standby host shell")
            if self.debug:
                self.logger.debug(transfer_to_standby_host["output"])
        else:
            self.logger.info("Failed to copy host audit app to standby host shell, Error:")
            self.logger.info(transfer_to_standby_host["output"])
            return False

        # Now Create the cron job in standby host to periodically execute the host audit app


        with open(IosxrAuditMain.current_dir() + '/host/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_host_"+timestamp


        cron_cleanup = self.cron_job(folder="/misc/app_host", action="delete")

        if cron_cleanup["status"] == "success":
            self.logger.info("Successfully cleaned up temp host audit cron jobs")

            # Clean up stale cron jobs in the standby host /etc/cron.d

            standby_host_cron_cleanup = self.standby_hostcmd(root_lr_user=root_lr_user, cmd="rm -f /etc/cron.d/audit_cron_host_\*")

            if standby_host_cron_cleanup["status"] == "success":
                self.logger.info("Successfully cleaned up old host audit cron jobs")
                check_standby_host_cron_cleanup = self.standby_hostcmd(root_lr_user=root_lr_user, cmd="ls /etc/cron.d/")

                if "audit_cron_host" in check_standby_host_cron_cleanup["output"]:
                    self.logger.info("Failed to clean up stale cron jobs in standby host shell under /etc/cron.d")
                    return False

            else:
                self.logger.info("Failed to initiate Standby host shell cron cleanup")
                return False


            # Set up the temp admin audit cron job before transfer to Standby host shell

            cron_setup = self.cron_job(folder="/misc/app_host", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.logger.info("Unable to create standby host cron Job in /misc/app_host")
                return False
        else:
            self.logger.info("Failed to clean existing audit cron jobs")
            return False

        # Finally copy the created cron file into standby host /etc/cron.d to activate it

        transfer_to_standby_host = self.standby_hostscp(root_lr_user=root_lr_user, src="/misc/app_host/"+cron_fname, dest="/etc/cron.d/"+cron_fname)

        if transfer_to_standby_host["status"] == "success":
            self.logger.info("Standby host audit cron file successfully copied and activated")
            if self.debug:
                self.logger.debug(transfer_to_standby_host["output"])
        else:
            self.logger.info("Failed to copy Standby host audit cron file, Error: %s" % transfer_to_standby_host["output"])
            return False

        return True



    def setup_collector(self, srcfolder=None, dstfolder="/misc/scratch",appName="collector.bin", cronName="audit_collector.cron"):

        if srcfolder is None:
            srcfolder = IosxrAuditMain.current_dir();


        clean_up_filename = self.run_bash(cmd="\"mv "+dstfolder+"/"+appName+" "+dstfolder+"/"+appName+".running && rm "+dstfolder+"/"+appName+".running 2>/dev/null\"")
        print clean_up_filename
        if self._copy_file(srcfolder+"/collector/"+appName, dstfolder+"/"+appName):
            self.logger.info("Collector app successfully copied")
        else:
            self.logger.info("Failed to copy collector app")
            return False

        # Create the cron job in XR to periodically collect the combined logs from XR LXC, Admin LXC and host 

        with open(IosxrAuditMain.current_dir() + '/collector/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_collector_"+timestamp


        cron_cleanup = self.cron_job(folder="/etc/cron.d", croncmd_fname="audit_cron_collector*", action="delete")

        if cron_cleanup["status"] == "success":
            self.logger.info("Successfully cleaned up old collector cron jobs")
            cron_setup = self.cron_job(folder="/etc/cron.d", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.logger.info("Unable to set up cron Job")
                return False

            self.logger.info("Collector cron job successfully set up in XR LXC")
        else:
            self.logger.info("Failed to clean existing audit cron jobs")
            return False

        return True



    def setup_standby_collector(self, srcfolder=None, dstfolder="/misc/scratch", appName="collector.bin", cronName="audit_collector.cron"):

        if srcfolder is None:
            srcfolder = IosxrAuditMain.current_dir();

        # Check if standby RP is present
        standby_status = self.is_ha_setup()

        if standby_status["status"] == "success":
            if standby_status["output"]:
               self.syslogger.info("Standby RP present")
            else:
                self.syslogger.info("Standby RP not present, bailing out")
                return False
        else:
            self.syslogger.info("Failed to get standby status, bailing out")
            return False


        # In case the binary is currently executing, then free up the current filename through mv + rm
        #  current execution will continue to use inode

        clean_up_filename = self.standby_xrruncmd(cmd="\"mv "+dstfolder+"/"+appName+" "+dstfolder+"/"+appName+".running && rm "+dstfolder+"/"+appName+".running 2>/dev/null\"")
        print clean_up_filename
        transfer_to_standby_xr = self.standby_xrscp(src=srcfolder+"/collector/"+appName, dest=dstfolder+"/"+appName)

        if transfer_to_standby_xr["status"] == "success":
            self.logger.info("collector successfully copied to standby XR LXC")
            if self.debug:
                self.logger.debug(transfer_to_standby_xr["output"])
        else:
            self.logger.info("Failed to copy to collector app to Standby XR LXC, Error:")
            self.logger.info(transfer_to_standby_xr["output"])
            return False

        # Now Create the cron job in Standby XR LXC to periodically execute the XR LXC audit app


        with open(IosxrAuditMain.current_dir() + '/collector/'+cronName, 'r') as f:
            cron_cmd = f.read()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cron_fname = "audit_cron_collector_"+timestamp


        cron_cleanup = self.cron_job(folder="/misc/app_host", action="delete")

        if cron_cleanup["status"] == "success":
            self.logger.info("Successfully cleaned up temp standby XR LXC collector cron jobs")

            # Clean up stale cron jobs in the standby XR LXC /etc/cron.d

            standby_xr_cron_cleanup = self.standby_xrruncmd(cmd="rm -f /etc/cron.d/audit_cron_collector_\*")

            if standby_xr_cron_cleanup["status"] == "success":
                self.logger.info("Successfully cleaned up old standby collector cron jobs")
                check_standby_xr_cron_cleanup = self.standby_xrruncmd(cmd="ls /etc/cron.d/")

                print check_standby_xr_cron_cleanup
                if "audit_cron_collector" in check_standby_xr_cron_cleanup["output"]:
                    self.logger.info("Failed to clean up stale collector cron jobs in standby XR LXC shell under /etc/cron.d")
                    return False

            else:
                self.logger.info("Failed to initiate standby XR LXC shell cron cleanup")
                return False


            # Set up the temp collector cron job before transfer to standby XR LXC shell

            cron_setup = self.cron_job(folder="/misc/app_host", croncmd = cron_cmd, croncmd_fname = cron_fname, action="add")

            if cron_setup["status"] == "error":
                self.logger.info("Unable to create standby XR LXC collector cron Job in /misc/app_host")
                return False
        else:
            self.logger.info("Failed to clean existing audit cron jobs")
            return False

        # Finally copy the created cron file into standby XR LXC /etc/cron.d to activate it

        transfer_to_standby_xr = self.standby_xrscp(src="/misc/app_host/"+cron_fname, dest="/etc/cron.d/"+cron_fname)

        if transfer_to_standby_xr["status"] == "success":
            self.logger.info("Standby XR LXC collector cron file successfully copied and activated")
            if self.debug:
                self.logger.debug(transfer_to_standby_xr["output"])
        else:
            self.logger.info("Failed to copy standby XR LXC collector cron file, Error: %s" % transfer_to_standby_xr["output"])
            return False

        return True




if __name__ == "__main__":

    # Create an Object of the child class, syslog parameters are optional. 
    # If nothing is specified, then logging will happen to local log rotated file.


    audit_obj = IosxrAuditMain(domain="INSTALLER", syslog_server="11.11.11.2", syslog_port=514)

    if audit_obj.exit:
        audit_obj.syslogger.info("Exit flag is set, aborting")
        sys.exit(1)

    audit_obj.toggle_debug(1)
    if audit_obj.debug:
        for root, directories, filenames in os.walk(IosxrAuditMain.current_dir()):
            for directory in directories:
                audit_obj.logger.debug(os.path.join(root, directory))
            for filename in filenames:
                audit_obj.logger.debug(os.path.join(root,filename))

    audit_obj.toggle_debug(0)
    audit_obj.setup_xr_audit()

    audit_obj.setup_admin_audit(root_lr_user="root")

    audit_obj.setup_host_audit(root_lr_user="root")

    audit_obj.setup_collector()

    audit_obj.setup_standby_xr_audit()

    audit_obj.setup_standby_admin_audit(root_lr_user="root")

    audit_obj.setup_standby_host_audit(root_lr_user="root")

    audit_obj.setup_standby_collector()
    
    #run_bash("cat /misc/scratch/try | ip netns exec global-vrf ssh -i "+bundle_dir+"/id_rsa_server -o StrictHostKeyChecking=no cisco@11.11.11.2 \"cat >> file_sent_by_main_apr8\"")

    #run_bash("cat /misc/scratch/try | ip netns exec global-vrf ssh -i "+bundle_dir+"/id_rsa_server -o StrictHostKeyChecking=no cisco@11.11.11.2")

    
