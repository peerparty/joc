#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
import threading

from functools import reduce
from anytree import Node, RenderTree, LevelOrderGroupIter, LevelOrderIter, PostOrderIter
from enum import Enum

round_time = 2 
user_time = 1 

class User:
    def __init__(self, user_id):
        self.questions = []
        self.prompts = []
        self.id = user_id 

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
        self.answers = []
        self.state = QuestionState.OPEN

    def add_answer(self, ans):
        self.answers.append(ans)

    def add_question(self, ques):
        global ques_count
        ques_count += 1
        q = Question(ques, parent=self)

        for user in users:
            user.questions.append(q)

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

#test_ans = [True, False, True, False, False, False, False, False, False, False]
test_ans = [True, False, True, False, True, True, False, False, False, True, False, True, False, True, False, True, False, False, True, True, True, False, True, True, True, True, True, True, False, True, False, True, False, False, True, False, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]

test_count = 0
test_input = []

def answer_question(user):
    global test_count
    global test_ans
    global test_input
    if len(user.questions) > 0:
        q = user.questions.pop(0)
        time.sleep(random.randint(1, user_time))
        #q.add_answer(Answer(user, random.randint(0,1) == 1))
        #q.add_answer(Answer(user, False if test_count >= len(test_ans) else test_ans[test_count]))
        ans = False if ques_count > 100 else random.randint(0,1) == 1
        q.add_answer(Answer(user, ans))
        test_input.append(ans)
        test_count += 1
        print("user %d answers %s" % (user.id, q.name))

def create_question(user):
    if len(user.prompts) > 0:
        p = user.prompts.pop(0)
        time.sleep(random.randint(1, user_time))
        p.ques.add_question(str(ques_count))

#def create_question(node):
#    thread.sleep(random.randint(1, 10))
#    node.add_question(str(ques_count))

#def open_answers(is_open):
#    questions = [[node for node in children] for children in LevelOrderGroupIter(root)][-1]
#    for question in questions:
#        question.ans_open = is_open 
#
#def open_prompts(is_open):
#    questions = [[node for node in children] for children in LevelOrderGroupIter(root)][-1]
#    for question in questions:
#        question.prompt_open = is_open 
# 

def get_height():
    return len([[node for node in children] for children in LevelOrderGroupIter(root)])

def get_siblings(question):
    return question.parent.children
    #questions = [[node for node in children] for children in LevelOrderGroupIter(root)]
    #for level in questions:
    #    if question in level:
    #        return level 

def sibling_consensus(question):
    sibs = get_siblings(question)
    sibs = list(filter(lambda q : not q.state == QuestionState.REASKED, sibs))
    print("SIBS %s" % [node.name for node in sibs])
    if len(sibs) > 1 and reduce(lambda a, q : q.check_consensus() and a, sibs, True):
        parent = question.parent
        if not parent.state == QuestionState.REASKED:
            print("the reask %s %s" % (parent.name, parent.state))
            parent.state = QuestionState.REASKED 
            parent.parent.add_question(parent.name)

def create_prompt(question, ans):
    ans.user.prompts.append(Prompt(question, ans))

def close_answers():
    q_size = reduce(lambda c, user : c + len(user.questions), users, 0)
    if(q_size > 0):
        collect_answers()
    else:
        questions = list(filter(lambda n : n.state == QuestionState.OPEN, [node for node in PostOrderIter(root)]))
        for question in questions:
            if not question.check_consensus():
                print("no consensus %s" % question.name)
                question.state = QuestionState.PROMPTED 
                for ans in question.answers:
                    create_prompt(question, ans)
            else:
                print("omg consensus %s" % question.name)
                question.state = QuestionState.CLOSED 
                sibling_consensus(question)
        print_root()
        print_users()


        q_size = reduce(lambda c, user : c + len(user.prompts) + len(user.questions), users, 0)
        if(q_size > 0):
            collect_prompts()
        else:
            print("DONE!!!")
            print_root()
            global test_input
            print(test_input)

def collect_answers():
    print("collect_answers")
    #open_answers(True)

    for user in users:
        user_thread = threading.Thread(target=answer_question, args=(user,))
        #user_thread.daemon = True
        user_thread.start()

    t = threading.Timer(round_time, close_answers)
    t.start()

def close_prompts():
    print("close_prompts")
    #open_prompts(False)
    collect_answers()

def collect_prompts():
    print("collect_prompts")
    #open_prompts(True)
    for user in users:
        user_thread = threading.Thread(target=create_question, args=(user,))
        #user_thread.daemon = True
        user_thread.start()

    t = threading.Timer(round_time, close_prompts)
    t.start()

ques_count = 0
#users = [User(1), User(2), User(3)]
users = [User(1), User(2)]
root = Question("Root")

def print_root():
    for pre, fill, node in RenderTree(root):
        ans_str = ','.join(map(str, [(ans.user.id, ans.val) for ans in node.answers]))
        print("%s%s,%s %s" % (pre, node.name, node.state, ans_str))

def print_users():
    for user in users:
        print("user %d %d - %d" % (user.id, len(user.questions), len(user.prompts)))

def main():

    root.add_question(str(ques_count))
    #root.add_question(str(ques_count))

    collect_answers()
 
if __name__== "__main__":
    main()

