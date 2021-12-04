import time
import json
import config
import logging
import log
import logging.config
import services
import sys
from service_ha import ServiceHa
from service_ovpn import ServiceOvpn
import socket
import ipaddress
import hashlib
import base64
import re
import dns.resolver

def timefmt(tme):
    return(time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(tme)))

def valuesToString(values, eq=':', sep=' ', nl="\n"):
    str=""
    for k in values.keys():
        str = str + "%s%s%s%s" % (k, eq, values[k], sep)
    return(str+nl)

def valuesToJson(values):
    str=json.dumps(values)
    return(str)

def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

def anonymise_ip(ip):
    if is_valid_ipv4_address(ip):
        srcnet = ipaddress.ip_network(ip+"/24", strict=False)
        h = hashlib.sha1()
        h.update(str(srcnet).encode("utf-8"))
        return(h.hexdigest())
    elif is_valid_ipv6_address(ip):
        srcnet = ipaddress.ip_network(ip+"/64", strict=False)
        h = hashlib.sha1()
        h.update(str(srcnet).encode("utf-8"))
        return(h.hexdigest())
    else:
        return(None)
    
def anonymise_uri(uri):
    h = hashlib.sha1()
    h.update(uri.encode("utf-8"))
    return(h.hexdigest())
    
def anonymise_paymentid(paymentid):
    p = base64.b64encode(paymentid.encode("utf-8")).decode("utf-8")
    return(p[0:3] + p[-3:])

def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True

def helpmsg(p):
    print(p.format_help())
    if (config.Config.VERBOSE):
        print(p.format_values())
        print('Service options (can be set by [service-id] sections in ini file:')
        ha = ServiceHa("00")
        ha.helpOpts("==Haproxy==")
        ovpn = ServiceOvpn("00")
        ovpn.helpOpts("==OpenVPN==")
        print('Use log level DEBUG during startup to see values assigned to services from SDP.')
        print()
    else:
        print("Use -v option to more help info.")
        print("Happy flying with better privacy!")

def commonArgs(p):
    p.add_argument('-l', '--log-level',               dest='d', metavar='LEVEL', help='Log level', default='WARNING')
    p.add_argument(      '--syslog',                  dest='syslog', const='syslog', action='store_const', help='Use syslog', default=None)
    p.add_argument('-v', '--verbose',                 metavar='VERBOSITY', action='store_const', dest='v', const='v', help='Be more verbose')
    p.add_argument('-h', '--help',                    metavar='HELP', required=None, action='store_const', dest='h', const='h', help='Help')
    p.add_argument('-f', '--config', metavar='CONFIGFILE', required=None, is_config_file=True, default=config.Config.CONFIGFILE, help='Config file')
    p.add_argument('-s', '--sdp', metavar='SDPFILE', required=None, default=config.Config.SDPFILE, help='SDP file')
    p.add_argument('-p', '--pid', dest='p', metavar='PIDFILE', required=None, default=config.Config.PIDFILE, help='PID file')
    p.add_argument('-A', '--authids',                 dest='A', metavar='FILE', help='Authids db file.', default="none")
    p.add_argument('-a', '--audit-log', dest='a', metavar='FILE', help='Audit log file', default=config.CONFIG.PREFIX + '/var/log/audit.log')
    p.add_argument(      '--audit-log-json',          dest='aj', action='store_const', const='aj', metavar='Bool', help='Audit log to JSON', default=None)
    p.add_argument('-lc' ,'--logging-conf',           dest='lc', metavar='FILE', help='Logging config file')
    p.add_argument(       '--service-conf-dir',       dest='serviceDir', metavar='DIR', required=None, default=None, help='Use this directory to save config files for service. Use only for config generation per one service!')
    p.add_argument(       '--haproxy-bin', dest='haproxyBin', metavar='Binary', required=None, help='Haproxy binary', default=config.Config.HAPROXY_BIN)
    p.add_argument(       '--openvpn-bin', dest='openvpnBin', metavar='Binary', required=None, help='OpenVPN binary', default=config.Config.OPENVPN_BIN)
    p.add_argument(       '--stunnel-bin', dest='stunnelBin', metavar='Binary', required=None, help='Stunnel binary', default=config.Config.STUNNEL_BIN)
    p.add_argument(       '--sdp-server-uri',         dest='sdpUri', metavar='URL', required=None, help='SDP server(s)', default='https://sdp.lethean.io')
    p.add_argument(       '--sdp-wallet-address',     dest='sdpWallet', metavar='ADDRESS', required=None, help='SDP server wallet address', default='iz4xKrEdzsF5dP7rWaxEUT4sdaDVFbXTnD3Y9vXK5EniBFujLVp6fiAMMLEpoRno3VUccxJPnHWyRctmsPiX5Xcd3B61aDeas')
    p.add_argument(       '--sdp-service-endpoint',   dest='serviceFqdn', metavar='FQDN', required=None, help='Service FQDN or IP')
    p.add_argument(       '--sdp-service-port',       dest='servicePort', metavar='NUMBER', required=None, help='Service port')
    p.add_argument(       '--sdp-service-proto',      dest='serviceProto', metavar='PROTOCOL', required=None, default=None, help='Service protocol')
    p.add_argument(       '--sdp-service-id',         dest='serviceId', metavar='NUMBER', required=None, help='Service ID')
    p.add_argument(       '--provider-id',            dest='providerid', metavar='PROVIDERID', required=None, default='<NOID>', help='ProviderID (public ed25519 key)')
    p.add_argument(       '--ca',                     dest='providerCa', metavar="ca.crt", required=None, default='<NOCA>', help='Set certificate authority file')
    p.add_argument(       '--wallet-address',         dest='walletAddr', metavar='ADDRESS', required=None, default='<NOADDR>', help='Provider wallet address')
    p.add_argument(       '--sdp-cache-dir', dest='sdpCacheDir', metavar='DIR', required=None, default=config.CONFIG.PREFIX + '/var/', help='SDP cache dir')
    p.add_argument(       '--sdp-cache-expiry',       dest='sdpCacheExpiry', metavar='SECONDS', required=None, default=300, help='SDP cache expiry in seconds')
    p.add_argument(       '--compatibility',          dest='comp', metavar='Level', required=None, default="v3", choices=["v3.1", "v3"], help='Compatibility level for remote node. Use v3.1 or v3')
    p.add_argument(       '--vpnd-dns',               dest='vpndDns', metavar='IP', required=None, default=None, help='Use and offer local DNS server for VPN clients')
    p.add_argument(       '--vpnd-more-user-sessions',dest='duplicateCN', metavar='bool', action='store_const', const='duplicateCN', required=None, default=None, help='If true, user can connect multiple sessions with one paymentid.')
    p.add_argument(       '--vpnd-iprange',           dest='vpndIPRange', metavar='IP', required=None, default="10.11.0.0", help='IP Range for client IPs. Client will get /30 subnet from this range.')
    p.add_argument(       '--vpnd-ipmask',            dest='vpndIPMask', metavar='MASK', required=None, default="255.255.0.0", help='IP mask for client IPs')
    p.add_argument(       '--vpnd-ip6range',          dest='vpndIP6Range', metavar='IP6', required=None, default=None, help='IP6 Range for client IPs. Client will get /30 subnet from this range.')
    p.add_argument(       '--vpnd-reneg',             dest='vpndReneg', metavar='S', required=None, default=600, help='Client has to renegotiate after this number of seconds to check if paymentid is still active')
    p.add_argument(       '--vpnd-tun',               dest='vpndTun', metavar='IF', required=None, default="tun0", help='Use specific tun device for server')
    p.add_argument(       '--vpnd-mgmt-port',         dest='vpndMgmtPort', metavar='PORT', required=None, default="11192", help='Use specific port for local mgmt')
    p.add_argument(       '--vpnc-standalone',        dest='vpncStandalone', action='store_const', const='vpncStandalone', metavar='Bool', required=None, help='Create standalone openvn config that can be run outside of dispatcher.')
    p.add_argument(       '--proxyc-standalone',      dest='proxycStandalone',  action='store_const', const='proxycStandalone', metavar='Bool', required=None, help='Create standalone haproxy config that can be run outside of dispatcher.')
    p.add_argument(       '--no-run',                 dest='noRun', action='store_const', const='vpncStandalone', metavar='Bool', required=None, help='Do not run openvpn or haproxy, just prepare configs')

def parseCommonArgs(parser, cfg, name):
    if (cfg.lc):
        logging.config.fileConfig(cfg.lc)
        log.L = log.Log(level=cfg.d, name=name)
        log.A = log.Audit(level=logging.WARNING)
    elif (cfg.syslog):
        h = logging.handlers.SysLogHandler(address="/dev/log")
        log.L = log.Log(level=cfg.d, name=name, handler=h)
        log.A = log.Audit(handler=h)
    else:
        ah = logging.FileHandler(cfg.a)
        log.L = log.Log(level=cfg.d, name=name)
        log.A = log.Audit(handler=ah)
    config.Config.VERBOSE = cfg.v
    config.Config.CONFIGFILE = cfg.config
    config.Config.SDPFILE = cfg.sdp
    config.Config.d = cfg.d
    config.Config.a = cfg.a
    config.Config.SDPURI = cfg.sdpUri
    config.CONFIG.PIDFILE = cfg.p
    if (config.Config.AUTHIDSFILE == "none"):
        config.Config.T_SAVE = 0
        config.Config.AUTHIDSFILE = ''
    if (cfg.comp=="v3"):
        cfg.mgmtHeader="X-ITNS-MgmtID"
        cfg.authidHeader="X-ITNS-PaymentID"
    elif (cfg.comp=="v3.1"):
        cfg.mgmtHeader="X-LTHN-MgmtID"
        cfg.authidHeader="X-LTHN-PaymentID"
    else:
        log.L.error("Bad compatibility level.")
        sys.exit(2)
    if cfg.sdpUri.endswith('/'):
        cfg.sdpUri = cfg.sdpUri[:-1]
    if not cfg.sdpUri.endswith('/v1'):
        cfg.sdpUri = cfg.sdpUri + '/v1'
    cfg.sdpUri = {'sdp': cfg.sdpUri}
    if cfg.noRun:
        cfg.vpncStandalone = True
        cfg.proxycStandalone = True
    
    # Initialise services
    services.SERVICES = services.Services()

    if (cfg.h):
        helpmsg(parser)
        sys.exit()

def testLocalPort(bind, port, type=socket.SOCK_STREAM):
    sock = socket.socket(socket.AF_INET, type)
    result = False
    try:
        sock.bind((bind, port))
        result = True
    except:
        log.L.error("Port %s is in use!" % (port))
        sys.exit(1)
    sock.close()
    return result

def parseProvider(provider):
    p = re.search("\.", provider)
    if (p):
        try:
            log.L.debug("Getting DNS TXT record at %s" % (provider))
            answers = dns.resolver.query(provider, 'TXT')
        except dns.exception.DNSException as e:
            log.L.error(e)
            return(None)

        for rdata in answers.rrset:
            for txt in rdata.strings:
                txt = txt.decode("utf-8")
                variables = txt.split(";")
                ver = variables[0]
                name, value = ver.split("=")
                if (name != "lv"):
                    log.L.debug("Ignoring DNS TXT record %s" % (txt))
                    continue
                if (name == "lv" and value != config.Config.CAP.comp):
                    log.L.debug("Ignoring DNS TXT record with bad version %s" % (txt))
                    continue
                log.L.debug("Processing DNS TXT record %s" % (txt))
                for v in variables:
                    name, value = v.split("=")
                    if (name=="lv"):
                        continue
                    if (name=="sdp"):
                        log.L.info("Adding SDP %s" % (value))
                        config.Config.CAP.sdpUri[provider] = value
                    if (name=="id"):
                        log.L.info("Adding providerid %s" % (value))
                        pid = value
        if pid:
            return(pid)
        else:
            return(provider)
    else:
        return(provider.upper())
