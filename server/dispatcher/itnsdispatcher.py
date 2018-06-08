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

# Starting here
def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hf:s:d:G:", ["help", "config=", "sdp=", "generate-providerid=", "generate-configs", "generate-client-config="])
    except getopt.GetoptError:
        print('itnsvpnd.py -h')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('itnsvpnd.py [-d DEBUG|INFO|WARNING|ERROR] [-h] [-f dispatcher.json] [-s sdp.json] [--generate-providerid file] [--generate-configs] [--generate-client-config id]')
            sys.exit()
        elif opt in ("-f", "--config"):
            Config.CONFIGFILE = arg
        elif opt in ("-s", "--sdp"):
            Config.SDPFILE = arg
        elif opt in ("-d", "--debug"):
            Config.LOGLEVEL = arg
        elif opt in ("-G", "--generate-providerid"):
            # Generate providerid to file.private, file.public, file.seed
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
            # Generate config files for Openvpn and Haproxy only and exit
            logging.basicConfig(level=Config.LOGLEVEL)
            CONFIG = Config()
            AUTHIDS = AuthIds()
            tmpauthids=AUTHIDS.load()
            if (tmpauthids):
                AUTHIDS=tmpauthids
            SERVICES = Services()
            SERVICES.createConfigs()
            sys.exit()
        elif opt in ("--generate-client-config"):
            # Generate client config for service id and put to stdout
            id = arg
            logging.basicConfig(level=loglevel)
            CONFIG = Config()
            SERVICES = Services()
            SERVICES.get(id).createClientConfig()
            sys.exit()

    logging.basicConfig(level=Config.LOGLEVEL)
    # Initialise config and globals 
    CONFIG = Config()
    # Initialise services
    SERVICES = Services()
    # Create empty authids
    AUTHIDS = AuthIds()
    # Try to load authids or leave empty
    tmpauthids=AUTHIDS.load()
    if (tmpauthids):
        AUTHIDS=tmpauthids
    AUTHIDS.getFromWallet(SERVICES)
    # Create empty sessions
    SESSIONS = Sessions()
    # Show services from SDP
    SERVICES.show()
    # Run all services
    SERVICES.run()
    
    while (1):
        start = time.time()
        SERVICES.orchestrate()
        #AUTHIDS.getFromWallet(SERVICES)
        AUTHIDS.show()
        time.sleep(0.1)
        #print(".")
        #authids.show()
        #authids.save(authidsfile)
        #authids.show()
        SERVICES.orchestrate()
        end = time.time()
        AUTHIDS.save()
        
if __name__ == "__main__":
    main(sys.argv[1:])