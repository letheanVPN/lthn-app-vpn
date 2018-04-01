
import json

class SDP(object):
    """SDP functions"""
    
    def load(self, filename):
        try:
            self.data = json.load(open(filename))
        except IOError:
            logging.error("Cannot read %s" % (filename))
            sys.exit(1)
        
    def listServices(self):
        ret = dict()
        for service in self.data["services"]:
            ret[service["id"]] = service["id"]
        return(ret)
    
    def getService(self, id):
        for value in self.data["services"]:
            if (value["id"] == id): 
                return(value)
            
