#!/bin/sh

ERRORS=false

echo > sudo.log 

if [ -z "$CLIENT" ] && [ -z "$SERVER" ]; then
    SERVER=y
    CLIENT=y
fi

if [ "$(whoami)" = "root" ] && [ -z "$NOSUDO" ]; then
    echo "Do not run install as root! It will invoke sudo automatically. Exiting!"
    exit 2
fi 

if [ -z "$LTHN_PREFIX" ]; then
    echo "You must configure intense-vpn!"
    exit 1
fi

mysudo() {
    if [ -n "$NOSUDO" ]; then
      echo "NOSUDO: ignoring $@" >&2
      echo "$@" >>sudo.log
    else
      sudo "$@"
    fi
}

install_dir() {
    if [ -n "$NOSUDO" ]; then
       install -d "$1" "$INSTALL_PREFIX/$LTHN_PREFIX/$1"
    else
      sudo install -o "$LTHN_USER" -g "$LTHN_GROUP" -d "$INSTALL_PREFIX/$LTHN_PREFIX/$1"
    fi
}

install_bin() {
    if [ -n "$NOSUDO" ]; then
      install -m 770 "$1" "$INSTALL_PREFIX/$LTHN_PREFIX/$2"
    else
      sudo install -o "$LTHN_USER" -g "$LTHN_GROUP" -m 770 "$1" "$INSTALL_PREFIX/$LTHN_PREFIX/$2"
      sed -i 's^/usr/bin/python^'$PYTHON_BIN'^' "$INSTALL_PREFIX/$LTHN_PREFIX/$2"
    fi
}

install_lib() {
    if [ -n "$NOSUDO" ]; then
      install -m 440 "$1" "$INSTALL_PREFIX/$LTHN_PREFIX/$2"
    else
      sudo install -m 440 -o "$LTHN_USER" -g "$LTHN_GROUP" "$1" "$INSTALL_PREFIX/$LTHN_PREFIX/$2"
    fi
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
install_dir var
install_dir var/ha
install_dir var/ovpn
install_dir var/log
install_dir var/run
install_dir lib
install_dir dev
install_dir dev/net

if ! [ -r "$INSTALL_PREFIX/$LTHN_PREFIX/dev/net/tun" ]; then
  install_dir /dev/net/
  mysudo mknod "$INSTALL_PREFIX/$LTHN_PREFIX/dev/net/tun" c 10 200
fi
mysudo chmod 600 "$INSTALL_PREFIX/$LTHN_PREFIX/dev/net/tun"
mysudo chown "$LTHN_USER" "$INSTALL_PREFIX/$LTHN_PREFIX/dev/net/tun"

# Copy bin files
install_bin ./server/unpriv-ip.sh bin/
if [ -n "$SERVER" ]; then
    install_bin ./server/lthnvpnd.py bin/lthnvpnd
    install_bin ./server/lvmgmt.py bin/lvmgmt
fi
if [ -n "$CLIENT" ]; then
    install_bin ./client/lthnvpnc.py bin/lthnvpnc
fi

# Copy lib files
for f in lib/*py; do
    install_lib $f lib/
done
sed -i 's^/opt/lthn^'"$LTHN_PREFIX"'^' $INSTALL_PREFIX/$LTHN_PREFIX/lib/config.py
sed -i 's^/usr/sbin/openvpn^'"$OPENVPN_BIN"'^' $INSTALL_PREFIX/$LTHN_PREFIX/lib/config.py
sed -i 's^/usr/sbin/haproxy^'"$HAPROXY_BIN"'^' $INSTALL_PREFIX/$LTHN_PREFIX/lib/config.py

# Copy dist configs
(cd conf; for f in *tmpl *ips *doms *http; do
    install_lib ./$f etc/ 
done)

if [ -n "$SERVER" ] && [ -z "$NOSUDO" ]; then
  if [ -f build/etc/systemd/system/lthnvpnd.service ]; then
    echo "Installing service file /etc/systemd/system/lthnvpnd.service as user $LTHN_USER"
    sed -i "s^User=lthn^User=$LTHN_USER^" build/etc/systemd/system/lthnvpnd.service
    LTHN_PREFIX=/ install_lib build/etc/systemd/system/lthnvpnd.service etc/systemd/system/
    LTHN_PREFIX=/ install_lib conf/lthnvpnd.env etc/default/lthnvpnd
  fi
fi

#if [ -n "$CLIENT" ]; then
#  if [ -f build/etc/systemd/system/lthnvpnd.service ]; then
#    echo "Installing service file /etc/systemd/system/lthnvpnc.service as user $LTHN_USER"
#    sed -i "s^User=lthn^User=$LTHN_USER^" build/etc/systemd/system/lthnvpnc.service
#    mysudo cp build/etc/systemd/system/lthnvpnc.service /etc/systemd/system/
#    mysudo cp conf/lthnvpnc.env /etc/default/lthnvpnc
#  fi
#fi

# Copy generated configs
if [ -n "$FORCE" ]; then
    mysudo cp -va build/etc/* $INSTALL_PREFIX/$LTHN_PREFIX/etc/
else
    mysudo cp -nva build/etc/* $INSTALL_PREFIX/$LTHN_PREFIX/etc/
fi

if [ -n "$SERVER" ] && [ -z "$NOSUDO" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/dispatcher.ini ]; then
    echo "ERROR: No dispatcher config file found. You have to create $INSTALL_PREFIX/$LTHN_PREFIX/etc/dispatcher.ini"
    echo "Use conf/dispatcher_example.ini as example"
    ERRORS=true
  fi
fi

if [ -n "$SERVER" ] && [ -z "$NOSUDO" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/sdp.json ]; then
    echo "ERROR: No SDP config file found. You can use lvmgmt --generate-sdp to create it for you."
    ERRORS=true 
  fi
fi

if [ -n "$SERVER" ] && [ -z "$NOSUDO" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/ca/index.txt ]; then
        if [ -f ./build/ca/index.txt ]; then
            install_dir etc/ca
            cp -R build/ca/* $INSTALL_PREFIX/$LTHN_PREFIX/etc/ca/
        else
            echo "CA directory $INSTALL_PREFIX/$LTHN_PREFIX/etc/ca/ not prepared! You should generate by configure or use your own CA!"
            ERRORS=true 
        fi
  fi
fi

if [ -n "$SERVER" ] && [ -z "$NOSUDO" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/dhparam.pem ] && [ -f build/dhparam.pem ]; then
    install_lib build/dhparam.pem etc/
  fi
fi

if [ -n "$SERVER" ] && [ -z "$NOSUDO" ]; then
  if ! [ -f $INSTALL_PREFIX/$LTHN_PREFIX/etc/openvpn.tlsauth ] && [ -n "$OPENVPN_BIN" ] ; then
    "$OPENVPN_BIN" --genkey --secret $INSTALL_PREFIX/$LTHN_PREFIX/etc/openvpn.tlsauth
  fi
fi

mysudo chown -R $LTHN_USER:$LTHN_GROUP $INSTALL_PREFIX/$LTHN_PREFIX/etc/
mysudo chmod -R 700 $INSTALL_PREFIX/$LTHN_PREFIX/etc/

if [ "$ERRORS" = true ]; then
    echo "Finished installing but with errors. See above."
else
    echo "Finished installing successfully!"
fi

