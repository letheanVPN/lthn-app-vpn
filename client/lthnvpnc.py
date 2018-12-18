#!/usr/bin/python

import os
import sys
# Add lib directory to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))

import ed25519
import getopt
import log
import logging
import logging.config
import config
import configargparse
import util
import pprint
import time
import services
import sdp
import sdps
import random
import string
import requests
import json
import socket
import re
import atexit

def parseUri(cfg, uri):
    # authid:mgmtid@providerid:serviceid
    p = re.search("(.*):(.*)@(.*):(.*)", uri)
    if (p):
        cfg.authId = p.group(1)
        cfg.uniqueId = p.group(2)
        cfg.providerid = p.group(3)
        cfg.serviceId = p.group(4)
    else:
        # authid@providerid:serviceid
        p = re.search("(.*)@(.*):(.*)", uri)
        if (p):
            cfg.authId = p.group(1)
            cfg.uniqueId = "_random_"
            cfg.providerid = p.group(2)
            cfg.serviceId = p.group(3)
        else:
            # providerid:serviceid
            p = re.search("(.*):(.*)", uri)
            if (p):
                cfg.authId = "_random_"
                cfg.uniqueId = "_random_"
                cfg.providerid = p.group(1)
                cfg.serviceId = p.group(2)
            else:
                log.L.error("Bad URI %s" % (uri))
                return(None)
    return(cfg)

def generateAuthId():
    return (''.join(random.choice('ABCDEF0123456789') for _ in range(16)))

def loadService(pid, sid):
    if (not sid or not pid):
        log.L.error("You must specify serviceid and providerid!")
        return(None)
    else:
        if sdps.SDPS.getSDP(pid):
            s = sdps.SDPS.getSDP(pid)
            services.SERVICES.loadClient(s)
            services.SERVICES.mgmt.disable()
            services.SERVICES.http.disable()
            if services.SERVICES.get(sid):
                return(True)
            else:
                log.L.error("Service id %s does not exists!" % (sid))
                return(None)
        else:
            log.L.error("Provider id %s does not exists!" % (pid))
            return(None)
        
def waitForLocal(port, id):
    timeout = 5
    err = None
    while timeout < config.Config.CAP.connectTimeout:
        try:
            log.L.warning("Waiting for local proxy (%s: %s) ..." % (config.Config.CAP.mgmtHeader, id))
            r = requests.get("http://localhost:%s/stats" % (port),
                     proxies={"http": None, "https": None},
                     headers={config.Config.CAP.mgmtHeader: id},
                     timeout=timeout
                     )
            if (r.status_code == 200):
                log.L.warning("Local proxy OK")
                return True
            elif (r.status_code == 503 and r.status_response == "BAD_ID"):
                log.L.error("This is not our proxy! Another instance is running on port %s?" % (port))
                sys.exit(2)
            err = r.status_code
        except Exception as e:
            timeout = timeout * 2
            err = e
        sleep(0.5)
    log.L.error("Error connecting to port %s (%s)." % (port, err))
    sys.exit(2)

def waitForRemote(port, id):
    timeout = 5
    while timeout < config.Config.CAP.connectTimeout:
        try:
            log.L.warning("Waiting for remote proxy...")
            headers = {config.Config.CAP.mgmtHeader: id}
            r = requests.get("http://remote.lethean/status",
                     proxies={
                        "http": "http://localhost:%s" % (port),
                        "https": None
                     },
                     headers=headers,
                     timeout=timeout
                     )
            if (r.status_code == 403):
                log.L.warning("Remote proxy is connected.")
                return True
            elif (r.status_code == 503 and r.status_response == "BAD_ID"):
                log.L.error("This is not our remote proxy! Something is bad.")
                sys.exit(2)
            else:
                print(headers)
                print(r.headers)
        except Exception as e:
            timeout = timeout * 2
            err = e
    log.L.error("Error connecting to port %s (%s)." % (port, err))
    sys.exit(2)
        
def waitForPayment(port, id, aid):
    timeout = 5
    while timeout < config.Config.CAP.paymentTimeout:
        try:
            headers = {config.Config.CAP.mgmtHeader: id, config.Config.CAP.authidHeader: aid}
            log.L.warning("Waiting for payment to settle (%s: %s, %s: %s)" % (config.Config.CAP.mgmtHeader, id, config.Config.CAP.authidHeader, aid))
            r = requests.get("http://remote.lethean/status",
                     proxies={
                        "http": "http://localhost:%s" % (port),
                        "https": None
                     },
                     headers=headers,
                     timeout=timeout
                     )
            if (r.status_code == 200):
                log.L.warning("Payment arrived. Happy flying!")
                return True
            elif (r.status_code == 403):
                time.sleep(timeout)
                timeout = timeout * 1.2
            elif (r.status_code == 503 and r.status_response == "BAD_ID"):
                log.L.error("This is not our remote proxy! Something is bad.")
                sys.exit(2)
            elif (r.status_code == 503 and r.status_response == "CONNECTION_ERROR"):
                log.L.error("Error connecting to provider (CONNECTION_ERROR). Blocked?")
                sys.exit(2)
            elif (r.status_code == 504):
                log.L.error("Error connecting to provider (TIMEOUT). Blocked?")
                sys.exit(2)
            else:
                pass
        except Exception as e:
            log.L.error("Error connecting to provider (%s)" % (e))
            sys.exit(2)

def PaymentStatus(port, id, aid):
    timeout = 5
    try:
        log.L.info("Checking payment status")
        headers = {config.Config.CAP.mgmtHeader: id, config.Config.CAP.authidHeader: aid}
        r = requests.get("http://remote.lethean/status",
                 proxies={
                    "http": "http://localhost:%s" % (port),
                    "https": None
                 },
                 headers=headers,
                 timeout=timeout
                 )
        if (r.status_code == 200):
            log.L.warning("Payment OK!")
            return True
        if (r.status_code == 403):
            return None
        elif (r.status_code == 503 and r.status_response == "BAD_ID"):
            log.L.error("This is not our remote proxy! Something is bad.")
            sys.exit(2)
        else:
           pass
    except Exception:
        log.L.warning("Cannot get remote status!")
        pass
        
def sleep(s):
    i = 0
    while (i < s):
        i = i + 0.1
        time.sleep(0.1)
        services.SERVICES.orchestrate()
    
# Starting here
def main(argv):
    
    config.CONFIG = config.Config("dummy")
    p = configargparse.getArgumentParser(ignore_unknown_config_file_keys=True, fromfile_prefix_chars='@')
    util.commonArgs(p)
    p.add('-C', '--generate-client-config', dest='C', action='store_const', const='C', required=None, help='Generate config for service')
    p.add('-O', '--connect', dest='O', action='store_const', const='O', required=None, help='Connect')
    p.add('-L', '--list-services', dest='L', action='store_const', const='L', required=None, help='List services')
    p.add('--authid', dest='authId', metavar='AUTHID', required=None, default=None, help='Authentication ID. Use "random" to generate.')
    p.add('--uniqueid', dest='uniqueId', metavar='UNIQUEID', required=None, default=None, help='Unique ID of proxy. Use "random" to generate.')
    p.add('--stunnel-port', dest='stunnelPort', metavar='PORT', required=None, default=8187, help='Use this stunnel local port for connections over proxy.')
    p.add('--https-proxy-host', dest='httpsProxyHost', metavar='HOST', required=None, default=None, help='Use this https proxy host.')
    p.add('--https-proxy-port', dest='httpsProxyPort', metavar='PORT', required=None, default=3128, help='Use this https proxy port.')
    p.add('--proxy-port', dest='proxyPort', metavar='PORT', required=None, default=8188, help='Use this port as local bind port for proxy.')
    p.add('--proxy-bind', dest='proxyBind', metavar='IP', required=None, default="127.0.0.1", help='Use this host as local bind for proxy.')
    p.add('--connect-timeout', dest='connectTimeout', metavar='S', required=None, default=30, help='Timeout for connect to service.')
    p.add('--payment-timeout', dest='paymentTimeout', metavar='S', required=None, default=1200, help='Timeout for payment to service.')
    p.add('--exit-on-no-payment', dest='exitNoPayment', metavar='Bool', required=None, default=None, help='Exit after payment is gone.')
 
    # Initialise config
    (cfg, args) = p.parse_known_args()
    config.CONFIG = config.Config("dummy")
    util.parseCommonArgs(p, cfg)
    
    if (len(args)==1):
        cmd = args[0]
        if (cmd == "list"):
            cfg.L = True
    elif (len(args)>1):
        cmd = args[0]
        uri = args[1]
        if (cmd == "connect"):
            cfg.O = True
            p = re.search("(.*)/(.*)", uri)
            if (p):
                log.L.error("Complex URI not supported yet :(")
                sys.exit(1)
            cfg = parseUri(cfg, uri)
            if not cfg:
                sys.exit(1)
        elif (cmd == "show"):
           log.L.error("Not implemented yet")
           sys.exit(1)
        else:
           log.L.error("Use lthnvpnc {show|connect} uri or lthnvpnc list.")
           sys.exit(1)
    else:
        log.L.error("Use lthnvpnc {show|connect} uri or lthnvpnc list.")
        sys.exit(1)
            
    if cfg.authId == "_random_":
        cfg.authId = generateAuthId()
    if cfg.uniqueId == "_random_":
        cfg.uniqueId = generateAuthId()
    
    config.Config.CAP = cfg

    # Initialise services
    services.SERVICES = services.Services()
    log.A.audit(log.A.START, log.A.SERVICE, "lthnvpnc")
    sdps.SDPS = sdps.SDPList()
    sdps.SDPS.parse()
    
    if (cfg.C):
        if (loadService(cfg.providerid, cfg.serviceId)):    
            services.SERVICES.get(cfg.serviceId).createConfig()
            sys.exit()
    elif (cfg.O):
        if (loadService(cfg.providerid, cfg.serviceId)):
            services.SERVICES.syslog.run()
            services.SERVICES.show()
            sid = services.SERVICES.get(cfg.serviceId)
            sdp = sdps.SDPS.getSDP(cfg.providerid)
            atexit.register(sid.stop)
            sid.run()
            scfg = sid.getCfg()
            waitForLocal(scfg["status_port"], scfg["uniqueid"])
            waitForRemote(scfg["proxy_port"], cfg.providerid)
            log.L.warning("Now you need to pay to provider's wallet.")
            log.A.audit(log.A.NPAYMENT, log.A.PWALLET, wallet=sdp["provider"]["wallet"], paymentid=cfg.authId, anon="no")
            waitForPayment(scfg["proxy_port"], cfg.providerid, cfg.authId)
            while True:
                sleep(6)
                if not PaymentStatus(scfg["proxy_port"], cfg.providerid, cfg.authId):
                    log.L.warning("Payment gone!")
                    if config.Config.CAP.exitNoPayment:
                        log.L.warning("Exiting.")
                        sys.exit(2)
                    else:
                        log.A.audit(log.A.NPAYMENT, log.A.PWALLET, wallet=sdp["provider"]["wallet"], paymentid=cfg.authId, anon="no")
                        waitForPayment(scfg["proxy_port"], cfg.providerid, cfg.authId)
                      
    elif (cfg.L):
        print("ProviderId:ServiceId,serviceType,ProviderName,ServiceName")
        for pid in sdps.SDPS.list():
            sdp = sdps.SDPS.getSDP(pid)
            for srv in sdp["services"]:
                sid = srv["id"]
                print("%s:%s,%s,%s,%s" % (pid, sid, srv["type"], sdp["provider"]["name"], srv["name"]))
    else:
        log.L.error("You must specify command (list|connect|show)")
        sys.exit(1)
            
if __name__ == "__main__":
    main(sys.argv[1:])
    
