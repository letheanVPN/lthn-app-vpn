#!/bin/sh

ERRORS=false

if [ -z "$CLIENT" ] && [ -z "$SERVER" ]; then
    SERVER=y
    CLIENT=y
fi

if [ "`whoami`" = "root" ]; then
    echo "Do not run install as root! It will invoke sudo automatically. Exiting!"
    exit 2
fi

if [ -z "$LTHN_PREFIX" ]; then
    echo "You must configure lethean-vpn!"
    exit 1
fi

install_dir() {
    sudo install $2 $3 $4 $5 $6 -o "$LTHN_USER" -g "$LTHN_GROUP" -d "$INSTALL_PREFIX/$LTHN_PREFIX/$1"
}

nopip() {
    echo 'You have to manually install python packages '$*
}

# Old lthnvpnd had /var/log as socket. Remove
[ -S "$INSTALL_PREFIX/$LTHN_PREFIX/var/log" ] && rm -f "$INSTALL_PREFIX/$LTHN_PREFIX/var/log"

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

if ! [ -r "$INSTALL_PREFIX/$LTHN_PREFIX/dev/net/tun" ]; then
  install_dir /dev/net/
  sudo mknod "$INSTALL_PREFIX/$LTHN_PREFIX/dev/net/tun" c 10 200
fi
sudo chmod 600 "$INSTALL_PREFIX/$LTHN_PREFIX/dev/net/tun"
sudo chown "$LTHN_USER" "$INSTALL_PREFIX/$LTHN_PREFIX/dev/net/tun"

# Copy bin files
sudo install -o "$LTHN_USER" -g "$LTHN_GROUP" -m 770 ./server/unpriv-ip.sh $INSTALL_PREFIX/$LTHN_PREFIX/bin/
if [ -n "$SERVER" ]; then
    sudo install -o "$LTHN_USER" -g "$LTHN_GROUP" -m 770 ./server/lthnvpnd.py $INSTALL_PREFIX/$LTHN_PREFIX/bin/lthnvpnd
    sudo install -o "$LTHN_USER" -g "$LTHN_GROUP" -m 770 ./server/lvmgmt.py $INSTALL_PREFIX/$LTHN_PREFIX/bin/lvmgmt
    sed -i 's^/usr/bin/python^'$PYTHON_BIN'^' $INSTALL_PREFIX/$LTHN_PREFIX/bin/lthnvpnd
    sed -i 's^/usr/bin/python^'$PYTHON_BIN'^' $INSTALL_PREFIX/$LTHN_PREFIX/bin/lvmgmt
fi
if [ -n "$CLIENT" ]; then
    sudo install -o "$LTHN_USER" -g "$LTHN_GROUP" -m 770 ./client/lthnvpnc.py $INSTALL_PREFIX/$LTHN_PREFIX/bin/lthnvpnc
    sed -i 's^/usr/bin/python^'$PYTHON_BIN'^' $INSTALL_PREFIX/$LTHN_PREFIX/bin/lthnvpnc
fi

# Copy lib files
for f in lib/*py; do
    sudo install -o "$LTHN_USER" -g "$LTHN_GROUP" -m 440 $f $INSTALL_PREFIX/$LTHN_PREFIX/lib/
done
sed -i 's^/opt/lthn^'"$LTHN_PREFIX"'^' $INSTALL_PREFIX/$LTHN_PREFIX/lib/config.py
sed -i 's^/usr/sbin/openvpn^'"$OPENVPN_BIN"'^' $INSTALL_PREFIX/$LTHN_PREFIX/lib/config.py
sed -i 's^/usr/sbin/haproxy^'"$HAPROXY_BIN"'^' $INSTALL_PREFIX/$LTHN_PREFIX/lib/config.py

# Copy dist configs
(cd conf; for f in *tmpl *ips *doms *http; do
    sudo install -C -o "$LTHN_USER" -g "$LTHN_GROUP" -m 440 ./$f $INSTALL_PREFIX/$LTHN_PREFIX/etc/
done)

if [ -n "$SERVER" ]; then
  if [ -f build/etc/systemd/system/lthnvpnd.service ]; then
    echo "Installing service file /etc/systemd/system/lthnvpnd.service as user $LTHN_USER"
    sed -i "s^User=lthn^User=$LTHN_USER^" build/etc/systemd/system/lthnvpnd.service
    sudo cp build/etc/systemd/system/lthnvpnd.service /etc/systemd/system/
    sudo cp conf/lthnvpnd.env /etc/default/lthnvpnd
  fi
fi

#if [ -n "$CLIENT" ]; then
#  if [ -f build/etc/systemd/system/lthnvpnd.service ]; then
#    echo "Installing service file /etc/systemd/system/lthnvpnc.service as user $LTHN_USER"
#    sed -i "s^User=lthn^User=$LTHN_USER^" build/etc/systemd/system/lthnvpnc.service
#    sudo cp build/etc/systemd/system/lthnvpnc.service /etc/systemd/system/
#    sudo cp conf/lthnvpnc.env /etc/default/lthnvpnc
#  fi
#fi

# Copy generated configs
if [ -n "$FORCE" ]; then
    sudo cp -va build/etc/* $INSTALL_PREFIX/$LTHN_PREFIX/etc/
else
    sudo cp -nva build/etc/* $INSTALL_PREFIX/$LTHN_PREFIX/etc/
fi

if [ -n "$SERVER" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/dispatcher.ini ]; then
    echo "ERROR: No dispatcher config file found. You have to create $INSTALL_PREFIX/$LTHN_PREFIX/etc/dispatcher.ini"
    echo "Use conf/dispatcher_example.ini as example"
    ERRORS=true
  fi
fi

if [ -n "$SERVER" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/sdp.json ]; then
    echo "ERROR: No SDP config file found. You can use lvmgmt --generate-sdp to create it for you."
    ERRORS=true
  fi
fi

if [ -n "$SERVER" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/ca/index.txt ]; then
        if [ -f ./build/ca/index.txt ]; then
            install_dir etc/ca -m 700
            cp -R build/ca/* $INSTALL_PREFIX/$LTHN_PREFIX/etc/ca/
        else
            echo "CA directory $INSTALL_PREFIX/$LTHN_PREFIX/etc/ca/ not prepared! You should generate by configure or use your own CA!"
            ERRORS=true
        fi
  fi
fi

if [ -n "$SERVER" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/dhparam.pem ] && [ -f build/dhparam.pem ]; then
    install build/dhparam.pem $INSTALL_PREFIX/$LTHN_PREFIX/etc/
  fi
fi

if [ -n "$SERVER" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/openvpn.tlsauth ] && [ -n "$OPENVPN_BIN" ] ; then
    "$OPENVPN_BIN" --genkey --secret $INSTALL_PREFIX/$LTHN_PREFIX/etc/openvpn.tlsauth
  fi
fi

sudo chown -R $LTHN_USER:$LTHN_GROUP $INSTALL_PREFIX/$LTHN_PREFIX/etc/
sudo chmod -R 700 $INSTALL_PREFIX/$LTHN_PREFIX/etc/

if [ "$ERRORS" = true ]; then
    echo "Finished installing but with errors. See above."
else
    echo "Finished installing successfully!"
fi
