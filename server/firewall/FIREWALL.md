# Firewall
This document is intended as a guide to help you setup a firewall to work with lethean-vpn.

## Client mode
There is no need to open incoming ports to run as client.

The client must be able to use a Lethean wallet. The Lethean wallet connects to the lethean daemon which either can be run locally or remotely. The default setting in the GUI wallet is to connect remotely to sync.lethean.io port number 48782/TCP. It is also possible to use port number 80/TCP if you use sync.lethean.io in case port 48782/TCP is blocked for outgoing connections in your network. In that case change 48782 to 80 in your wallet settings.
If you are using a local wallet daemon then you change the setting to localhost port 48782 in the wallet. However the wallet daemon is using peer-to-peer communication with other wallet daemons over internet. The lethean daemon p2p port is 48772/TCP and your network must allow outgoing connections to this port when using a local daemon.

To connect to Proxy exit nodes the network must allow the TCP port specified by the exit node operator. This is not standardized but default setting is port 8080. However many exit nodes use different ports to allow more services or avoid network limitations on server end.

## Server mode
The exit node server provides proxy services and optionally also OpenVPN services.

Exit nodes use the Lethean wallet to receive payments fro services. The same firewall requirements applies to the server in order to make the wallet work.

Currently exit nodes are only supported on Linux. It is common to remote control Linux servers over ssh on port 22/TCP. The firewall must allow incoming connections to this port for ssh to work. Alternatively the ssh server can be setup to use some other port.

### Proxy server
A common setup is to allow all outgoing connections and to allow the incoming connections to the endpoint port which was set in sdp.json file. The access rights for the proxy server users is then configured in the endpoint proxy settings. If you are using squid you can set access control lists in squid.conf. If using Tinyproxy you can do similar setup in tinyproxy.conf.
To further increase security you can setup firewall in Linux operating system on the exit node or use external network setup that make your exit node isolated from your private networks.

### OpenVPN server
The openVPN server creates a Virtual Private Network which is going through an encrypted tunnel accross public networks like the internet. There is one virtual network interface on the client machine and another virtual network interface on the server machine. The encrypted tunnel can be seen as a virtual network cable between client and server. OpenVPN server broadcast network IP addresses with DHCP to the clients. The server see this as a separate network that connects to the server. Connections to the server is handled similar as connections from the public interface to internet. So you can open incoming ports and do firewalling in similar way as with any other network interface on the server.

To let users on one network talk with users on another network you need to do routing between the networks. People connecting to Lethean exit nodes are probably more interested to access internet than talk only with the server and the server owner is probably not interested in letting the VPN users connect to the server. Well it depends on your setup. Maybe you are providing paid services like a paywall to some website or game server but that is more special cases.
Either way you probably need VPN clients to access internet. So this means you must make your exit node server to work like a router to let clients communicate with internet.

By default Linux operating systems normally have routing possibility (forwarding) disabled.
The first step is to enable ip forwarding:
```
echo 1 > /proc/sys/net/ipv4/ip_forward
```
This command above only enables it at runtime. To make the setting stick after a reboot we make it permanent.
Edit /etc/sysctl.conf and add the following line
```
net.ipv4.ip_forward = 1
```

#### iptables

Then you need to setup the rules in the firewall to forward traffic from the VPN interface (normally tun0) to your network interface connected to the internet.
You may wish to block certain outgoing ports to prevent abuse of your server (email spamming for example) and you probably want to block incoming connections to VPN clients. The setup can be pretty complicated so we have provided some examples you can study and use as you wish. Remember that as server owner you are responsible for your setup so you have to make sure the examples work for your special setup. You probably need to edit the scripts.
The scripts were created using this as inspiration: https://wiki.archlinux.org/index.php/Simple_stateful_firewall
The examples are located in the directory server/firewall/examples

##### The Raspberry Pi example

To apply the firewall rules example for raspberry pi:
```
sudo ./iptables_raspberrypi.sh
```

You can export the applied rules to a file using following command
```
sudo iptables-save > rules.v4
```

This file is in a format that is cleaner than the iptables script so it may be a good idea to take a look at it

```
cat rules.v4
```

If everything works as expected we would like to make this firewall be applied also after a reboot.
On debian we can install the iptables-persistent package and then copy the rules.v4 file to /etc/iptables directory

```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install iptables-persistent
sudo cp rules.v4 /etc/iptables
```

You can read more about iptables on debian here https://wiki.debian.org/iptables
There is also ipv6tables if you are using ipv6 and the approach is similar.

##### The Lethernet example
This exit node setup is a bit more advanced. A script for iptables was created with the purpose of making it easier to setup firewall on different Lethernet exit nodes. In the example variables are used to set ports and firewall policies. By editing the script file and chaange the variable contents it can be adopted for many types of exit nodes.
In the example exit node there is DNS servers running on a dedicated network bridge created by docker. Note that docker as default applies it own set of iptable rules which could break this firewall setup so iptables was disabled in docker configuration and everything was applied using this script instead. The docker network interfaces are virtual interfaces similar to the OpenVPN tun interfaces so there is nothing special about them but they are handled also in the script.
The Lethernet nodes have 3 different DNS servers setup as FREEDOM, SAFE or SAFEST with different levels of blocking of contents and the setup is used to force clients to the DNS server that corresponds to their chosen service. Up to three proxies and three OpenVPN services is handled by the script.

The script have a lot of comments so to start with read the script and all the comments.
Most is self explained but we could need a summary here of the variables:

```
EXTIF=enp1s0       # The name of the network interface which is connected to internet

POLICY=reduced     # See description of polices below
TORRENTS=no        # Setting TORRENTS=no does not mean all torrents are blocked, just that common torrents port are blocked.

PROXYPORT1=8081    # This is the endport port set in sdp.json for the first proxy service
PROXYPORT2=8086    # This is the endport port set in sdp.json for the second proxy service
PROXYPORT3=8088    # This is the endport port set in sdp.json for the third proxy service

VPNPORT_UDP1=      # This is the endpoint port set in sdp.json for the first OpenVPN service if using UDP
VPNPORT_UDP2=20006 # This is the endpoint port set in sdp.json for the second OpenVPN service if using UDP
VPNPORT_UDP3=20008 # This is the endpoint port set in sdp.json for the third OpenVPN service if using UDP

VPNPORT_TCP1=443   # This is the endpoint port set in sdp.json for the first OpenVPN service if using TCP
VPNPORT_TCP2=      # This is the endpoint port set in sdp.json for the first OpenVPN service if using TCP
VPNPORT_TCP3=      # This is the endpoint port set in sdp.json for the first OpenVPN service if using TCP

DNS1=172.28.0.11   # IP-address to DNS server that is forced to be used on VPN1 (clients on tun0 interface)
DNS2=172.28.0.16   # IP-address to DNS server that is forced to be used on VPN2 (clients on tun1 interface)
DNS3=172.28.0.18   # IP-address to DNS server that is forced to be used on VPN3 (clients on tun2 interface)

HOSTDNS=false      # Set to true if the exit node have a "bare metal" DNS server like unbound, dnsmasq or bind
                   # and you want to allow VPN clients on tun interfaces to use that DNS server (on 127.0.0.1 port 53)
                   # When the service is run directly on host and not in a container
                   # then  we must use INPUT chain instead of FORWARD

PUBLICDNS=no       # If set to yes it permits VPN clients to use unencrypted public DNS.
                   # Beware of the risk of man-in-the-middle attacks!

IPRANGE_TUN0=10.11.0.0/16    # The IP address range used by tun0 interface. This is set in dispatcher.ini for first OpenVPN Service
IPRANGE_TUN1=10.16.0.0/16    # The IP address range used by tun1 interface. This is set in dispatcher.ini for second OpenVPN Service
IPRANGE_TUN2=10.18.0.0/16    # The IP address range used by tun2 interface. This is set in dispatcher.ini for third OpenVPN Service


# To fully welcome torrents set TORRENTS=yes and use POLICY normal or maximum
# To block most torrent usage set POLICY to reduced or minimum and TORRENTS=no
# Note there may still be "web torrents" so it is not possible to block torrents completely if you allow web browsing.

#----------POLICY DESCRIPTIONS-------------------
# POLICY=minimum : This only allows VPN clients to web browsing and Lethean wallet usage
# POLICY=reduced : SECTION 2 - similar to Tor reduced exit policy, should make torrents less likely
# POLICY=normal  : SECTION 3 - opens up registered ports (1024 to 49151) plus the opened ports in SECTION 2
# POLICY=maximum : SECTION 4 - opens up system ports as well as registered ports (0 to 49151)
# No matter of which policy is selected the ports in SECTION 1 are always rejected for outgoing VPN client connections
# This is to avoid that the exit node is used for some known types of spam and DoS attacks

```

This script could also be used on the raspberry pi if variables are adjusted. Maybe only use one proxy service and one OpenVPN service? Then leave port variables not in use empty. Not using docker DNS then leave DNS1, DNS2 and DNS3 empty and set PUBLICDNS=yes. Using a DNS cache like unbound or bind 9 directly on the host and want VPN clients use it? Then set HOSTDNS=true.
Always check that it works before making it permanent. See description above how to make iptables rules permanent.
The scripts may contain errors. Be careful and check before applying. They are only intended as guidance and examples how you can get started creating your customized firewall setup foru your own exit node.

