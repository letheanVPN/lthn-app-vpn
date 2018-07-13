#!/usr/bin/env bash

# set PATH to find all binaries
PATH=$PATH:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin
export TOPDIR=$(realpath $(dirname $0))
export PARMS="$@"

# Static defaults
ITNS_PREFIX=/opt/itns/

# General usage help
usage() {
   echo $0 "[--openvpn-bin bin] [--openssl-bin bin] [--haproxy-bin bin] [--python-bin bin] [--pip-bin bin] [--runas-user user] [--runas-group group] [--prefix prefix] [--with-capass pass] [--generate-ca] [--generate-dh] [--generate-sdp] [--install-service]"
   echo
   exit
}

# Find command or report error. If env is already set, only test availability
# $1 - cmd
# $2 - env to get/set
# $3 - optional
findcmd() {
    local cmd="$1"
    local env="$2"
    eval "bin=\$$env"

    if [ -z "$bin" ]; then
        bin=$(which $cmd)
    fi

    if [ -z "$3" ]; then
      if [ -z "$bin" ]; then
        echo "Missing $cmd!"
      else
        echo "Found $env at $bin"
      fi
    else
      if [ -n "$bin" ]; then
        echo "Found $env at $bin"
      else
        echo "Not found $cmd"
      fi
    fi
    eval "$env=$bin"
}

defaults() {
    findcmd openvpn OPENVPN_BIN optional
    findcmd openssl OPENSSL_BIN
    findcmd haproxy HAPROXY_BIN
    if $HAPROXY_BIN -v |grep -qv "version 1.7"; then
        echo "Your haproxy is outdated! You need at least 1.7 version:"
        $HAPROXY_BIN -v
        exit 1
    fi
    findcmd python3 PYTHON_BIN
    findcmd pip3 PIP_BIN optional
    findcmd sudo SUDO_BIN optional

    [ -z "$ITNS_USER" ] && ITNS_USER=root
    [ -z "$ITNS_GROUP" ] && ITNS_GROUP=root
}

summary() {
    echo
    if [ -z "$PYTHON_BIN" ] || [ -z "$HAPROXY_BIN" ] || [ -z "$OPENSSL_BIN" ]; then
        echo "Missing some dependencies to run intense-vpn. Look above. Exiting."
        usage
        exit 1
    fi

    echo "Intense-vpn configured."
    echo "Python bin:   $PYTHON_BIN"
    echo "pip bin:      $PIP_BIN"
    echo "sudo bin:     $SUDO_BIN"
    echo "Openssl bin:  $OPENSSL_BIN"
    echo "Openvpn bin:  $OPENVPN_BIN"
    echo "HAproxy bin:  $HAPROXY_BIN"
    echo "Prefix:       $ITNS_PREFIX"
    echo "Bin dir:      $bin_dir"
    echo "Conf dir:     $sysconf_dir"
    echo "CA dir:       $ca_dir"
    echo "Data dir:     $data_dir"
    echo "Temp dir:     $tmp_dir"
    echo "Run as user:  $ITNS_USER"
    echo "Run as group:  $ITNS_GROUP"
    echo
}


# Generate root CA and keys
generate_ca() {
    local prefix="$1"
    local cn="$2"

    echo "Generating CA $cn"
    cd $prefix || exit 2
    mkdir -p private certs csr newcerts || exit 2
    touch index.txt
    echo -n 00 >serial
    "${OPENSSL_BIN}" genrsa -aes256 -out private/ca.key.pem -passout pass:$cert_pass 4096
    chmod 400 private/ca.key.pem
    "${OPENSSL_BIN}" req -config $TOPDIR/conf/ca.cfg -batch -subj "/CN=$cn" -passin pass:$cert_pass \
      -key private/ca.key.pem \
      -new -x509 -days 7300 -sha256 -extensions v3_ca \
      -out certs/ca.cert.pem
    if ! [ -f certs/ca.cert.pem ]; then
        echo "Error generating CA! See messages above."
        exit 2
    fi
}

generate_crt() {
    local name="$1"
    local cn="$2"
    echo "Generating crt (name=$name,cn=$cn)"
    "${OPENSSL_BIN}" genrsa -aes256 \
      -out private/$name.key.pem -passout pass:$cert_pass 4096
    chmod 400 private/$name.key.pem
    "${OPENSSL_BIN}" req -config $TOPDIR/conf/ca.cfg -batch -subj "/CN=$cn" -passin "pass:$cert_pass" \
      -key private/$name.key.pem \
      -new -sha256 -out csr/$name.csr.pem
    "${OPENSSL_BIN}" ca -batch -config $TOPDIR/conf/ca.cfg -subj "/CN=$cn" -passin "pass:$cert_pass" \
      -extensions server_cert -days 375 -notext -md sha256 \
      -in csr/$name.csr.pem \
      -out certs/$name.cert.pem
    (cat certs/ca.cert.pem certs/$name.cert.pem; openssl rsa -passin "pass:$cert_pass" -text <private/$name.key.pem) >certs/$name.all.pem
    (cat certs/$name.cert.pem; openssl rsa -passin "pass:$cert_pass" -text <private/$name.key.pem) >certs/$name.both.pem
    if ! [ -f certs/$name.cert.pem ]; then
        echo "Error generating cert $name! See messages above."
        exit 2
    fi
}

generate_env() {
    cat <<EOF
ITNS_PREFIX="$ITNS_PREFIX"
OPENVPN_BIN="$OPENVPN_BIN"
PYTHON_BIN="$PYTHON_BIN"
PIP_BIN="$PIP_BIN"
SUDO_BIN="$SUDO_BIN"
HAPROXY_BIN="$HAPROXY_BIN"
OPENSSL_BIN="$OPENSSL_BIN"
ITNS_USER="$ITNS_USER"
ITNS_GROUP="$ITNS_GROUP"

export ITNS_PREFIX OPENVPN_BIN HAPROXY_BIN OPENSSL_BIN ITNS_USER ITNS_GROUP
EOF
}

if [ -f build/env.sh ]; then
    defaults=1
    . build/env.sh
else
    defaults
fi

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -h|--help)
        usage
    ;;
    --prefix)
        ITNS_PREFIX="$2"
        shift
        shift
    ;;
    --openvpn-bin)
        OPENVPN_BIN="$2"
        shift
        shift
    ;;
    --haproxy-bin)
        HAPROXY_BIN="$2"
        shift
        shift
    ;;
    --openssl-bin)
        OPENSSL_BIN="$2"
        shift
        shift
    ;;
    --python-bin)
        PYTHON_BIN="$2"
        shift
        shift
    ;;
    --pip-bin)
        PIP_BIN="$2"
        shift
        shift
    ;;
    --sudo-bin)
        SUDO_BIN="$2"
        shift
        shift
    ;;
    --runas-user)
        ITNS_USER="$2"
        shift
        shift
    ;;
    --runas-group)
        ITNS_GROUP="$2"
        shift
        shift
    ;;
    --with-capass)
        cert_pass="$2"
        shift
        shift
    ;;
    --with-cn)
        cert_cn="$2"
        shift
        shift
    ;;
    --generate-ca)
        generate_ca=1
        shift
    ;;
    --generate-dh)
        generate_dh=1
        shift
    ;;
    --generate-sdp)
        generate_sdp=1
        shift
    ;;
    --install-service)
        install_service=1
        shift
    ;;
    *)
    echo "Unknown option $1"
    usage
    exit 1;
    ;;
esac
done

bin_dir=${ITNS_PREFIX}/bin/
sysconf_dir=${ITNS_PREFIX}/etc/
ca_dir=${ITNS_PREFIX}/etc/ca/
data_dir=${ITNS_PREFIX}/var/
tmp_dir=${ITNS_PREFIX}/tmp/

mkdir -p build
if [ -n "$generate_ca" ] && ! [ -f build/ca/index.txt ]; then
    export cert_pass cert_cn
    if [ -z "$cert_pass" ] || [ -z "$cert_cn" ] ; then
        echo "You must specify --with-capass yourpassword --with_cn CN!"
        exit 2
    fi
    if [ "$cert_pass" = "1234" ]; then
    	echo "Generating with default password!"
    fi
    (
    rm -rf build/ca
    mkdir -p build/ca
    generate_ca build/ca/ "$cert_cn"
    generate_crt openvpn "$cert_cn.openvpn"
    generate_crt ha "$cert_cn.ha"
    )
fi

if [ -n "$generate_dh" ]; then
    if ! [ -f  build/dhparam.pem ]; then 
      "$OPENSSL_BIN" dhparam -out build/dhparam.pem 2048
    fi
else
    if [ -f etc/dhparam.pem ]; then
        cp etc/dhparam.pem build/
    fi
fi

if [ -n "$generate_sdp" ]; then
    "$PYTHON_BIN" server/dispatcher/config.py sdp
fi

if [ -n "$install_service" ]; then
    cp conf/itnsdispatcher.service build/
fi

summary
generate_env >| build/env.sh

if [ -n "$PARMS" ]; then
    echo "./configure.sh $PARMS" >configure.log
fi

echo "Used build/env.sh as env. Remove that file for reconfigure."
echo "You can continue by sudo ./install.sh"
echo
