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
import services

# Starting here
def main(argv):
    config.CONFIG = config.Config("dummy")
    p = configargparse.getArgumentParser(ignore_unknown_config_file_keys=True, fromfile_prefix_chars='@')
    util.commonArgs(p)
    p.add('-f', '--config',                  metavar='CONFIGFILE', required=None, is_config_file=True, default=config.Config.CONFIGFILE, help='Config file')
    p.add('-h', '--help',                    metavar='HELP', required=None, action='store_const', dest='h', const='h', help='Help')
    p.add('-s', '--sdp',                     metavar='SDPFILE', required=None, default=config.Config.SDPFILE, help='SDP file')
    p.add('-l', '--log-level',               dest='d', metavar='LEVEL', help='Log level', default='WARNING')
    p.add('-a', '--audit-log',               dest='a', metavar='FILE', help='Audit log file', default=config.CONFIG.PREFIX + '/var/log/audit.log')
    p.add(       '--wallet-address',            dest='walletAddr', metavar='ADDRESS', required=True, help='Wallet address')
    p.add(       '--wallet-rpc-uri',            dest='walletUri', metavar='URI', default='http://127.0.0.1:13660/json_rpc', help='Wallet URI')
    p.add(       '--wallet-username',           dest='walletUsername', metavar='USER', required=None, default='dispatcher', help='Wallet username')
    p.add(       '--wallet-password',           dest='walletPassword', metavar='PW', required=None, help='Wallet passwd')
    p.add(       '--sdp-server-uri',            dest='sdpUri', metavar='URL', required=None, help='SDP server(s)', default='https://sdp.staging.cloud.lethean.io/v1')

    # Initialise config
    cfg = p.parse_args()    
    config.CONFIG = config.Config("dummy")
    util.parseCommonArgs(p, cfg)
    config.Config.CAP = cfg

    # Initialise services
    services.SERVICES = services.Services()

    log.A.audit(log.A.START, log.A.SERVICE, "itnsconnect")
    
    services.SERVICES.load()
    sys.exit()
        
if __name__ == "__main__":
    main(sys.argv[1:])
    
