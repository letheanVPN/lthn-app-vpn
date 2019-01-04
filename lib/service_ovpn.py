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
        cmd = [config.Config.SUDO_BIN, config.Config.OPENVPN_BIN, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb, "--writepid", self.pidfile]
        os.chdir(self.dir)
        if (os.path.isfile(self.pidfile)):
            os.remove(self.pidfile)
        log.A.audit(log.A.START, log.A.SERVICE, cmd=" ".join(cmd), serviceid=self.id)
        if (config.Config.CAP.vpncStandalone):
            command = cmd[0]
            os.execv(command, cmd)
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        log.L.info("Waiting for pid")
        i=0
        while not os.path.isfile(self.pidfile) and i<20:
            time.sleep(0.1)
            i = i+1
        if (i==20):
            log.L.error("Error runing service %s: %s" % (self.id, " ".join(cmd)))
            sys.exit(1)
        self.pid = int(open(self.pidfile).read())
        log.L.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.pid))
        self.stdout = select.poll()
        self.stderr = select.poll()
        self.stdout.register(self.process.stdout, select.POLLIN)
        self.stderr.register(self.process.stderr, select.POLLIN)
        self.mgmtConnect("127.0.0.1", self.cfg["mgmtport"])
        log.L.warning("Started service %s[%s]" % (self.name, self.id))
        
    def mgmtConnect(self, ip=None, port=None):
        return(super().mgmtConnect("127.0.0.1", self.cfg["mgmtport"]))
        
    def mgmtEvent(self, msg):
        p = re.search("^>CLIENT:CONNECT,(\d*),(\d*)", msg)
        if (p):
            cid = p.group(1)
            kid = p.group(2)
            self.mgmtAuthClient(cid, kid)
        p = re.search("^>PASSWORD:Need 'Auth' username/password", msg)
        if (p):
            self.mgmtWrite("username 'Auth' '%s'\r\n" % (self.cfg["paymentid"]))
            self.mgmtRead()
            self.mgmtWrite("password 'Auth' '%s'\r\n" % (self.cfg["paymentid"]))
            self.mgmtRead()
            
    def unHold(self):
        self.mgmtWrite("hold off\r\n")
        l = self.mgmtRead()
        self.mgmtWrite("hold release\r\n")
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
    
