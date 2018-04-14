
import json
import logging
import sys
from config import *

class SDP(object):
    """SDP functions"""
    
    def load(self):
        try:
            self.data = json.load(open(Config.SDPFILE))
        except IOError:
            logging.error("Cannot read %s" % (Config.SDPFILE))
            sys.exit(1)
    def upload(self):
        """
        Upload to SDP server..
        """
    
    def listServices(self):
        ret = dict()
        for service in self.data["services"]:
            ret[service["id"]] = service["id"]
        return(ret)
    
    def getService(self, id):
        for value in self.data["services"]:
            if (value["id"] == id): 
                return(value)
            
