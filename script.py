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

##########################
# Get tasks and projects #
##########################

due_tasks = user.get_project(sys.argv[1]).get_tasks()
inbox_tasks = user.get_project("Inbox-tasks")
inbox_flashcards = user.get_project("Inbox-flashcards")
inbox_process_improvements = user.get_project("Inbox-process-improvements")
inbox_considerations = user.get_project("Inbox-considerations")

#####################
# Utility functions #
#####################

def task_to_project(task, project):
    task.move(project)
    l.info("{} received '{}'").format(project.name, task.content)

def spawn_process(function, args):
    """
        Spawns a new process.
        Takes 2 args:
            function to run
            args [tuple]
    """
    threading.Thread(target=function, args=args).start()
    l.info("Spawning process with function: {}\n args: {}".format(function, args))

####################
# Script functions #
####################

def process_no_prefix(task):
    task_string = task.content
    project = None
    response = input("\n    Date?\n    @context? [@f/@h/@b/@c/@a]\n\n\n    ")

    contexts = {
        "@focus",
        "@home",
        "@børglum",
        "@computer",
        "@anywhere"
    }

    for context in contexts:
        if context[0:2] in response:
            task_string += " " + context
            task_string +=" #Actionable"

    user.quick_add(task_string)
    task.delete()

def process_prefixed(task):
    project = None

    if task.content[0] == "F": #If flashcard
        project = inbox_flashcards
    elif task.content[0] == "I": #If process improvement
        project = inbox_process_improvements
    elif task.content[0] == "C": #If consideration
        project = inbox_considerations

    task.content = task.content[3:]
    task.update()
    spawn_process_task(task_to_project, (task, project))

for task in due_tasks:
    os.system("clear")
    print("\n" * 2)
    print("    " + task.content)

    response = input("\n    [D]elete?/[I]mportant?/[N]ecessary? ([F/I/C])\n\n\n    ")

    if response[0] == ("I" or "N"):
        if task.content[1:3] == ": ": ## If contains colon, categorize by prefix
            process_prefixed(task)
        if len(response) == "2": ## Categorise as sub-type if necessary
            if response[1] == "F":
                spawn_process_task(task_to_project, (task, inbox_flashcards))
            elif response[1] == "I":
                spawn_process_task(task_to_project, (task, inbox_process_improvements))
            elif response[1] == "C":
                spawn_process_task(task_to_project, (task, inbox_considerations))
        else:
            process_no_prefix(task)

    elif text == "D":
        threading.Thread(target=task.delete).start()
        l.info("Deleted {}".format(task.content))

    else:
        l.ERROR("Incorrect type")

os.system("clear")
