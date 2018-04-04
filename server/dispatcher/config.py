
import json
import os
import sys
import logging

class Config(object):
    """Configuration container"""
    
    PREFIX="/opt/itns"
    OPENVPN_BIN="/usr/sbin/openvpn"
    HAPROXY_BIN="/usr/sbin/haproxy"
    
    def __init__(self):
        if (os.getenv('ITNS_PREFIX')):
            self.PREFIX=os.getenv('ITNS_PREFIX')
    
    def load(self, filename):
        try:
            self.data = json.load(open(filename))
        except IOError:
            logging.error("Cannot read %s" % (filename))
            sys.exit(1)
            
    def get(self, key):
        idx = ""
        for k in key.split("."):
            idx += "['" + k + "']"
        try: 
            exec("ret=self.data%s" % (idx))
        except KeyError:
            return(None)
        else:
            return(ret)
