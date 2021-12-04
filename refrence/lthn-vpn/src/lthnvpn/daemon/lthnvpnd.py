#!/usr/bin/python

import os
import sys
import ed25519
import getopt
import logging
import logging.config
import atexit
from pprint import pprint
import time
import pickle
import binascii
import configargparse
import pwd
import grp
from lthnvpn.lib import config, log, services, util, authids, sessions, sdp

def remove_pidfile():
    pf = open(config.CONFIG.PIDFILE,"r")
    pid = int(pf.read())
    if (os.getpid() == pid):
        os.remove(config.CONFIG.PIDFILE)

# Starting here
def main(argv):
    # Chroot and drop privileges first
    config.CONFIG = config.Config("dummy")
    p = configargparse.getArgumentParser(ignore_unknown_config_file_keys=True, fromfile_prefix_chars='@', add_help=None)
    p.add(      '--user',                    dest='user', metavar='USERNAME', help='Switch privileges to this user', default=None)
    p.add(      '--group',                   dest='group', metavar='GROUP', help='Switch privileges to this group', default=None)
    p.add(      '--chroot',                  dest='chroot', action='store_const', const='chroot', help='Chroot to prefix', default=None)
    cfg = p.parse_known_args()
    cfg = cfg[0]
    if (os.geteuid() == 0):
        if (cfg.user):
             runningUid = pwd.getpwnam(cfg.user).pw_uid
        else:
            logging.error("Cannot run as root! Exiting.")
            sys.exit(2)

        if (cfg.group):
            runningGid = grp.getgrnam(cfg.group).gr_gid

        if (cfg.chroot):
            os.chroot(config.CONFIG.PREFIX)
            logging.info("Chroot to to: %s" % (config.CONFIG.PREFIX))
            os.environ["LTHN_PREFIX"] = "/"
            config.CONFIG = config.Config()

        os.setgroups([])
        if (cfg.group):
            os.setgid(runningGid)

        os.setuid(runningUid)
        logging.info("Dropped privileges to: %s" % (cfg.user)) 
    else:
        if (cfg.user or cfg.group or cfg.chroot):
            logging.error("Cannot switch privileges as non root! Exiting.")
            sys.exit(2)

    util.commonArgs(p)
    p.add(      '--refresh-time',            dest='ct', metavar='SEC', help='Refresh frequency. Set to 0 for disable autorefresh.', default=config.CONFIG.T_CLEANUP, type=int)
    p.add(      '--save-time',               dest='st', metavar='SEC', help='Save authid frequency. Use 0 to not save authid regularly.', default=config.CONFIG.T_SAVE, type=int)
    p.add(      '--max-wait-to-spend',       dest='maxToSpend', metavar='SEC', help='When payment arrive, we will wait max this number of seconds for first session before spending credit.', default=30, type=int)
    p.add(      '--run-services',            dest='runServices', default=True, type=bool, required=None, help='Run services from dispatcher or externally. Default to run by itnsdispatcher.')
    p.add(      '--track-sessions',          dest='trackSessions', default=True, type=bool, required=None, help='If true, dispatcher will track sessions. If not, existing sessions will not be terminated after payment is spent.')
    p.add('-S', '--generate-server-configs', dest='S', action='store_const', const='generate_server_configs', required=None, help='Generate configs for services and exit')
    p.add('-H',  '--from-height',            dest='initHeight', metavar='HEIGHT', required=None, type=int, default=-1, help='Initial height to start scan payments. Default is actual height.')
    p.add(       '--no-check-wallet-rpc',    dest='walletNoCheck', metavar='BOOL', action='store_const', const='walletNoCheck', help='Do not check wallet collection at start.')
    p.add(       '--wallet-rpc-uri',         dest='walletUri', metavar='URI', default='http://127.0.0.1:13660/json_rpc', help='Wallet RPC URI')
    p.add(       '--wallet-username',        dest='walletUsername', metavar='USER', required=None, default='dispatcher', help='Wallet RPC username')
    p.add(       '--wallet-password',        dest='walletPassword', metavar='PW', required=None, help='Wallet RPC passwd')
    p.add(       '--provider-key',           dest='providerkey', metavar='PROVIDERKEY', required=True, help='ProviderID (private ed25519 key)')

    # Initialise config
    cfg = p.parse_args()
    config.CONFIG = config.Config("dummy")
    util.parseCommonArgs(p, cfg, 'lthnvpnd')
    config.Config.CAP = cfg
    
    config.Config.T_SAVE = cfg.st
    config.Config.T_CLEANUP = cfg.ct
    config.Config.AUTHIDSFILE = cfg.A

    if (cfg.S):
        services.SERVICES.loadServer()
        # Generate config files for Openvpn and Haproxy only and exit
        services.SERVICES.createConfigs()
        sys.exit()
        
    log.A.audit(log.A.START, log.A.SERVICE, "lthnvpnd")
    pid = os.getpid()
    if os.path.exists(config.CONFIG.PIDFILE):
        log.L.error("PID file %s exists! Is another dispatcher running?" % (config.CONFIG.PIDFILE))
        sys.exit(2)
    else:
        pf = open(config.CONFIG.PIDFILE,"w")
        pf.write("%s" % (pid))
        pf.close()
        atexit.register(remove_pidfile)
    
    services.SERVICES.loadServer()
        
    # Initialise sessions
    sessions.SESSIONS = sessions.Sessions()
    # Show services from SDP
    services.SERVICES.show()
    # Run all services
    services.SERVICES.run()
    
    # Preinitialise authids
    authids.AUTHIDS = authids.AuthIds()
    
    # Load authids from file
    if (cfg.A != "none"):
        tmpauthids=authids.AUTHIDS.load()
        if (tmpauthids):
            if not hasattr(tmpauthids,'version') or tmpauthids.getVersion()<authids.AUTHIDS.getVersion():
                log.L.error("You have incompatible authids database. You need to remove authids file %s to continue." % (config.Config.AUTHIDSFILE))
                sys.exit(2)
        authids.AUTHIDS=tmpauthids
    
    if not authids.AUTHIDS.getFromWallet():
        log.L.error("No connection to wallet!")
        if not cfg.walletNoCheck:
            log.L.warning("Exiting.")
            sys.exit(2)
        else:
            log.L.warning("Forcing continue without wallet connection. Will check connection later.")
        
    # Wait for all services to settle
    if (config.CONFIG.CAP.runServices):
        i = 1
        while i < 20:
            services.SERVICES.orchestrate()
            time.sleep(0.1)
            i = i + 1
    
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
        
def entry():
    main(sys.argv[1:])

if __name__ == "__main__":
    entry()
    
