#!/bin/sh

. env.sh

if [ -z "$ITNS_PREFIX" ]; then
    echo "You must configure intense-vpn!"
    exit 1
fi


# Generate root CA and keys
generate_ca() {
    local prefix="$1"

    cd $prefix || exit 2
    mkdir -p private certs csr newcerts || exit 2
    touch index.txt
    echo -n 00 >serial
    $openssl_bin genrsa -aes256 -out private/ca.key.pem -passout pass:abcd 4096 
    chmod 400 private/ca.key.pem
    $openssl_bin req -config $sysconf_dir/openssl.cnf -passin pass:abcd \
      -key private/ca.key.pem \
      -new -x509 -days 7300 -sha256 -extensions v3_ca \
      -out certs/ca.cert.pem 
}

generate_crt() {
    local name="$1"
    $openssl_bin genrsa -aes256 \
      -out private/$name.key.pem -passout pass:abcd 4096
    chmod 400 private/$name.key.pem
    $openssl_bin req -config $sysconf_dir/openssl.cnf -subj "/CN=$name" -passin pass:abcd \
      -key private/$name.key.pem \
      -new -sha256 -out csr/$name.csr.pem
    $openssl_bin ca -batch -config $sysconf_dir/openssl.cnf -passin pass:abcd \
      -extensions server_cert -days 375 -notext -md sha256 \
      -in csr/$name.csr.pem \
      -out certs/$name.cert.pem
}

set_perms() {
    chown -R "$runas_user:$runas_group"  "$data_dir" "$tmp_dir"
    chmod 770 "$data_dir" "$tmp_dir"
}