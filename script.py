import logging
from datetime import datetime
from pytodoist import todoist
from credentials import USER, PASS
from pynput import keyboard
import os
import sys
import threading

#Setup loggging
FORMAT = '%(asctime)-15s, %(levelname)s: %(message)s'
logging.basicConfig(filename="triage.log", level=logging.INFO, format=FORMAT)
l = logging.getLogger(__name__)

print("Starting script")
#Setup pytodoist.todoist
user = todoist.login(USER, PASS)
print("Finished setting up todoist login")

due_tasks = user.get_project(sys.argv[1]).get_tasks()
inbox_tasks = user.get_project("Inbox-tasks")
inbox_flashcards = user.get_project("Inbox-flashcards")
inbox_process_improvements = user.get_project("Inbox-process-improvements")

def strip_prefix_and_move(task, project):
    task.content= task.content[3:]
    task.update()
    task.move(project)
    l.info("{} stripped and moved".format(task.content))

def task_to_project(task, project):
    task.move(project)

for task in due_tasks:
    os.system("clear")
    print("\n" * 3)
    print(task.content)

    if task.content[0:3] == "F: ": #If flashcard
        threading.Thread(target=strip_prefix_and_move,
                         args=(task, inbox_flashcards)).start()
        continue
    elif task.content[0:3] == "I: ": #If process improvement
        threading.Thread(target=strip_prefix_and_move,
                         args=(task, inbox_process_improvements)).start()
        continue

    text = input("\n[I]mportant? [N]ecessary? [D]elete? \n\n\n")

    if text == "I":
        threading.Thread(target=task_to_project,
                         args=(task, inbox_tasks)).start()
    elif text == "N":
        threading.Thread(target=task_to_project,
                         args=(task, inbox_tasks)).start()
    elif text == "D":
        threading.Thread(target=task.delete).start()
        l.info("Deleted {}".format(task.content))
    else:
        l.ERROR("Incorrect type")

os.system("clear")
