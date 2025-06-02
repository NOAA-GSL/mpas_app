#!/bin/sh

if [ $# = 0 ]; then
   L_MACHINE=${MACHINE}
   cat << EOF_USAGE
Usage: source etc/lmod-setup.sh PLATFORM

OPTIONS:
   PLATFORM - name of machine you are building on
      (e.g. hera | jet | hercules)
EOF_USAGE
   exit 1
else
   L_MACHINE=$1
fi

if [ "$L_MACHINE" != wcoss2 ]; then
  [[ ${SHELLOPTS} =~ nounset ]] && has_mu=true || has_mu=false
  [[ ${SHELLOPTS} =~ errexit ]] && has_me=true || has_me=false
  $has_mu && set +u
  $has_me && set +e
  source /etc/profile
  $has_mu && set -u
  $has_me && set -e
fi

if $(echo "hera hercules jet ursa" | grep -q "\b$L_MACHINE\b"); then
   module purge
else
   echo "ERROR: Unsupported platform ${L_MACHINE}"
   return 1
fi
