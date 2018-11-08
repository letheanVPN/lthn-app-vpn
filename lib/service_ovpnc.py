from service import Service
import config
import os
import sys
import re
import log
import time
import select
from subprocess import Popen
from subprocess import PIPE
from service_ovpn import ServiceOvpn
ON_POSIX = 'posix' in sys.builtin_module_names

class ServiceOvpnClient(ServiceOvpn):
    """
    Openvpn service client class
    """ 
    
    OPTS = dict(
        http_proxy = "localhost:3128",
        crt = None, key = None, crtkey = None,
        reneg = 600
    )
    OPTS_HELP = dict(
        http_proxy = "HTTP proxy used for connection to ovpn",
        reneg = "Renegotiation interval"
    )
    
    def createConfig(self):
        tfile = Config.PREFIX + "/etc/openvpn_client.tmpl"
        try:
            tf = open(tfile, "rb")
            tmpl = tf.read()
        except (IOError, OSError):
            log.L.error("Cannot open openvpn template file %s" % (tfile))
            sys.exit(1)
        with open (Config.PREFIX + '/etc/ca/certs/ca.cert.pem', "r") as f:
            f_ca = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/ca/certs/openvpn.cert.pem', "r") as f:
            f_crt = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/openvpn.tlsauth', "r") as f:
            f_ta = "".join(f.readlines())
        with open (Config.PREFIX + '/etc/dhparam.pem', "r") as f:
            f_dh = "".join(f.readlines())
        out = tmpl.decode("utf-8").format(
                          port=11194,
                          proto="udp",
                          ip="172.17.4.14",
                          f_ca=f_ca,
                          f_crt=f_crt,
                          f_ta=f_ta,
                          reneg=60,
                          mtu=1400,
                          mssfix=1300
                          )
        try:
            print(out)
            sys.exit()
        except (IOError, OSError):
            log.L.error("Cannot write openvpn config file")

