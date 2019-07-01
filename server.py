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

from functools import reduce
from anytree import Node, RenderTree, LevelOrderGroupIter, LevelOrderIter, PostOrderIter
from enum import Enum

# Used for testing - JBG
test = False 
user_time = 1
test_ans = [True, False, True, False, True, True, False, False, False, True, False, True, False, True, False, True, False, False, True, True, True, False, True, True, True, True, True, True, False, True, False, True, False, False, True, False, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]
test_count = 0
test_input = []

def random_txt():
  return ''.join(
      random.choice(string.ascii_uppercase + string.digits)
      for _ in range(32)
  )

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
            #print("check consensus " + str(answer.val))
            if answer.val:
                count_yes += 1
            else:
                count_no += 1
        return (
            (count_yes > 0 and count_no == 0)
            or (count_no > 0 and count_yes == 0)
        )

class ConsensusServer:
    def __init__(self):
        self.answer_time = 15 
        self.prompt_time = 30 
        #self.answer_time = 2 
        #self.prompt_time = 2 
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
        self.print_root()

    def prompt_response(self, user_id, prompt):
        user = self.users[user_id]
        if len(prompt) > 0: 
            self.add_question(prompt, user.p.ques)
        self.print_root()

    def get_height(self):
        return len([[node for node in children]
              for children in LevelOrderGroupIter(root)])

    def get_siblings(self, question):
        return question.parent.children

    def sibling_consensus(self, question):
        sibs = self.get_siblings(question)
        sibs = list(filter(lambda q : not q.state == QuestionState.REASKED,
            sibs))
        #print("SIBS %s" % [node.name for node in sibs])
        #if len(sibs) > 1 and reduce(lambda a, q :
        #    q.check_consensus() and a, sibs, True):
        if reduce(lambda a, q : q.check_consensus() and a, sibs, True):
            parent = question.parent
            if parent == self.root:
                print("We should be done here.")
            elif not parent.state == QuestionState.REASKED:
                #print("the reask %s %s" % (parent.name, parent.state))
                parent.state = QuestionState.REASKED 
                self.add_question(parent.name, parent=parent.parent)

    def create_prompt(self, question, ans):
        ans.user.prompts.append(Prompt(question, ans))

    def open_questions(self, questions):
        for question in questions:
            if not question.check_consensus():
                #print("no consensus %s" % question.name)
                question.state = QuestionState.PROMPTED 
                for ans in question.answers:
                    self.create_prompt(question, ans)
            else:
                #print("omg consensus %s" % question.name)
                question.state = QuestionState.CLOSED 
                self.sibling_consensus(question)

    def hanging_prompts(self, questions):
        for question in questions:
            question.state = QuestionState.REASKED 
            self.add_question(question.name, parent=question.parent)

    def close_answers(self):
        q_size = reduce(lambda c, user : c + len(user.questions),
            list(self.users.values()), 0)
        if(q_size > 0):
            self.collect_answers()
        else:
            questions = list(filter(lambda n : n.state == QuestionState.OPEN,
                [node for node in PostOrderIter(self.root)]))
            if len(questions) > 0:
                self.open_questions(questions)
            else:
                questions = list(filter(lambda n :
                    n.state == QuestionState.PROMPTED,
                    [node for node in PostOrderIter(self.root)]))
                self.hanging_prompts(questions)

            self.print_root()
            #self.print_users()

            p_size = reduce(lambda c, user : c + len(user.prompts),
                list(self.users.values()), 0)
            q_size = reduce(lambda c, user : c + len(user.questions),
                list(self.users.values()), 0)
            if(p_size > 0):
                self.collect_prompts()
            elif(q_size > 0):
                self.collect_answers()
            else:
                self.send_done()
                print("DONE!!!")
                self.root.state = QuestionState.CLOSED
                self.print_root()
                time.sleep(self.answer_time)

    def send_done(self):
        for user_id, user in self.users.items():
            if not test:
                #print('sending done', user_id)
                payload = { 'cmd': 'DONE' }
                user.ws.sendMessage(json.dumps(payload))

    def test_answer(self, user):
        #print("test_answer")
        global test_count
        global test_ans
        global test_input
        if len(user.questions) > 0:
            user.q = user.questions.pop(0)
            time.sleep(random.randint(1, user_time))
            #ans = (False if self.ques_count > 100
            #    else random.randint(0,1) == 1)
            ans = (False if test_count >= len(test_ans)
                else test_ans[test_count])
            #print("User %d answered: %s on %d" % (user.id, ans, test_count))
            test_count += 1 
            user.q.add_answer(Answer(user, ans))
            test_input.append(ans)

    def test_answers(self):
        for user_id, user in self.users.items():
            user_thread = threading.Thread(target=self.test_answer,
                args=(user,))
            #user_thread.daemon = True
            user_thread.start()

    def broadcast_questions(self):
        for user_id, user in self.users.items():
            payload = { 'cmd': 'ANSWERS' }
            user.ws.sendMessage(json.dumps(payload))
            if len(user.questions) > 0:
                user.q = user.questions.pop(0)
                payload = { 'cmd': 'QUESTION', 'txt': user.q.name }
                user.ws.sendMessage(json.dumps(payload))

    def collect_answers(self):
        #print("collect_answers")
        global test
        if test:
            self.test_answers()
        else:
            self.broadcast_questions()

        t = threading.Timer(self.answer_time, self.close_answers)
        t.start()

    def close_prompts(self):
        #print("close_prompts")
        self.collect_answers()

    def broadcast_prompts(self):
        for user_id, user in self.users.items():
            if len(user.prompts) > 0:
                user.p = user.prompts.pop(0)
                payload = {
                    'cmd': 'PROMPT',
                    'txt': user.p.ques.name,
                    'ans': user.p.ans.val
                }
                user.ws.sendMessage(json.dumps(payload))

    def test_prompt(self, user):
        #print('test_prompt')
        if len(user.prompts) > 0:
            user.p = user.prompts.pop(0)
            time.sleep(random.randint(1, user_time))
            self.add_question(random_txt(), user.p.ques)

    def test_prompts(self):
        for user_id, user in self.users.items():
            user_thread = threading.Thread(target=self.test_prompt,
                args=(user,))
            #user_thread.daemon = True
            user_thread.start()

    def collect_prompts(self):
        #print("collect_prompts")
        global test
        if test:
            self.test_prompts()
        else:
            self.broadcast_prompts()

        t = threading.Timer(self.prompt_time, self.close_prompts)
        t.start()

    def get_emoji(self, state):
        if state == QuestionState.OPEN:
            return '🙋'
        elif state == QuestionState.CLOSED:
            return '🌈'
        elif state == QuestionState.REASKED:
            return '↩️ '
        else:
            return '🤔'
        

    def print_root(self):
        for pre, fill, node in RenderTree(self.root):
            ans_str = ','.join(map(str,
                [(ans.user.id, ans.val) for ans in node.answers]))
            print("%s%s,%s %s" % (pre, self.get_emoji(node.state), node.name, ans_str))

    def print_users(self):
        for user_id, user in self.users.items():
            print("user %d %d - %d" % (
                user.id,
                len(user.questions),
                len(user.prompts)))

    def add_user(self, ws):
        self.user_count += 1 
        self.users[self.user_count] = User(self.user_count, ws)
        return self.user_count

    def test_users(self):
        self.user_count += 1
        self.users[self.user_count] = User(self.user_count, None)
        self.user_count += 1
        self.users[self.user_count] = User(self.user_count, None)
        #print("%d Test users ..." % (len(self.users)))

    def handle_msg(self, ws):
        data = json.loads(ws.data)
        #print('handle_msg', data)
        cmd = data['cmd']
        if cmd == 'HELLO':
            user_id = self.add_user(ws)
            #print("created user %d" % user_id)
            ws.sendMessage(json.dumps({ 'cmd': 'USER', 'id': user_id })) 
        elif cmd == 'ANSWER':
            self.answer_response(data['id'], data['val'])
        elif cmd == 'PROMPT':
            self.prompt_response(data['id'], data['val'])

    def init_questions(self):
        #print("init_questions")
        print("Enter the starting question:")
        question = input()
        self.add_question(question, parent=self.root)
        self.print_root()

        self.collect_answers()

    def start(self):
        if test:
          self.test_users()
        self.init_questions()
        #t = threading.Timer(self.round_time, self.init_questions)
        #t.start()
  
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

