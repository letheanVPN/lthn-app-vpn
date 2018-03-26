#!/usr/bin/env bash

# set PATH to find all binaries
PATH=$PATH:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# Static defaults
prefix=/opt/itns/vpn

# General usage help
usage() {
   echo $0 [--with-openvpn bin] [--with-openssl bin] [--with-haproxy bin]
   echo
   exit
}

# Find command or report error. If env is already set, only test availability
# $1 - cmd
# $2 - env to get/set
findcmd() {
    local cmd="$1"
    local env="$2"
    eval "bin=\$$env"

    if [ -z "$bin" ]; then
        bin=$(which $cmd)
    fi

    if [ -z "$bin" ]; then
        echo "Missing $cmd!"
    else
        echo "Found $env at $bin"
    fi
    eval "$env=$bin"
}

defaults() {
    findcmd openvpn openvpn_bin
    findcmd openssl openssl_bin
    findcmd haproxy haproxy_bin
    findcmd python python_bin

    bin_dir=${prefix}/bin/
    sysconf_dir=${prefix}/etc/
    ca_dir=${prefix}/etc/ca/
    data_dir=${prefix}/var/
    tmp_dir=${prefix}/tmp/
}

summary() {
    echo
    if [ -z "$python_bin" ] || [ -z "$haproxy_bin" ] || [ -z "$openvpn_bin" ] || [ -z "$openssl_bin" ]; then
        echo "Missing some dependencies to run HA. Look above. Exiting."
        usage
        exit 1
    fi
    echo "Intense-vpn configured."
    echo "Python bin:   $python_bin"
    echo "Openssl bin:  $openssl_bin"
    echo "Openvpn bin:  $openvpn_bin"
    echo "HAproxy bin:  $haproxy_bin"
    echo "Prefix:       $prefix"
    echo "Bin dir:      $bin_dir"
    echo "Conf dir:     $sysconf_dir"
    echo "CA dir:       $ca_dir"
    echo "Data dir:     $data_dir"
    echo "Temp dir:     $tmp_dir"
    echo
}

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -h)
    usage
    ;;
    --prefix)
    prefix="$2"
    shift
    shift
    ;;
    --openvpn-bin)
    openvpn_bin="$2"
    shift
    shift
    ;;
    --haproxy_bin)
    haproxy_bin="$2"
    shift
    shift
    ;;
    --openssl_bin)
    openssl_bin="$2"
    shift
    shift
    ;;
esac
done

defaults

summary

exit;