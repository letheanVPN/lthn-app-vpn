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
import util
import configargparse
import binascii
import services
import sdp

# Starting here
def main(argv):
    # Chroot and drop privileges first
    config.CONFIG = config.Config("dummy")
    p = configargparse.getArgumentParser(ignore_unknown_config_file_keys=True, fromfile_prefix_chars='@')
    util.commonArgs(p)
    p.add('-G', '--generate-providerid',     dest='G', metavar='PREFIX', required=None, help='Generate providerid files')
    p.add('-D',  '--generate-sdp',           dest='D', action='store_const', const='generate-sdp', required=None, help='Generate SDP by wizzard')
    p.add('-E',  '--edit-sdp',               dest='E', action='store_const', const='edit-sdp', required=None, help='Edit existing SDP config')
    p.add('-U',  '--upload-sdp',             dest='U', action='store_const', const='upload-sdp', required=None, help='Upload SDP')
    p.add('-S', '--generate-server-configs', dest='S', action='store_const', const='generate_server_configs', required=None, help='Generate configs for services and exit')
    p.add('-C', '--generate-client-config',  dest='C', metavar='SERVICEID', required=None, help='Generate config for given service')
    p.add(       '--sdp-service-crt',        dest='serviceCrt', metavar='FILE', required=None, help='Provider Proxy crt (for SDP edit/creation only)')
    p.add(       '--sdp-service-type',       dest='serviceType', metavar='TYPE', required=None, help='Service type (proxy or vpn)')
    p.add(       '--sdp-service-name',       dest='serviceName', metavar='NAME', required=None, help='Service name (for SDP service edit/creation only)')
    p.add(       '--sdp-service-cost',       dest='serviceCost', metavar='ITNS', required=None, help='Service cost (for SDP service edit/creation only)')
    p.add(       '--sdp-service-disable',    dest='serviceDisable', metavar='NUMBER', required=None, help='Set to true to disable service; otherwise leave false.', default=False)
    p.add(       '--sdp-service-refunds',    dest='serviceAllowRefunds', metavar='NUMBER', required=None, help='Allow refunds for Service (for SDP service edit/creation only)', default=False)
    p.add(       '--sdp-service-dlspeed',    dest='serviceDownloadSpeed', metavar='Mbps', default=10, required=None, help='Download speed for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-ulspeed',    dest='serviceUploadSpeed', metavar='Mbps', default=10, required=None, help='Upload speed for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-prepaid-mins',  dest='servicePrepaidMinutes', default=30, metavar='TIME', required=None, help='Prepaid minutes for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-service-verifications', dest='serviceVerificationsNeeded', default=0, metavar='NUMBER', required=None, help='Verifications needed for Service (for SDP service edit/creation only)')
    p.add(       '--sdp-provider-name',         dest='providerName', metavar='NAME', required=None, help='Provider Name') 
    p.add(       '--sdp-provider-type',         dest='nodeType', metavar='TYPE', required=None, help='Provider type', default='residential', choices=['commercial', 'residential', 'government'])
    p.add(       '--sdp-provider-terms',        dest='providerTerms', metavar='TEXT', required=None, help='Provider terms')
    p.add(       '--provider-key',           dest='providerkey', metavar='PROVIDERKEY', required=True, help='ProviderID (private ed25519 key)')

    # Initialise config
    config.CONFIG = config.Config("dummy")
    cfg = p.parse_args()
    util.parseCommonArgs(p, cfg, 'lvmgmt')
    config.Config.CAP = cfg
    
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
    
    elif (cfg.U):
        log.L.warning("Uploading SDP to server %s" % (config.CONFIG.CAP.sdpUri))
        log.A.audit(log.A.UPLOAD, log.A.SDP, config.CONFIG.SDPFILE)
        log.A.audit(log.A.NPAYMENT, log.A.SWALLET, wallet=config.CONFIG.CAP.sdpWallet, paymentid=config.CONFIG.CAP.providerid.upper(), anon="no")
        s=sdp.SDP()
        s.load(config.CONFIG.SDPFILE)
        if (not s.upload(config.CONFIG)):
            log.L.error("Error uploading SDP!")
            sys.exit(2)
        sys.exit()
        
    elif (cfg.D):
        config.CONFIG=config.Config("init", services.SERVICES)
        sys.exit()

    elif (cfg.E):
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
    elif (cfg.S):
        print("Use " + os.path.abspath(os.path.dirname(__file__)) + '/lthnvpnd' + '-S')
        sys.exit(1)
    elif (cfg.C):
        print("Use " + os.path.abspath(os.path.dirname(__file__)) + '/lthnvpnc' + '-C id')
        sys.exit(1)
    else:
        util.helpmsg(p)
        log.L.error("You need to specify action. Exiting.")
        sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])
    