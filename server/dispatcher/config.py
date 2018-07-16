
import configparser
import json
import logging
import os
from sdp import SDP
import sys

class Config(object):
    """Configuration container"""
    
    PREFIX = "/opt/itns"
    OPENVPN_BIN = None
    HAPROXY_BIN = None
    SUDO_BIN = None
    OPENVPN_SUDO = None
    LOGLEVEL = logging.WARNING
    VERBOSE = None
    CONFIGFILE = None
    SDPFILE = None
    AUTHIDSFILE = None
    # configargparse results
    CAP = None
    
    def __init__(self, action="read", services=None):
        if (os.getenv('ITNS_PREFIX')):
            type(self).PREFIX = os.getenv('ITNS_PREFIX')
        
        type(self).OPENVPN_BIN = "/usr/sbin/openvpn"
        type(self).HAPROXY_BIN = "/usr/sbin/haproxy"
        type(self).SUDO_BIN = "/usr/bin/sudo"
        type(self).OPENVPN_SUDO = True
        type(self).LOGLEVEL = logging.WARNING
        type(self).CONFIGFILE = type(self).PREFIX + "/etc/dispatcher.ini"
        type(self).SDPFILE = type(self).PREFIX + "/etc/sdp.json"
        type(self).AUTHIDSFILE = type(self).PREFIX + '/var/authids.db'
        
        s = SDP()
        self.load(self.CONFIGFILE)
        if (action == "init"):
            # generate SDP configuration file based on user input
            print('Initialising SDP file %s' % self.SDPFILE)
            s.addService(self.CAP)
            s.configFile = self.SDPFILE
            s.save()
        elif (action == "read"):
            self.load(self.CONFIGFILE)
            s.load(self.SDPFILE)
        elif (action == "dummy"):
            if (os.path.exists(self.SDPFILE)):
                s.load(self.SDPFILE)
            else:
                logging.warning("Missing SDP file" + self.SDPFILE)
        elif (action == "edit"):
            # generate SDP configuration file based on user input
            print('Editing SDP file %s' % self.SDPFILE)
            s.editService(self.CAP)
            print('YOUR CHANGES TO THE SDP CONFIG file ARE UNSAVED!')
            choice = input('Save the file? This will overwrite your existing config file! [y/N] ').strip().lower()[:1]
            if (choice == 'y'):
                s.save()
        elif (action == "add"):
            # Add service into SDP file based on user input
            print('Editing configuration file %s' % self.SDPFILE)
            s.addService(self.CAP)
            print('YOUR CHANGES TO THE SDP CONFIG file ARE UNSAVED!')
            choice = input('Save the file? This will overwrite your existing config file! [y/N] ').strip().lower()[:1]
            if (choice == 'y'):
                s.save()
        elif (action == "upload"):
            s.load(self.SDPFILE)
            s.upload()
        else:
            logger.error("Bad option to Config!")
            sys.exit(2)
            
    def load(self, filename):
        try:
            logging.debug("Reading config file %s" % (filename))
            cfg = configparser.ConfigParser()
            cfg.read(filename)
            self.cfg = cfg
        except IOError:
            logging.error("Cannot read %s. Exiting." % (filename))
            sys.exit(1)
            
    def getService(self, id):
        section = "service-" + id
        for s in self.cfg.sections():
            if s.lower() == section.lower():
                return(self.cfg[s])
        return(None)

CONFIG = Config("dummy")
