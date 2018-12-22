# lethean-vpn
This repository contains code needed to setup and run an exit node on the Lethean Virtual Private Network (VPN) or to use Lethean service as client in CLI mode.
If you are looking for GUI, please look [here](https://github.com/LetheanMovement/lethean-gui)

**This is development version! If you are seeking for stable version, use** [latest release](https://github.com/LetheanMovement/lethean-vpn/releases/tag/v3.0.0.b2). 
**The exit node is currently only supported on Linux.**

# Design
ITNS (aka LTHN) VPN dispatcher is a tool that orchestrates all other modules (proxy, VPN, config, etc.). It does not provide any VPN functionality by itself.
The dispatcher uses system packages whenever possible but it runs all instances manually after invoking.
More info about technical design can be found [here](https://lethean.io/vpn-whitepaper/)

## Client mode
As a client, dispatcher uses global SDP platform to fetch data about provider and connect there. There is no automatic payment functionality inside client. It is up to user to send corresponding payments from wallet to provider.
Client will show only instructions what to pay. We do not want to have any connection from client to your wallet allowing automatic payment.
More information about client mode is [here](CLIENT.md)

## Server mode
As a server, dispatcher helps you to create, publish and run your service as a provider. More info about server mode is [here](SERVER.md)

## Docker
We have prepared docker images for you. It is probably easiest way how to run client or exit node.
There is directory which needs to be mounted to host: /opt/lthn/etc . If you want to get syslog events from docker, you must bind /dev/log too.

### General usage
```
 docker run -p expose:internal \
   --mount type=bind,source=$(pwd)/etc,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   limosek/lethean-vpn:devel [cmd [args]]
```
where cmd can be run,easy-deploy or sh
localetc is local directory to store configs
locallog is local directory to store logs
expose is port to expose to outside
internal is internal port of dispatcher

### Recomended steps to use exit node
Create configs and certificates (or copy your existing /opt/lthn/etc dir here.)
Easiest way to create from scratch is probably to easy-deploy:
```
 mkdir etc
 docker run --mount type=bind,source=$(pwd)/etc,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   limosek/lethean-vpn:devel easy-deploy
```
After easy-deploy, all config files will be stored in your local etc directory. 
You can edit sdp.json, dispatcher.ini and other things to respect your needs.
To upload your local SDP, use 
```
 docker run --mount type=bind,source=$(pwd)/etc,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   limosek/lethean-vpn:devel upload-sdp
```

Than to run dispatcher:
```
 docker run -p 8080:8080 --mount type=bind,source=$(pwd)/etc,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   limosek/lethean-vpn:devel
```

### Recomended steps to use client
Please note this is low level client. By default it does not dynamically create authid or mgmtid. It just need strict instructions what to do.
Even more, it will not send any payments for service. It will only instruct you how much pay and how to pay. You can parse your syslog messages to see how to pay.

List all services from SDP platform:
```
 docker run limosek/lethean-vpn:devel list
```

Simple URI is constructed of [authid[:mgmtid]]@providerid:serviceid
authid is 16 bytes hexa string which identifies payment. Keep in mind that first two letters of authid must be same as serviceid.
mgmtid is 16 bytes hexa string which identifies this instance of client. Used by external tools to identify instance.

More complex URI is still in development. By more complex URI, it will be possible to combine services and create enhanced privacy mode:

URI1[[/URI2]/URI3] means "Connet to URI2, use it as proxy to connect to URI1". Can be chained more times. Latest URI will be connected first.
URI1/{URI2,URI3,URI4} means  "Connect to URI2, URI3 and URI4 simultaneously and use it as round-robin set of proxies for connecting to URI1" 

Connect to URI:
```
 docker run --mount type=bind,source=/dev/log,target=/dev/log limosek/lethean-vpn:devel connect providerid:serviceid
```

## FAQ

### Provider

#### Q: Is it legal to be provider?
There can be local laws and legality issues in your country or company. Check your legislative about this. We cannot say universally that something is legal or not.
It can differ in countries over the world but you should follow at last some basic rules:

##### Safe your infrastructure #####
You should not allow user to connect to your own network until you are sure you want to. Please refer to [server](SERVER.md) documentation about access lists.

##### Do not allow bad users to do bad things #####
This is probably most critical and complex part. Primary goal of entire Lethean project is privacy for users. But, of course, somebody can use privacy to harmful somebody other. 
It is your responsibility as a provider to do maximum against these users. Our project is here for good users which needs privacy. We will implement many features how to help you with this filtering.

##### Filter traffic #####
You can filter your traffic for specific sites. Please refer to [server](SERVER.md)
 
#### Q: As a provider, do I need audit log?
If somebody does something harmful, you are responsible as an exit node. It is up to you.

#### Q: What is status of IPv4/IPv6 support?
Both client and server works perfectly on IPv4 network. We are working on full native IPv6 support but for now, see this matrix.

| Client  | Provider | Web        | Support             |
| ------- | -------- | -------    | ------------------- | 
| IPv4    | IPv4     | IPv4/IPv6  | Full                |
| IPv6    | IPv6     | IPv4/IPv6  | No-session-tracking |

### Client

#### Q: Will Lethean project make me anonymous? ####
There are lot of next dependencies which you *MUST* follow to be anonymous. Refer to [tor](https://www.torproject.org/). I a short review, your browser, your OS and all other tools around can be used to identify you. 
At least, use dedicated browser with anonymous mode enabled. 

## Directories

### client
 Everything related to client part. More information [here](CLIENT.md)
 
### conf
 Example config files and config templates.
 
### server
 Code related to VPN server part. More information [here](SERVER.md)

### lib
 Library files

 
