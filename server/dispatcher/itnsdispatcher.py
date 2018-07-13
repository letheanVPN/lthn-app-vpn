#!/usr/bin/python

import os
import sys
# Add lib directory to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))

import ed25519
import getopt
import logging
import atexit
from pprint import pprint
import time
import pickle
import binascii
from util import *
from sdp import *
from services import Services, Service, SERVICES
from authids import AuthIds, AuthId, AUTHIDS
from sessions import Sessions, SESSIONS
from config import Config
import configargparse

# Starting here
def main(argv):
    p = configargparse.getArgumentParser(ignore_unknown_config_file_keys=True)
    p.add('-f', '--config',                  metavar='CONFIGFILE', required=None, is_config_file=True, default=Config.CONFIGFILE, help='Config file')
    p.add('-h', '--help',                    metavar='HELP', required=None, action='store_const', dest='h', const='h', help='Help')
    p.add('-s', '--sdp',                     metavar='SDPFILE', required=None, default=Config.SDPFILE, help='SDP file')
    p.add('-d', '--debug',                   dest='d', metavar='LEVEL', help='Debug level', default='WARNING')
    p.add('-v', '--verbose',                 metavar='VERBOSITY', action='store_const', dest='v', const='v', help='Be more verbose on output')
    p.add('-G', '--generate-providerid',     dest='G', metavar='PREFIX', required=None, help='Generate providerid files')
    p.add('-S', '--generate-server-configs', dest='S', action='store_const', const='generate_server_configs', required=None, help='Generate configs for services and exit')
    p.add('-C', '--generate-client-config',  dest='C', metavar='SERVICEID', required=None, help='Generate client config for specified service on stdout and exit')
    p.add('-D',  '--generate-sdp',           dest='D', action='store_const', const='generate-sdp', required=None, help='Generate SDP by wizzard')
    p.add(       '--sdp-provider-type',          dest='nodeType', metavar='TYPE', required=None, help='Provider type (for SDP edit/creation only)', default='commercial', choices=['commercial', 'residential', 'government'])
    p.add(       '--sdp-provider-id',            dest='providerId', metavar='ID', required=None, help='Provider ID (for SDP edit/creation only)')
    p.add(       '--sdp-provider-name',          dest='providerName', metavar='NAME', required=None, help='Provider Name (for SDP edit/creation only)')
    p.add(       '--sdp-wallet-address',         dest='walletAddr', metavar='ADDR', required=None, help='Wallet address (for SDP edit/creation only)')
    p.add(       '--sdp-provider-terms',         dest='providerTerms', metavar='TEXT', required=None, help='Provider terms (for SDP edit/creation only)')
    p.add(       '--sdp-provider-ca',           dest='providerCa', metavar='FILE', required=None, help='Provider CA file (for SDP edit/creation only)')
    p.add(       '--sdp-service-crt',         dest='serviceCrt', metavar='FILE', required=None, help='Provider Proxy crt (for SDP edit/creation only)')
    p.add(       '--sdp-service-type',         dest='serviceType', metavar='TYPE', required=None, help='Provider VPN crt (for SDP edit/creation only)')
    p.add(       '--sdp-service-fqdn',         dest='serviceFqdn', metavar='FQDN', required=None, help='Service FQDN or IP (for SDP service edit/creation only)')
    p.add(       '--sdp-service-port',         dest='servicePort', metavar='NUMBER', required=None, help='Service port (for SDP service edit/creation only)')
    p.add(       '--sdp-service-name',         dest='serviceName', metavar='NAME', required=None, help='Service name (for SDP service edit/creation only)')
    p.add(       '--sdp-service-id',           dest='serviceId', metavar='NUMBER', required=None, help='Service ID (for SDP service edit/creation only)')
    p.add(       '--sdp-service-cost',         dest='serviceCost', metavar='ITNS', required=None, help='Service cost (for SDP service edit/creation only)')
    p.add(       '--sdp-service-refunds',      dest='serviceAllowRefunds', metavar='NUMBER', required=None, help='Allow refunds for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-dlspeed',      dest='serviceDownloadSpeed', metavar='Mbps', required=None, help='Download speed for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-ulspeed',      dest='serviceUploadSpeed', metavar='Mbps', required=None, help='Upload speed for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-prepaid-mins',      dest='servicePrepaidMinutes', metavar='TIME', required=None, help='Prepaid minutes for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-verifications',      dest='serviceVerificationsNeeded', metavar='NUMBER', required=None, help='Verifications needed for Service (for SDP service edit/creation only)')
    p.add(       '--ca',                        metavar="ca.crt", required=True, help='Set certificate authority file')
    p.add(       '--provider-id',  dest='providerid', metavar='PROVIDERID', required=True, help='ProviderID (public ed25519 key)')
    p.add(       '--provider-key',  dest='providerkey', metavar='PROVIDERKEY', required=True, help='ProviderID (private ed25519 key)')
    
    cfg = p.parse_args()    
    Config.CAP = cfg
    Config.CONFIGFILE = cfg.config
    Config.SDPFILE = cfg.sdp
    if (cfg.d):
        Config.LOGLEVEL = cfg.d
    if (cfg.v):
        Config.VERBOSE = True
    # Initialise logger
    Log = logging.getLogger()
    Log.setLevel(cfg.d)
    # Initialise config
    CONFIG = Config()
    # Initialise authids
    AUTHIDS = AuthIds()
    tmpauthids=AUTHIDS.load()
    if (tmpauthids):
        AUTHIDS=tmpauthids
    # Initialise services
    SERVICES = Services()

    if (cfg.h):
        print(p.format_help())
        if (Config.VERBOSE):
            print(p.format_values()) 
        sys.exit()
    if (cfg.G):
        # Generate providerid to file.private, file.public, file.seed
        privatef = cfg.G
        try:
            signing_key, verifying_key = ed25519.create_keypair()
            open(privatef + ".private", "wb").write(signing_key.to_ascii(encoding="hex"))
            open(privatef + ".public", "wb").write(verifying_key.to_ascii(encoding="hex"))
            open(privatef + ".seed", "wb").write(binascii.hexlify(signing_key.to_seed()))
            print("Your providerid keys are stored in files %s, %s, %s." % (privatef + ".private". privatef + ".public", privatef + ".seed"))
            print("You must edit your ini file.")
        except (IOError, OSError):
            logging.error("Cannot open/write %s" % (privatef))
        sys.exit()
    
    if (cfg.S):
        # Generate config files for Openvpn and Haproxy only and exit
        SERVICES.createConfigs()
        sys.exit()
    if (cfg.C):
        # Generate client config for service id and put to stdout
        id = cfg.C
        SERVICES.get(id).createClientConfig()
        sys.exit()
    if (cfg.D):
        CONFIG=Config("init")
        sys.exit()

    # Initialise sessions
    SESSIONS = Sessions()
    # Show services from SDP
    SERVICES.show()
    # Run all services
    SERVICES.run()
    
    while (1):
        start = time.time()
        SERVICES.orchestrate()
        #AUTHIDS.getFromWallet(SERVICES)
        #AUTHIDS.show()
        time.sleep(0.1)
        SERVICES.orchestrate()
        end = time.time()
        AUTHIDS.save()
        
if __name__ == "__main__":
    main(sys.argv[1:])