#!/usr/bin/env bash
set -o nounset
set -o errexit

##
### Bootstrapping steps must be complete at this point
###  -- gpu drivers, cuda, and all of that should have been installed by now and reboot completed
##

##
### BASIC APP REQUIRED OS PACKAGES AND FIREWALL CONFIG
##

# other basic packages git/zip/python3
yum install -y git zip unzip python3 python3-pip python3-devel

# whitelist APP port in firewall (if it's even being used)
firewall-cmd --add-port=5000/tcp --permanent
firewall-cmd --reload

##
### REDIS SETUP
##

# install redis (this one or whichever one was already approved for Advana)
yum -y install https://rpms.remirepo.net/enterprise/remi-release-7.rpm
yum install -y redis --enablerepo=remi
# make sure redis starts up after reboots
systemctl enable redis
# start redis now
systemctl start redis

##
### PYTHON PACKAGE SETUP
##

# create application python env
python3 -m venv /opt/gc-transformer-venv-green
# first base python pip, setuptools, and wheel packages have to be upgraded since system ones are too old to work properly
/opt/gc-transformer-venv-green/bin/pip install --upgrade pip setuptools wheel

# install packages into the venv
/opt/gc-transformer-venv-green/bin/pip install -r /root/gc-setup-scripts/venv-requirements.txt
