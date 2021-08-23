#!/usr/bin/env python
from SimpleWebSocketServer import SimpleSSLWebSocketServer, SimpleWebSocketServer, WebSocket
import json
import ssl

class WS():
  def __init__(self, handler, remover):
    global msg_handler
    msg_handler = handler
    global user_remover
    user_remover = remover
    
  
  def start(self):
    self.server = SimpleWebSocketServer('', 8000, WSClient)
#    self.server = SimpleSSLWebSocketServer(
#        '',
#        8000,
#        WSClient,
#        './cert.pem',
#        './key.pem',
#        version=ssl.PROTOCOL_TLSv1)
    self.server.serveforever()

  def stop(self):
    print("^C received, shutting down server")
    self.server.close() 

class WSClient(WebSocket):

  def handleMessage(self):
    #print(self.address, 'message')
    global msg_handler
    msg_handler(self)

  def handleConnected(self):
    self.user_id = self.address[1]
    print(self.user_id, 'connected')

  def handleClose(self):
    print(self.address, 'closed')
    global user_remover 
    user_remover(self)
    #clients.remove(self)

