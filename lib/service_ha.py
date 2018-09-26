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
from subprocess import Popen
from subprocess import PIPE
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceHa(Service):
    """
    HAproxy service class
    """
    
    OPTS = dict(
        name='Proxy', backend_proxy_server = '127.0.0.1:3128',
        client_bind = '127.0.0.1', client_port = 8180, status_port = 8181,
        bind_addr = '0.0.0.0',
        crt = None, key = None, crtkey = None,
        max_connections = 2000, timeout = '30s', connect_timeout = '5s',
        paymentid = 'authid1', uniqueid = 'abcd1234', 
        dispatcher_http_host = '127.0.0.1', dispatcher_http_port = 8188,
        track_sessions = True,
        max_conns_per_ip = 100, max_conns_per_period = 100, max_requests_per_period = 100,
        conns_period = "10s"
    )
    OPTS_HELP = dict(
        client_bind = 'Client bind address',
        max_conns_per_ip = 'Maximum number of simultanous connections per IP',
        max_conns_per_period = 'Maximum number of tcp connections per IP for period',
        max_requests_per_period = 'Maximum number of HTTP requests per IP for period',
        conns_period = 'Measuring period'
    )
    OPTS_REQUIRED = (
         'backend_proxy_server', 
         'crt',
         'key',
         'crtkey',
         'bind_addr'
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
    
    def addAuthId(self, authid, msg=""):
        """ Add authid to internal acl on haproxy """
        self.mgmtConnect()
        self.mgmtWrite("add acl #20 " + authid.getId() + "\n")
        self.mgmtClose()
        super().addAuthId(authid, msg)
        
    def delAuthId(self, authid, msg=""):
        """ Remove authid from internal acl on haproxy """
        self.mgmtConnect()
        self.mgmtWrite("del acl #20 " + authid.getId() + "\n")
        self.mgmtClose()
        super().delAuthId(authid, msg)
    
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
                    log.L.info("Unknown haproxy session " + l)
            l=self.mgmtRead()
        self.mgmtClose()
        return(sessions)
        
    def createConfig(self):
        if (not os.path.exists(self.dir)):
            os.mkdir(self.dir)
        if (os.path.exists(self.mgmtfile)):
            os.remove(self.mgmtfile)
        tfile = config.Config.PREFIX + "/etc/haproxy_server.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open haproxy template file %s" % (tfile))
        shutil.copy(config.Config.PREFIX + '/etc/ha_credit.http', self.dir + '/ha_credit.http')
        proxy_host, proxy_port = self.cfg['backend_proxy_server'].split(":")
        port=self.json['proxy'][0]['port'].split('/')[0]
        out = tmpl.decode("utf-8").format(
                          bind_addr=self.cfg['bind_addr'],
                          bind_port=port,
                          maxconn=self.cfg['max_connections'],
                          timeout=self.cfg['timeout'],
                          ctimeout=self.cfg['connect_timeout'],
                          ttimeout=random.randint(500,2000),
                          f_logsocket=config.Config.PREFIX + '/var/run/log local0',
                          f_sock=self.mgmtfile,
                          s_port=self.cfg['status_port'],
                          max_conns_per_ip = int(self.cfg['max_conns_per_ip']),
                          max_conns_per_period = int(self.cfg['max_conns_per_period']),
                          max_requests_per_period = int(self.cfg['max_requests_per_period']),
                          conns_period = self.cfg['conns_period'],
                          forward_proxy=proxy_host+":"+proxy_port,
                          forward_proxy_host=proxy_host,
                          forward_proxy_port=proxy_port,
                          payment_header='X-ITNS-PaymentID',
                          mgmt_header='X-ITNS-MgmtID',
                          mgmtid=config.Config.CAP.providerid,
                          ctrldomain='(^remote.lethean$|^_remote_$)',
                          ctrlpath='/status',
                          disp_http_host=self.cfg['dispatcher_http_host'],
                          disp_http_port=self.cfg['dispatcher_http_port'],
                          providerid=config.Config.CAP.providerid,
                          f_dh=config.Config.PREFIX + '/etc/dhparam.pem',
                          cabase=config.Config.PREFIX + '/etc/ca/certs',
                          crtbase=config.Config.PREFIX + '/etc/ca/certs',
                          f_sdp=config.CONFIG.SDPFILE,
                          f_status=config.Config.PREFIX + '/etc/ha_info.http',
                          f_err_connect=config.Config.PREFIX + '/etc/ha_err_connect.http',
                          f_err_badid=config.Config.PREFIX + '/etc/ha_err_badid.http',
                          f_err_nopayment=config.Config.PREFIX + '/etc/ha_err_nopayment.http',
                          f_err_overlimit=config.Config.PREFIX + '/etc/ha_err_overlimit.http',
                          f_err_generic=config.Config.PREFIX + '/etc/ha_err_generic.http',
                          f_site_pem=self.cfg['crtkey'],
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
        shutil.copy(config.Config.PREFIX + '/etc/ha_err_connect.http', '.')
        shutil.copy(config.Config.PREFIX + '/etc/ha_err_badid.http', '.')
        shutil.copy(config.Config.PREFIX + '/etc/ha_info.http', '.')
        port=self.json['proxy'][0]['port'].split('/')[0]
        out = tmpl.decode("utf-8").format(
                          server=self.json['proxy'][0]['endpoint'],
                          maxconn=self.cfg['max_connections'],
                          timeout=self.cfg['timeout'],
                          ctimeout=self.cfg['connect_timeout'],
                          port=port,
                          sport=8181,
                          f_ca=f_ca,
                          ctrldomain='(^local.lethean$|^_local_$)',
                          ctrlpath='/status',
                          mgmtid=self.cfg['uniqueid'],
                          ca=config.Config.CAP.providerCa,
                          payment_header='X-ITNS-PaymentID',
                          mgmt_header='X-ITNS-MgmtID',
                          proxyport=self.cfg['client_port'],
                          bindaddr=self.cfg['client_bind'],
                          s_port=self.cfg['status_port'],
                          f_status='ha_info.http',
                          f_err_connect='ha_err_connect.http',
                          f_err_badid='ha_err_badid.http',
                          paymentid=self.cfg['paymentid'])
        try:
            print(out)
            sys.exit()
        except (IOError, OSError):
            log.L.error("Cannot write haproxy config file")
