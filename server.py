#!/usr/bin/python3
# -*- coding: utf-8 -*-

import random
import string
import time
import threading
import json
import sys
import datetime

import ws
import cs

class TreeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, cs.Answer):
            return {'user_id': o.user.id, 'val': o.val}
        return super(TreeEncoder, self).default(o)

class ConsensusManager:
    def __init__(self):
        self.join_time = 600 
        #self.tutorial_time = 31 
        self.tutorial_time = 10
        #self.tutorial_time = 5 
        self.servers = {}
        self.last_server_id = -1
        self.server_count = 0
        self.screens = []
        self.stmts = [
            "The Netherlands can do without the EU",
            "The leaders of this country do not represent me",
            "You have to pay a lot to be a politician.",
            "Most politicians are reliable (or unreliable)",
            "It is the large companies that ultimately govern us",
            "It would be good if more low-educated people entered the parliament",
            "If people don't feel well represented, they have to take action themselves.",
            "In a democracy, the minority must adapt to the majority",
            "Politicians must keep their election promise at all costs.",
            "Lobbyists should be banned."
        ]

    def create_server(self):
        consensus_server = cs.ConsensusServer(self)
        self.servers[self.server_count] = consensus_server
        self.last_server_id = self.server_count
        self.server_count += 1
        return self.last_server_id

    def add_user(self, ws, server_id):
        cs = self.servers[self.last_server_id]
        if self.running:
            ws.sendMessage(json.dumps({
                'cmd': 'USER_FULL',
            }))
        elif server_id != self.last_server_id or ws.user_id not in cs.users:
            user = cs.add_user(ws)
            print("created user %d @ server %d" %
                  (user.id, self.last_server_id))
            ws.sendMessage(json.dumps({
                'cmd': 'USER',
                'id': ws.user_id,
                'server_id': self.last_server_id,
                'start_time': self.start_time,
                'count': cs.user_count
            }))
        else:
            print("FAIL: USER CREATE.",
                server_id,
                self.last_server_id,
                ws.user_id)
        
        self.screencast({
            'cmd': 'SCREEN_USER_COUNT',
            'count': cs.user_count 
        })

    def rm_user(self, ws):
        cs = self.servers[self.last_server_id]
        cs.rm_user(ws)
        print("USER COUNT", cs.user_count)

    def add_screen(self, ws):
        self.screens.append(ws)

    def handle_msg(self, ws):
        data = json.loads(ws.data)
        print('handle_msg', data)
        cmd = data['cmd']

        # USER COMMANDS - JBG
        if cmd == 'USER_HELLO':
            self.add_user(ws, data['server_id'])
        elif cmd == 'USER_ANSWER':
            cs = self.servers[data['server_id']]
            cs.answer_response(data['id'], data['val'])
        elif cmd == 'USER_PROMPT':
            cs = self.servers[data['server_id']]
            cs.prompt_response(data['id'], data['val'])
        elif cmd == 'USER_RESPONSE':
            cs = self.servers[data['server_id']]
            cs.check_start(data['id'], data['val'])

        # SCREEN COMMANDS - JBG
        elif cmd == 'SCREEN_JOIN':
            self.screens.append(ws)
            self.screen_init(ws)

        # ADMIN COMMANDS - JBG
#        elif cmd == 'ADMIN_CREATE':
#            server_id = self.create_server()
#            ws.sendMessage(json.dumps({
#                'cmd': 'ADMIN_SERVER_CREATED',
#                'id': server_id
#            }))
#        elif cmd == 'ADMIN_START':
#            cs = self.servers[data['id']]  
#            cs.start(data['val'])
#
    def screen_init(self, ws):
        cs = self.servers[self.last_server_id]  
        ws.sendMessage(json.dumps({
            'cmd': 'SCREEN_INIT',
            # TODO: get real data - JBG
            'count': cs.user_count,
            'data': self.read_file()[-5:],
            'stmt': self.stmt,
            'start_time': self.start_time,
            'id': self.last_server_id
        }))

    def start_session(self):
        #cs.start(data['val'])
        cs = self.servers[self.last_server_id]  
        cs.start(self.stmt)
        #self.screencast({ 'cmd': 'SCREEN_START' })

    def start_cs(self):
        if not self.running:
            self.running = True
            cs = self.servers[self.last_server_id]  
            cs.broadcast_tutorial()
            t = threading.Timer(self.tutorial_time, self.start_session)
            t.start()

    def screencast(self, payload):
        print('SCREENCAST', payload)
        for ws in self.screens:
            ws.sendMessage(json.dumps(payload, cls=TreeEncoder))

    def write_file(self, stmt):
        with open('consensus.txt', 'a') as f:
            f.write(str(int(time.time())) + ',' + stmt + '\n')

    def read_file(self):
        stmts = []
        with open('consensus.txt', 'r') as f:
            content = f.readlines()
        content = [x.strip() for x in content] 
        for line in content:
            elems = line.split(',')
            if len(elems) == 2:
                stmts.append({ 'time': int(elems[0]), 'stmt': elems[1] })
        return stmts
          
    def send_consensus(self, stmt):
        self.write_file(stmt)
        self.screencast({
            'cmd': 'SCREEN_CONSENSUS',
            'data': stmt,
            'id': self.last_server_id
        })

    def not_enough(self):
        self.screencast({ 'cmd': 'SCREEN_NOT_ENOUGH' })
        self.next_round()
        
    def next_round(self):
        self.stmt = random.choice(self.stmts)
        self.running = False
        server_id = self.create_server()
        self.start_time = int(
            time.mktime((datetime.datetime.now() +
                datetime.timedelta(seconds = self.join_time))
                .timetuple()
            )
        )

        for ws in self.screens:
            self.screen_init(ws)

def main():
    try:
        cm = ConsensusManager()
        cm.next_round()

        ws_server = ws.WS(cm.handle_msg, cm.rm_user)
        #ws_thread = threading.Thread(target=ws_server.start)
        #ws_thread.daemon = True
        #ws_thread.start()
        ws_server.start()

    except KeyboardInterrupt:
        print("^C received, shutting down server")
        ws_server.stop()

if __name__== "__main__":
    main()
    

