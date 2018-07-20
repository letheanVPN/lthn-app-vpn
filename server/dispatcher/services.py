
import atexit
import config
import log
from sdp import *
import sys
from service_mgmt import ServiceMgmt
from service_ha import ServiceHa
from service_syslog import ServiceSyslog
from service_ovpn import ServiceOvpn

SERVICES = None

class Services(object):
    
    def load(self):
        
        self.services = {}
        sdp = SDP()
        sdp.load(config.Config.SDPFILE)
        for id in sdp.listServices():
            s = sdp.getService(id)
            if (s["type"]):
                if (s["type"] == "vpn"):
                    so = ServiceOvpn(id, s)
                elif (s["type"] == "proxy"):
                    so = ServiceHa(id, s)
                else:
                    log.L.error("Unknown service type %s in SDP!" % (s["type"]))
                    sys.exit(1)
            self.services[id.upper()] = so
        self.syslog = ServiceSyslog(config.Config.PREFIX + "/var/run/log")
        self.mgmt = ServiceMgmt(config.Config.PREFIX + "/var/run/mgmt")
 
    def run(self):
        for id in self.services:
            s = self.services[id]
            s.run()
        atexit.register(self.stop)
    
    def createConfigs(self):
        for id in self.services:
            s = self.services[id]
            s.createConfig()
            
    def orchestrate(self):
        self.syslog.orchestrate()
        self.mgmt.orchestrate()
        for id in self.services:
            if (not self.services[id].orchestrate()):
                log.L.error("Service %s died! Exiting!" % (self.services[id].id))
                self.stop()
                sys.exit(3)

    def stop(self):
        for id in self.services:
            s = self.services[id]
            if (s.isAlive()):
                s.stop()
        self.syslog.stop()
            
    def show(self):
        for id in self.services:
            s = self.services[id]
            s.show()
            
    def getAll(self):
        return(self.services.keys())
    
    def get(self, id):
        key = "%s" % (id)
        if key.upper() in self.services:
            return(self.services[key.upper()])
        else:
            return(None)


