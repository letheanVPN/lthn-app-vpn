import logging
from lthnvpn.lib import config

class Log(object):
    
    def __init__(self, handler=None, level=logging.WARNING, name='lthn'):
        logging.basicConfig(level=level,
                    format='%(asctime)s %(name)-12s %(process)d %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
                    )
        self.logger = logging.getLogger(name)
        if (handler):
            self.logger.addHandler(handler)
        self.logger.setLevel(level)
    
    def debug(self, msg, *args, **kwargs):
        return self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        return self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        return self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        return self.logger.error(msg, *args, **kwargs)
