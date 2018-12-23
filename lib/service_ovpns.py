from service import Service
import config
import os
import sys
import re
import log
import time
import select
import authids
from subprocess import Popen
from subprocess import PIPE
from service_ovpn import ServiceOvpn
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceOvpnServer(ServiceOvpn):
    """
    Openvpn service class
    """ 
    
    OPTS = dict(
        crt = None, key = None, crtkey = None,
        tundev = "tun0",
        mgmtport = "11193",
        proto = "UDP"
    )
    OPTS_HELP = dict(
        tundev = "Local tun device"
    )
    
    def mgmtAuthClient(self, cid, kid):
        global AUTHIDS
        
        username = ""
        password = ""
        untrusted_ip = ""
        untrusted_port = ""
        msg = self.mgmtRead()
        while (True):
            if (msg==None):
                continue
            p = re.search(">CLIENT:ENV,END", msg)
            if (p):
                break
            p = re.search(">CLIENT:ENV,username=(.*)", msg)
            if (p):
                username = p.group(1).strip()
            p = re.search(">CLIENT:ENV,password=(.*)", msg)
            if (p):
                password = p.group(1).strip()
            p = re.search(">CLIENT:ENV,untrusted_ip=(.*)", msg)
            if (p):
                untrusted_ip = p.group(1).strip()
            p = re.search(">CLIENT:ENV,untrusted_port=(.*)", msg)
            if (p):
                untrusted_port = p.group(1).strip()
            msg = self.mgmtRead()
            
        if (username == password and authids.AUTHIDS.get(username)):
            self.mgmtWrite("client-auth %s %s\r\n" % (cid, kid))
            self.mgmtWrite("END\r\n")
            log.A.audit(log.A.SESSION, log.A.ADD, paymentid=username, srcip=untrusted_ip, srcport=untrusted_port, serviceid=self.getId())
        else:
            log.A.audit(log.A.SESSION, log.A.NPAYMENT, paymentid=username, srcip=untrusted_ip, srcport=untrusted_port, serviceid=self.getId())
            self.mgmtWrite("client-deny %s %s \"Bad auth\"\r\n" % (cid, kid))
    
    def createConfig(self):
        if (not os.path.exists(self.dir)):
            os.mkdir(self.dir)
        self.cfgfile = self.dir + "/cfg"
        self.pidfile = self.dir + "/pid"
        self.mgmtfile = self.dir + "/mgmt"
        if (os.path.exists(self.mgmtfile)):
            os.remove(self.mgmtfile)
        tfile = config.Config.PREFIX + "/etc/openvpn_server.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open openvpn template file %s" % (tfile))
        with open (config.Config.CAP.providerCa, "r") as f:
            f_ca = "".join(f.readlines())
        with open (self.cfg["crt"], "r") as f:
            f_crt = "".join(f.readlines())
        with open (self.cfg["crtkey"], "r") as f:
            f_key = "".join(f.readlines())
        if (config.Config.CAP.vpndDns):
            dns = "dhcp-option dns " + config.Config.CAP.vpndDns
        else:
            dns = ""
        self.cfg["tundev"] = config.Config.CAP.vpndTun
        self.cfg["mgmtport"] = config.Config.CAP.vpndMgmtPort
        
        if (config.Config.CAP.servicePort):
            self.cfg['port'] = config.Config.CAP.servicePort
        elif ('proto' not in self.cfg):
            self.cfg['proto'] = self.json['vpn'][0]['port'].split('/')[1]
        if (config.Config.CAP.serviceProto):
            self.cfg['proto'] = config.Config.CAP.serviceProto
        elif ('port' not in self.cfg):
            self.cfg['port'] = self.json['vpn'][0]['port'].split('/')[0]
        if (config.Config.CAP.serviceFqdn):
            self.cfg['endpoint'] = config.Config.CAP.serviceFqdn
        elif ('endpoint' not in self.cfg):
            self.cfg['endpoint'] = self.json['vpn'][0]['endpoint']
        out = tmpl.decode("utf-8").format(
                          port=self.cfg['port'],
                          proto=self.cfg['proto'].lower(),
                          f_dh=config.Config.PREFIX + '/etc/dhparam.pem',
                          tunnode=config.Config.PREFIX + '/dev/net/tun',
                          tundev=self.cfg["tundev"],
                          f_ca=f_ca,
                          f_crt=f_crt,
                          f_key=f_key,
                          unprivip=config.Config.PREFIX + "/bin/unpriv-ip.sh",
                          workdir=self.dir,
                          user="nobody",
                          group="nogroup",
                          f_status="status",
                          iprange=config.Config.CAP.vpndIPRange,
                          ipmask=config.Config.CAP.vpndIPMask,
                          mgmt_sock="127.0.0.1 %s" % self.cfg["mgmtport"],
                          reneg=config.Config.CAP.vpndReneg,
                          mtu=1400,
                          mssfix=1300,
                          push_dns=dns
                          )
        try:
            cf = open(self.cfgfile, "wb")
            cf.write(out.encode())
        except (IOError, OSError):
            log.L.error("Cannot write openvpn config file %s" % (self.cfgfile))
        log.L.info("Created openvpn config file %s" % (self.cfgfile))
        