
import json
import logging
import os
import sys
from sdp import SDP

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
        
        if (sys.argv[1] and sys.argv[1] == 'sdp'):
            # generate SDP configuration file based on user input
            print('Using SDP configuration file %s' % self.SDPFILE)

            s = SDP()
            s.load(self.SDPFILE, self.PREFIX)
            choice = input('Would you like to [g]enerate a new service or [e]dit an existing one? ').strip().lower()[:1]

            if (choice == 'g'):
                s.addService()
            elif (choice == 'e'):
                s.editService()
            else:
                print('Unknown response.')

            print('YOUR CHANGES TO THE SDP CONFIG file ARE UNSAVED!')
            choice = input('Save the file? This will overwrite your existing config file! [y/N] ').strip().lower()[:1]
            if (choice == 'y'):
                s.save()
    
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
