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

  def _get_content_type(self):
    if 'mpeg' in self.path:
      return 'audio/mpeg'
    elif 'gif' in self.path:
      return 'image/gif'
    elif 'png' in self.path:
      return 'image/png'
    elif 'css' in self.path:
      return 'text/css'
    else:
      return 'text/html'

  def _set_headers(self, content_type):
    self.send_response(200)
    self.send_header('Content-type', content_type)
    self.end_headers()

  def _handle_binary(self):
    self._set_headers(self._get_content_type())
    try:
      f = open('./' + self.path, 'rb')
      self.wfile.write(f.read())
      f.close()
      return
    except IOError:
      self.send_error(404, 'file not found')

  def _handle_txt(self):
    self._set_headers(self._get_content_type())
    try:
      f = open('./' + self.path)
      self.wfile.write(f.read().encode('utf-8'))
      f.close()
      return
    except IOError:
      self.send_error(404, 'file not found')

  def do_GET(self):
    if ('mpeg' in self.path or
        'gif' in self.path or
        'png' in self.path or
        'ico' in self.path):
      self._handle_binary()
    else:
      if self.path == '/':
        self.path = '/index.html'
      elif self.path == '/admin':
        self.path = '/admin.html'
      self._handle_txt()     
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


