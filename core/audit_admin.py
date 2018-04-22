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


    audit_obj = IosxrAuditMain(domain="ADMIN-LXC",
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



    xml_file = audit_obj.create_xml_dump()

    if audit_obj.validate_xml_dump(xml_file):
        audit_obj.syslogger.info('Valid XML! :)')
        audit_obj.syslogger.info('Successfully created output XML: '+str(xml_file))
        if not audit_obj.transfer_admin_to_host(
                         src=xml_file,
                         dest="/misc/app_host/ADMIN-LXC.xml"):
            audit_obj.syslogger.info("Successfully transferred output XML"
                                "file to host /misc/app_host")
            sys.exit(0)
        else:
            audit_obj.syslogger.info("Failed to transfer output XML to host")
            sys.exit(1)
    else:
        audit_obj.syslogger.info('Output XML Not valid! :(')
        sys.exit(1)
