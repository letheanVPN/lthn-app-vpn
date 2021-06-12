# VPN Overview

LTHN VPN dispatcher is a tool that orchestrates all other modules (proxy, VPN, config, etc.). It does not provide any VPN functionality by itself.
The dispatcher uses system packages whenever possible but it runs all instances manually after invoking.
More info about technical design can be found in the [Lethean Whitepapers](https://lethean.io/vpn-whitepaper/)

## Runtime Modes

### Client mode
As a client, dispatcher uses global SDP platform to fetch data about provider and connect there. There is no automatic payment functionality inside client. It is up to user to send corresponding payments from wallet to provider.
Client will show only instructions what to pay. We do not want to have any connection from client to your wallet allowing automatic payment.


### Server mode
As a server, dispatcher helps you to create, publish and run your service as a provider.

## Directories

```
/
 client/  Files for Client Mode
 conf/    Templates and example config files
 server/  Files for Server Mode
 lib/     Library files
 scripts/ Various scripts and tools
```