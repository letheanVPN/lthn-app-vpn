from service import Service
import config
import os
import sys
import re
import log
import time
import select
from subprocess import Popen
from subprocess import PIPE
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceOvpn(Service):
    
    def run(self):
        self.createConfig()
        verb = "3"
        if (config.Config.OPENVPN_SUDO):
            cmd = ["/usr/bin/sudo", config.Config.OPENVPN_BIN, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb]
        else:
            cmd = [config.Config.SUDO_BIN, Config.OPENVPN_BIN, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb]
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        time.sleep(0.3)
        if (os.path.exists(self.pidfile)):
            with open (self.pidfile, "r") as p:
                self.pid = int(p.readline().strip())
        else:
            self.pid = self.process.pid
        log.L.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.pid))
        self.stdout = select.poll()
        self.stderr = select.poll()
        self.stdout.register(self.process.stdout, select.POLLIN)
        self.stderr.register(self.process.stderr, select.POLLIN)
        self.mgmtConnect("127.0.0.1", "11112")
        log.L.warning("Started service %s[%s]" % (self.name, self.id))
        
    def mgmtEvent(self, msg):
        p = re.search("^>CLIENT:CONNECT,(\d*),(\d*)", msg)
        if (p):
            cid = p.group(1)
            kid = p.group(2)
            self.mgmtAuthClient(cid, kid)
        
    def unHold(self):
        self.mgmtWrite("hold release\r\n")
        l = self.mgmtRead()
        while (l is not None):
            l = self.mgmtRead()
            
    def stop(self):
        self.mgmtWrite("signal SIGTERM\r\n")
        l = self.mgmtRead()
        while (l is not None):
            l = self.mgmtRead()
        log.L.warning("Stopped service %s[%s]" % (self.name, self.id))
        return()
    
    def orchestrate(self):
        l = self.mgmtRead()
        while (l is not None):
            l = self.mgmtRead()
        if (self.initphase):
            self.unHold()
            self.initphase = None
        l = self.getLine()
        while (l is not None):
            log.L.debug("%s[%s]-stderr: %s" % (self.type, self.id, l))
            l = self.getLine()
        
        return(self.isAlive())
    
