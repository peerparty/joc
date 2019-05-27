#!/usr/bin/env python
from http.server import BaseHTTPRequestHandler, HTTPServer
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

import logging
import json
import threading

logging.basicConfig(level=logging.DEBUG)

port_number = 3333

clients = []
client_count = 0

def create_user():
  global client_count
  client_count += 1
  return client_count

class WSClient(WebSocket):

  def handleMessage(self):
    print(self.data)
    cmd = json.loads(self.data)['cmd']
    if cmd == 'PING':
      self.sendMessage('PONG')
    elif cmd == 'HELLO':
      self.sendMessage(json.dumps({ 'cmd': 'USER', 'payload': create_user()}))
    else:
      self.sendMessage('UNKNOWN')

  def handleConnected(self):
    print(self.address, 'connected')
    clients.append(self)

  def handleClose(self):
    print(self.address, 'closed')
    clients.remove(self)

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

def http_server():
  server = HTTPServer(('', port_number), S)
  print("Started HTTP server on port", port_number)
  server.serve_forever()
 
if __name__ == "__main__":

  try:
    http_thread = threading.Thread(target=http_server)
    http_thread.daemon = True
    http_thread.start()

    server = SimpleWebSocketServer('', 8000, WSClient)
    server.serveforever()

  except KeyboardInterrupt:
    print("^C received, shutting down server")
    server.socket.close()



