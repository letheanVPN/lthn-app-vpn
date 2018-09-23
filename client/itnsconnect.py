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
import atexit
from pprint import pprint
import time
import pickle
import binascii
from util import *
import sdp
import services
import authids
import sessions
import config
import log
import configargparse
from service_ha import ServiceHa
from service_ovpn import ServiceOvpn
import atexit

# Starting here
def main(argv):
    config.CONFIG = config.Config("dummy")
    p = configargparse.getArgumentParser(ignore_unknown_config_file_keys=True, fromfile_prefix_chars='@')
    p.add('-f', '--config',                  metavar='CONFIGFILE', required=None, is_config_file=True, default=config.Config.CONFIGFILE, help='Config file')
    p.add('-h', '--help',                    metavar='HELP', required=None, action='store_const', dest='h', const='h', help='Help')
    p.add('-s', '--sdp',                     metavar='SDPFILE', required=None, default=config.Config.SDPFILE, help='SDP file')
    p.add('-l', '--log-level',               dest='d', metavar='LEVEL', help='Log level', default='WARNING')
    p.add('-a', '--audit-log',               dest='a', metavar='FILE', help='Audit log file', default=config.CONFIG.PREFIX + '/var/log/audit.log')
    p.add('-v', '--verbose',                 metavar='VERBOSITY', action='store_const', dest='v', const='v', help='Be more verbose')
    p.add(       '--wallet-address',            dest='walletAddr', metavar='ADDRESS', required=True, help='Wallet address')
    p.add(       '--wallet-rpc-uri',            dest='walletUri', metavar='URI', default='http://127.0.0.1:13660/json_rpc', help='Wallet URI')
    p.add(       '--wallet-username',           dest='walletUsername', metavar='USER', required=None, default='dispatcher', help='Wallet username')
    p.add(       '--wallet-password',           dest='walletPassword', metavar='PW', required=None, help='Wallet passwd')
    p.add(       '--sdp-uri',                   dest='sdpUri', metavar='URL', required=None, help='SDP server(s)', default='https://slsf2fy3eb.execute-api.us-east-1.amazonaws.com/qa/v1')

    cfg = p.parse_args()
    
    log.L = log.Log(level=cfg.d)
    ah = logging.FileHandler(cfg.a)
    log.A = log.Audit(handler=ah)
    
    # Initialise config
    config.CONFIG = config.Config("dummy")
    config.Config.CAP = cfg
    config.Config.VERBOSE = cfg.v
    config.Config.CONFIGFILE = cfg.config
    config.Config.SDPFILE = cfg.sdp
    config.Config.d = cfg.d
    config.Config.SDPURI = cfg.sdpUri

    if cfg.sdpUri.endswith('/'):
        cfg.sdpUri = cfg.sdpUri[:-1]
    
    # Initialise services
    services.SERVICES = services.Services()

    if (cfg.h):
        print(p.format_help())
        if (config.Config.VERBOSE):
            print(p.format_values())
            print('Service options (can be set by [service-id] sections in ini file:')
            ha = ServiceHa()
            ha.helpOpts("==Haproxy==")
            ovpn = ServiceOvpn()
            ovpn.helpOpts("==OpenVPN==")
            print('Use log level DEBUG during startup to see values assigned to services from SDP.')
            print()
        else:
            print("Use -v option to more help info.")
            print("Happy flying with better privacy!")
        sys.exit()
        
    log.A.audit(log.A.START, log.A.SERVICE, "itnsconnect")
    services.SERVICES.load()
    # Missing code here
    sys.exit()
        
if __name__ == "__main__":
    main(sys.argv[1:])
    
