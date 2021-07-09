### lthnvpnd (Lethean VPN dispatcher)
```bash
/opt/lthn/bin/lthnvpnd  -h
usage: lthnvpnd [--user USERNAME] [--group GROUP] [--chroot] [-l LEVEL] [-v]
                [-h] [-f CONFIGFILE] [-s SDPFILE] [-p PIDFILE] [-A FILE]
                [-a FILE] [-lc FILE] --wallet-address ADDRESS
                [--wallet-rpc-uri URI] [--wallet-username USER]
                [--wallet-password PW] [--sdp-server-uri URL]
                [--sdp-wallet ADDRESS] --provider-id PROVIDERID --provider-key
                PROVIDERKEY --provider-name NAME [--provider-type TYPE]
                [--provider-terms TEXT] --ca ca.crt [--refresh-time SEC]
                [--save-time SEC] [--max-wait-to-spend SEC]
                [--run-services RUNSERVICES] [--track-sessions TRACKSESSIONS]
                [-S] [-H HEIGHT]

Args that start with '--' (eg. --user) can also be set in a config file
(specified via -f). Config file syntax allows: key=value, flag=true,
stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). If an arg is
specified in more than one place, then commandline values override config file
values which override defaults.

optional arguments:
  --user USERNAME       Switch privileges to this user (default: None)
  --group GROUP         Switch privileges to this group (default: None)
  --chroot              Chroot to prefix (default: None)
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
  --refresh-time SEC    Refresh frequency. Set to 0 for disable autorefresh.
                        (default: 30)
  --save-time SEC       Save authid frequency. Use 0 to not save authid
                        regularly. (default: 10)
  --max-wait-to-spend SEC
                        When payment arrive, we will wait max this number of
                        seconds for first session before spending credit.
                        (default: 1800)
  --run-services RUNSERVICES
                        Run services from dispatcher or externally. Default to
                        run by itnsdispatcher. (default: True)
  --track-sessions TRACKSESSIONS
                        If true, dispatcher will track sessions. If not,
                        existing sessions will not be terminated after payment
                        is spent. (default: True)
  -S, --generate-server-configs
                        Generate configs for services and exit (default: None)
  -H HEIGHT, --from-height HEIGHT
                        Initial height to start scan payments. Default is
                        actual height. (default: -1)

Use -v option to more help info.
Happy flying with better privacy!

```
