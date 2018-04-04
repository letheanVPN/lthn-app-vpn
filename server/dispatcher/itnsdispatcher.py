#!/usr/bin/python

import sys
import os
# Add lib directory to search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))

import ed25519
import getopt
import logging
import atexit
import pprint
import time
import pickle
import binascii
from util import *
from sdp import *
from services import *
from authids import *
from sessions import *
from config import *

def initConf(configfile):
    config = Config()
    config.load(configfile)
    return(config)

def initAuthids(authidsfile):
    if (os.path.isfile(authidsfile)):
        try:
            logging.info("Trying to load authids db from %s" % (authidsfile))
            authids=pickle.load( open( authidsfile, "rb" ) )
        except (OSError, IOError) as e:
            logging.warning("Error reading or creating authids db %s" % (authidsfile))
            sys.exit(2)
    else:
        authids = AuthIds()
        authids.save(authidsfile)
        sys.exit(1)
    return(authids)

def main(argv):
    loglevel = logging.WARNING
    configfile = Config.PREFIX + "/etc/dispatcher.json"
    sdpfile = Config.PREFIX + "/etc/sdp.json"
    authidsfile = Config.PREFIX + '/var/authids.db'
 
    try:
        opts, args = getopt.getopt(argv, "hf:s:d:G:", ["help", "config=", "sdp=","gen-ed25519=", "generate-configs"])
    except getopt.GetoptError:
        print('itnsvpnd.py -h')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('itnsvpnd.py [-l DEBUG|INFO|WARNING|ERROR] [-h] [-f dispatcher.json] [-s sdp.json] [--generate-providerid file] [--generate-configs]')
            sys.exit()
        elif opt in ("-f", "--config"):
            configfile = arg
        elif opt in ("-s", "--sdp"):
            sdpfile = arg
        elif opt in ("-d", "--debug"):
            loglevel = arg
        elif opt in ("-G", "gen-ed25519"):
            logging.basicConfig(level=loglevel)
            privatef = arg
            try:
                signing_key, verifying_key = ed25519.create_keypair()
                open(privatef + ".private", "wb").write(signing_key.to_ascii(encoding="hex"))
                open(privatef + ".public", "wb").write(verifying_key.to_ascii(encoding="hex"))
                open(privatef + ".seed", "wb").write(binascii.hexlify(signing_key.to_seed()))
            except (IOError, OSError):
                logging.error("Cannot open/write %s" % (privatef))
            sys.exit()
        elif opt in ("--generate-configs"):
            initConf(configfile)
            config=logging.basicConfig(level=loglevel)
            services = Services(sdpfile)
            authids=initAuthids(authidsfile)
            services.createConfigs()
            sys.exit()

    logging.basicConfig(level=loglevel)
    config=logging.basicConfig(level=loglevel)
    services = Services(sdpfile)
    authids=initAuthids(authidsfile)
    services.show()
    services.run()
    
    while (1):
        start = time.time()
        services.orchestrate()
        authids.getFromWallet(services)
        #authids.show()
        time.sleep(1)
        #authids.show()
        authids.save(authidsfile)
        #authids.show()
        services.orchestrate()
        end = time.time()
        
if __name__ == "__main__":
    main(sys.argv[1:])