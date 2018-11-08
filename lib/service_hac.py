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

class ServiceHaClient(ServiceHa):
    """
    HAproxy client service class
    """
    
    OPTS = dict(
        name='ProxyClient', http_proxy = None,
        client_bind = '127.0.0.1', client_port = 8180, status_port = 8181,
        crt = None, key = None, crtkey = None,
        max_connections = 2000, timeout = '30s', connect_timeout = '5s',
        paymentid = 'authid1', uniqueid = 'abcd1234', 
        max_conns_per_ip = 10000, max_conns_per_period = 10000, max_requests_per_period = 10000,
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
         'http_proxy', 
         'crt',
         'key',
         'crtkey'
    )

    def createConfig(self):
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
                          ctrldomain='^(local.lethean|_local_)$',
                          ctrlpath='/status',
                          mgmtid=self.cfg['uniqueid'],
                          ca=config.Config.CAP.providerCa,
                          payment_header='X-LTHN-PaymentID',
                          mgmt_header='X-LTHN-MgmtID',
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
