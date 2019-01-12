import logging
from datetime import datetime
from pytodoist import todoist
from credentials import USER, PASS, AIRTABLE_API_KEY
from pynput import keyboard

from airtable import Airtable
from time import sleep
import os
import sys
import re
import threading
import time

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

airtable = Airtable("apphAhOCdt16lulNj", "Process-improvements", api_key=AIRTABLE_API_KEY)

#####################
# Utility functions #
#####################

def task_to_project(task, project):
    task.move(project)
    l.info("{} received '{}'".format(project.name, task.content))

def quick_add_task(task_string):
    user.quick_add(task_string)

def delete_task(task):
    task.delete()

def update_and_task_to_project(task, project):
    task.update()
    task.move(project)
    l.info("{} received '{}'".format(project.name, task.content))

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
def add_improvement(task):
    airtable.insert({"Description": task.content,
                     "Phase": "Incubating"})
    task.delete()

def process_no_prefix(task):
    l.info("Processing without prefix")
    task_string = task.content
    project = None
    response = input("\n    Date? [+t/+xd/+xw/+xm/+xy]\n    @context? [@f/@h/@b/@c/@a]\n\n\n    ")

    contexts = {
        "@fokus",
        "@home",
        "@børglum",
        "@computer",
        "@anywhere"
    }

    for context in contexts: # Check for context matches
        if context[0:2] in response:
            task_string += " " + context
            task_string +=" #Actionable"

    if "+t" in response:
        task_string += " today"

    time_units = [
        "day",
        "week",
        "month",
        "year"
    ]

    for time_unit in time_units:
        if re.search("\+[\d]*" + time_unit[0], response):
            digit_matches = re.findall("[\d]*", response)
            digits = ""
            for digit in digit_matches:
                if len(digit) is not 0:
                    digits += digit

            task_string += " +" + digits + time_unit
            l.info("Date matched: ".format(task_string))

    if "#" not in task_string:
        task_string += " #Inbox-tasks"

    l.info("Adding: \n'{}'".format(task_string))
    spawn_process(quick_add_task, (task_string,))
    spawn_process(delete_task, (task,))

def process_prefixed(task):
    l.info("Processing as prefixed")
    project = None

    if task.content[0] == "F": #If flashcard
        project = inbox_flashcards
    elif task.content[0] == "I": #If process improvement
        task.content = task.content[3:]
        add_improvement(task)
        return
    elif task.content[0] == "C": #If consideration
        project = inbox_considerations

    task.content = task.content[3:]
    spawn_process(update_and_task_to_project, (task, project))

def process_suffixed(task):
    l.info("Processing as suffixed")
    project = None

    if task.content[-2:-1] == "I": #If process improvement
        task.content = task.content[0:-2]
        add_improvement(task)
        return
    elif task.content[-1:] == "?": #If consideration
        project = inbox_considerations
        task.content = task.content[0:-1]

    spawn_process(update_and_task_to_project, (task, project))

i = 0

for task in due_tasks:
    i += 1
    if len(task.get_notes()) != 0:
        l.info("{} has note(s), skipping".format(task.content))
        spawn_process(task_to_project, (task, inbox_tasks))
        continue

    if task.due_date_utc is not None: # No due_date handling implemented, if task has due date, move and skip
        l.info("{} has a due date, skipping".format(task.content))
        spawn_process(task_to_project, (task, inbox_tasks))
        continue

    elif task.content[0:3] == "F: ": # If flashcard, just send straight to flashcards. Pruning can happen later.
        l.info("{} is a flashcard, moving".format(task.content))
        spawn_process(process_prefixed, (task,))
        time.sleep(0.3)
        continue

    os.system("clear")
    print("\n" * 1)
    print("    " + "[{}/{}]: ".format(i, len(due_tasks)) + task.content)

    response = ""
    while response == "":
        response = input("\n     [D]elete?/[I]mportant?/[N]ecessary? ([F/I/C]) \n\n\n   ")
    l.info("Response length {}".format(len(response)))

    if response[0] in ("I", "N"):
        l.info("Processing as {}".format(response[0]))

        if len(response) == 2: ## Categorise as sub-type if necessary
            l.info("Processing as sub-type")
            if response[1] == "F":
                spawn_process(task_to_project, (task, inbox_flashcards))
            elif response[1] == "I":
                spawn_process(add_improvement, (task,))
            elif response[1] == "C":
                spawn_process(task_to_project, (task, inbox_considerations))
        elif task.content[1:3] == ": ": ## If contains colon, categorize by prefix
            process_prefixed(task)
        elif task.content[-1:] == ":" or task.content[-1:] == "?": ## If contains colon, categorize by prefix
            process_suffixed(task)
        else:
            process_no_prefix(task)

    elif response == "D":
        threading.Thread(target=task.delete).start()
        l.info("Deleted {}".format(task.content))

    else:
        l.critical("Incorrect type")

os.system("clear")
