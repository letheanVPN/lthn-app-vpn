from service import Service
import config
import http.server
import socketserver
import log
import socket
import authids
import re
import time
import os
import sys
import signal
import atexit
import services

class HttpStatusRequest(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        log.L.debug("HTTP server GET %s" % (self.path))
        time.sleep(1)
        p = re.search("^/authid/(.*)$", self.path)
        if (p):
            authid = p.group(1).upper()
            payment = authids.AUTHIDS.get(authid)
            if (payment):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET')
                self.end_headers()
                content = payment.toJson()+"\n"
                self.wfile.write(content.encode("utf-8"))
                return        
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.end_headers()
        self.wfile.write(b'{status: "ERROR"}')

class HttpStatusServer(http.server.HTTPServer):
    
    def handle_timeout(self):
        return
    
class ServiceHttp(Service):
    """
    HTTP status service class
    """
    
    OPTS = dict(
        name='HTTP status', bind_addr = '127.0.0.1', port = 8188, host = ''
    )
    OPTS_HELP = dict(
        bind_addr = 'Bind address'
    )
    OPTS_REQUIRED = (
         'bind_addr', 'port'
    )
            
    def run(self):
        self.httpd = HttpStatusServer((self.cfg['bind_addr'],int(self.cfg['port'])), HttpStatusRequest)
        self.httpd.timeout = self.SOCKET_TIMEOUT
        atexit.register(self.stop)
        self.name = "HTTP server"
        self.pid = -1
        super().run()
        
    def stop(self):
        if (self.pid > 0):
            os.kill(self.pid, signal.SIGTERM)
            os.wait()
        super().stop()
        
    def orchestrate(self):
        needfork = None
        if (self.pid != 0):
            try:
                if (self.pid == -1):
                    needfork = True
                else:
                    os.kill(self.pid, 0)
            except OSError:
                needfork = True
        if needfork:
            self.pid = os.fork()
            if (self.pid != 0):
                log.L.debug("Spawning new http process with pid %s" % (self.pid))    
            else:
                atexit.unregister(services.SERVICES.stop)
                atexit.unregister(self.stop)
                now = time.time()
                while (time.time()-now<10):
                   self.httpd.handle_request()
                sys.exit();
        else:
            os.waitpid(self.pid, os.WNOHANG)

        
        
