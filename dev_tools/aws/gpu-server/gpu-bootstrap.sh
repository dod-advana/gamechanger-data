#!/usr/bin/env bash
set -o nounset
set -o errexit

# set as preferred
CUDA_MAJOR_VERSION="11"
# set as preferred
CUDA_MINOR_VERSION="2"
# from /etc/os-release
DISTRO=rhel7
# from /bin/arch
ARCH=x86_64

# Expire cached repo lists
yum clean expire-cache
# Add EPEL Repo
yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

# on CSN commercial advana rhel7 govcloud AMI, it was 3.10.0-1127.el7.x86_64
KERNEL_RELEASE="$(uname -r)"
# Install kernel development libs and headers
yum install -y kernel-devel-"$KERNEL_RELEASE" kernel-headers-"$KERNEL_RELEASE"

# https://access.redhat.com/articles/4599971
yum-config-manager --enable \
  rhel-7-server-rhui-optional-rpms \
  rhel-7-server-rhui-extras-rpms
# if doesn't work, see workaround below
yum install -y vulkan-filesystem

# workaround for installing vulkan-filesystem if AWS RHEL repos are not available above
# yum install -y http://mirror.centos.org/centos/7/os/x86_64/Packages/vulkan-filesystem-1.1.97.0-1.el7.noarch.rpm

# add cuda repository
yum-config-manager --add-repo http://developer.download.nvidia.com/compute/cuda/repos/${DISTRO}/${ARCH}/cuda-${DISTRO}.repo

# install nvidia drivers & CUDA
# we can just use latest version because they're backwards compatible for CUDA purposes
# nvidia-driver-latest-dkms
yum install -y \
  cuda-runtime-"$CUDA_MAJOR_VERSION"-"$CUDA_MINOR_VERSION" \
  cuda-toolkit-"$CUDA_MAJOR_VERSION"-"$CUDA_MINOR_VERSION"

# make sure alt drivers never get used
cat << EOF | sudo tee --append /etc/modprobe.d/blacklist.conf
blacklist vga16fb
blacklist nouveau
blacklist rivafb
blacklist nvidiafb
blacklist rivatv
EOF

# makew sure FIPS enforcement is disabled so Python packages that want to use functions like md5 can do so without breaking
# this is not used for any crypto purposes and authentication/authorization/encryption does not happen on this server anyway
sed -r '/^[:blank:]*GRUB_CMDLINE_LINUX/ s/fips=1/fips=0/' -i /etc/default/grub

# generate new grub cfg
grub2-mkconfig -o /boot/grub2/grub.cfg

# and reboot
reboot