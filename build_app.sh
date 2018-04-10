#!/bin/bash
set -x

SCRIPT_PATH=$(dirname `which $0`)

cd $SCRIPT_PATH

#Clean up
rm -r build/
rm -r dist/


# First build the individual cron scripts
pyinstaller specs/xr.spec
pyinstaller specs/admin.spec
pyinstaller specs/host.spec
pyinstaller specs/collector.spec

# Now build the higher level binary

pyinstaller specs/main.spec
