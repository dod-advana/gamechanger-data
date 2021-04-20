#!/usr/bin/env bash
set -o errexit
set -o nounset

##         ##
## CAUTION ## THIS SCRIPT IS SUPPOSED TO ONLY RUN ONCE
##         ##

## set bitbucket username/personal_token vars or script will fail
# BITBUCKET_USERNAME=
# BITBUCKET_PERSONAL_TOKEN=
AUTHORIZED_SSH_HOST_PUBKEY="${AUTHORIZED_SSH_HOST_PUBKEY:-ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCNVC8bLrbwGr8eGar/Lv6fmj8EBhXt0+O38TQCaSgJj5aqhyjscdhjL3Uha9UT2fLR1ZJGIGUAkod1pogvnHFsc0xkhMCxZaLiY4pzH+IrZF0/r29Em+8psdB7SHSPFsl0zh2BB8LFfjwsPNMH0Xp02pwjfQtSeu76edsI5AH1K5hsVaoK3tHtKNpe/HDdZMffpBSMorcXcEBtwa163cwIDQvItY2pF0TbDdh7HaZNpOJjjVH8lKGmR5NfY9phjL3AWSsdtFN7IzXpRNMBdDAcoDzqpOfGOUXHCo/5QoU3xCKvfuA5mh6XF9xT5myK/Yvs5dKUNFH9TYX4rqfrPN19 uot}"

# make sure we got git, python, zip
yum install -y git python3 python3-devel python3-pip zip unzip

# create gamechanger user
useradd gamechanger
usermod -aG wheel gamechanger

# set password to "gamechanger"
echo gamechanger | passwd gamechanger --stdin

# set git credentials
echo "https://${BITBUCKET_USERNAME}:{$BITBUCKET_PERSONAL_TOKEN}@bitbucket.di2e.net" > /home/gamechanger/.git-credentials
chmod 600 /home/gamechanger/.git-credentials

# set credential helper to store creds
printf "[credential]\n\thelper = store\n" > /home/gamechanger/.gitconfig
chmod 664 /home/gamechanger/.gitconfig

# allow login with UOT ssh key
mkdir /home/gamechanger/.ssh
chmod 700 /home/gamechanger/.ssh
echo "" \
  > /home/gamechanger/.ssh/authorized_keys
chmod 600 /home/gamechanger/.ssh/authorized_keys

# fix permissions in user home dir
chown -R gamechanger:gamechanger /home/gamechanger/

# pull down copy of the repo
su --login \
  --command='git clone https://bitbucket.di2e.net/scm/uot/gamechanger.git ; cd gamechanger; git checkout origin/dev; git checkout -b dev; git branch --set-upstream-to=origin/dev dev' \
  gamechanger