
import base64
import config
import ed25519
import json
import jsonpickle
import log
import os
import pprint
import re
import sdp
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request
from urllib.request import urlopen

class SDPList(object):
    
    data = {}

    def download(self, filter=None):
        if self.isFresh():
            log.L.info('SDP cache is fresh, not reloading.')
            return(True)
        sdpSearch = config.Config.CAP.sdpUri + '/services/search'
        log.L.info('Using SDP endpoint %s' % sdpSearch)
        request = Request(sdpSearch)
        request.add_header('Content-Type', 'application/json')        
        try:
            response = urlopen(request).read()
            jsonResp = json.loads(response.decode('utf-8'))
            if jsonResp and jsonResp['protocolVersion']:
                try:
                    cf = open(config.Config.CAP.sdpCacheFile, "wb")
                    cf.write(response)
                    return True
                except (IOError, OSError):
                    log.L.error("Cannot write SDP cache %s" % (config.Config.CAP.sdpCacheFile))
                    sys.exit(2)
        except Exception as err:
            log.L.error("Cannot fetch from SDP server!")
            print(err)
            sys.exit(2)

        return False
    
    def isFresh(self):
        if os.path.isfile(config.Config.CAP.sdpCacheFile):
            stat = os.stat(config.Config.CAP.sdpCacheFile)
            if (time.time()-stat.st_mtime > config.Config.CAP.sdpCacheExpiry):
                return(None)
            else:
                return(True)
        else:
            return(None)
        
    def list(self):
        return(self.data.keys())
    
    def getSDP(self, id_):
        if id_ in self.data:
            return(self.data[id_])
        
    def parse(self):
        self.download()
        try:
            cf = open(config.Config.CAP.sdpCacheFile, "rb")
            sdpf = cf.read()
            cf.close()
        except (IOError, OSError):
            log.L.error("Cannot read SDP cache %s" % (config.Config.CAP.sdpCacheFile))
            sys.exit(2)
        self.data={}
        allJson = json.loads(sdpf.decode('utf-8'))
        for prov in allJson['providers']:
            id_ = prov['provider']
            if id_ in allJson:
                providerJson = allJson[id_]
            else:
                providerJson = dict(
                    protocolVersion=1,                
                    provider=dict(
                        id='{providerid}',
                        name='',
                        nodeType='{nodetype}',
                        certificates={},
                        wallet='{walletaddress}',
                        terms='{providerterms}',
                    ),                                
                    services=[],
                    )
            providerJson['provider']['id'] = id_
            providerJson['provider']['name'] = prov['providerName']
            providerJson['provider']['wallet'] = prov['providerWallet']
            ca = base64.b64decode(prov['certArray'][0]['certContent']).decode('utf-8')
            providerJson['provider']['certificates'] = {}
            providerJson['provider']['certificates']['cn'] = 'ignored'
            providerJson['provider']['certificates']['id'] = 0
            providerJson['provider']['certificates']['content'] = ca
            sid = prov["id"]
            newservice = True
            for service in providerJson["services"]:
                if (service['id'] == sid):
                    newservice = None
            if newservice:
                log.L.info("Adding service %s:%s to SDP list" % (id_, prov['id']))
                service=dict(
                    id=sid,
                    type=prov["type"],
                    name=prov["name"],
                    allowRefunds=prov["allowRefunds"],
                    firstVerificationsNeeded=prov["firstVerificationsNeeded"],
                    subsequentVerificationsNeeded=prov["subsequentVerificationsNeeded"],
                    downloadSpeed=prov["downloadSpeed"],
                    uploadSpeed=prov["uploadSpeed"],
                    firstPrePaidMinutes=prov["firstPrePaidMinutes"],
                    subsequentPrePaidMinutes=prov["subsequentPrePaidMinutes"],
                    cost=prov["cost"]
                )
                if prov["type"]=="proxy":
                    service["proxy"]=prov["proxy"]
                else:
                    service["vpn"]=prov["vpn"]
                self.data[id_]=providerJson
                self.data[id_]["services"].append(service)
        if (os.path.exists(config.CONFIG.SDPFILE)):
            try:
                jf = open(config.CONFIG.SDPFILE, "r")
                localSdp = jf.read()
                cf = open(config.CONFIG.PREFIX + "/etc/ca/certs/ca.cert.pem", "r")
                localCa = cf.read()
            except (IOError, OSError):
                log.L.warning("Cannot read local SDP file %s" % (config.CONFIG.SDPFILE))
            localJson = json.loads(localSdp)
            localJson['provider']['certificates'] = {}
            localJson['provider']['certificates']['cn'] = 'ignored'
            localJson['provider']['certificates']['id'] = 0
            localJson['provider']['certificates']['content'] = localCa
            id_ = localJson["provider"]["id"]
            self.data[id_]=localJson
