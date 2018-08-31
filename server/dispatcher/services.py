
import atexit
import config
import log
from sdp import *
import sys
from service_mgmt import ServiceMgmt
from service_ha import ServiceHa
from service_syslog import ServiceSyslog
from service_ovpn import ServiceOvpn
from service_http import ServiceHttp

SERVICES = None

class Services(object):
    
    def load(self):
        
        self.services = {}
        sdp = SDP()
        sdp.load(config.Config.SDPFILE)
        for id_ in sdp.listServices():
            s = sdp.getService(id_)
            if (s["type"]):
                if (s["type"] == "vpn"):
                    so = ServiceOvpn(id_, s)
                elif (s["type"] == "proxy"):
                    so = ServiceHa(id_, s)
                else:
                    log.L.error("Unknown service type %s in SDP!" % (s["type"]))
                    sys.exit(1)
            self.services[id_.upper()] = so
        self.syslog = ServiceSyslog(config.Config.PREFIX + "/var/run/log")
        self.mgmt = ServiceMgmt(config.Config.PREFIX + "/var/run/mgmt")
        self.http = ServiceHttp()
 
    def run(self):
        for id in self.services:
            s = self.services[id]
            s.run()
        self.http.run()
        atexit.register(self.stop)
    
    def createConfigs(self):
        for id in self.services:
            s = self.services[id]
            s.createConfig()
            
    def orchestrate(self):
        self.syslog.orchestrate()
        self.mgmt.orchestrate()
        self.http.orchestrate()
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
        self.mgmt.stop()
            
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


