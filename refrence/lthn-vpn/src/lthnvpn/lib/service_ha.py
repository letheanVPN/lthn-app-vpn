import os
import sys
import time
import select
import signal
import re
import shutil
import random
import subprocess
import atexit
from lthnvpn.lib.service import Service
from lthnvpn.lib import config, log, services

ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceHa(Service):
    """
    HAproxy service class
    """
    
    def isClient(self):
        return(self.__class__.__name__=="ServiceHaClient")
        
    def run(self):
        self.createConfig()
        cmd = [config.Config.CAP.haproxyBin, "-Ds", "-p", self.pidfile, "-f", self.cfgfile]
        if (os.path.isfile(self.pidfile)):
            os.remove(self.pidfile)
        os.chdir(self.dir)
        log.A.audit(log.A.START, log.A.SERVICE, cmd=" ".join(cmd), serviceid=self.id)
        if self.isClient():
            if (config.Config.CAP.proxycStandalone):
                command = cmd[0]
                if config.Config.CAP.noRun:
                    log.L.warning("Exiting from dispatcher. Run manually:\n%s" % (" ".join(cmd)))
                    atexit.unregister(services.SERVICES.stop)
                    sys.exit()
                else:
                    if not os.path.isfile(config.Config.CAP.haproxyBin):
                        log.L.error("Haproxy binary %s not found. Cannot continue!" % (config.Config.CAP.haproxyBin))
                        sys.exit(1)
                    log.L.warning("Running %s and exiting from dispatcher." % (" ".join(cmd)))
                    os.execv(command, cmd)
        if not os.path.isfile(config.Config.CAP.haproxyBin):
            log.L.error("Haproxy binary %s not found. Cannot continue!" % (config.Config.CAP.haproxyBin))
            sys.exit(1)
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=None)
        self.pid = self.waitForPid()
        log.L.info("Service %s: [pid=%s]" % (self.id, self.pid))
        if self.isClient():
            self.mgmtConnect("127.0.0.1", self.cfg["mgmtport"])
        else:
            self.mgmtConnect("socket", self.mgmtfile)
        super().run()
        
    def stop(self):
        if self.pid is not None:
            log.L.info("Kill service PID %s: [pid=%s]" % (self.id, self.pid))
            os.kill(self.pid, signal.SIGTERM)
        super().stop()
            
    def isAlive(self):
        try:
            if self.pid:
                os.kill(self.pid, 0)
        except OSError:
            return False
        else:
            return True
        
    def mgmtWaitPrompt(self):
        sent = None
        i = 1
        while not sent and i<10:
            l = self.mgmtRead()
            i = i + 1
            if l:
                sent = re.search("^> ", l)
        return(i<10)
        
    def mgmtWrite(self, msg, inside=None):
        log.L.debug("%s[%s]-mgmt-out: %s" % (self.type, self.id, repr(msg)))
        try:
            self.mgmt.send(b"prompt\n")
            self.mgmt.send(msg.encode())
        except:
            pass
        self.mgmtWaitPrompt()
        
    def orchestrate(self):
        self.mgmtConnect()
        l = self.getLine()
        while (l is not None):
            log.L.debug("%s[%s]-stderr: %s" % (self.type, self.id, l))
            l = self.getLine()
        l = self.mgmtRead()
        while (l is not None):
            l = self.mgmtRead()
        self.mgmtClose()
        return(self.isAlive())
