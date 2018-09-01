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

# Starting here
def main(argv):
    config.CONFIG = config.Config("dummy")
    p = configargparse.getArgumentParser(ignore_unknown_config_file_keys=True, fromfile_prefix_chars='@')
    p.add('-f', '--config',                  metavar='CONFIGFILE', required=None, is_config_file=True, default=config.Config.CONFIGFILE, help='Config file')
    p.add('-h', '--help',                    metavar='HELP', required=None, action='store_const', dest='h', const='h', help='Help')
    p.add('-s', '--sdp',                     metavar='SDPFILE', required=None, default=config.Config.SDPFILE, help='SDP file')
    p.add('-l', '--log-level',               dest='d', metavar='LEVEL', help='Log level', default='WARNING')
    p.add('-A', '--authids',                 dest='A', metavar='FILE', help='Authids db file. Use "none" to disable.', default=config.Config.AUTHIDSFILE)
    p.add('-a', '--audit-log',               dest='a', metavar='FILE', help='Audit log file', default=config.CONFIG.PREFIX + '/var/log/audit.log')
    p.add(      '--refresh-time',            dest='ct', metavar='SEC', help='Refresh frequency. Set to 0 for disable autorefresh.', default=config.CONFIG.T_CLEANUP, type=int)
    p.add(      '--save-time',               dest='st', metavar='SEC', help='Save authid frequency. Use 0 to not save authid regularly.', default=config.CONFIG.T_SAVE, type=int)
    p.add('-lc' ,'--logging-conf',           dest='lc', metavar='FILE', help='Logging config file')
    p.add('-v', '--verbose',                 metavar='VERBOSITY', action='store_const', dest='v', const='v', help='Be more verbose on output')
    p.add('-G', '--generate-providerid',     dest='G', metavar='PREFIX', required=None, help='Generate providerid files')
    p.add('-S', '--generate-server-configs', dest='S', action='store_const', const='generate_server_configs', required=None, help='Generate configs for services and exit')
    p.add('-C', '--generate-client-config',  dest='C', metavar='SERVICEID', required=None, help='Generate client config for specified service on stdout and exit')
    p.add('-D',  '--generate-sdp',           dest='D', action='store_const', const='generate-sdp', required=None, help='Generate SDP by wizzard')
    p.add('-E',  '--edit-sdp',               dest='E', action='store_const', const='edit-sdp', required=None, help='Edit existing SDP config')
    p.add('-U',  '--upload-sdp',             dest='U', action='store_const', const='upload-sdp', required=None, help='Upload SDP')
    p.add(       '--sdp-service-crt',        dest='serviceCrt', metavar='FILE', required=None, help='Provider Proxy crt (for SDP edit/creation only)')
    p.add(       '--sdp-service-type',       dest='serviceType', metavar='TYPE', required=None, help='Service type (proxy or vpn)')
    p.add(       '--sdp-service-fqdn',       dest='serviceFqdn', metavar='FQDN', required=None, help='Service FQDN or IP (for SDP service edit/creation only)')
    p.add(       '--sdp-service-port',       dest='servicePort', metavar='NUMBER', required=None, help='Service port (for SDP service edit/creation only)')
    p.add(       '--sdp-service-name',       dest='serviceName', metavar='NAME', required=None, help='Service name (for SDP service edit/creation only)')
    p.add(       '--sdp-service-id',         dest='serviceId', metavar='NUMBER', required=None, help='Service ID (for SDP service edit/creation only)')
    p.add(       '--sdp-service-cost',       dest='serviceCost', metavar='ITNS', required=None, help='Service cost (for SDP service edit/creation only)')
    p.add(       '--sdp-service-disable',    dest='serviceDisable', metavar='NUMBER', required=None, help='Set to true to disable service; otherwise leave false.', default=False)
    p.add(       '--sdp-service-refunds',    dest='serviceAllowRefunds', metavar='NUMBER', required=None, help='Allow refunds for Service (for SDP service edit/creation only)', default=False)
    p.add(       '--sdp-service-dlspeed',    dest='serviceDownloadSpeed', metavar='Mbps', required=None, help='Download speed for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-ulspeed',    dest='serviceUploadSpeed', metavar='Mbps', required=None, help='Upload speed for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-prepaid-mins',  dest='servicePrepaidMinutes', metavar='TIME', required=None, help='Prepaid minutes for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-verifications', dest='serviceVerificationsNeeded', metavar='NUMBER', required=None, help='Verifications needed for Service (for SDP service edit/creation only)')
    p.add(       '--ca',                        dest='providerCa', metavar="ca.crt", required=True, help='Set certificate authority file')
    p.add(       '--wallet-address',            dest='walletAddr', metavar='ADDRESS', required=True, help='Wallet address')
    p.add(       '--wallet-rpc-uri',            dest='walletUri', metavar='URI', default='http://127.0.0.1:13660/json_rpc', help='Wallet URI')
    p.add(       '--wallet-username',           dest='walletUsername', metavar='USER', required=None, default='dispatcher', help='Wallet username')
    p.add('-H',  '--from-height',               dest='initHeight', metavar='HEIGHT', required=None, type=int, default=-1, help='Initial height to start scan payments. Default is actual height.')
    p.add(       '--wallet-password',           dest='walletPassword', metavar='PW', required=None, help='Wallet passwd')
    p.add(       '--sdp-uri',                   dest='sdpUri', metavar='URL', required=None, help='SDP server(s)', default='https://jhx4eq5ijc.execute-api.us-east-1.amazonaws.com/dev/v1')
    p.add(       '--provider-id',               dest='providerid', metavar='PROVIDERID', required=True, help='ProviderID (public ed25519 key)')
    p.add(       '--provider-key',              dest='providerkey', metavar='PROVIDERKEY', required=True, help='ProviderID (private ed25519 key)')
    p.add(       '--provider-name',             dest='providerName', metavar='NAME', required=True, help='Provider Name') 
    p.add(       '--provider-type',             dest='nodeType', metavar='TYPE', required=None, help='Provider type', default='residential', choices=['commercial', 'residential', 'government'])
    p.add(       '--provider-terms',            dest='providerTerms', metavar='TEXT', required=None, help='Provider terms')

    cfg = p.parse_args()
    
    if (cfg.lc):
        logging.config.fileConfig(cfg.lc)
        log.L = log.Log(level=cfg.d)
        log.A = log.Audit(level=logging.WARNING)
    else:
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
    config.Config.a = cfg.a
    config.Config.T_SAVE = cfg.st
    config.Config.T_CLEANUP = cfg.ct
    config.Config.AUTHIDSFILE = cfg.A
    config.Config.SDPURI = cfg.sdpUri
    if (config.Config.AUTHIDSFILE == "none"):
        config.Config.T_SAVE = 0
        config.Config.AUTHIDSFILE = ''
        
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
        
    if (cfg.G):
        # Generate providerid to file.private, file.public, file.seed
        privatef = cfg.G
        try:
            signing_key, verifying_key = ed25519.create_keypair()
            open(privatef + ".private", "wb").write(signing_key.to_ascii(encoding="hex"))
            open(privatef + ".public", "wb").write(verifying_key.to_ascii(encoding="hex"))
            open(privatef + ".seed", "wb").write(binascii.hexlify(signing_key.to_seed()))
            os.chmod(privatef + ".private", 0o700)
            os.chmod(privatef + ".seed", 0o700)
            print("Your providerid keys are stored in files %s, %s, %s." % (privatef + ".private", privatef + ".public", privatef + ".seed"))
            print("You must edit your ini file.")
        except (IOError, OSError):
            log.L.error("Cannot open/write %s" % (privatef))
        sys.exit()
        
    if (cfg.U):
        log.L.warning("Uploading SDP to server %s" % (config.CONFIG.CAP.sdpUri))
        log.A.audit(log.A.UPLOAD, log.A.SDP, config.CONFIG.SDPFILE)
        s=sdp.SDP()
        s.load(config.CONFIG.SDPFILE)
        if (not s.upload(config.CONFIG)):
            log.L.error("Error uploading SDP!")
            sys.exit(2)
        sys.exit()

    if (cfg.E):
        log.L.warning("Editing SDP config %s" % (config.CONFIG.SDPFILE))
        s=sdp.SDP()
        s.load(config.CONFIG.SDPFILE)
        if (not s.editService(config.CONFIG)):
            log.L.error("Error editing config!")
            sys.exit(2)
        else:
            print('YOUR CHANGES TO THE SDP CONFIG file ARE UNSAVED!')
            choice = input('Save the file? This will overwrite your existing config file! [y/N] ').strip().lower()[:1]
            if (choice == 'y'):
                s.save(config.CONFIG)
        sys.exit()
        
    if (cfg.S):
        services.SERVICES.load()
        # Generate config files for Openvpn and Haproxy only and exit
        services.SERVICES.createConfigs()
        sys.exit()
        
    if (cfg.C):
        services.SERVICES.load()
        # Generate client config for service id and put to stdout
        id = cfg.C
        services.SERVICES.get(id).createClientConfig()
        sys.exit()
        
    if (cfg.D):
        config.CONFIG=config.Config("init", services.SERVICES)
        sys.exit()
        
    log.A.audit(log.A.START, log.A.SERVICE, "itnsdispatcher")
    
    services.SERVICES.load()
        
    # Initialise sessions
    sessions.SESSIONS = sessions.Sessions()
    # Show services from SDP
    services.SERVICES.show()
    # Run all services
    services.SERVICES.run()
    
    # Preinitialise authids
    authids.AUTHIDS = authids.AuthIds()
    
    # Wait for all services to settle
    i = 1
    while i < 20:
        services.SERVICES.orchestrate()
        time.sleep(0.1)
        i = i + 1
    
    # Load authids from file
    tmpauthids=authids.AUTHIDS.load()
    if (tmpauthids):
        authids.AUTHIDS=tmpauthids
    
    authids.AUTHIDS.getFromWallet()
    
    overaltime = 0
    savedcount = 0
    cleanupcount = 0
    starttime = time.time()
    loopstart = starttime
    lastrefresh = starttime
    while (1):
        looptime = time.time() - loopstart
        loopstart = time.time()
        time.sleep(config.Config.MAINSLEEP)
        services.SERVICES.orchestrate()
        
        if ((config.Config.T_SAVE > 0 and overaltime / config.Config.T_SAVE > savedcount) or config.Config.FORCE_SAVE):
            authids.AUTHIDS.save()
            savedcount = savedcount + 1
            config.Config.FORCE_SAVE = None
            
        if ((config.Config.T_CLEANUP > 0 and overaltime / config.Config.T_CLEANUP > cleanupcount) or config.Config.FORCE_REFRESH):
            authids.AUTHIDS.getFromWallet()
            authids.AUTHIDS.cleanup()
            sessions.SESSIONS.refresh(time.time() - lastrefresh)
            cleanupcount = cleanupcount + 1
            lastrefresh = time.time()
            config.Config.FORCE_REFRESH = None
            
        overaltime = time.time() - starttime
        
if __name__ == "__main__":
    main(sys.argv[1:])
    