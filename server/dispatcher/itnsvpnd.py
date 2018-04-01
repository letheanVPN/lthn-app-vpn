#!/usr/bin/env python

import ed25519
import getopt
import logging
import os
import pprint
import sys
import time
import pickle
import binascii
from util import *
from sdp import *
from services import *
from authids import *
from sessions import *
from config import *

def main(argv):
    loglevel = logging.WARNING
    configfile = Config.PREFIX + "/etc/dispatcher.json"
    sdpfile = Config.PREFIX + "/etc/sdp.json"
    authidsfile = Config.PREFIX + '/var/authids.db'
 
    try:
        opts, args = getopt.getopt(argv, "hf:s:d:G:", ["help", "config=", "sdp=","gen-ed25519="])
    except getopt.GetoptError:
        print('itnsvpnd.py -h')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('itnsvpnd.py [-l DEBUG|INFO|WARNING|ERROR] [-h] [-f dispatcher.json] [-s sdp.json] [--generate-providerid file]')
            sys.exit()
        elif opt in ("-f", "--config"):
            configfile = arg
        elif opt in ("-s", "--sdp"):
            sdpfile = arg
        elif opt in ("-d", "--debug"):
            loglevel = arg
        elif opt in ("-G", "gen-ed25519"):
            privatef = arg
            try:
                signing_key, verifying_key = ed25519.create_keypair()
                open(privatef + ".private", "wb").write(signing_key.to_ascii(encoding="hex"))
                open(privatef + ".public", "wb").write(verifying_key.to_ascii(encoding="hex"))
                open(privatef + ".seed", "wb").write(binascii.hexlify(signing_key.to_seed()))
            except (IOError, OSError):
                logging.error("Cannot open/write %s" % (privatef))
            sys.exit()
    
    logging.basicConfig(level=loglevel)
    config = Config()
    config.load(configfile)
    
    services = Services(sdpfile)
    try:
        logging.warning("Reading authids db from %s" % (authidsfile))
        authids=pickle.load( open( authidsfile, "rb" ) )
    except (OSError, IOError) as e:
        logging.warning("Creating empty authids db %s" % (authidsfile))
        authids = AuthIds()
        authids.save(authidsfile)
    else:
        authids = AuthIds()

    services.show()
    services.runAll()
    sessions = Sessions(authids)
    
    while (1):
        start = time.time()
        services.checkAll()
        authids.getFromWallet(services)
        #authids.show()
        time.sleep(10)
        authids.show()
        authids.save(authidsfile)
        authids.show()
        services.checkAll()
        end = time.time()
        
if __name__ == "__main__":
    main(sys.argv[1:])