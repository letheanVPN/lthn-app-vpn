import os
import random
import re
import select
import shutil
import signal
import subprocess
import sys
import time
import requests
import atexit
import pathlib
from lthnvpn.lib.service import Service
from lthnvpn.lib.service_ha import ServiceHa
from lthnvpn.lib.service_stn import ServiceStunnel
from lthnvpn.lib import config, log, services, util

ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceHaClient(ServiceHa):
    """
    HAproxy client service class
    """
    
    OPTS = dict(
                name='ProxyClient', outbound_proxy_host=None, outbound_proxy_port=3128,
                proxy_bind='127.0.0.1', proxy_port=8180, status_port=8181, mgmtport="11194",
                max_connections=2000, timeout='30s', connect_timeout='5s',
                paymentid='authid1', uniqueid='abcd1234', 
                max_conns_per_ip=10000, max_conns_per_period=10000, max_requests_per_period=10000,
                conns_period="10s",
                endpoint=None,
                port=None
                )
    OPTS_HELP = dict(
                     proxy_bind='Client bind address',
                     max_conns_per_ip='Maximum number of simultanous connections per IP',
                     max_conns_per_period='Maximum number of tcp connections per IP for period',
                     max_requests_per_period='Maximum number of HTTP requests per IP for period',
                     conns_period='Measuring period',
                     endpoint='Override endpoint',
                     port='Override port'
                     )
           
    OK = 1
    OK_NOPAYMENT = 2
    E_EXPIRED = -5
    E_CONERR = -4
    E_BADID = -2
    E_TIMEOUT = -3
    E_GENERAL = -1
    
    def run(self):
        self.pid = None
        r = super().run()
        if self.stunnel:
            self.stunnel.run()
        return(r)
    
    def connect(self, sdp):
        providerid = sdp["provider"]["id"]
        code = self.waitForLocalEndpoint()
        if (code<0):
            return code
        code = self.waitForRemoteEndpoint(providerid)
        if (code<0):
            return code
        if (code==self.OK_NOPAYMENT):
            log.L.warning("Now you need to pay to provider's wallet.")
            log.A.audit(log.A.NPAYMENT, log.A.PWALLET, wallet=sdp["provider"]["wallet"], paymentid=self.cfg["paymentid"], anon="no")
            code = self.waitForPayment(providerid)
            if (code<0):
                return code
        log.L.warning("We are connected! Happy flying!")
        if config.CONFIG.CAP.forkOnConnect:
            log.L.warning("Forking into background.")
            if (os.fork()):
                atexit.unregister(services.SERVICES.stop)
                atexit.unregister(self.stop)
                sys.exit()
        while True:
            services.SERVICES.sleep(60)
            if self.PaymentStatus(providerid) == self.E_EXPIRED:
                log.L.warning("Payment gone!")
                if config.Config.CAP.exitNoPayment:
                    log.L.warning("Exiting.")
                    return self.E_EXPIRED
                else:
                    log.A.audit(log.A.NPAYMENT, log.A.PWALLET, wallet=sdp["provider"]["wallet"], paymentid=self.cfg["paymentid"], anon="no")
                    self.waitForPayment(providerid)
            
    def orchestrate(self):
        if config.CONFIG.isWindows():
            return True
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
            cfg["outbound_proxy_host"] = config.CONFIG.CAP.httpsProxyHost
            cfg["outbound_proxy_port"] = "%s" % config.CONFIG.CAP.httpsProxyPort
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
        sc=''
        if (config.CONFIG.isWindows()):
            wc='#'
        else:
            wc=''
        if (config.CONFIG.CAP.proxySSLNoVerify):
            nosslverify='verify none'
            comment_nossl='#'
        else:
            nosslverify=''
            comment_nossl=''
        self.cfg["mgmtport"] = config.Config.CAP.proxyMgmtPort
        out = tmpl.decode("utf-8").format(
                                          server=self.cfg['endpoint'],
                                          maxconn=self.cfg['max_connections'],
                                          timeout=self.cfg['timeout'],
                                          ctimeout=self.cfg['connect_timeout'],
                                          port=self.cfg["port"],
                                          sport=self.cfg['status_port'],
                                          f_sock="127.0.0.1:"+ self.cfg["mgmtport"],
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
                                          f_status=str(pathlib.Path(self.dir + 'ha_info.http')),
                                          f_err_connect=str(pathlib.Path(self.dir + 'ha_err_connect.http')),
                                          f_err_badid=str(pathlib.Path(self.dir + 'ha_err_badid.http')),
                                          comment_tls=comment_tls,
                                          comment_clr=comment_clr,
                                          paymentid=paymentid,
                                          stats_comment=sc,
                                          log_comment=wc,
                                          comment_nossl=comment_nossl,
                                          nosslverify=nosslverify
                                          )
        try:
            cf = open(self.cfgfile, "wb")
            cf.write(out.encode())
            log.L.warning("Configuration files created at %s" % (self.dir))
        except (IOError, OSError):
            log.L.error("Cannot write haproxy config file %s" % (self.cfgfile))
            
    """
    Wait for local proxy to be ready
    """
    def waitForLocalEndpoint(self):
        timeout = 5
        err = None
        while timeout < config.Config.CAP.connectTimeout:
            try:
                log.L.warning("Waiting for local proxy...")
                r = requests.get("http://localhost:%s/stats" % (self.cfg["proxy_port"]),
                                 proxies={"http": None, "https": None},
                                 headers={config.Config.CAP.mgmtHeader: self.cfg["uniqueid"]},
                                 timeout=timeout
                                 )
                if (r.status_code == 200):
                    log.L.warning("Local proxy OK")
                    return self.OK
                elif (r.status_code == 503 and r.reason == "BAD_ID"):
                    log.L.error("This is not our proxy! Another instance is running on port %s?" % (self.cfg["proxy_port"]))
                    return self.E_BADID
                log.L.debug("Request http://localhost:%s/stats (%s: %s, %s: %s) => %s [%s]" % (self.cfg["proxy_port"], config.Config.CAP.mgmtHeader, self.cfg["uniqueid"], config.Config.CAP.authidHeader, self.cfg["paymentid"], r.status_code, r.reason))
            except Exception as e:
                log.L.debug("Request http://localhost:%s/stats (%s: %s, %s: %s) => %s" % (self.cfg["proxy_port"], config.Config.CAP.mgmtHeader, self.cfg["uniqueid"], config.Config.CAP.authidHeader, self.cfg["paymentid"], e))
                timeout = timeout * 2
            services.SERVICES.sleep(timeout)
        log.L.error("Timeout connecting to local endpoint!")
        return self.E_TIMEOUT
    
    def waitForRemoteEndpoint(self, providerid):
        timeout = 5
        while timeout < config.Config.CAP.connectTimeout:
            try:
                log.L.warning("Waiting for remote proxy...")
                headers = {config.Config.CAP.mgmtHeader: providerid}
                r = requests.get("http://remote.lethean/status",
                         proxies={
                            "http": "http://localhost:%s" % (self.cfg["proxy_port"]),
                            "https": None
                         },
                         headers=headers,
                         timeout=timeout
                         )  
                log.L.debug("Request http://remote.lethean/status (%s: %s, %s: %s) => %s [%s]" % (
                config.Config.CAP.mgmtHeader, providerid, config.Config.CAP.authidHeader, self.cfg["paymentid"], r.status_code, r.reason))
                if 'X-LTHN-Status' in r.headers:
                    reason=r.headers['X-LTHN-Status']
                elif 'X-ITNS-Status' in r.headers:
                    reason=r.headers['X-ITNS-Status']
                else:
                    reason = r.reason
                if (r.status_code == 403 and reason == "NO_PAYMENT"):
                    log.L.warning("Remote proxy is connected.")
                    return self.OK_NOPAYMENT
                elif (r.status_code == 200 and reason == "OK"):
                    log.L.warning("Remote proxy is connected and prepaid.")
                    return self.OK
                elif (r.status_code == 503 and reason == "BAD_ID"):
                    log.L.error("This is not our remote proxy! Something is bad.")
                    return self.E_BADID
            except Exception as e:
                timeout = timeout * 2
                log.L.debug("Request http://localhost:%s/stats (%s: %s, %s: %s) => %s" % (self.cfg["proxy_port"], config.Config.CAP.mgmtHeader, providerid, config.Config.CAP.authidHeader, self.cfg["paymentid"], e))
            services.SERVICES.sleep(timeout)
        log.L.error("Timeout connecting to remote endpoint.")
        return self.E_TIMEOUT

    """
    Wait for payment to be propagated to remote node
    """
    def waitForPayment(self, providerid):
        timeout = 5
        while timeout < config.Config.CAP.paymentTimeout:
            try:
                headers = {config.Config.CAP.mgmtHeader: providerid, config.Config.CAP.authidHeader: self.cfg["paymentid"]}
                log.L.warning("Waiting for payment to settle...")
                r = requests.get("http://remote.lethean/status",
                         proxies={
                            "http": "http://localhost:%s" % (self.cfg["proxy_port"]),
                            "https": None
                         },
                         headers=headers,
                         timeout=timeout
                         )
                if 'X-LTHN-Status' in r.headers:
                    reason=r.headers['X-LTHN-Status']
                elif 'X-ITNS-Status' in r.headers:
                    reason=r.headers['X-ITNS-Status']
                else:
                    reason = r.reason
                log.L.debug("Request http://remote.lethean/status (%s: %s, %s: %s) => %s [%s,%s]" % (
                config.Config.CAP.mgmtHeader, providerid, config.Config.CAP.authidHeader, self.cfg["paymentid"], r.status_code, r.reason, reason))
                if (r.status_code == 200):
                    log.L.warning("Payment arrived. Happy flying!")
                    return self.OK
                elif (r.status_code == 403):
                    time.sleep(timeout)
                    timeout = timeout * 2
                elif (r.status_code == 503 and reason == "BAD_ID"):
                    log.L.error("This is not our remote proxy! Something is bad.")
                    return self.E_BADID
                elif (r.status_code == 503 and reason == "CONNECTION_ERROR"):
                    log.L.error("Error connecting to provider (CONNECTION_ERROR). Blocked?")
                    return self.E_CONERR
                elif (r.status_code == 504):
                    log.L.error("Error connecting to provider (TIMEOUT). Blocked?")
                    return self.E_CONERR
                else:
                    pass
            except Exception as e:
                log.L.error("Error connecting to provider (%s)" % (e))
                return self.E_TIMEOUT
            services.SERVICES.sleep(timeout)
        log.L.error("Timeout waiting for payment!")
        return self.E_TIMEOUT

    def PaymentStatus(self, providerid):
        timeout = 5
        try:
            log.L.info("Checking payment status")
            headers = {config.Config.CAP.mgmtHeader: providerid, config.Config.CAP.authidHeader: self.cfg["paymentid"]}
            r = requests.get("http://remote.lethean/status",
                     proxies={
                        "http": "http://localhost:%s" % (self.cfg["proxy_port"]),
                        "https": None
                     },
                     headers=headers,
                     timeout=timeout
                     )
            if 'X-LTHN-Status' in r.headers:
                reason=r.headers['X-LTHN-Status']
            elif 'X-ITNS-Status' in r.headers:
                reason=r.headers['X-ITNS-Status']
            else:
                reason = r.reason
            log.L.debug("Request http://remote.lethean/status (%s: %s, %s: %s) => %s [%s,%s]" % (
            config.Config.CAP.mgmtHeader, providerid, config.Config.CAP.authidHeader, self.cfg["paymentid"], r.status_code, r.reason, reason))
            if (r.status_code == 200):
                log.L.warning("Payment OK!")
                log.L.debug(r.text)
                return self.OK
            if (r.status_code == 403):
                return self.E_EXPIRED
            elif (r.status_code == 503 and reason == "BAD_ID"):
                return E_BADID
            else:
               pass
        except Exception as e:
            log.L.warning("Cannot get remote status! (%s)" % (e))
            return self.E_GENERAL
        
