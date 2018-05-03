#!/bin/bash

set -x

SCRIPT_PATH=$(dirname `which $0`)

cd $SCRIPT_PATH


# Clean up all the build and dist directories
# top level + at the xr, admin and host level

if [[ -d build ||  -d dst ]]; then
    rm -r build/
    rm -r dist/
fi
