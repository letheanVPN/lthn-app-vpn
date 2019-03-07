
import atexit
import config
import log
from sdp import *
import sys
import time
from service_mgmt import ServiceMgmt
from service_ha import ServiceHa
from service_hac import ServiceHaClient
from service_has import ServiceHaServer
from service_syslog import ServiceSyslog
from service_ovpn import ServiceOvpn
from service_ovpnc import ServiceOvpnClient
from service_ovpns import ServiceOvpnServer
from service_http import ServiceHttp
import pprint

SERVICES = None

class Services(object):
    
    sdp = None
    
    def loadServer(self):
        
        self.services = {}
        sdp = SDP()
        sdp.load(config.Config.SDPFILE)
        self.sdp = sdp
        for id_ in sdp.listServices():
            s = sdp.getService(id_)
            cfg = config.CONFIG.getService(id_)
            if "enabled" not in cfg:
                cfg["enabled"] = "true"
            if (cfg["enabled"]=="true"):
                if (s["type"]):
                    if (s["type"] == "vpn"):
                        so = ServiceOvpnServer(id_, s)
                    elif (s["type"] == "proxy"):
                        so = ServiceHaServer(id_, s)
                    else:
                        log.L.error("Unknown service type %s in SDP!" % (s["type"]))
                        sys.exit(1)
                self.services[id_.upper()] = so
            else:
                log.L.warning("Service %s disabled in config file." % (id_))
        self.syslog = ServiceSyslog("SS")
        self.mgmt = ServiceMgmt("MS")
        self.http = ServiceHttp("HS")
        
    def loadClient(self, sdp, sid):
        
        self.sdp = SDP()
        self.sdp.loadJson(sdp)
        self.services = {}
        s = self.sdp.getService(sid)
        if (s and s["type"]):
            if (s["type"] == "vpn"):
                so = ServiceOvpnClient(sdp["provider"]["id"] + "_" + sid, s)
            elif (s["type"] == "proxy"):
                so = ServiceHaClient(sdp["provider"]["id"] + "_" + sid, s)
            else:
                log.L.error("Unknown service type %s in SDP!" % (s["type"]))
                sys.exit(1)
            self.services[sid.upper()] = so
            self.syslog = ServiceSyslog("SS")
            self.mgmt = ServiceMgmt("MS")
            self.http = ServiceHttp("HS")
        else:
            log.L.error("Unknown service %s in SDP!" % (sid))
 
    def run(self):
        if self.syslog.isEnabled():
            self.syslog.run()
        if self.mgmt.isEnabled():
            self.mgmt.run()
        if self.http.isEnabled():
            self.http.run()
        if (config.CONFIG.CAP.runServices):
            for id in self.services:
                s = self.services[id]
                if s.isEnabled():
                    s.run()
                else:
                    log.L.warining("Service id %s disabled." % (id))
        atexit.register(self.stop)
    
    def createConfigs(self):
        for id in self.services:
            s = self.services[id]
            s.createConfig()
            
    def orchestrate(self, err=None):
        if self.syslog.isEnabled():
            self.syslog.orchestrate()
        if self.mgmt.isEnabled():
            self.mgmt.orchestrate()
        if self.http.isEnabled():
            self.http.orchestrate()
        for id in self.services:
            s = self.services[id]
            if (s.isEnabled()):
                o = s.orchestrate()
                if (not err and not o):
                    log.L.error("Service %s died! Exiting!" % (self.services[id].id))
                    # Wait for all other processes to settle
                    i = 1
                    while i<20:
                        self.orchestrate(True)
                        i = i + 1
                    self.stop()
                    sys.exit(3)

    def sleep(self, s):
        i = 0
        while (i < s):
            i = i + 0.1
            time.sleep(0.1)
            self.orchestrate()

    def stop(self):
        for id in self.services:
            s = self.services[id]
            if (s.isEnabled() and s.isAlive()):
                s.stop()
        if self.syslog.isEnabled():
            self.syslog.stop()
        if self.mgmt.isEnabled():
            self.mgmt.stop()
        if self.http.isEnabled():
            self.http.stop()
            
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


