from service import Service
import config
import os
import sys
import time
import log
import select
import signal
import re
from subprocess import Popen
from subprocess import PIPE
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceHa(Service):
    """
    HAproxy service class
    """
    
    OPTS = dict(
        name='Proxy', backend_proxy_server = 'localhost:3128',
        client_bind = 'localhost', client_port = 3128,
        crt = None, key =None, crtkey = None,
        max_connections = 2000, timeout = '10m', connect_timeout = '30s'
    )
    
    def run(self):
        self.createConfig()
        cmd = [config.Config.HAPROXY_BIN, "-Ds", "-p", self.pidfile, "-f", self.cfgfile]
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
        while not sent:
            l = self.mgmtRead()
            if l:
                sent = re.search("^> ", l)
        
    def mgmtWrite(self, msg, inside=None):
        log.L.debug("%s[%s]-mgmt-out: %s" % (self.type, self.id, repr(msg)))
        self.mgmt.send(b"prompt\n")
        self.mgmt.send(msg.encode())
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
    
    def addAuthId(self, authid):
        self.mgmtConnect()
        self.mgmtWrite("del acl #20 " + authid + "\n")
        self.mgmtWrite("add acl #20 " + authid + "\n")
        self.mgmtClose()
        
    def delAuthId(self, authid):
        self.mgmtConnect()
        self.mgmtWrite("del acl #20 " + authid + "\n")
        self.mgmtClose()
    
    def killSession(self, id, info=''):
        self.mgmtConnect()
        self.mgmtWrite("shutdown session " + id + "\n")
        log.A.audit(log.A.SESSION, log.A.KILL, id, info)
        self.mgmtClose()
        
    def getSessions(self):
        self.mgmtConnect()
        self.mgmtWrite("show sess\n")
        l=self.mgmtRead()
        sessions = {}
        while (l):
            if (re.search("proto=tcp", l)):
                p = re.search("^.{0,2}(.*):.*proto=(.*) src=(\d*\.\d*\.\d*\.\d*):(\d*)", l)
                if (p):
                    sessid = p.group(1)
                    proto = p.group(2)
                    ip = p.group(3)
                    port = p.group(4)
                    sessions[sessid] = { 'ip': ip, 'port': port, 'id': sessid }
                    sessions[ip + ':' + port] = sessid
                else:
                    log.L.debug("Unknown haproxy session " + l)
            l=self.mgmtRead()
        self.mgmtClose()
        return(sessions)
        
    def createConfig(self):
        if (not os.path.exists(self.dir)):
            os.mkdir(self.dir)
        self.cfgfile = self.dir + "/cfg"
        self.pidfile = self.dir + "/pid"
        self.mgmtfile = self.dir + "/mgmt"
        if (os.path.exists(self.mgmtfile)):
            os.remove(self.mgmtfile)
        tfile = config.Config.PREFIX + "/etc/haproxy_server.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open haproxy template file %s" % (tfile))
            
        port=self.json['proxy'][0]['port'].split('/')[0]
        out = tmpl.decode("utf-8").format(
                          port=port,
                          maxconn=self.cfg['max_connections'],
                          timeout=self.cfg['timeout'],
                          ctimeout=self.cfg['connect_timeout'],
                          f_logsocket=config.Config.PREFIX + '/var/run/log local0',
                          f_sock=self.mgmtfile,
                          forward_proxy=self.cfg['backend_proxy_server'],
                          header='X-ITNS-PaymentID',
                          ctrluri='http://_ITNSVPN_',
                          f_dh=config.Config.PREFIX + '/etc/dhparam.pem',
                          cabase=config.Config.PREFIX + '/etc/ca/certs',
                          crtbase=config.Config.PREFIX + '/etc/ca/certs',
                          ctrldomain='_ITNSVPN_',
                          f_site_pem=self.cfg['crtkey'],
                          f_credit=config.Config.PREFIX + '/var/hasrv/credit-',
                          f_status=config.Config.PREFIX + '/etc/ha_info.http',
                          f_allow_src_ips=config.Config.PREFIX + '/etc/src_allow.ips',
                          f_deny_src_ips=config.Config.PREFIX + '/etc/src_deny.ips',
                          f_deny_dst_ips=config.Config.PREFIX + '/etc/dst_deny.ips',
                          f_deny_dst_doms=config.Config.PREFIX + '/etc/dst_deny.doms'
                          )
        try:
            cf = open(self.cfgfile, "wb")
            cf.write(out.encode())
        except (IOError, OSError):
            log.L.error("Cannot write haproxy config file %s" % (self.cfgfile))
        log.L.info("Created haproxy config file %s" % (self.cfgfile))

    def createClientConfig(self):
        tfile = config.Config.PREFIX + "/etc/haproxy_client.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open openvpn template file %s" % (tfile))
            sys.exit(1)
        with open (config.Config.CAP.providerCa, "r") as f_ca:
            f_ca = "".join(f_ca.readlines())
        port=self.json['proxy'][0]['port'].split('/')[0]
        out = tmpl.decode("utf-8").format(
                          server=self.json['proxy'][0]['endpoint'],
                          maxconn=self.cfg['max_connections'],
                          timeout=self.cfg['timeout'],
                          ctimeout=self.cfg['connect_timeout'],
                          port=port,
                          f_ca=f_ca,
                          ca=config.Config.CAP.providerCa,
                          header='X-ITNS-PaymentID',
                          proxyport=self.cfg['client_port'],
                          bindaddr=self.cfg['client_bind'],
                          paymentid='PaymentID')
        try:
            print(out)
            sys.exit()
        except (IOError, OSError):
            log.L.error("Cannot write haproxy config file")
