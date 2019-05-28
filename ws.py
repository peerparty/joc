#!/usr/bin/env python
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import json

class WS():
  def __init__(self, handler):
    global msg_handler
    msg_handler = handler
  
  def start(self):
    self.server = SimpleWebSocketServer('', 8000, WSClient)
    self.server.serveforever()

  def stop(self):
    print("^C received, shutting down server")
    self.server.socket.close() 

class WSClient(WebSocket):

  def handleMessage(self):
    print(self.address, 'message')
    global msg_handler
    msg_handler(self)

  def handleConnected(self):
    print(self.address, 'connected')

  def handleClose(self):
    print(self.address, 'closed')
    clients.remove(self)

   

