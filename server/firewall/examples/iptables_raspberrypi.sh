#!/bin/bash

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

# We are not filtering outgoing traffic from the host itself so we set default output policy to ACCEPT.
iptables -P OUTPUT ACCEPT

# Set default INPUT policy to drop
iptables -P INPUT DROP

# Allow traffic that belongs to established connections
iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Accept all traffic from the "loopback" (lo) interface.
iptables -A INPUT -i lo -j ACCEPT

# Drop all traffic with an "INVALID" state match.
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Accept all new incoming ICMP echo requests, also known as pings.
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



# The TCP and UDP chains

# Allow lethean-vpn proxy "browser VPN" new connections to port 8080.
iptables -A TCP -i eth0 -p tcp --dport 8080 -j ACCEPT

# Allow incoming connecions from internet to Lethean VPN exit node OpenVPN port
iptables -A UDP -i eth0 -p udp --dport 20001 -j ACCEPT

# Mitigate SSH bruteforce attacks.
iptables -A IN_SSH -m recent --name sshbf --rttl --rcheck --hitcount 3 --seconds 10 -j DROP
iptables -A IN_SSH -m recent --name sshbf --rttl --rcheck --hitcount 4 --seconds 1800 -j DROP
iptables -A IN_SSH -m recent --name sshbf --set -j ACCEPT

# Allow VPN clients to connect to local DNS server port 53 UDP
iptables -A UDP -i tun+ -p udp --dport 53 -j ACCEPT

# Setting up the FORWARD chain

# Now we set up a rule with the conntrack match, identical to the one in the INPUT chain
iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

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
# Setting up the POSTROUTING chain

# See https://wiki.archlinux.org/index.php/Simple_stateful_firewall#Setting_up_a_NAT_gateway
# In this example, assume tun+ are the openVPN interfaces clients connects through
# that should have internet access and that they have the subnet 10.11.0.0/16

# iptables -A fw-interfaces -i tun+ -j ACCEPT

# Now, we have to alter all outgoing packets so that they have our public IP address as the source address, 
# instead of the local LAN address. To do this, we use the MASQUERADE target

iptables -t nat -A POSTROUTING -s 10.11.0.0/16 -o eth0 -j MASQUERADE

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
# iptables -t nat -A PREROUTING -i ppp0 -p tcp --dport 8000 -j DNAT --to 192.168.0.6:80
# iptables -A fw-open -d 192.168.0.6 -p tcp --dport 80 -j ACCEPT

# Allow web surfing for VPN clients
iptables -A VPN_TCP -p tcp --dport 80 -j ACCEPT
iptables -A VPN_TCP -p tcp --dport 443 -j ACCEPT
iptables -A VPN_UDP -p udp --dport 53 -j ACCEPT

# Allow Tradeogre websocket for VPN clients
iptables -A VPN_TCP -p tcp --dport 8443 -j ACCEPT

# Allow  Lethean daemon and remote node connections for vpn clients
iptables -A VPN_TCP -p tcp --dport 48772 -j ACCEPT
iptables -A VPN_TCP -i tun+ -p tcp --dport 48782 -j ACCEPT


# ipv6 is disabled on this raspberry pi
# See https://wiki.archlinux.org/index.php/IPv6#Disable_IPv6
# This caused problems with unbound so I had also to disable ipv6 in unbound config on raspberry pi.
# Alternatively ipv6tables should be set up for ipv6.

