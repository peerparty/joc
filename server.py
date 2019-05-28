#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import string
import time
import threading
import json

import hs 
import ws

from functools import reduce
from anytree import Node, RenderTree, LevelOrderGroupIter, LevelOrderIter, PostOrderIter
from enum import Enum

def random_txt():
  return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))

class User:
    def __init__(self, user_id, ws):
        self.questions = []
        self.prompts = []
        self.id = user_id
        self.ws = ws

class Prompt:
    def __init__(self, ques, ans):
        self.ques = ques 
        self.ans = ans 

class Answer:
    def __init__(self, user, val):
        self.user = user
        self.val = val

class QuestionState(Enum):
    OPEN = 1 
    CLOSED = 2 
    REASKED = 3 
    PROMPTED = 4 

class Question(Node):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.id = kwargs['id']
        self.answers = []
        self.state = QuestionState.OPEN

    def add_answer(self, ans):
        self.answers.append(ans)

    def add_question(self, txt, id):
        q = Question(txt, parent=self, id=id)
        return q

    def check_consensus(self):
        consensus = False
        count_yes = 0
        count_no = 0
        
        for answer in self.answers:
            if answer.val:
                count_yes += 1
            else:
                count_no += 1
        return (count_yes > 0 and count_no == 0) or (count_no > 0 and count_yes == 0)

class ConsensusServer:
    def __init__(self):
        self.round_time = 10 
        self.users = {} 
        self.user_count = 0
        self.ques_count = 0
        self.root = Question("Root", id=self.ques_count)

    def add_question(self, txt, parent):
        self.ques_count += 1
        q = parent.add_question(txt, self.ques_count)

        for user_id, user in self.users.items():
            user.questions.append(q)

    def answer_response(self, user_id, ans):
        user = self.users[user_id]
        user.q.add_answer(Answer(user, ans))

    def prompt_response(self, user_id, prompt):
       user = self.users[user_id]
       self.add_question(prompt, user.p.ques)

    def get_height(self):
        return len([[node for node in children] for children in LevelOrderGroupIter(root)])

    def get_siblings(self, question):
        return question.parent.children

    def sibling_consensus(self, question):
        sibs = self.get_siblings(question)
        sibs = list(filter(lambda q : not q.state == QuestionState.REASKED, sibs))
        print("SIBS %s" % [node.name for node in sibs])
        if len(sibs) > 1 and reduce(lambda a, q : q.check_consensus() and a, sibs, True):
            parent = question.parent
            if not parent.state == QuestionState.REASKED:
                print("the reask %s %s" % (parent.name, parent.state))
                parent.state = QuestionState.REASKED 
                self.add_question(parent.name, parent=parent.parent)

    def create_prompt(self, question, ans):
        ans.user.prompts.append(Prompt(question, ans))

    def close_answers(self):
        q_size = reduce(lambda c, user : c + len(user.questions), list(self.users.values()), 0)
        if(q_size > 0):
            self.collect_answers()
        else:
            questions = list(filter(lambda n : n.state == QuestionState.OPEN, [node for node in PostOrderIter(self.root)]))
            for question in questions:
                if not question.check_consensus():
                    print("no consensus %s" % question.name)
                    question.state = QuestionState.PROMPTED 
                    for ans in question.answers:
                        self.create_prompt(question, ans)
                else:
                    print("omg consensus %s" % question.name)
                    question.state = QuestionState.CLOSED 
                    self.sibling_consensus(question)
            self.print_root()
            self.print_users()

            q_size = reduce(lambda c, user : c + len(user.prompts) + len(user.questions), list(self.users.values()), 0)
            if(q_size > 0):
                self.collect_prompts()
            else:
                print("DONE!!!")
                self.print_root()

    def collect_answers(self):
        print("collect_answers")

        for user_id, user in self.users.items():
            if len(user.questions) > 0:
                user.q = user.questions.pop(0)
                payload = { 'cmd': 'QUESTION', 'txt': user.q.name }
                user.ws.sendMessage(json.dumps(payload))

        t = threading.Timer(self.round_time, self.close_answers)
        t.start()

    def close_prompts(self):
        print("close_prompts")
        self.collect_answers()

    def collect_prompts(self):
        print("collect_prompts")

        for user_id, user in self.users.items():
            if len(user.prompts) > 0:
                user.p = user.prompts.pop(0)
                payload = { 'cmd': 'PROMPT', 'txt': user.p.ques.name }
                user.ws.sendMessage(json.dumps(payload))

        t = threading.Timer(self.round_time, self.close_prompts)
        t.start()

    def print_root(self):
        for pre, fill, node in RenderTree(self.root):
            ans_str = ','.join(map(str, [(ans.user.id, ans.val) for ans in node.answers]))
            print("%s%s,%s %s" % (pre, node.name, node.state, ans_str))

    def print_users(self):
        for user_id, user in self.users.items():
            print("user %d %d - %d" % (user.id, len(user.questions), len(user.prompts)))

    def add_user(self, ws):
        self.user_count += 1 
        self.users[self.user_count] = User(self.user_count, ws)
        return self.user_count

    def handle_msg(self, ws):
        data = json.loads(ws.data)
        print('handle_msg', data)
        cmd = data['cmd']
        if cmd == 'HELLO':
            user_id = self.add_user(ws)
            print("created user %d" % user_id)
            ws.sendMessage(json.dumps({ 'cmd': 'USER', 'id': user_id })) 
        elif cmd == 'ANSWER':
            self.answer_response(data['id'], data['val'])
        elif cmd == 'PROMPT':
            self.prompt_response(data['id'], data['val'])

    def init_questions(self):
        print("init_questions")
        self.add_question(random_txt(), parent=self.root)
        self.print_root()
        self.collect_answers()

    def start(self):
        print("Waiting for users to join ...")
        t = threading.Timer(self.round_time, self.init_questions)
        t.start()
  
def main():
    try:
        consensus_server = ConsensusServer()

        ws_server = ws.WS(consensus_server.handle_msg)
        ws_thread = threading.Thread(target=ws_server.start)
        ws_thread.daemon = True
        ws_thread.start()

        http_server = hs.HTTP()
        http_thread = threading.Thread(target=http_server.start)
        http_thread.daemon = True
        http_thread.start()

        consensus_server.start()

    except KeyboardInterrupt:
        print("^C received, shutting down server")
        ws_server.stop()

if __name__== "__main__":
    main()

