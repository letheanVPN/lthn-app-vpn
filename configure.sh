#!/usr/bin/env bash

# set PATH to find all binaries
PATH=$PATH:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin

# Static defaults
prefix=/opt/itns/

# General usage help
usage() {
   echo $0 [--openvpn-bin bin] [--openssl-bin bin] [--haproxy-bin bin] [--runas-user user] [--runas-group group] [--prefix prefix] [--generate-ca]
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

    [ -z "$runas_user" ] && runas_user=root
    [ -z "$runas_group" ] && runas_group=root
}

summary() {
    echo
    if [ -z "$python_bin" ] || [ -z "$haproxy_bin" ] || [ -z "$openvpn_bin" ] || [ -z "$openssl_bin" ]; then
        echo "Missing some dependencies to run HA. Look above. Exiting."
        usage
        exit 1
    fi
    if ! [ -f $ca_dir/index.txt ]; then
        echo "CA directory $ca_dir not prepared! You should generate by configure or use your own CA!"
        exit 3
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
    echo "Run as user:  $runas_user"
    echo "Run as group:  $runas_group"
    echo
}

generate_env() {
    cat >env.sh <<EOF
ITNS_PREFIX=$prefix
OPENVPN_BIN=$openvpn_bin
HAPROXY_BIN=$haproxy_bin
OPENSSL_BIN=$openssl_bin
ITNS_USER=$runas_user
ITNS_GROUP=$runas_group
GENERATE_CA=$generate_ca

export ITNS_PREFIX OPENVPN_BIN HAPROXY_BIN OPENSSL_BIN ITNS_USER ITNS_GROUP GENERATE_CA
EOF
}

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -h|--help)
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
    --haproxy-bin)
        haproxy_bin="$2"
        shift
        shift
    ;;
    --openssl-bin)
        openssl_bin="$2"
        shift
        shift
    ;;
    --runas-user)
        runas_user="$2"
        shift
        shift
    ;;
    --runas-group)
        runas_group="$2"
        shift
        shift
    ;;
    --generate-ca)
        generate_ca=1
        shift
    ;;
    *)
    echo "Unknown option $1"
    usage
    exit 1;
    ;;
esac
done

defaults
if [ -n "$generate_ca" ]; then
    mkdir ca
    if [ -f $ca_dir/index.txt ]; then
        echo "Will not generate new CA over existing! Backup and remove $ca_dir and rerun!"
        exit 2
    fi
    if ! [ -d $ca_dir ]; then
        mkdir -p $ca_dir || exit
    fi
    generate_ca $ca_dir
    generate_crt openvpn
    generate_crt ha
fi
summary
generate_env

echo "You can contunue by ./install.sh"
