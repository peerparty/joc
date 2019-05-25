#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import time
import threading

from anytree import Node, RenderTree, LevelOrderGroupIter

class User:
  questions = []
  prompts = []

class Prompt:
  ques = None
  ans = None
  def __init__(self, ques, ans):
    self.ques = ques 
    self.ans = ans 

class Answer:
  user = None 
  val = False

  def __init__(self, user, val):
    self.user = user
    self.val = val

class Question(Node):
  ans_open = True
  prompt_open = True
  answers = []

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
    time.sleep(random.randint(1, 10))
    q.add_answer(Answer(user, random.randint(0,1) == 1))

def create_question(user):
  if len(user.prompts) > 0:
    p = user.prompts.pop(0)
    time.sleep(random.randint(1, 10))
    p.ques.add_question(str(ques_count))

#def create_question(node):
#  thread.sleep(random.randint(1, 10))
#  node.add_question(str(ques_count))

def open_answers(is_open):
  questions = [[node for node in children] for children in LevelOrderGroupIter(root)]
  for question in questions[-1]:
    question.ans_open = is_open 

def open_prompts(is_open):
  questions = [[node for node in children] for children in LevelOrderGroupIter(root)]
  for question in questions[-1]:
    question.prompt_open = is_open 
  
def create_prompt(question, ans):
  ans.user.prompts.append(Prompt(question, ans))

def close_answers():
  print("close_answers")
  print_root()
  open_answers(False)
  questions = [[node for node in children] for children in LevelOrderGroupIter(root)]
  for question in questions[-1]:
    if not question.check_consensus():
      print("no consensus")
      print_root()
      for ans in question.answers:
        create_prompt(question, ans)
    else:
      print("omg consensus")
      print_root()
  collect_prompts()

def collect_answers():
  print("collect_answers")
  print_root()
  open_answers(True)
  for user in users:
    user_thread = threading.Thread(target=answer_question, args=(user,))
    #user_thread.daemon = True
    user_thread.start()

  t = threading.Timer(5, close_answers)
  t.start()

def close_prompts():
  print("close_prompts")
  print_root()
  open_prompts(False)
  collect_answers()

def collect_prompts():
  print("collect_prompts")
  print_root()
  open_prompts(True)
  for user in users:
    user_thread = threading.Thread(target=create_question, args=(user,))
    #user_thread.daemon = True
    user_thread.start()

  t = threading.Timer(5, close_prompts)
  t.start()

ques_count = 0
users = [User(), User(), User()]
root = Question("Root")

def print_root():
  for pre, fill, node in RenderTree(root):
#    ans_str = for  
    print("%s%s" % (pre, node.name))

def main():

  root.add_question(str(ques_count))
  root.add_question(str(ques_count))

  collect_answers()
 
if __name__== "__main__":
  main()

