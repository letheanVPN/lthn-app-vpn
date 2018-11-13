from service import Service
import config
import os
import sys
import time
import log
import select
import signal
import re
import shutil
import random
import subprocess
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceHa(Service):
    """
    HAproxy service class
    """
        
    def run(self):
        self.createConfig()
        cmd = "stdbuf -oL " + config.Config.HAPROXY_BIN + " -Ds" + " -p " + self.pidfile + " -f " + self.cfgfile
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=True)
        time.sleep(0.3)
        if (os.path.exists(self.pidfile)):
            with open (self.pidfile, "r") as p:
                self.pid = int(p.readline().strip())
        else:
            self.pid = self.process.pid
        log.L.info("Run service %s: %s [pid=%s]" % (self.id, cmd, self.pid))
        self.mgmtConnect("socket", self.mgmtfile)
        super().run()
        
    def stop(self):
        os.kill(self.pid, signal.SIGTERM)
        super().stop()
            
    def isAlive(self):
        try:
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
