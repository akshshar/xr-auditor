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



if __name__ == "__main__":

    # Create an Object of the child class, syslog parameters are optional. 
    # If nothing is specified, then logging will happen to local log rotated file.


    audit_obj = IosxrAuditMain(syslog_file="/root/audit_python.log", syslog_server="11.11.11.2", syslog_port=514,
                               compliance_xsd=IosxrAuditMain.current_dir()+"/userfiles/compliance.xsd",
                               compliance_cfg=IosxrAuditMain.current_dir()+"/userfiles/compliance.cfg.yml",
                               id_rsa_file=IosxrAuditMain.current_dir()+"/userfiles/id_rsa_server",
                               server_host=IosxrAuditMain.current_dir()+"/userfiles/server_host")

    if audit_obj is None:
        sys.exit(1)

    audit_obj.toggle_debug(1)
    if audit_obj.debug:
        for root, directories, filenames in os.walk(IosxrAuditMain.current_dir()):
            for directory in directories:
                audit_obj.logger.debug(os.path.join(root, directory))
            for filename in filenames:
                audit_obj.logger.debug(os.path.join(root,filename))

    audit_obj.toggle_debug(0)

    if audit_obj.validate_xml_dump(domain="XR-LXC"):
        print('Valid! :)')
    else:
        print('Not valid! :(')

