import config
import log
import os
import random
import re
import select
from service import Service
from service_ha import ServiceHa
from service_stn import ServiceStunnel
import services
import shutil
import signal
import subprocess
import sys
import time

ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceHaClient(ServiceHa):
    """
    HAproxy client service class
    """
    
    OPTS = dict(
                name='ProxyClient', https_proxy_host=None, https_proxy_port=3128,
                proxy_bind='127.0.0.1', proxy_port=8180, status_port=8181,
                max_connections=2000, timeout='30s', connect_timeout='5s',
                paymentid='authid1', uniqueid='abcd1234', 
                max_conns_per_ip=10000, max_conns_per_period=10000, max_requests_per_period=10000,
                conns_period="10s",
                endpoint=None,
                port=None
                )
    OPTS_HELP = dict(
                     client_bind='Client bind address',
                     max_conns_per_ip='Maximum number of simultanous connections per IP',
                     max_conns_per_period='Maximum number of tcp connections per IP for period',
                     max_requests_per_period='Maximum number of HTTP requests per IP for period',
                     conns_period='Measuring period',
                     endpoint='Override endpoint',
                     port='Override port'
                     )
    
    def run(self):
        r = super().run()
        if self.stunnel:
            self.stunnel.run()
        return(r)
            
    def orchestrate(self):
        if self.stunnel:
            if not self.stunnel.orchestrate():
                return None
        return(super().orchestrate())
    
    def createConfig(self):
        if (not os.path.exists(self.dir)):
            os.mkdir(self.dir)
        os.chdir(self.dir)
        tfile = config.Config.PREFIX + "/etc/haproxy_client.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open openvpn template file %s" % (tfile))
            sys.exit(1)
        ca = services.SERVICES.sdp.getCertificates()
        cafile = self.dir + "ca.crt"
        try:
            caf = open(cafile, "wb")
            caf.write(ca.encode())
        except (IOError, OSError):
            log.L.error("Cannot write ca file %s" % (cafile))
            sys.exit(1)
        shutil.copy(config.Config.PREFIX + '/etc/ha_err_connect.http', self.dir)
        shutil.copy(config.Config.PREFIX + '/etc/ha_err_badid.http', self.dir)
        shutil.copy(config.Config.PREFIX + '/etc/ha_info.http', self.dir)
        if (config.Config.CAP.authId):
            paymentid = config.Config.CAP.authId
        else:
            paymentid = self.cfg['paymentid']
        if (config.Config.CAP.uniqueId):
            mgmtid = config.Config.CAP.uniqueId
        else:
            mgmtid = self.cfg['uniqueid']
        if (config.Config.CAP.servicePort):
            self.cfg['port'] = config.Config.CAP.servicePort
        elif ('port' not in self.cfg):
            self.cfg['port'] = self.json['proxy'][0]['port'].split('/')[0]
        if (config.Config.CAP.proxyPort):
            self.cfg['proxy_port'] = "%s" % config.Config.CAP.proxyPort
        if (config.Config.CAP.proxyBind):
            self.cfg['proxy_bind'] = config.Config.CAP.proxyBind
        if (config.Config.CAP.serviceFqdn):
            self.cfg['endpoint'] = config.Config.CAP.serviceFqdn
        elif ('endpoint' not in self.cfg):
            self.cfg['endpoint'] = self.json['proxy'][0]['endpoint']
        if (config.CONFIG.CAP.httpsProxyHost):
            cfg = self.cfg
            cfg["port"] = "%s" % config.CONFIG.CAP.stunnelPort
            cfg["https_proxy_host"] = config.CONFIG.CAP.httpsProxyHost
            cfg["https_proxy_port"] = "%s" % config.CONFIG.CAP.httpsProxyPort
            cfg["remote_port"] = "%s" % self.json['proxy'][0]['port'].split('/')[0]
            cfg["remote_host"] = "%s" % self.cfg['endpoint']
            self.stunnel = ServiceStunnel(self.id, cfg=cfg)
            self.stunnel.dir = self.dir
            self.stunnel.cfgfile = self.dir + "/stunnel.cfg"
            self.stunnel.pidfile = self.dir + "/stunnel.pid"
            self.cfg["endpoint"] = '127.0.0.1'
            self.cfg["port"] = "%s" % config.CONFIG.CAP.stunnelPort
            comment_tls = '#'
            comment_clr = ''
        else:
            self.stunnel = None
            comment_tls = ''
            comment_clr = '#'
        out = tmpl.decode("utf-8").format(
                                          server=self.cfg['endpoint'],
                                          maxconn=self.cfg['max_connections'],
                                          timeout=self.cfg['timeout'],
                                          ctimeout=self.cfg['connect_timeout'],
                                          port=self.cfg["port"],
                                          sport=self.cfg['status_port'],
                                          f_sock=self.mgmtfile,
                                          f_logsocket=config.Config.PREFIX + '/var/run/log local0',
                                          ctrldomain='^(local.lethean|_local_)$',
                                          ctrlpath='/status',
                                          mgmtid=self.cfg['uniqueid'],
                                          ca=cafile,
                                          payment_header=config.Config.CAP.authidHeader,
                                          mgmt_header=config.Config.CAP.mgmtHeader,
                                          proxyport=self.cfg['proxy_port'],
                                          bindaddr=self.cfg['proxy_bind'],
                                          s_port=self.cfg['status_port'],
                                          f_status='ha_info.http',
                                          f_err_connect='ha_err_connect.http',
                                          f_err_badid='ha_err_badid.http',
                                          comment_tls=comment_tls,
                                          comment_clr=comment_clr,
                                          paymentid=paymentid)
        try:
            cf = open(self.cfgfile, "wb")
            cf.write(out.encode())
            log.L.warning("Configuration files created at %s" % (self.dir))
        except (IOError, OSError):
            log.L.error("Cannot write haproxy config file %s" % (self.cfgfile))
