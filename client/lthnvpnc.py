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
    
