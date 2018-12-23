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
        cmd = [ config.Config.HAPROXY_BIN, "-Ds", "-p", self.pidfile, "-f", self.cfgfile ]
        if (os.path.isfile(self.pidfile)):
            os.remove(self.pidfile)
        os.chdir(self.dir)
        log.L.info("Run service %s (%s)" % (self.id, cmd))
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=None, preexec_fn=os.setsid)
        log.L.info("Waiting for pid")
        i=0
        while not os.path.isfile(self.pidfile) and i<20:
            time.sleep(0.1)
            i = i+1
        if (i==20):
            log.L.error("Error runing service %s: %s" % (self.id, " ".join(cmd)))
            sys.exit(1)
        self.pid = int(open(self.pidfile).read())
        log.L.info("Service %s: [pid=%s]" % (self.id, self.pid))
        self.mgmtConnect("socket", self.mgmtfile)
        super().run()
        
    def stop(self):
        log.L.info("Kill service PID %s: [pid=%s]" % (self.id, self.pid))
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
