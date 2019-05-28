#!/usr/bin/env python
from http.server import BaseHTTPRequestHandler, HTTPServer

import json

port_number = 3333

class HTTP():
  def start(self):
    server = HTTPServer(('', port_number), S)
    print("Started HTTP server on port", port_number)
    server.serve_forever()
   
class S(BaseHTTPRequestHandler):

  def _set_headers(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()

  def do_GET(self):
    self._set_headers()
    if self.path == '/':
      self.path = '/index.html'
    f = open('./' + self.path)
    try:
      self.wfile.write(f.read().encode('utf-8'))
      f.close()
      return
    except IOError:
      self.send_error(404, 'file not found')

#  def do_POST(self):
#    self._set_headers()
#
#    # Read what was sent - JBG
#    data = self.rfile.read(int(self.headers['Content-Length']))
#    data = json.loads(data)
#
#    # Do your whatever here - JBG
#    
#    # Send something back, in this case "Hello POST" - JBG
#    self.wfile.write(bytes("Hello POST, foo is " + data['foo'], "utf-8"))
#
#    return 
#


