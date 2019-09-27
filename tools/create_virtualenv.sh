#!/bin/bash

virtualenv='/tmp/acts_preupload_virtualenv'

python3 -m pip install virtualenv
python3 -m virtualenv -p python3 $virtualenv
cp -r acts/framework $virtualenv/
cd $virtualenv/framework
$virtualenv/bin/python3 setup.py develop
cd -
