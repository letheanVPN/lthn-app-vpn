#!/bin/sh

. build/env.sh
ERRORS=false

if [ -z "$ITNS_PREFIX" ]; then
    echo "You must configure intense-vpn!"
    exit 1
fi

install_dir() {
    install $2 $3 $4 $5 $6 -o "$ITNS_USER" -g "$ITNS_GROUP" -d "$INSTALL_PREFIX/$ITNS_PREFIX/$1"
}

nopip() {
    echo 'You have to manually install python packages '$*
}

# Create directories
install_dir 
install_dir bin
install_dir etc
install_dir var -m 770
install_dir var/ha -m 770
install_dir var/ovpn -m 770
install_dir lib
install_dir dev

# Copy bin files
install -o "$ITNS_USER" -g "$ITNS_GROUP" -m 770 ./server/dispatcher/itnsdispatcher.py $INSTALL_PREFIX/$ITNS_PREFIX/bin/itnsdispatcher
sed -i 's^/usr/bin/python^'$PYTHON_BIN'^' $INSTALL_PREFIX/$ITNS_PREFIX/bin/itnsdispatcher

# Copy lib files
for f in authids.py  config.py sdp.py  services.py  sessions.py  util.py; do
    install -o "$ITNS_USER" -g "$ITNS_GROUP" -m 440 ./server/dispatcher/$f $INSTALL_PREFIX/$ITNS_PREFIX/lib/
done
sed -i 's^/opt/itns^'"$ITNS_PREFIX"'^' $INSTALL_PREFIX/$ITNS_PREFIX/lib/config.py
sed -i 's^/usr/sbin/openvpn^'"$OPENVPN_BIN"'^' $INSTALL_PREFIX/$ITNS_PREFIX/lib/config.py
sed -i 's^/usr/sbin/haproxy^'"$HAPROXY_BIN"'^' $INSTALL_PREFIX/$ITNS_PREFIX/lib/config.py

# Copy configs
(cd conf; for f in *tmpl *cfg *ips *doms *http; do
    install -C -o "$ITNS_USER" -g "$ITNS_GROUP" -m 440 ./$f $INSTALL_PREFIX/$ITNS_PREFIX/etc/ 
done)
if ! [ -f $INSTALL_PREFIX/$ITNS_PREFIX/etc/dispatcher.json ]; then
    echo "ERROR: No dispatcher config file found. You have to create $INSTALL_PREFIX/$ITNS_PREFIX/etc/dispatcher.json"
    echo "Use conf/dispatcher_example.json as example"
    ERRORS=true
fi

if ! [ -f $INSTALL_PREFIX/$ITNS_PREFIX/etc/sdp.json ]; then
    echo "ERROR: No SDP config file found. You have to create $INSTALL_PREFIX/$ITNS_PREFIX/etc/sdp.json"
    echo "Use conf/sdp_example.json as example and create your own config"
    ERRORS=true 
fi

if ! [ -f $INSTALL_PREFIX/$ITNS_PREFIX/etc/ca/index.txt ]; then
        if [ -f ./build/ca/index.txt ]; then
            install_dir etc/ca -m 700
            cp -R build/ca/* $INSTALL_PREFIX/$ITNS_PREFIX/etc/ca/
        else
            echo "CA directory $INSTALL_PREFIX/$ITNS_PREFIX/etc/ca/ not prepared! You should generate by configure or use your own CA!"
            exit 3
        fi
fi

if ! [ -f $INSTALL_PREFIX/$ITNS_PREFIX/etc/dhparam.pem ] && [ -f build/dhparam.pem ]; then
    install build/dhparam.pem $INSTALL_PREFIX/$ITNS_PREFIX/etc/
fi

if ! [ -f $INSTALL_PREFIX/$ITNS_PREFIX/etc/openvpn.tlsauth ] && [ -n "$OPENVPN_BIN" ] ; then
    "$OPENVPN_BIN" --genkey --secret $INSTALL_PREFIX/$ITNS_PREFIX/etc/openvpn.tlsauth
fi

chown -R $ITNS_USER:$ITNS_GROUP $INSTALL_PREFIX/$ITNS_PREFIX/etc/
chmod -R 700 $INSTALL_PREFIX/$ITNS_PREFIX/etc/

if [ "$ERRORS" = true ]; then
    echo "Finished installing but with errors. See above."
else
    echo "Finished installing successfully!"
fi
