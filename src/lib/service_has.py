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
from service_ha import ServiceHa
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceHaServer(ServiceHa):
    """
    HAproxy server service class
    """
    
    OPTS = dict(
        name='Proxy', backend_proxy_server = '127.0.0.1:3128', status_port = 8181,
        bind_addr = '0.0.0.0',
        port = None,
        crt = None, key = None, crtkey = None,
        max_connections = 2000, timeout = '30s', connect_timeout = '5s',
        paymentid = 'authid1', uniqueid = 'abcd1234', 
        dispatcher_http_host = '127.0.0.1', dispatcher_http_port = 8188,
        track_sessions = True,
        max_conns_per_ip = 10000, max_conns_per_period = 10000, max_requests_per_period = 10000,
        conns_period = "10s"
    )
    OPTS_HELP = dict(
        client_bind = 'Client bind address',
        max_conns_per_ip = 'Maximum number of simultanous connections per IP',
        max_conns_per_period = 'Maximum number of tcp connections per IP for period',
        max_requests_per_period = 'Maximum number of HTTP requests per IP for period',
        conns_period = 'Measuring period',
        port = 'Override port'
    )
    OPTS_REQUIRED = (
         'backend_proxy_server', 
         'crt',
         'key',
         'crtkey',
         'bind_addr'
    )
        
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
    
    def createConfig(self):
        if (not os.path.exists(self.dir)):
            os.mkdir(self.dir)
        os.chdir(self.dir)
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
        if ('port' in self.cfg):
            port=self.cfg['port']
        else:
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
                          payment_header=config.Config.CAP.authidHeader,
                          mgmt_header=config.Config.CAP.mgmtHeader,
                          mgmtid=config.Config.CAP.providerid,
                          ctrldomain='^(remote.lethean|_remote_)$',
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
