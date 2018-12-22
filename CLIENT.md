# Lethean VPN client
This repository contains code needed to setup and run CLI client of the Lethean Virtual Private Network (VPN).
If you are searching GUI client, please refer [here](https://github.com/LetheanMovement/lethean-gui)

## Payments
This client will not pay anything for you. It only helps to create local configs and connect to remote service. It will instruct you in audit.log, how to pay for service.
It will wait until service is paid and checkes each 60 seconds if credit is still OK.

## Exiting from client
By default, client tries to connect and if there is some error, it exits after connect-timeout. Next, it waits for payment and if payment does not arrive, it exits after payment-timeout.
If you want to have client trying forever, use big numbers for timeouts. Keep in mind, that timeout starts as small number but it is increased by two in each loop to avoid network congestion.
You can use --fork-on-connect to fork to the background after successfull connect. This can be used for chaining (see below).

## Compatibility
There are two versions of dispatchers - v3 and v4. We changed names of headers due to letheanisation. If you want to connect to old (v3) dispatcher, use --compatibility v3.
Client will not connect if compatibility level does not match!

## Usage
```
lthnvpnc --help
usage: lthnvpnc [-l LEVEL] [-v] [-h] [-f CONFIGFILE] [-s SDPFILE] [-p PIDFILE]
                [-A FILE] [-a FILE] [-lc FILE] [--sdp-server-uri URL]
                [--sdp-wallet-address ADDRESS] [--sdp-service-endpoint FQDN]
                [--sdp-service-port NUMBER] [--sdp-service-id NUMBER]
                [--provider-id PROVIDERID] [--ca ca.crt]
                [--wallet-address ADDRESS] [--sdp-cache-file FILE]
                [--sdp-cache-expiry SECONDS] [--compatibility Level]
                [--authid AUTHID] [--uniqueid UNIQUEID] [--stunnel-port PORT]
                [--https-proxy-host HOST] [--https-proxy-port PORT]
                [--proxy-port PORT] [--proxy-bind IP] [--connect-timeout S]
                [--payment-timeout S] [--exit-on-no-payment Bool]
                [--fork-on-connect Bool]
                Command


```

Command is connect or list.

List active services in SDP:
```
lthnvpnc list
```

Connect to service:
```
lthnvpnc connect providerid:serviceid
```

## Examples

### Connect to service using HTTPS proxy
```
lthnvpnc connect providerid:serviceid --https-proxy-host=host --https-proxy-port=port
```

### Debugging
```
lthnvpnc connect providerid:serviceid --https-proxy-host=host --https-proxy-port=port -l DEBUG
```

### Chaining
This example will connect to provider1 and after connection, it uses first provider as transport proxy for second provider.
Your connection will be more expensive but you will get more privacy here. Happy chaining! 
```
lthnvpnc --fork-on-connect connect provider1:serviceid1 --proxy-port 7777 && \
lthnvpnc connect provider2:serviceid2 --https-proxy-host 127.0.0.1 --https-proxy-port 7777
```

