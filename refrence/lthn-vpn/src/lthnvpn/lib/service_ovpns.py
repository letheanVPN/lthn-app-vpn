import os
import sys
import re
import time
import select
from subprocess import Popen
from subprocess import PIPE
from lthnvpn.lib.service_ovpn import ServiceOvpn
from lthnvpn.lib.service import Service
from lthnvpn.lib import config, log, authids, sessions

ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceOvpnServer(ServiceOvpn):
    """
    Openvpn service class
    """ 
    
    OPTS = dict(
        crt = None, key = None, crtkey = None,
        tundev = "",
        mgmtport = "",
        enabled = True,
        iprange = "",
        ipmask = "",
        ip6range = "",
        dns = ""
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
                username = p.group(1).strip().upper()
            p = re.search(">CLIENT:ENV,password=(.*)", msg)
            if (p):
                password = p.group(1).strip().upper()
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
            sessions.SESSIONS.add(username, untrusted_ip, untrusted_port, proto=self.cfg['proto'], id="%s:%s" % (cid, kid))
        else:
            log.L.warning("Bad authentication from remote IP %s and authid %s" % (untrusted_ip, username))
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
        elif ('dns' in self.cfg):
            dns = "dhcp-option dns " + self.cfg['dns']
        else:
            dns = ""
        if "tundev" in self.cfg:
            tundev = self.cfg["tundev"]
        else:
            tundev = config.Config.CAP.vpndTun
        if "mgmtport" in self.cfg:    
            mgmtport = self.cfg["mgmtport"]
        else:
            mgmtport = config.Config.CAP.vpndMgmtPort
            self.cfg["mgmtport"] = config.Config.CAP.vpndMgmtPort
        if (config.Config.CAP.duplicateCN):
            duplicate_cn = 'duplicate-cn'
        else:
            duplicate_cn = ''
        if (config.Config.CAP.servicePort):
            self.cfg['port'] = config.Config.CAP.servicePort
        elif ('port' not in self.cfg):
            self.cfg['port'] = self.json['vpn'][0]['port'].split('/')[0]
        if (config.Config.CAP.serviceProto):
            self.cfg['proto'] = config.Config.CAP.serviceProto
        elif ('proto' not in self.cfg):
            self.cfg['proto'] = self.json['vpn'][0]['port'].split('/')[1]
        if (config.Config.CAP.serviceFqdn):
            self.cfg['endpoint'] = config.Config.CAP.serviceFqdn
        elif ('endpoint' not in self.cfg):
            self.cfg['endpoint'] = self.json['vpn'][0]['endpoint']
        if "iprange" in self.cfg:
            iprange = self.cfg["iprange"]
        else:
            iprange = config.Config.CAP.vpndIPRange
        if "ipmask" in self.cfg:
            ipmask = self.cfg["ipmask"]
        else:
            ipmask = config.Config.CAP.vpndIPMask    
        if "ip6range" in self.cfg:
            ip6range = self.cfg["ip6range"]
        else:
            ip6range = config.Config.CAP.vpndIP6Range
        if ip6range:
            ip6comment=''
        else:
            ip6comment='#'
        out = tmpl.decode("utf-8").format(
                          port=self.cfg['port'],
                          proto=self.cfg['proto'].lower(),
                          f_dh=config.Config.PREFIX + '/etc/dhparam.pem',
                          tunnode=config.Config.PREFIX + '/dev/net/tun',
                          tundev=tundev,
                          f_ca=f_ca,
                          f_crt=f_crt,
                          f_key=f_key,
                          unprivip=config.Config.PREFIX + "/bin/unpriv-ip.sh",
                          workdir=self.dir,
                          user="nobody",
                          group="nogroup",
                          f_status="status",
                          iprange=iprange,
                          ipmask=ipmask,
                          ip6range=ip6range,
                          ip6comment=ip6comment,
                          mgmt_sock="127.0.0.1 %s" % mgmtport,
                          reneg=config.Config.CAP.vpndReneg,
                          mtu=1400,
                          mssfix=1300,
                          push_dns=dns,
                          duplicate_cn=duplicate_cn
                          )
        try:
            cf = open(self.cfgfile, "wb")
            cf.write(out.encode())
        except (IOError, OSError):
            log.L.error("Cannot write openvpn config file %s" % (self.cfgfile))
        log.L.info("Created openvpn config file %s" % (self.cfgfile))
        
