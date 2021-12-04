import os
import sys
import time
import select
import signal
import re
import shutil
import random
import subprocess
from lthnvpn.lib.service import Service
from lthnvpn.lib.service_ha import ServiceHa
from lthnvpn.lib import config, log

ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceStunnel(Service):
    """
    Stunnel proxy service class
    This service passes TCP traffic over HTTP proxy
    """
    
    OPTS = dict(
        name='Stunnel', https_proxy_host = "", https_proxy_port = 3128,
        bind_addr = '127.0.0.1',
        port = None
    )
    OPTS_REQUIRED = (
         'outbound_proxy_host',
         'outbound_proxy_port',
         'port'
    )
    
    def run(self):
        self.createConfig()
        cmd = [config.Config.CAP.stunnelBin, self.cfgfile]
        if not os.path.isfile(config.Config.CAP.stunnelBin):
            log.L.error("Stunnel binary %s not found. Cannot continue!" % (config.Config.CAP.stunnelBin))
            sys.exit(1)
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, shell=False, universal_newlines=True)
        time.sleep(0.3)
        if (os.path.exists(self.pidfile)):
            time.sleep(0.3)
            with open (self.pidfile, "r") as p:
                self.pid = int(p.readline().strip())
        else:
            self.pid = self.process.pid
        log.L.info("Run service %s: %s [pid=%s]" % (self.id, cmd, self.pid))
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
        
    def createConfig(self):
        if (not os.path.exists(self.dir)):
            os.mkdir(self.dir)
        os.chdir(self.dir)
        if (os.path.exists(self.mgmtfile)):
            os.remove(self.mgmtfile)
        tfile = config.Config.PREFIX + "/etc/stunnel.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open stunnel template file %s" % (tfile))
        port=self.cfg['port']
        cafile = self.dir + "ca.crt"
        if (config.CONFIG.CAP.proxySSLNoVerify):
            verifyssl='no'
        else:
            verifyssl='yes'
        out = tmpl.decode("utf-8").format(
                          bind_addr=self.cfg['bind_addr'],
                          port=port,
                          pidfile=self.pidfile,
                          https_proxy_host=self.cfg["outbound_proxy_host"],
                          https_proxy_port=self.cfg["outbound_proxy_port"],
                          remote_host=self.cfg["remote_host"],
                          remote_port=self.cfg["remote_port"],
                          ca=cafile,
                          verifyssl=verifyssl
                          )
        try:
            cf = open(self.cfgfile, "wb")
            cf.write(out.encode())
        except (IOError, OSError):
            log.L.error("Cannot write stunnel config file %s" % (self.cfgfile))
        log.L.info("Created stunnel config file %s" % (self.cfgfile))

    def orchestrate(self):
        l = self.getLine()
        while (l is not None):
            log.L.debug("%s[%s]-stderr: %s" % (self.type, self.id, l))
            l = self.getLine()
        return(self.isAlive())
