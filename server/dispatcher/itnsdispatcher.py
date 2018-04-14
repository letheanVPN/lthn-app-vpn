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
from sessions import *
from config import Config

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hf:s:d:G:", ["help", "config=", "sdp=", "gen-ed25519=", "generate-configs", "generate-client-config="])
    except getopt.GetoptError:
        print('itnsvpnd.py -h')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('itnsvpnd.py [-l DEBUG|INFO|WARNING|ERROR] [-h] [-f dispatcher.json] [-s sdp.json] [--generate-providerid file] [--generate-configs] [--generate-client-config id]')
            sys.exit()
        elif opt in ("-f", "--config"):
            Config.CONFIGFILE = arg
        elif opt in ("-s", "--sdp"):
            Config.SDPFILE = arg
        elif opt in ("-d", "--debug"):
            Config.LOGLEVEL = arg
        elif opt in ("-G", "gen-ed25519"):
            logging.basicConfig(level=Config.LOGLEVEL)
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
            initConf()
            l = logging.basicConfig(level=Config.LOGLEVEL)
            authids.load(authidsfile)
            services.createConfigs()
            sys.exit()
        elif opt in ("--generate-client-config"):
            id = arg
            initConf(configfile)
            l = logging.basicConfig(level=loglevel)
            SERVICES.get(id).createClientConfig()
            sys.exit()

    logging.basicConfig(level=Config.LOGLEVEL)
    CONFIG=Config()
    SERVICES=Services()
    AUTHIDS=AuthIds()
    pprint(AUTHIDS)
    sys.exit()
    SERVICES.show()
    SERVICES.run()
    
    while (1):
        start = time.time()
        #services.orchestrate()
        #authids.getFromWallet(services)
        #authids.show()
        time.sleep(0.1)
        #print(".")
        #authids.show()
        #authids.save(authidsfile)
        #authids.show()
        SERVICES.orchestrate()
        end = time.time()
        
if __name__ == "__main__":
    main(sys.argv[1:])