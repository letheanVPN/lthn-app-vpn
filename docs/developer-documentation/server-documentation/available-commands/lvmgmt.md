### lvmgmt (Lethean VPN mgmt tool)
```
 /opt/lthn/bin/lvmgmt -h
usage: lvmgmt [-l LEVEL] [-v] [-h] [-f CONFIGFILE] [-s SDPFILE] [-p PIDFILE]
              [-A FILE] [-a FILE] [-lc FILE] --wallet-address ADDRESS
              [--wallet-rpc-uri URI] [--wallet-username USER]
              [--wallet-password PW] [--sdp-server-uri URL]
              [--sdp-wallet ADDRESS] --provider-id PROVIDERID --provider-key
              PROVIDERKEY --provider-name NAME [--provider-type TYPE]
              [--provider-terms TEXT] --ca ca.crt [-G PREFIX] [-D] [-E] [-U]
              [--sdp-service-crt FILE] [--sdp-service-type TYPE]
              [--sdp-service-fqdn FQDN] [--sdp-service-port NUMBER]
              [--sdp-service-name NAME] [--sdp-service-id NUMBER]
              [--sdp-service-cost ITNS] [--sdp-service-disable NUMBER]
              [--sdp-service-refunds NUMBER] [--sdp-service-dlspeed Mbps]
              [--sdp-service-ulspeed Mbps] [--sdp-service-prepaid-mins TIME]
              [--sdp-service-verifications NUMBER]

Args that start with '--' (eg. -l) can also be set in a config file (specified
via -f). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for
details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more
than one place, then commandline values override config file values which
override defaults.

optional arguments:
  -l LEVEL, --log-level LEVEL
                        Log level (default: WARNING)
  -v, --verbose         Be more verbose (default: None)
  -h, --help            Help (default: None)
  -f CONFIGFILE, --config CONFIGFILE
                        Config file (default: /opt/lthn//etc/dispatcher.ini)
  -s SDPFILE, --sdp SDPFILE
                        SDP file (default: /opt/lthn//etc/sdp.json)
  -p PIDFILE, --pid PIDFILE
                        PID file (default: /opt/lthn//var/run/lthnvpnd.pid)
  -A FILE, --authids FILE
                        Authids db file. Use "none" to disable. (default:
                        /opt/lthn//var/authids.db)
  -a FILE, --audit-log FILE
                        Audit log file (default: /opt/lthn//var/log/audit.log)
  -lc FILE, --logging-conf FILE
                        Logging config file (default: None)
  --wallet-address ADDRESS
                        Wallet address (default: None)
  --wallet-rpc-uri URI  Wallet URI (default: http://127.0.0.1:13660/json_rpc)
  --wallet-username USER
                        Wallet username (default: dispatcher)
  --wallet-password PW  Wallet passwd (default: None)
  --sdp-server-uri URL  SDP server(s) (default:
                        https://sdp.staging.cloud.lethean.io/v1)
  --sdp-wallet ADDRESS  SDP server wallet address (default: iz4xKrEdzsF5dP7rWa
                        xEUT4sdaDVFbXTnD3Y9vXK5EniBFujLVp6fiAMMLEpoRno3VUccxJP
                        nHWyRctmsPiX5Xcd3B61aDeas)
  --provider-id PROVIDERID
                        ProviderID (public ed25519 key) (default: None)
  --provider-key PROVIDERKEY
                        ProviderID (private ed25519 key) (default: None)
  --provider-name NAME  Provider Name (default: None)
  --provider-type TYPE  Provider type (default: residential)
  --provider-terms TEXT
                        Provider terms (default: None)
  --ca ca.crt           Set certificate authority file (default: None)
  -G PREFIX, --generate-providerid PREFIX
                        Generate providerid files (default: None)
  -D, --generate-sdp    Generate SDP by wizzard (default: None)
  -E, --edit-sdp        Edit existing SDP config (default: None)
  -U, --upload-sdp      Upload SDP (default: None)
  --sdp-service-crt FILE
                        Provider Proxy crt (for SDP edit/creation only)
                        (default: None)
  --sdp-service-type TYPE
                        Service type (proxy or vpn) (default: None)
  --sdp-service-fqdn FQDN
                        Service FQDN or IP (for SDP service edit/creation
                        only) (default: None)
  --sdp-service-port NUMBER
                        Service port (for SDP service edit/creation only)
                        (default: None)
  --sdp-service-name NAME
                        Service name (for SDP service edit/creation only)
                        (default: None)
  --sdp-service-id NUMBER
                        Service ID (for SDP service edit/creation only)
                        (default: None)
  --sdp-service-cost ITNS
                        Service cost (for SDP service edit/creation only)
                        (default: None)
  --sdp-service-disable NUMBER
                        Set to true to disable service; otherwise leave false.
                        (default: False)
  --sdp-service-refunds NUMBER
                        Allow refunds for Service (for SDP service
                        edit/creation only) (default: False)
  --sdp-service-dlspeed Mbps
                        Download speed for Service (for SDP service
                        edit/creation only) (default: 10)
  --sdp-service-ulspeed Mbps
                        Upload speed for Service (for SDP service
                        edit/creation only) (default: 10)
  --sdp-service-prepaid-mins TIME
                        Prepaid minutes for Service (for SDP service
                        edit/creation only) (default: 30)
  --sdp-service-verifications NUMBER
                        Verifications needed for Service (for SDP service
                        edit/creation only) (default: 0)

Use -v option to more help info.
Happy flying with better privacy!

```
