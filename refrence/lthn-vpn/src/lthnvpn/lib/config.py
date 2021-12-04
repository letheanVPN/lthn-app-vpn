import configparser
import json
import logging
import os
import sys
import pathlib
import platform
import glob
import shutil
from os.path import expanduser
from lthnvpn.lib.sdp import SDP
from lthnvpn.lib import log

class Config(object):
    """Configuration container"""
    
    PREFIX = "/opt/lthn"
    OPENVPN_BIN = None
    HAPROXY_BIN = None
    SUDO_BIN = None
    LOGLEVEL = logging.WARNING
    AUDITLOG = None
    VERBOSE = None
    CONFIGFILE = None
    SDPFILE = None
    AUTHIDSFILE = None
    MAINSLEEP = 0.1
    T_SAVE = 10 # How often to save authids (sec)
    T_CLEANUP = 30 # How often to cleanup stale authids
    FORCE_REFRESH = None
    FORCE_SAVE = None
    
    # configargparse results
    CAP = None
    
    def isWindows(self):
        if (platform.system()=="Windows"):
            return True
        else:
            return None
        
    def isClient(self):
        if "lthnvpnc" in sys.argv[0]:
            return True
        else:
            return None
    
    def __init__(self, action="read", services=None):
        if self.isWindows():
            homeDir = ''
            if (os.getenv('USERPROFILE')):
                homeDir = os.getenv('USERPROFILE')
            elif (os.getenv('HOMEDRIVE') and os.getenv('HOMEPATH')):
                homeDir = os.getenv('HOMEDRIVE') + os.getenv('HOMEPATH')

            prefix = str(pathlib.Path(homeDir + '/lthn'))
            type(self).PREFIX = prefix
            if getattr(sys, 'frozen', False):
                binprefix = str(pathlib.Path(sys._MEIPASS + "/bin"))
                cfgprefix = str(pathlib.Path(sys._MEIPASS + "/conf"))
            else:
                binprefix = "."
                cfgprefix = "conf"
            type(self).OPENVPN_BIN = str(pathlib.Path(binprefix + "/openvpn.exe"))
            type(self).HAPROXY_BIN = str(pathlib.Path(binprefix + "/haproxy.exe"))
            type(self).SUDO_BIN = None
            type(self).STUNNEL_BIN = str(pathlib.Path(binprefix + "/tstunnel.exe"))
            type(self).LOGLEVEL = logging.WARNING
            type(self).SDPFILE = None
            type(self).PIDFILE = None
            type(self).AUTHIDSFILE = None
            if not os.path.exists(prefix):
                os.mkdir(prefix)
            if not os.path.exists(prefix + "/etc"):    
                os.mkdir(prefix + "/etc")
            if not os.path.exists(prefix + "/var"): 
                os.mkdir(prefix + "/var")
            if not os.path.exists(prefix + "/var/log"): 
                os.mkdir(prefix + "/var/log")
            if not os.path.exists(prefix + "/var/run"): 
                os.mkdir(prefix + "/var/run")
            for file in glob.glob(cfgprefix + '/*.http'):
                shutil.copy(file, prefix + '/etc/')
            for file in glob.glob(cfgprefix + '/*.tmpl'):
                shutil.copy(file, prefix + '/etc/')
            if not os.path.exists(prefix + "/etc/dispatcher.ini"):
                shutil.copy(cfgprefix + '/dispatcher.ini.tmpl', prefix + '/etc/dispatcher.ini')

        else:
            type(self).OPENVPN_BIN = "/usr/sbin/openvpn"
            type(self).HAPROXY_BIN = "/usr/sbin/haproxy"
            type(self).SUDO_BIN = "/usr/bin/sudo"
            type(self).STUNNEL_BIN = "/usr/bin/stunnel"
            type(self).LOGLEVEL = logging.WARNING

        if (os.getenv('LTHN_PREFIX')):
            type(self).PREFIX = os.getenv('LTHN_PREFIX')
        type(self).CONFIGFILE = type(self).PREFIX + "/etc/dispatcher.ini"
        type(self).SDPFILE = type(self).PREFIX + "/etc/sdp.json"
        type(self).PIDFILE = type(self).PREFIX + "/var/run/lthnvpnd.pid"
        type(self).AUTHIDSFILE = type(self).PREFIX + '/var/authids.db'

        s = SDP()
        self.load(self.CONFIGFILE)
        if (action == "init"):
            # generate SDP configuration file based on user input
            print('Initialising SDP file %s' % self.SDPFILE)
            s.addService(self.CAP)
            s.configFile = self.SDPFILE
            s.save(self.SDPFILE)
        elif (action == "read"):
            self.load(self.CONFIGFILE)
            s.load(self.SDPFILE)
        elif (action == "dummy"):
            if (os.path.exists(self.SDPFILE)):
                s.load(self.SDPFILE)
            else:
                if not self.isClient():
                    logging.error("Missing SDP file" + self.SDPFILE)
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
            if os.path.exists(filename):
                logging.debug("Reading config file %s" % (filename))
                cfg = configparser.ConfigParser()
                cfg.read(filename)
                self.cfg = cfg
            else:
                cfg = configparser.ConfigParser()
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

CONFIG = None
