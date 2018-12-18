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

def timefmt(tme):
    return(time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(tme)))

def valuesToString(values):
    str=""
    for k in values.keys():
        str = str + "%s:%s " % (k,values[k])
    return(str+"\n")

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
    print(p)
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
    p.add('-l', '--log-level',               dest='d', metavar='LEVEL', help='Log level', default='WARNING')
    p.add('-v', '--verbose',                 metavar='VERBOSITY', action='store_const', dest='v', const='v', help='Be more verbose')
    p.add('-h', '--help',                    metavar='HELP', required=None, action='store_const', dest='h', const='h', help='Help')
    p.add('-f', '--config',                  metavar='CONFIGFILE', required=None, is_config_file=True, default=config.Config.CONFIGFILE, help='Config file')    
    p.add('-s', '--sdp',                     metavar='SDPFILE', required=None, default=config.Config.SDPFILE, help='SDP file')
    p.add('-p', '--pid',                     dest='p', metavar='PIDFILE', required=None, default=config.Config.PIDFILE, help='PID file')
    p.add('-A', '--authids',                 dest='A', metavar='FILE', help='Authids db file.', default="none")
    p.add('-a', '--audit-log',               dest='a', metavar='FILE', help='Audit log file', default=config.CONFIG.PREFIX + '/var/log/audit.log')
    p.add('-lc' ,'--logging-conf',           dest='lc', metavar='FILE', help='Logging config file')
    p.add(       '--sdp-server-uri',         dest='sdpUri', metavar='URL', required=None, help='SDP server(s)', default='https://sdp.lethean.io/v1')
    p.add(       '--sdp-wallet-address',     dest='sdpWallet', metavar='ADDRESS', required=None, help='SDP server wallet address', default='iz4xKrEdzsF5dP7rWaxEUT4sdaDVFbXTnD3Y9vXK5EniBFujLVp6fiAMMLEpoRno3VUccxJPnHWyRctmsPiX5Xcd3B61aDeas')
    p.add(       '--sdp-service-endpoint',   dest='serviceFqdn', metavar='FQDN', required=None, help='Service FQDN or IP')
    p.add(       '--sdp-service-port',       dest='servicePort', metavar='NUMBER', required=None, help='Service port')
    p.add(       '--sdp-service-id',         dest='serviceId', metavar='NUMBER', required=None, help='Service ID')
    p.add(       '--provider-id',            dest='providerid', metavar='PROVIDERID', required=True, help='ProviderID (public ed25519 key)')
    p.add(       '--ca',                     dest='providerCa', metavar="ca.crt", required=True, help='Set certificate authority file')
    p.add(       '--wallet-address',         dest='walletAddr', metavar='ADDRESS', required=True, help='Provider wallet address')
    p.add(       '--sdp-cache-file',         dest='sdpCacheFile', metavar='FILE', required=None, default=config.CONFIG.PREFIX + '/var/sdps.json', help='SDP cache')
    p.add(       '--sdp-cache-expiry',       dest='sdpCacheExpiry', metavar='SECONDS', required=None, default=300, help='SDP cache expiry in seconds')
    p.add(       '--compatibility',          dest='comp', metavar='Level', required=None, default="v3", help='Compatibility level for remote node. Use v3 or v4')


def parseCommonArgs(parser, cfg):
    if (cfg.lc):
        logging.config.fileConfig(cfg.lc)
        log.L = log.Log(level=cfg.d)
        log.A = log.Audit(level=logging.WARNING)
    else:
        ah = logging.FileHandler(cfg.a)
        log.L = log.Log(level=cfg.d)
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
    elif (cfg.comp=="v4"):
        cfg.mgmtHeader="X-LTHN-MgmtID"
        cfg.authidHeader="X-LTHN-PaymentID"
    else:
        log.L.error("Bad compatibility level. Use v3 or v4 now.")
        sys.exit(2)
    if cfg.sdpUri.endswith('/'):
        cfg.sdpUri = cfg.sdpUri[:-1]
    
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