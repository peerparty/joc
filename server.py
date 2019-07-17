#!/usr/bin/python3
# -*- coding: utf-8 -*-

import random
import string
import time
import threading
import json
import sys

import hs 
import ws
import cs

class ConsensusManager:
    def __init__(self):
        self.servers = {}
        self.last_server_id = -1
        self.server_count = 0

    def create_server(self):
        consensus_server = cs.ConsensusServer()
        self.servers[self.server_count] = consensus_server
        self.last_server_id = self.server_count
        self.server_count += 1
        return self.last_server_id

    def add_user(self, ws):
        cs = self.servers[self.last_server_id]
        user_id = cs.add_user(ws)
        print("created user %d @ server %d" %
            (user_id, self.last_server_id))
        ws.sendMessage(json.dumps({
            'cmd': 'USER',
            'id': user_id,
            'server_id': self.last_server_id
        })) 

    def handle_msg(self, ws):
        data = json.loads(ws.data)
        print('handle_msg', data)
        cmd = data['cmd']
        if cmd == 'HELLO':
          self.add_user(ws)
        elif cmd == 'ANSWER':
            cs = self.servers[data['server_id']]
            cs.answer_response(data['id'], data['val'])
        elif cmd == 'PROMPT':
            cs = self.servers[data['server_id']]
            cs.prompt_response(data['id'], data['val'])

        # ADMIN COMMANDS - JBG
        elif cmd == 'ADMIN_CREATE':
            server_id = self.create_server()
            ws.sendMessage(json.dumps({
                'cmd': 'ADMIN_SERVER_CREATED',
                'id': server_id
            }))
        elif cmd == 'ADMIN_START':
            cs = self.servers[data['id']]  
            cs.start(data['val'])

def main():
    try:
        cm = ConsensusManager()

        ws_server = ws.WS(cm.handle_msg)
        ws_thread = threading.Thread(target=ws_server.start)
        ws_thread.daemon = True
        ws_thread.start()

        http_server = hs.HTTP()
        #http_thread = threading.Thread(target=http_server.start)
        #http_thread.daemon = True
        #http_thread.start()
        http_server.start()

    except KeyboardInterrupt:
        print("^C received, shutting down server")
        ws_server.stop()

if __name__== "__main__":
    main()

