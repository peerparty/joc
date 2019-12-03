from functools import reduce
from anytree import Node, RenderTree, LevelOrderGroupIter, LevelOrderIter, PostOrderIter
from anytree.exporter import DictExporter
from enum import IntEnum

import random
import string
import time
import threading
import json
import sys

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

class QuestionState(IntEnum):
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
    def __init__(self, cm):
        self.answer_time = 30 
        self.prompt_time = 60 
        self.session_time = 600 
        #self.answer_time = 2 
        #self.prompt_time = 2 
        self.users = {} 
        self.user_count = 0
        self.ques_count = 0
        self.consensus_stmts = []
        self.root = Question("Root", id=self.ques_count)

        self.cm = cm

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
        prompt = prompt.strip()
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
                self.consensus_stmts.append(question.name)
                self.cm.send_consensus(question.name)
                question.state = QuestionState.CLOSED 
                self.sibling_consensus(question)
                self.cm.screencast({ 'cmd': 'SCREEN_CONSENSUS', 'data': question.name })

    def hanging_prompts(self, questions):
        for question in questions:
            question.state = QuestionState.REASKED 

            # Requires more testing this one - JBG
            if question.parent:
                self.add_question(question.name, parent=question.parent)
            #else:
            #    self.send_done()

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
            #print('sending done', user_id)
            payload = { 'cmd': 'USER_DONE', 'data': self.consensus_stmts }
            user.ws.sendMessage(json.dumps(payload))
        self.cm.next_round()

    def broadcast_tutorial(self):
        for user_id, user in self.users.items():
            payload = { 'cmd': 'USER_TUTORIAL' }
            user.ws.sendMessage(json.dumps(payload))

    def broadcast_questions(self):
        for user_id, user in self.users.items():
            payload = { 'cmd': 'USER_ANSWERS' }
            user.ws.sendMessage(json.dumps(payload))
            if len(user.questions) > 0:
                user.q = user.questions.pop(0)
                payload = {
                    'cmd': 'USER_QUESTION',
                    'txt': user.q.name,
                    'time': self.answer_time
                }
                user.ws.sendMessage(json.dumps(payload))

    def collect_answers(self):
        #print("collect_answers")
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
                    'cmd': 'USER_PROMPT',
                    'txt': user.p.ques.name,
                    'ans': user.p.ans.val,
                    'time': self.prompt_time
                }
                user.ws.sendMessage(json.dumps(payload))

    def collect_prompts(self):
        #print("collect_prompts")
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
        exporter = DictExporter()
        self.cm.screencast({
            'cmd': 'SCREEN_TREE',
            'data': exporter.export(self.root)
        })

    def print_users(self):
        for user_id, user in self.users.items():
            print("user %d %d - %d" % (
                user.id,
                len(user.questions),
                len(user.prompts)))

    def add_user(self, ws):
        self.user_count += 1 
        user = User(ws.user_id, ws)
        self.users[ws.user_id] = user
        if self.user_count > 1:
            self.broadcast_new_user()
        self.cm.screencast({
            'cmd': 'SCREEN_USER_JOIN',
            'id': ws.user_id,
            'count': self.user_count
        })
        return user 

    def rm_user(self, ws):
      if ws.user_id in self.users and self.user_count > 0:
        print("REMOVING USER", ws.user_id, self.user_count)
        self.user_count -= 1 
        del self.users[ws.user_id]
        if self.user_count < 2: 
            for user_id, user in self.users.items():
                payload = { 'cmd': 'USER_NOT_ENOUGH' }
                user.ws.sendMessage(json.dumps(payload))
            self.cm.next_round()
        self.cm.screencast({ 'cmd': 'SCREEN_USER_QUIT', 'id': ws.user_id })

    def broadcast_new_user(self):
        self.user_responses = {} 
        for user_id, user in self.users.items():
            payload = {
                'cmd': 'USER_JOIN',
                'count': len(self.users)
            }
            user.ws.sendMessage(json.dumps(payload))

    def broadcast_wait(self):
        for user_id, user in self.users.items():
            payload = { 'cmd': 'USER_WAIT' }
            user.ws.sendMessage(json.dumps(payload))
    
    def check_start(self, user_id, val):

        self.user_responses[user_id] = val
        if (len(self.user_responses) == len(self.users) and
            sum(self.user_responses.values()) == len(self.users)):
            self.cm.start_cs()
        elif len(self.user_responses) == len(self.users):
          self.broadcast_not_enough()
        
    def end_session(self): 
        self.send_done()

    def broadcast_not_enough(self):
      for user_id, user in self.users.items():
          payload = { 'cmd': 'USER_NOT_ENOUGH' }
          user.ws.sendMessage(json.dumps(payload))
      self.cm.not_enough()

    def start(self, stmt):
        #print("init_questions")
        #print("Enter the starting question:")
        #question = input()
        if len(self.users) > 1:        
            self.add_question(stmt, parent=self.root)
            self.print_root()
            self.collect_answers()
        else:
            broadcast_not_enough()
        t = threading.Timer(self.session_time, self.end_session)
        t.start()


