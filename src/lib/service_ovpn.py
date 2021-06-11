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
import atexit
import services
import time
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceOvpn(Service):
    
    def isClient(self):
        return(self.__class__.__name__=="ServiceOvpnClient")
    
    def run(self):
        self.createConfig()
        if config.Config.CAP.d== 'INFO':
            verb="2"
        elif config.Config.CAP.d== 'DEBUG':
            verb="3"
        else:
            verb="1"
        if config.Config.SUDO_BIN:
            cmd = [config.Config.SUDO_BIN, config.Config.CAP.openvpnBin, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb, "--writepid", self.pidfile]
        else:
            cmd = [config.Config.CAP.openvpnBin, "--config", self.cfgfile, "--writepid", self.pidfile, "--verb", verb, "--writepid", self.pidfile]
        os.chdir(self.dir)
        if (os.path.isfile(self.pidfile)):
            os.remove(self.pidfile)
        log.A.audit(log.A.START, log.A.SERVICE, cmd=" ".join(cmd), serviceid=self.id)
        if self.isClient():
            if (config.Config.CAP.vpncStandalone):
                command = cmd[0]
                if config.Config.CAP.noRun:
                    log.L.warning("Exiting from dispatcher. Run manually:\n%s" % (" ".join(cmd)))
                    atexit.unregister(services.SERVICES.stop)
                    sys.exit()
                else:
                    if not os.path.isfile(config.Config.CAP.openvpnBin):
                        log.L.error("Openvpn binary %s not found. Cannot continue!" % (config.Config.CAP.openvpnBin))
                        sys.exit(1)
                    log.L.warning("Running %s and exiting from dispatcher." % (" ".join(cmd)))
                    os.execv(command, cmd)
        if not os.path.isfile(config.Config.CAP.openvpnBin):
            log.L.error("Openvpn binary %s not found. Cannot continue!" % (config.Config.CAP.openvpnBin))
            sys.exit(1)
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX)
        self.pid = self.waitForPid()
        log.L.info("Run service %s: %s [pid=%s]" % (self.id, " ".join(cmd), self.pid))
        if not config.CONFIG.isWindows():
            self.stdout = select.poll()
            self.stderr = select.poll()
            self.stdout.register(self.process.stdout, select.POLLIN)
            self.stderr.register(self.process.stderr, select.POLLIN)
        else:
            self.stdout=None
            self.stderr=None
        self.mgmtConnect("127.0.0.1", self.cfg["mgmtport"])
        log.L.warning("Started service %s[%s]" % (self.name, self.id))
        self.starttime=time.time()
        
    def mgmtConnect(self, ip=None, port=None):
        return(super().mgmtConnect("127.0.0.1", self.cfg["mgmtport"]))
        
    def mgmtEvent(self, msg):
        p = re.search("^>CLIENT:(CONNECT|REAUTH),(\d*),(\d*)", msg)
        if (p):
            cid = p.group(2)
            kid = p.group(3)
            self.mgmtAuthClient(cid, kid)
        p = re.search("^>PASSWORD:Need 'Auth' username/password", msg)
        if (p):
            self.mgmtWrite("username 'Auth' '%s'\r\n" % (self.cfg["paymentid"]))
            l = self.mgmtRead()
            while (l is not None):
                l = self.mgmtRead()
            self.mgmtWrite("password 'Auth' '%s'\r\n" % (self.cfg["paymentid"]))
            l = self.mgmtRead()
            while (l is not None):
                l = self.mgmtRead()
        p = re.search("^>STATE:(\d*),RECONNECTING,auth-failure,,", msg)
        if (p and self.isClient()):
            if self.initphase==1:
                log.A.audit(log.A.NPAYMENT, log.A.PWALLET, wallet=self.sdp["provider"]["wallet"], paymentid=self.cfg["paymentid"], anon="no")
                self.initphase += 1
            elif time.time()-self.starttime>float(config.Config.CAP.paymentTimeout):
                log.L.error("Timeout waiting for payment!")
                sys.exit(2)
        p = re.search("^>STATE:(\d*),EXITING,tls-error,,", msg)
        if (p and self.isClient()):
            log.L.error("TLS Error! Bad configuration or old SDP? Exiting.")
            sys.exit(2)
        p = re.search("^>STATE:(\d*),CONNECTED,SUCCESS", msg)    
        if (p and self.isClient()):
            log.L.warning("Connected!")
        p = re.search("^>LOG:(\d*),W,ERROR:(.*)", msg)
        if (p and self.isClient()):
            log.L.error("Error seting up VPN! (%s). Exiting." % p.group(2).strip())
            sys.exit(2)
        return True
            
    def unHold(self):
        self.mgmtWrite("hold off\r\n")
        l = self.mgmtRead()
        self.mgmtWrite("hold release\r\n")
        while (l is not None):
            l = self.mgmtRead()
        self.mgmtWrite("log on\r\n")
        while (l is not None):
            l = self.mgmtRead()
        self.mgmtWrite("state on\r\n")
        while (l is not None):
            l = self.mgmtRead()
                    
    def stop(self):
        if config.Config.CAP.noRun:
            return()
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
        if (self.initphase==0):
            self.unHold()
            self.initphase = 1
        l = self.getLine()
        while (l is not None):
            log.L.debug("%s[%s]-stderr: %s" % (self.type, self.id, l))
            l = self.getLine()
        
        return(self.isAlive())
    
