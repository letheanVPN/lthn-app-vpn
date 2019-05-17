#!/bin/bash

# This example is from a real Lethernet exit node setup.
# Note: This script replaces all your current iptable configuration. Please backup first.

EXTIF=enp1s0       # The name of the network interface which is connected to internet

POLICY=reduced     # See description of polices below
TORRENTS=no        # Setting TORRENTS=no does not mean all torrents are blocked, just that common torrents port are blocked.

PROXYPORT1=8081    # This is the endport port set in sdp.json for the first proxy service
PROXYPORT2=8086    # This is the endport port set in sdp.json for the second proxy service
PROXYPORT3=8088    # This is the endport port set in sdp.json for the third proxy service

VPNPORT_UDP1=20001 # This is the endpoint port set in sdp.json for the first OpenVPN service if using UDP
VPNPORT_UDP2=20006 # This is the endpoint port set in sdp.json for the second OpenVPN service if using UDP
VPNPORT_UDP3=20008 # This is the endpoint port set in sdp.json for the third OpenVPN service if using UDP

VPNPORT_TCP1=      # This is the endpoint port set in sdp.json for the first OpenVPN service if using TCP
VPNPORT_TCP2=      # This is the endpoint port set in sdp.json for the first OpenVPN service if using TCP
VPNPORT_TCP3=      # This is the endpoint port set in sdp.json for the first OpenVPN service if using TCP

DNS1=172.28.0.11   # IP-address to DNS server that is forced to be used on VPN1 (clients on tun0 interface)
DNS2=172.28.0.16   # IP-address to DNS server that is forced to be used on VPN2 (clients on tun1 interface)
DNS3=172.28.0.18   # IP-address to DNS server that is forced to be used on VPN3 (clients on tun2 interface)

HOSTDNS=false      # Set to true if the exit node have a "bare metal" DNS server like unbound, dnsmasq or bind
                   # and you want to allow VPN clients on tun interfaces to use that DNS server (on 127.0.0.1 port 53)
                   # When the service is run directly on host and not in a container, we must use INPUT chain instead of FORWARD

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

# Command to check of active interfaces:
# ip address | grep inet


# Resetting rules (see https://wiki.archlinux.org/index.php/Iptables#Resetting_rules)
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X
iptables -t raw -F
iptables -t raw -X

# See https://wiki.archlinux.org/index.php/Simple_stateful_firewall
iptables -N TCP
iptables -N UDP
iptables -N IN_SSH
iptables -N fw-interfaces
iptables -N fw-open
iptables -N VPN_TCP
iptables -N VPN_UDP

# Setting default forwarding policy to drop packets.
iptables -P FORWARD DROP

# Traffic from the host itself -  default output policy is set to ACCEPT.
iptables -P OUTPUT ACCEPT

# Set default INPUT policy to drop
iptables -P INPUT DROP

# exempt udp dns of connection tracking
# See how to do it here: https://jeanbruenn.info/2017/04/30/conntrack-and-udp-dns-with-iptables/
# See why to do it here: https://kb.isc.org/docs/aa-01183
iptables -t raw -A PREROUTING -p udp --sport 53 -j NOTRACK
iptables -t raw -A PREROUTING -p udp --dport 53 -j NOTRACK
iptables -t raw -A OUTPUT -p udp --sport 53 -j NOTRACK
iptables -t raw -A OUTPUT -p udp --dport 53 -j NOTRACK


# Allow traffic that belongs to established connections
iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow untracked packets
iptables -A INPUT -m conntrack --ctstate UNTRACKED -j ACCEPT

# Accept all traffic from the "loopback" (lo) interface.
iptables -A INPUT -i lo -j ACCEPT

# Drop all traffic with an "INVALID" state match.
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Accept all new incoming and forwarded ICMP echo requests, also known as pings.
iptables -A INPUT -p icmp --icmp-type 8 -m conntrack --ctstate NEW -j ACCEPT
iptables -A FORWARD -p icmp --icmp-type 8 -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -p icmp --icmp-type 0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Now we attach the IN_SSH, TCP and UDP chains to the INPUT chain
# to handle all new incoming connections.
iptables -A INPUT -p tcp --dport ssh -m conntrack --ctstate NEW -j IN_SSH
iptables -A INPUT -p udp -m conntrack --ctstate NEW -j UDP
iptables -A INPUT -p tcp --syn -m conntrack --ctstate NEW -j TCP

# We reject TCP connections with TCP RESET packets
# and UDP streams with ICMP port unreachable messages
# if the ports are not opened.
iptables -A INPUT -p udp -j REJECT --reject-with icmp-port-unreachable
iptables -A INPUT -p tcp -j REJECT --reject-with tcp-reset

# For other protocols, we add a final rule to the INPUT chain
# to reject all remaining incoming traffic with icmp protocol unreachable messages.
iptables -A INPUT -j REJECT --reject-with icmp-proto-unreachable


#------------------------------------------------------------------
# The TCP and UDP chains

# Allow Lethean incoming daemon p2p and remote node connections (for sync.lethernet.com)
iptables -A TCP -i $EXTIF -p tcp --dport 48772 -j ACCEPT
iptables -A TCP -i $EXTIF -p tcp --dport 48782 -j ACCEPT


# Allow lethean-vpn proxy "browser VPN" new connections to ports set in variables.
# PROXYPORT 1, PROXYPORT2 and PROXYPORT 3
# If variable is empty the command is not executed
if [ ! -z "$PROXYPORT1" ]; then
   iptables -A TCP -i $EXTIF -p tcp --dport $PROXYPORT1 -j ACCEPT
fi
if [ ! -z "$PROXYPORT2" ]; then
   iptables -A TCP -i $EXTIF -p tcp --dport $PROXYPORT2 -j ACCEPT
fi
if [ ! -z "$PROXYPORT3" ]; then
   iptables -A TCP -i $EXTIF -p tcp --dport $PROXYPORT3 -j ACCEPT
fi

# Allow incoming connecions from internet to Lethean VPN exit node OpenVPN
# UDP ports as in variables. If variable is empty the command is not executed.
if [ ! -z "$VPNPORT_UDP1" ]; then
iptables -A UDP -i $EXTIF -p udp --dport $VPNPORT_UDP1 -j ACCEPT
fi
if [ ! -z "$VPNPORT_UDP2" ]; then
iptables -A UDP -i $EXTIF -p udp --dport $VPNPORT_UDP2 -j ACCEPT
fi
if [ ! -z "$VPNPORT_UDP3" ]; then
iptables -A UDP -i $EXTIF -p udp --dport $VPNPORT_UDP3 -j ACCEPT
fi

# Allow lethean-vpn OpenVPN new connections to TCP ports set in variables.
# If variable is empty the command is not executed
if [ ! -z "$VPNPORT_TCP1" ]; then
   iptables -A TCP -i $EXTIF -p tcp --dport $VPNPORT_TCP1 -j ACCEPT
fi
if [ ! -z "$VPNPORT_TCP2" ]; then
   iptables -A TCP -i $EXTIF -p tcp --dport $VPNPORT_TCP2 -j ACCEPT
fi
if [ ! -z "$VPNPORT_TCP3" ]; then
   iptables -A TCP -i $EXTIF -p tcp --dport $VPNPORT_TCP3 -j ACCEPT
fi


# Mitigate SSH bruteforce attacks.
iptables -A IN_SSH -m recent --name sshbf --rttl --rcheck --hitcount 3 --seconds 10 -j DROP
iptables -A IN_SSH -m recent --name sshbf --rttl --rcheck --hitcount 4 --seconds 1800 -j DROP
iptables -A IN_SSH -m recent --name sshbf --set -j ACCEPT

# Allow VPN clients to connect to local DNS server (localhost 127.0.0.1 port 53 UDP)
if [ $HOSTDNS = true ]
then
   iptables -A UDP -i tun+ -p udp --dport 53 -j ACCEPT
fi

#-----------------------------------------------------------------------
# Setting up the FORWARD chain

# Now we set up a rule with the conntrack match, identical to the one in the INPUT chain
iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate UNTRACKED -j ACCEPT # For UDP DNS, untracked

# The next step is to enable forwarding for trusted interfaces and to make all packets pass the fw-open chain.
iptables -A FORWARD -j fw-interfaces
iptables -A FORWARD -j fw-open

# Outgoing packets from VPN clients are filtered in VPN_TCP and VPN_UDP chains
iptables -A FORWARD -i tun+ -p udp -m conntrack --ctstate NEW -j VPN_UDP
iptables -A FORWARD -i tun+ -p tcp --syn -m conntrack --ctstate NEW -j VPN_TCP


# The remaining packets are denied with an ICMP message
iptables -A FORWARD -j REJECT --reject-with icmp-host-unreachable
iptables -P FORWARD DROP


# Setting up the fw-interfaces and fw-open chains
# The meaning of the fw-interfaces and fw-open chains is explained later,
# when we deal with the POSTROUTING and PREROUTING chains in the nat table, respectively. 

# Setting up the nat table
# All over this section, we assume that the outgoing interface (the one with the public internet IP) is eth0.
# Keep in mind that you have to change the name in all following rules if your outgoing interface has another name.
# On this server the external interface name is $EXTIF (replaces eth0)
# Setting up the POSTROUTING chain

# See https://wiki.archlinux.org/index.php/Simple_stateful_firewall#Setting_up_a_NAT_gateway
# Trusted interfaces that should allow outgoing internet access are added to fw-interfaces
# Note the tun+ interfaces from VPN clients are not concidered as trusted.

# Docker containers are allowed to use all outgoing ports everywhere
iptables -A fw-interfaces -i docker0 -j ACCEPT
iptables -A fw-interfaces -i br_dns -j ACCEPT

# Now, we have to alter all outgoing packets so that they have our public IP address as the source address, 
# instead of the local LAN address. To do this, we use the MASQUERADE target

# VPN clients on tun0, tun1 and tun2
if [ ! -z "$IPRANGE_TUN0" ]; then
   iptables -t nat -A POSTROUTING -s $IPRANGE_TUN0 -o $EXTIF -j MASQUERADE
fi
if [ ! -z "$IPRANGE_TUN1" ]; then
   iptables -t nat -A POSTROUTING -s $IPRANGE_TUN1 -o $EXTIF -j MASQUERADE
fi
if [ ! -z "$IPRANGE_TUN2" ]; then
   iptables -t nat -A POSTROUTING -s $IPRANGE_TUN2 -o $EXTIF -j MASQUERADE
fi
# Docker
iptables -t nat -A POSTROUTING -s 172.17.0.1/16 -o $EXTIF -j MASQUERADE

# Special docker bridge br_dns used for DNS servers and squid containers
iptables -t nat -A POSTROUTING -s 172.28.0.1/24 -o $EXTIF -j MASQUERADE

# Let's assume we have another subnet, 10.3.0.0/16 (which means all addresses 10.3.*.*),
# on the interface eth1. We add the same rules as above again:
# iptables -A fw-interfaces -i eth1 -j ACCEPT
# iptables -t nat -A POSTROUTING -s 10.3.0.0/16 -o eth0 -j MASQUERADE


# Packet forwarding must be enabled in the operating system.
# See this guide for Arch Linux : https://wiki.archlinux.org/index.php/Internet_sharing#Enable_packet_forwarding
# So what is done is to put following line in /etc/sysctl.d/30-ipforward.conf
# sysctl net.ipv4.ip_forward=1



# Setting up the PREROUTING chain
# Sometimes, we want to change the address of an incoming packet from the gateway to a LAN machine.
# To do this, we use the fw-open chain defined above,
# as well as the PREROUTING chain in the nat table in the following two simple examples.

# First, we want to change all incoming SSH packets (port 22) to the ssh server of the machine 192.168.0.5:
# iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 22 -j DNAT --to 192.168.0.5
# iptables -A fw-open -d 192.168.0.5 -p tcp --dport 22 -j ACCEPT

# The second example will show you how to change packets to a different port than the incoming port.
# We want to change any incoming connection on port 8000 to our web server on 192.168.0.6, port 80:
# iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8000 -j DNAT --to 192.168.0.6:80
# iptables -A fw-open -d 192.168.0.6 -p tcp --dport 80 -j ACCEPT

# We want VPN clients using tun0 to only use the DNS server on address in variable DNS1
# So packets coming from interface tun0 on UDP port 53 should be routed to $DNS1 IP address
if [ ! -z "$DNS1" ] && [ $HOSTDNS = false ] && [ $PUBLICDNS != yes ]; then
   iptables -t nat -A PREROUTING -i tun0 -p udp --dport 53 -j DNAT --to $DNS1
   iptables -A fw-open -i tun0 -d $DNS1 -p udp --dport 53 -j ACCEPT
   # Make the response from this DNS server look like it comes from the gateway ip address for VPN clients on tun0
   iptables -t nat -A POSTROUTING -s $DNS1 -o tun0 -j MASQUERADE
fi

# We want VPN clients using tun1 to only use the DNS server on address in variable DNS2
# So packets coming from interface tun1 on UDP port 53 should be routed to $DNS2 IP address
if [ ! -z "$DNS2" ] && [ $HOSTDNS = false ] && [ $PUBLICDNS != yes ]; then
   iptables -t nat -A PREROUTING -i tun1 -p udp --dport 53 -j DNAT --to $DNS2
   iptables -A fw-open -i tun1 -d $DNS2 -p udp --dport 53 -j ACCEPT
   # Make the response from this DNS server look like it comes from the gateway ip address for VPN clients on tun1
   iptables -t nat -A POSTROUTING -s $DNS2 -o tun1 -j MASQUERADE
fi

# We want VPN clients using tun2 to only use the DNS server on address in variable DNS3
# So packets coming from interface tun2 on UDP port 53 should be routed to $DNS3 IP address
if [ ! -z "$DNS3" ] && [ $HOSTDNS = false ] && [ $PUBLICDNS != yes ]; then
   iptables -t nat -A PREROUTING -i tun2 -p udp --dport 53 -j DNAT --to $DNS3
   iptables -A fw-open -i tun2 -d $DNS3 -p udp --dport 53 -j ACCEPT
   # Make the response from this DNS server look like it comes from the gateway ip address for VPN clients on tun2
   iptables -t nat -A POSTROUTING -s $DNS3 -o tun2 -j MASQUERADE
fi


#------------------------------------------------------------------------
# Allow web surfing for VPN clients
iptables -A VPN_TCP -p tcp --dport 80 -j ACCEPT
iptables -A VPN_TCP -p tcp --dport 443 -j ACCEPT

# Allow Tradeogre websocket for VPN clients
iptables -A VPN_TCP -p tcp --dport 8443 -j ACCEPT

# Allow  Lethean daemon and remote node connections for vpn clients
iptables -A VPN_TCP -p tcp --dport 48772 -j ACCEPT
iptables -A VPN_TCP -p tcp --dport 48782 -j ACCEPT

# DNS
# We are only allowing DNS over TLS from local DNS servers so port 53 should not be opened to internet for VPN clients.
# But if you want to do it, set the variable PUBLICDNS to yes. 
if [ $PUBLICDNS = yes ]
then
   iptables -A VPN_UDP -p udp --dport 53 -j ACCEPT
fi


# ipv6 is disabled on this server
# See https://wiki.archlinux.org/index.php/IPv6#Disable_IPv6
# This caused problems with unbound so I had also to disable ipv6 in unbound config on this server.
# Alternatively ipv6tables should be set up for ipv6.


#-------------------------------------------------------------------------
# SECTION 1: Filter outgoing ports that are not allowed to be opened at all.
# These are ports commonly used by spam bots
#
# "Herewith, an alternative Reduced-Reduced ExitPolicy to avoid Tor DNSBL and prevent some common outgoing port scanning / 'attack' ABUSE issues. 
# Reject Ports (Optional Advisory): 22, 23, 194, 465, 563, 587, 994, 3128, 3389, 6660-6669, 6679, 6697, 8000, 8080 and 9999 
# It should be noted that to avoid Tor DNSBL an exit nodes ORPort and/or DirPort must not use the 'default' ports 9001 or 9030.
# If your computer isn't running a webserver, and you haven't set AccountingMax, 
# please consider changing your ORPort to 443 and/or your DirPort to 80. 
# Tor DNSBL = Every IP which is known to run a tor server and allow their clients
# to connect to one of the following ports get listed: 
# 25, 194, 465, 587, 994, 6657, 6660-6670, 6697, 7000-7005, 7070, 
# 8000-8004, 9000, 9001, 9998, 9999 . (source) - mxtoolbox.com/problem/blacklist/sectoor"
#
#
# Also see the default Tor Exit policy:
# https://2019.www.torproject.org/docs/faq.html.en#DefaultExitPorts

# To avoid that the proxy accidentically connects to local networks like your home router login page
# Or some other "stupid" setup in squid.conf or tinyproxy.conf. Or that your home exit node get hacked.
# We make sure with iptables that the OUTPUT chain (connections from local services) can not connect to any local networks
# similar as the VPN clients can't do it in the default rules (as in "same as default Tor exit policy" below).
# You may need to adjust this to your local setup to not block things you need the exit node server to connect to
# Also you might need to add this to any local network interfaces
# (if this is a router your local network is probably not connected to WAN port $EXTIF)
# Remember that your device may also have a Wifi network
# By specifying -o $EXTIF we still can on the host itself allow local virtual machines,
# docker containers, VPN networks and such in these network ranges
iptables -A OUTPUT -o $EXTIF -p tcp -d 169.254.0.0/16 -j REJECT --reject-with tcp-reset
iptables -A OUTPUT -o $EXTIF -p udp -d 169.254.0.0/16 -j REJECT --reject-with icmp-port-unreachable
iptables -A OUTPUT -o $EXTIF -p tcp -d 192.168.0.0/16 -j REJECT --reject-with tcp-reset
iptables -A OUTPUT -o $EXTIF -p udp -d 192.168.0.0/16 -j REJECT --reject-with icmp-port-unreachable
iptables -A OUTPUT -o $EXTIF -p tcp -d 10.0.0.0/8 -j REJECT --reject-with tcp-reset
iptables -A OUTPUT -o $EXTIF -p udp -d 10.0.0.0/8 -j REJECT --reject-with icmp-port-unreachable
iptables -A OUTPUT -o $EXTIF -p tcp -d 172.16.0.0/12 -j REJECT --reject-with tcp-reset
iptables -A OUTPUT -o $EXTIF -p udp -d 172.16.0.0/12 -j REJECT --reject-with icmp-port-unreachable

# Using the same as default Tor exit policy
iptables -A VPN_TCP -p tcp -d 0.0.0.0/8 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp -d 0.0.0.0/8 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp -d 169.254.0.0/16 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp -d 169.254.0.0/16 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp -d 127.0.0.0/8 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp -d 127.0.0.0/8 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp -d 192.168.0.0/16 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp -d 192.168.0.0/16 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp -d 10.0.0.0/8 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp -d 10.0.0.0/8 -j REJECT  --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp -d 172.16.0.0/12 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp -d 172.16.0.0/12 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 25 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 25 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 119 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 119 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 135:139 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 135:139 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 445 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 445 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 563 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 563 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 1214 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 1214 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 4661:4666 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 4661:4666 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 6346:6429 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 6346:6429 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 6699 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 6699 -j REJECT --reject-with icmp-port-unreachable

# Most commonly used bittorrent ports. Set TORRENTS=yes to not block these ports
if [ $TORRENTS != yes ]
then
   iptables -A VPN_TCP -p tcp --dport 6881:6999 -j REJECT --reject-with tcp-reset
   iptables -A VPN_UDP -p udp --dport 6881:6999 -j REJECT --reject-with icmp-port-unreachable
else
   echo "Warning: Bittorrent port range 6881-6999 is not blocked"
fi

# Reject Ports (Optional Advisory):
# 22, 23, 194, 465, 563, 587, 994, 3128, 3389, 6660-6669, 6679, 6697, 8000, 8080 and 9999
iptables -A VPN_TCP -p tcp --dport 22:23 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 22:23 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 194 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 194 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 465 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 465 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 587 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 587 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 994 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 994 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 3128 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 3128 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 3389 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 3389 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 6660:6669 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 6660:6669 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 6679 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 6679 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 6697 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 6697 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 8000 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 8000 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 8080 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 8080 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 9999 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 9999 -j REJECT --reject-with icmp-port-unreachable

# Tor DNSBL = Every IP which is known to run a tor server and allow their clients
# to connect to one of the following ports get listed: 
# 25, 194, 465, 587, 994, 6657, 6660-6670, 6697, 7000-7005, 7070, 
# 8000-8004, 9000, 9001, 9998, 9999 . (source) - mxtoolbox.com/problem/blacklist/sectoor"

iptables -A VPN_TCP -p tcp --dport 6657 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 6657 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 6670 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 6670 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 7000:7005 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 7000:7005 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 7070 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 7070 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 8001:8004 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 8001:8004 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 9000:9001 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 9000:9001 -j REJECT --reject-with icmp-port-unreachable
iptables -A VPN_TCP -p tcp --dport 9998 -j REJECT --reject-with tcp-reset
iptables -A VPN_UDP -p udp --dport 9998 -j REJECT --reject-with icmp-port-unreachable

# In addition I want to comply with https://buyvm.net/acceptable-use-policy/
# If you're operating an Exit Node, please make sure your exit policy blocks the following ports: 
# TCP 25 (SMTP)
# TCP 465 (SMTP over SSL)
# TCP 587 (SMTP over TLS)
# TCP 6660-6667 (IRC - Optional but you may save yourself from DDOS attacks)
# TCP 6697 (IRC over SSL - Optional but you may save yourself from DDOS attacks)
# All these ports are already rejected above.

# If POLICY is set to minimum we should now exit this script, to be sure nothing else is applied
# This if condition is actually redundant now when we added conditions for all other policies, but anyway...
if [ $POLICY = minimum ]; then
   exit 0
fi

#-------------------------------------------------------------------------
# SECTION 2: POLICY = reduced
# Open additional ports other than minimum required for allowing web browsing. This is the reduced exit policy.
# Note ports in SECTION 1 are already rejected so these will not be opened here even if you try :-)
#
# Opening up outgoing ports for VPN clients corresponding to https://trac.torproject.org/projects/tor/wiki/doc/ReducedExitPolicy
# Also check ports here: https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
#
# The default policy in FORWARD chain is previously set to DROP so we need to open ports.

if [ $POLICY = reduced ] || [ $POLICY = normal ]
then

   # FTP
   iptables -A VPN_TCP -p tcp --dport 20:21 -j ACCEPT

   # WHOIS
   iptables -A VPN_TCP -p tcp --dport 43 -j ACCEPT

   # finger
   iptables -A VPN_TCP -p tcp --dport 79 -j ACCEPT

   # Web port 80 is already opened before

   # HTTP
   iptables -A VPN_TCP -p tcp --dport 81 -j ACCEPT

   # kerberos
   iptables -A VPN_TCP -p tcp --dport 88 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 88 -j ACCEPT

   # Pop3 receive email only
   iptables -A VPN_TCP -p tcp --dport 110 -j ACCEPT

   # The reduced exit policy seems to not include NTP port 123 UDP. Reason for that?
   # iptables -A VPN_UDP -p udp --dport 123 -j ACCEPT

   # IMAP receive email only
   iptables -A VPN_TCP -p tcp --dport 143 -j ACCEPT

   # IMAP3 receive email only
   iptables -A VPN_TCP -p tcp --dport 220 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 220 -j ACCEPT

   # LDAP
   iptables -A VPN_TCP -p tcp --dport 389 -j ACCEPT

   # HTTPS port 443 is already opened before (as minimum config)

   # kpasswd - Kerberos change / set password
   iptables -A VPN_TCP -p tcp --dport 464 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 464 -j ACCEPT

   # AOL instant messenger was closed 2017-12-15
   # https://sv.wikipedia.org/wiki/AOL_Instant_Messenger
   # So there is no need to open port 531

   # Kerberos login
   iptables -A VPN_TCP -p tcp --dport 543 -j ACCEPT

   # Kerberos remote shell port 544
   # https://www.speedguide.net/port.php?port=544
   # Note that vulnerability in Cisco IOS we might need to close this port.
   # Kerberos seems to need it though.
   iptables -A VPN_TCP -p tcp --dport 544 -j ACCEPT

   # RTSP streaming protocol
   iptables -A VPN_TCP -p tcp --dport 554 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 554 -j ACCEPT

   # LDAPS
   iptables -A VPN_TCP -p tcp --dport 636 -j ACCEPT

   # Secure Internet Live Conferencing
   iptables -A VPN_TCP -p tcp --dport 706 -j ACCEPT

   # Kerberos 5 admin/changepw
   iptables -A VPN_TCP -p tcp --dport 749 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 749 -j ACCEPT

   # rsync
   iptables -A VPN_TCP -p tcp --dport 873 -j ACCEPT

   # VMware
   iptables -A VPN_TCP -p tcp --dport 902:903 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 902 -j ACCEPT

   # Firewall
   iptables -A VPN_TCP -p tcp --dport 981 -j ACCEPT

   # FTP over TLS/SSL
   iptables -A VPN_TCP -p tcp --dport 989:990 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 989:990 -j ACCEPT

   # NAS Netnews admin, seems not so necessary... port 991

   # Telnet over TLS / SSL. I think not necessary.

   # IMAP over SSL (receive email only)
   iptables -A VPN_TCP -p tcp --dport 993 -j ACCEPT

   # POP3 over SSL (receive email only)
   iptables -A VPN_TCP -p tcp --dport 995 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 995 -j ACCEPT

   # OpenVPN
   iptables -A VPN_TCP -p tcp --dport 1194 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 1194 -j ACCEPT

   # Quicktime streaming server admin
   iptables -A VPN_TCP -p tcp --dport 1220 -j ACCEPT

   # PKT-KRB-IPSec
   iptables -A VPN_TCP -p tcp --dport 1293 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 1293 -j ACCEPT

   # VLSI License Manager - Firewall (NT4-based) Remote Management / Server
   iptables -A VPN_TCP -p tcp --dport 1500 -j ACCEPT

   # Sametime - IM—Virtual Places Chat MS SQL Server
   iptables -A VPN_TCP -p tcp --dport 1533 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 1533 -j ACCEPT

   # GroupWise - clients in client/server access mode
   iptables -A VPN_TCP -p tcp --dport 1677 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 1677 -j ACCEPT

   # PPTP - Point-to-Point Tunneling Protocol
   iptables -A VPN_TCP -p tcp --dport 1723 -j ACCEPT

   # RTSP - Media Services (MMS, ms-streaming)
   iptables -A VPN_TCP -p tcp --dport 1755 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 1755 -j ACCEPT

   # MSNP - MS Notification Protocol, MS Messenger service / Instant Messaging clients
   # Does not exist anymore so why open this port? We don't

   # Infowave Mobility Server and CPanel default
   iptables -A VPN_TCP -p tcp --dport 2082 -j ACCEPT

   # Secure Radius Service (radsec) and CPanel default SSL
   iptables -A VPN_TCP -p tcp --dport 2083 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 2083 -j ACCEPT

   # GNUnet, ELI - Web Host Manager default and Web Host Manager default SSL
   iptables -A VPN_TCP -p tcp --dport 2086:2087 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 2086 -j ACCEPT

   # NBX - CPanel default web mail and CPanel default SSL web mail
   iptables -A VPN_TCP -p tcp --dport 2095:2096 -j ACCEPT

   # Zephyr - Project Athena Notification Service server / connection / host manager
   iptables -A VPN_TCP -p tcp --dport 2102:2104 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 2102:2104 -j ACCEPT

   # SVN - Subversion version control system
   iptables -A VPN_TCP -p tcp --dport 3690 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 3690 -j ACCEPT

   # RWHOIS - Referral Who is Protocol
   iptables -A VPN_TCP -p tcp --dport 4321 -j ACCEPT

   # Virtuozzo
   iptables -A VPN_TCP -p tcp --dport 4643 -j ACCEPT

   # Yahoo messenger was closed 2012 so we don't open port 5050

   # AOL Messenger was closed 2017 so we don't open port 5190

   # XMPP, XMPP over SSL - Extensible Messaging and Presence Protocol client connection
   iptables -A VPN_TCP -p tcp --dport 5222:5223 -j ACCEPT

   # Android Market - Google Play, Android Cloud, Google Cloud Messaging / HP Virtual Room Service
   iptables -A VPN_TCP -p tcp --dport 5228 -j ACCEPT

   # HTTP alternate / Server administration default
   iptables -A VPN_TCP -p tcp --dport 8008 -j ACCEPT

   # Gadu-gadu
   iptables -A VPN_TCP -p tcp --dport 8074 -j ACCEPT

   # Lethernet FREEDOM proxy :-)
   # HTTPS Electrum Bitcoin port
   iptables -A VPN_TCP -p tcp --dport 8081:8082 -j ACCEPT

   # Lethernet SAFE proxy :-)
   iptables -A VPN_TCP -p tcp --dport 8086 -j ACCEPT

   # Lethernet SAFEST proxy :-)
   iptables -A VPN_TCP -p tcp --dport 8088 -j ACCEPT

   # Bitcoin
   iptables -A VPN_TCP -p tcp --dport 8332:8333 -j ACCEPT

   # HTTP Proxies, NewsEDGE - HyperVM, Freenet, MAMP Server
   iptables -A VPN_TCP -p tcp --dport 8888 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 8888 -j ACCEPT

   # Litecoin
   iptables -A VPN_TCP -p tcp --dport 9332:9333 -j ACCEPT

   # git - Git pack transfer service
   iptables -A VPN_TCP -p tcp --dport 9418 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 9418 -j ACCEPT

   # Network Data Management Protocol - Webmin, Web-based Unix/Linux system administration tool
   iptables -A VPN_TCP -p tcp --dport 10000 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 10000 -j ACCEPT

   # OpenPGP hkp (http keyserver protocol)
   iptables -A VPN_TCP -p tcp --dport 11371 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 11371 -j ACCEPT

   # Google Voice TCP - Voice and Video connections
   # Discontinued so don't need that right?
   # iptables -A VPN_TCP -p tcp --dport 19294 -j ACCEPT

   # Monero
   iptables -A VPN_TCP -p tcp --dport 18080:18081 -j ACCEPT

   # Lethernet VPN FREEDOM, SAFE and SAFEST OpenVPN
   iptables -A VPN_UDP -p udp --dport 20001 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 20006 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 20008 -j ACCEPT

   # Electrum Bitcoin SSL
   iptables -A VPN_TCP -p tcp --dport 50001:50002 -j ACCEPT

   # Mumble - voice over IP
   iptables -A VPN_TCP -p tcp --dport 64738 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 64738 -j ACCEPT
fi


#-------------------------------------------------------------------
# SECTION 3: Normal policy
# SECTION 3 overrides SECTION 2 for port range 1024 and higher.
# Will allow all registered ports (in the range 1024 - 49151) that was not rejected in SECTION 1.
# Will also allow the previously opened system ports (0 - 1023) in SECTION 2.
# Note that SECTION 3 will probably get you a lot of bittorrent users because many open ports allow that.
# Even if you set TORRENTS=no

if [ $POLICY = normal ]; then
   iptables -A VPN_TCP -p tcp --dport 1024:49151 -j ACCEPT
   iptables -A VPN_UDP -p udp --dport 1024:49151 -j ACCEPT
fi

#------------------------------------------------------------------
# SECTION 4: Maximum policy
# Open all outgoing ports including system ports, except those already rejected in SECTION 1
# Note that SECTION 4 will probably get you a lot of bittorrent users because many open ports allow that.
# Even if you set TORRENTS=no

if [ $POLICY = maximum ]; then
   iptables -A VPN_TCP -p tcp -j ACCEPT
   iptables -A VPN_UDP -p udp -j ACCEPT
fi
