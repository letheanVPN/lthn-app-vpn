
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
    # configargparse results
    CAP = None
    
    def __init__(self,action="read"):
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
        
        s = SDP()
        if (action=="init"):
            # generate SDP configuration file based on user input
            print('Initialising configuration file %s' % self.SDPFILE)
            s.addService(self.CAP)
            s.configFile=self.SDPFILE
            s.save()
        elif (action=="read"):
            s.load(self.SDPFILE)
        elif (action=="dummy"):
            if (os.path.exists(self.SDPFILE)):
                s.load(self.SDPFILE)
            else:
                logging.warning("Missing config file" + self.SDPFILE)
        elif (action=="edit"):
            # generate SDP configuration file based on user input
            print('Editing configuration file %s' % self.SDPFILE)
            s.editService(Config.CAP)
            print('YOUR CHANGES TO THE SDP CONFIG file ARE UNSAVED!')
            choice = input('Save the file? This will overwrite your existing config file! [y/N] ').strip().lower()[:1]
            if (choice == 'y'):
                s.save()
        elif (action=="add"):
            # Add service into SDP file based on user input
            print('Editing configuration file %s' % self.SDPFILE)
            s.addService(Config.CAP)
            print('YOUR CHANGES TO THE SDP CONFIG file ARE UNSAVED!')
            choice = input('Save the file? This will overwrite your existing config file! [y/N] ').strip().lower()[:1]
            if (choice == 'y'):
                s.save()
        elif (action =="upload"):
            s.load(self.SDPFILE)
            s.upload()
        else:
            logger.error("Bad option to Config!")
            sys.exit(2)
    
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

CONFIG = Config("dummy")
