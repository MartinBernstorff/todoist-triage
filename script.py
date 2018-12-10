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

assert sys.argv[1] is not None

print("Starting script")
#Setup pytodoist.todoist
user = todoist.login(USER, PASS)
print("Finished setting up todoist login")

due_tasks = user.get_project(sys.argv[1]).get_tasks()
inbox_tasks = user.get_project("Inbox-tasks")
inbox_flashcards = user.get_project("Inbox-flashcards")
inbox_process_improvements = user.get_project("Inbox-process-improvements")
inbox_considerations = user.get_project("Inbox-considerations")

def spawn_process_task(task, project):
    threading.Thread(target=process_task, args=(task, project)).start()
    l.info("Spawning process to add {} to {}".format(task.content, project.name))

def process_task(task, project):
    l.info("Processing {}".format(task.content))
    if task.content[1] == ":":
        task.content=task.content[3:]
        task.update()
        l.info("{} stripped".format(task.content))

    task.move(project)
    l.info("Finished processing '{}', \nmoved to {}".format(task.content, project.name))

def task_to_project(task, project):
    task.move(project)

def categorize(task):
    if task.content[0:3] == "F: ": #If flashcard
        spawn_process_task(task, inbox_flashcards)
    elif task.content[0:3] == "I: ": #If process improvement
        spawn_process_task(task, inbox_process_improvements)
    elif task.content[0:3] == "C: ": #If consideration
        spawn_process_task(task, inbox_considerations)
    else:
        spawn_process_task(task, inbox_tasks)

for task in due_tasks:
    os.system("clear")
    print("\n" * 2)
    print("    " + task.content)

    text = input("\n    [D]elete? [I]mportant? [N]ecessary?\n\n\n    ")

    if text == "I":
        categorize(task)
        continue
    elif text == "N":
        categorize(task)
    elif text == "D":
        threading.Thread(target=task.delete).start()
        l.info("Deleted {}".format(task.content))
    elif text == ("IF" or "NF"):
        spawn_process_task(task, inbox_flashcards)
    elif text == ("II" or "NI"):
        spawn_process_task(task, inbox_process_improvements)
    elif text == ("IC" or "NC"):
        spawn_process_task(task, inbox_considerations)
    else:
        l.ERROR("Incorrect type")

os.system("clear")
