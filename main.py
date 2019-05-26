#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
import threading

from anytree import Node, RenderTree, LevelOrderGroupIter, LevelOrderIter

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

class Question(Node):
  def __init__(self, *args, **kwargs):
    super(self.__class__, self).__init__(*args, **kwargs)
    self.ans_open = True
    self.prompt_open = True
    self.answers = []

  def add_answer(self, ans):
    if self.ans_open:
      self.answers.append(ans)

  def add_question(self, ques):
    global ques_count
    if self.prompt_open:
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

def answer_question(user):
  if len(user.questions) > 0:
    q = user.questions.pop(0)
    time.sleep(random.randint(1, 5))
    print("user %d answers %s" % (user.id, q.name))
    print_root()
    q.add_answer(Answer(user, random.randint(0,1) == 1))

def create_question(user):
  if len(user.prompts) > 0:
    p = user.prompts.pop(0)
    time.sleep(random.randint(1, 5))
    p.ques.add_question(str(ques_count))

#def create_question(node):
#  thread.sleep(random.randint(1, 10))
#  node.add_question(str(ques_count))

def open_answers(is_open):
  questions = [[node for node in children] for children in LevelOrderGroupIter(root)][-1]
  for question in questions:
    question.ans_open = is_open 

def open_prompts(is_open):
  questions = [[node for node in children] for children in LevelOrderGroupIter(root)][-1]
  for question in questions:
    question.prompt_open = is_open 
  
def create_prompt(question, ans):
  ans.user.prompts.append(Prompt(question, ans))

def close_answers():
  print("close_answers")
  #open_answers(False)
  #questions = [[node for node in children] for children in LevelOrderGroupIter(root)][-1]
  questions = list(filter(lambda n : len(n.children) == 0, [node for node in LevelOrderIter(root)]))
  for question in questions:
    if not question.check_consensus():
      print("no consensus")
      print_root()
      for ans in question.answers:
        create_prompt(question, ans)
    else:
      print("omg consensus")
      print_root()
  print_users()
  collect_prompts()

def collect_answers():
  print("collect_answers")
  #open_answers(True)

  for user in users:
    user_thread = threading.Thread(target=answer_question, args=(user,))
    #user_thread.daemon = True
    user_thread.start()

  t = threading.Timer(10, close_answers)
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

  t = threading.Timer(10, close_prompts)
  t.start()

ques_count = 0
#users = [User(1), User(2), User(3)]
users = [User(1), User(2)]
root = Question("Root")

def print_root():
  for pre, fill, node in RenderTree(root):
    ans_str = ','.join(map(str, [(ans.user.id, ans.val) for ans in node.answers]))
    print("%s%s %s" % (pre, node.name, ans_str))

def print_users():
    for user in users:
        print("user %d %d - %d" % (user.id, len(user.questions), len(user.prompts)))

def main():

  root.add_question(str(ques_count))
  root.add_question(str(ques_count))

  collect_answers()
 
if __name__== "__main__":
  main()

