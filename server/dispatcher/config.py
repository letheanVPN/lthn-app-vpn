
import json
import logging
import os
import sys

class Config(object):
    """Configuration container"""
    
    PREFIX = "/opt/itns"
    OPENVPN_BIN = None
    HAPROXY_BIN = None
    SUDO_BIN = None
    OPENVPN_SUDO = None
    LOGLEVEL = logging.WARNING
    CONFIGFILE = None
    SDPFILE = None
    AUTHIDSFILE = None
    
    def __init__(self):
        if (os.getenv('ITNS_PREFIX')):
            type(self).PREFIX = os.getenv('ITNS_PREFIX')
        
        type(self).OPENVPN_BIN = "/usr/sbin/openvpn"
        type(self).HAPROXY_BIN = "/usr/sbin/haproxy"
        type(self).SUDO_BIN = "/usr/bin/sudo"
        type(self).OPENVPN_SUDO = True
        type(self).LOGLEVEL = logging.WARNING
        type(self).CONFIGFILE = type(self).PREFIX + "/etc/dispatcher.json"
        type(self).SDPFILE = type(self).PREFIX + "/etc/sdp.json"
        type(self).AUTHIDSFILE = type(self).PREFIX + '/var/authids.db'
            
    
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

CONFIG = Config()
