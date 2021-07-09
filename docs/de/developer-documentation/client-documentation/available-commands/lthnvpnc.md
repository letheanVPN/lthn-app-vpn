
## List active services in SDP:
```
lthnvpnc list
```

## Connect to service:
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



## lthnvpnc Usage
```
lthnvpnc help
usage: lthnvpnc [-l LEVEL] [--syslog] [-v] [-h] [-f CONFIGFILE] [-s SDPFILE]
                [-p PIDFILE] [-A FILE] [-a FILE] [--audit-log-json] [-lc FILE]
                [--sdp-server-uri URL] [--sdp-wallet-address ADDRESS]
                [--sdp-service-endpoint FQDN] [--sdp-service-port NUMBER]
                [--sdp-service-proto PROTOCOL] [--sdp-service-id NUMBER]
                [--provider-id PROVIDERID] [--ca ca.crt]
                [--wallet-address ADDRESS] [--sdp-cache-dir DIR]
                [--sdp-cache-expiry SECONDS] [--compatibility Level]
                [--vpnd-dns IP] [--vpnd-iprange IP] [--vpnd-mask MASK]
                [--vpnd-reneg S] [--vpnd-tun IF] [--vpnd-mgmt-port PORT]
                [--vpnc-standalone] [--proxyc-standalone] [--authid AUTHID]
                [--uniqueid UNIQUEID] [--stunnel-port PORT]
                [--https-proxy-host HOST] [--https-proxy-port PORT]
                [--proxy-port PORT] [--proxy-bind IP] [--connect-timeout S]
                [--payment-timeout S] [--exit-on-no-payment Bool]
                [--fork-on-connect Bool] [--vpnc-tun IF]
                [--vpnc-mgmt-port PORT] [--vpnc-block-route Bool]
                [--vpnc-block-dns Bool]
                {list|connect|help}

Args that start with '--' (eg. -l) can also be set in a config file (specified
via -f). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for
details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more
than one place, then commandline values override config file values which
override defaults.

positional arguments:
  {list|connect|help}   Command to execute.

optional arguments:
  -l LEVEL, --log-level LEVEL
                        Log level (default: WARNING)
  --syslog              Use syslog (default: None)
  -v, --verbose         Be more verbose (default: None)
  -h, --help            Help (default: None)
  -f CONFIGFILE, --config CONFIGFILE
                        Config file (default: /opt/lthn//etc/dispatcher.ini)
  -s SDPFILE, --sdp SDPFILE
                        SDP file (default: /opt/lthn//etc/sdp.json)
  -p PIDFILE, --pid PIDFILE
                        PID file (default: /opt/lthn//var/run/lthnvpnd.pid)
  -A FILE, --authids FILE
                        Authids db file. (default: none)
  -a FILE, --audit-log FILE
                        Audit log file (default: /opt/lthn//var/log/audit.log)
  --audit-log-json      Audit log to JSON (default: None)
  -lc FILE, --logging-conf FILE
                        Logging config file (default: None)
  --sdp-server-uri URL  SDP server(s) (default: https://sdp.lethean.io)
  --sdp-wallet-address ADDRESS
                        SDP server wallet address (default: iz4xKrEdzsF5dP7rWa
                        xEUT4sdaDVFbXTnD3Y9vXK5EniBFujLVp6fiAMMLEpoRno3VUccxJP
                        nHWyRctmsPiX5Xcd3B61aDeas)
  --sdp-service-endpoint FQDN
                        Service FQDN or IP (default: None)
  --sdp-service-port NUMBER
                        Service port (default: None)
  --sdp-service-proto PROTOCOL
                        Service protocol (default: None)
  --sdp-service-id NUMBER
                        Service ID (default: None)
  --provider-id PROVIDERID
                        ProviderID (public ed25519 key) (default: <NOID>)
  --ca ca.crt           Set certificate authority file (default: <NOCA>)
  --wallet-address ADDRESS
                        Provider wallet address (default: <NOADDR>)
  --sdp-cache-dir DIR   SDP cache dir (default: /opt/lthn//var/)
  --sdp-cache-expiry SECONDS
                        SDP cache expiry in seconds (default: 300)
  --compatibility Level
                        Compatibility level for remote node. Use v3 or v4
                        (default: v3)
  --vpnd-dns IP         Use and offer local DNS server for VPN clients
                        (default: None)
  --vpnd-iprange IP     IP Range for client IPs. Client will get /30 subnet
                        from this range. (default: 10.11.0.0)
  --vpnd-mask MASK      IP mask for client IPs (default: 255.255.0.0)
  --vpnd-reneg S        Client has to renegotiate after this number of seconds
                        to check if paymentid is still active (default: 600)
  --vpnd-tun IF         Use specific tun device for server (default: tun0)
  --vpnd-mgmt-port PORT
                        Use specific port for local mgmt (default: 11192)
  --vpnc-standalone     Create standalone openvn config that can be run
                        outside of dispatcher. (default: None)
  --proxyc-standalone   Create standalone haproxy config that can be run
                        outside of dispatcher. (default: None)
  --authid AUTHID       Authentication ID. Use "random" to generate. (default:
                        None)
  --uniqueid UNIQUEID   Unique ID of proxy. Use "random" to generate.
                        (default: None)
  --stunnel-port PORT   Use this stunnel local port for connections over
                        proxy. (default: 8187)
  --https-proxy-host HOST
                        Use this https proxy host. (default: None)
  --https-proxy-port PORT
                        Use this https proxy port. (default: 3128)
  --proxy-port PORT     Use this port as local bind port for proxy. (default:
                        8180)
  --proxy-bind IP       Use this host as local bind for proxy. (default:
                        127.0.0.1)
  --connect-timeout S   Timeout for connect to service. (default: 30)
  --payment-timeout S   Timeout for payment to service. (default: 1200)
  --exit-on-no-payment Bool
                        Exit after payment is gone. (default: None)
  --fork-on-connect Bool
                        Fork after successful paid connection. Client will
                        fork into background. (default: None)
  --vpnc-tun IF         Use specific tun device for client (default: tun1)
  --vpnc-mgmt-port PORT
                        Use specific port for local mgmt (default: 11193)
  --vpnc-block-route Bool
                        Filter router changes from server (default: True)
  --vpnc-block-dns Bool
                        Filter router DNS server from server (default: True)

Use -v option to more help info.
Happy flying with better privacy!

```
