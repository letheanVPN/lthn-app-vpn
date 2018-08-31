from service import Service
import config
import http.server
import socketserver
import log
import socket
import authids
import re

class HttpStatusServer(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        log.L.debug("HTTP server GET %s" % (self.path))
        p = re.search("^/authid/(.*)$", self.path)
        if (p):
            authid = p.group(1).upper()
            payment = authids.AUTHIDS.get(authid)
            if (payment):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                content = payment.toJson()+"\n"
                self.wfile.write(content.encode("utf-8"))
                return
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{status: "ERROR"}')

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
    
    def __init__(self):
        super().__init__()
        self.id  = "HH"
        self.name = "HTTP status server"
        log.L.info("Run service %s" % (self.id))
        self.mgmtfile = None
        self.process = None
        self.pidfile = None
            
    def run(self):
        server_class = http.server.HTTPServer
        server_address = ('', 8188)
        self.httpd = server_class(server_address, HttpStatusServer)
        self.httpd.timeout = self.SOCKET_TIMEOUT
        
    def orchestrate(self):
        self.httpd.handle_request()
        
