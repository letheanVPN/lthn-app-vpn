#!/bin/sh

ERRORS=false

if [ "$USER" = "root" ]; then
    echo "Do not run install as root! It will invoke sudo automatically. Exiting!"
    exit 2
fi 

if [ -z "$ITNS_PREFIX" ]; then
    echo "You must configure intense-vpn!"
    exit 1
fi

install_dir() {
    sudo install $2 $3 $4 $5 $6 -o "$ITNS_USER" -g "$ITNS_GROUP" -d "$INSTALL_PREFIX/$ITNS_PREFIX/$1"
}

nopip() {
    echo 'You have to manually install python packages '$*
}

# Old itnsdispatcher had /var/log as socket. Remove
[ -S "$INSTALL_PREFIX/$ITNS_PREFIX/var/log" ] && rm -f "$INSTALL_PREFIX/$ITNS_PREFIX/var/log"

# Create directories
install_dir /
install_dir bin
install_dir etc
install_dir var -m 770
install_dir var/ha -m 770
install_dir var/ovpn -m 770
install_dir var/log -m 770
install_dir var/run -m 770
install_dir lib
install_dir dev
install_dir dev/net

if ! [ -r "$INSTALL_PREFIX/$ITNS_PREFIX/dev/net/tun" ]; then
  install_dir /dev/net/
  sudo mknod "$INSTALL_PREFIX/$ITNS_PREFIX/dev/net/tun" c 10 200
fi
sudo chmod 600 "$INSTALL_PREFIX/$ITNS_PREFIX/dev/net/tun"
sudo chown "$ITNS_USER" "$INSTALL_PREFIX/$ITNS_PREFIX/dev/net/tun"

# Copy bin files
sudo install -o "$ITNS_USER" -g "$ITNS_GROUP" -m 770 ./server/itnsdispatcher.py $INSTALL_PREFIX/$ITNS_PREFIX/bin/itnsdispatcher
sudo install -o "$ITNS_USER" -g "$ITNS_GROUP" -m 770 ./client/itnsconnect.py $INSTALL_PREFIX/$ITNS_PREFIX/bin/itnsconnect
sed -i 's^/usr/bin/python^'$PYTHON_BIN'^' $INSTALL_PREFIX/$ITNS_PREFIX/bin/itnsdispatcher
sed -i 's^/usr/bin/python^'$PYTHON_BIN'^' $INSTALL_PREFIX/$ITNS_PREFIX/bin/itnsconnect

# Copy lib files
for f in lib/*py; do
    sudo install -o "$ITNS_USER" -g "$ITNS_GROUP" -m 440 $f $INSTALL_PREFIX/$ITNS_PREFIX/lib/
done
sed -i 's^/opt/itns^'"$ITNS_PREFIX"'^' $INSTALL_PREFIX/$ITNS_PREFIX/lib/config.py
sed -i 's^/usr/sbin/openvpn^'"$OPENVPN_BIN"'^' $INSTALL_PREFIX/$ITNS_PREFIX/lib/config.py
sed -i 's^/usr/sbin/haproxy^'"$HAPROXY_BIN"'^' $INSTALL_PREFIX/$ITNS_PREFIX/lib/config.py

# Copy dist configs
(cd conf; for f in *tmpl *ips *doms *http; do
    sudo install -C -o "$ITNS_USER" -g "$ITNS_GROUP" -m 440 ./$f $INSTALL_PREFIX/$ITNS_PREFIX/etc/ 
done)

if [ -f build/etc/systemd/system/itnsdispatcher.service ]; then
    echo "Installing service file /etc/systemd/system/itnsdispatcher.service as user $ITNS_USER"
    sed -i "s^User=root^User=$ITNS_USER^" build/etc/systemd/system/itnsdispatcher.service
    if ! diff -q build/etc/systemd/system/itnsdispatcher.service /etc/systemd/system/itnsdispatcher.service; then
      sudo cp build/etc/systemd/system/itnsdispatcher.service /etc/systemd/system/
    fi
fi

# Copy generated configs
if [ -n "$FORCE" ]; then
    sudo cp -va build/etc/* $INSTALL_PREFIX/$ITNS_PREFIX/etc/
else
    sudo cp -nva build/etc/* $INSTALL_PREFIX/$ITNS_PREFIX/etc/
fi

if ! [ -f $INSTALL_PREFIX/$ITNS_PREFIX/etc/dispatcher.ini ]; then
    echo "ERROR: No dispatcher config file found. You have to create $INSTALL_PREFIX/$ITNS_PREFIX/etc/dispatcher.ini"
    echo "Use conf/dispatcher_example.ini as example"
    ERRORS=true
fi

if ! [ -f $INSTALL_PREFIX/$ITNS_PREFIX/etc/sdp.json ]; then
    echo "ERROR: No SDP config file found. You can use itnsdispatcher --generate-sdp to create it for you."
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

sudo chown -R $ITNS_USER:$ITNS_GROUP $INSTALL_PREFIX/$ITNS_PREFIX/etc/
sudo chmod -R 700 $INSTALL_PREFIX/$ITNS_PREFIX/etc/

if [ "$ERRORS" = true ]; then
    echo "Finished installing but with errors. See above."
else
    echo "Finished installing successfully!"
fi
