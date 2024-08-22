from discord_webhook import DiscordWebhook
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import requests
import random
import datetime
import json
import aiohttp
import asyncio

# Reddit Server webhook
WEBHOOK = "<YOUR WEBHOOK HERE"

# Below webhook is for local debugging

VERBOSE = True
RUN_TEST = False


VOTE_MINUTE = 0
VOTE_SECOND = 2

DELAY_VOTES_TIME = 0.33

now = datetime.datetime.now(datetime.UTC)
# random.seed(now.hour)
print(now.hour)
VOTE_PERCENT_FOR_MAIN = 100 
print("RUNNING VOTING WITH {} PERCENT FOR MAIN".format(VOTE_PERCENT_FOR_MAIN))
TRACK_SECOND = os.path.exists('track_second.txt')

# LOGGING SETTINGS
LIVE_LOGGING = False
TARGET_INDEX = 0 # breaking it for now at the end of the hour
print("TARGET INDEX: {}".format(TARGET_INDEX))

bad_emails = set()
bad_passwords = set()
successful_votes = set()
ostracized_votes = set()
duplicate_votes = set()
cred_tokens = set()

invalid_tokens = set()
duplicate_tokens = set()
ostracized_tokens = set()

all_emails = []
all_passwords = []
all_tokens = []
priority_list = []
email_token_lookup = {}

def create_vote_task(recaptcha, type="ostracize"):
    current_target = get_target()

    if current_target == "SKIP":
        return None
    
    if len(all_tokens) > 0:
        current_token = all_tokens.pop(0)
    else:
        populate_creds()
        return None

    payload = {
        'type': type,
		'username': current_target,
		'recaptcha': recaptcha,
		'token':	current_token
    }

    print(f"Adding task #{len(vote_tasks)}: {len(all_tokens)} tokens left", current_target, current_token)
    return payload

def update_priority_list():
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/ostracizedPlayers"
 
    response = requests.get(url)
    jsonData = response.json()

    players = jsonData['players']

    ostracized_players = []

    for player in players:
        ostracized_players.append(player['username'])

    # Get our current priority list
    with open('priority_list.txt', 'r') as f:
        priority_list = f.read().splitlines()  
    
    # Remove players that are ostracized
    for user in priority_list:
        if user in ostracized_players:
            print(f"Removing {user}")
            priority_list.remove(user)

    with open('priority_list.txt', 'w') as f:
        f.write('\n'.join(priority_list))

    return priority_list

def clean_priority_list():
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/players?type=ostracize&quantity=11000&startIndex=0&reversed=true"
 
    response = requests.get(url)
    jsonData = response.json()

    players = jsonData['players']

    living_players = []

    for p in players:
        living_players.append(p['username'])
    
    # Get our current priority list
    with open('priority_list.txt', 'r') as f:
        priority_list = f.read().splitlines()  
    
    # Remove players that are ostracized
    for user in priority_list:
        if user not in living_players:
            print(f"Removing {user}")
            priority_list.remove(user)

    with open('priority_list.txt', 'w') as f:
        f.write('\n'.join(priority_list))
    
    return priority_list

def get_target():
    global priority_list, TARGET_INDEX, TRACK_SECOND, VOTE_PERCENT_FOR_MAIN
    if VOTE_PERCENT_FOR_MAIN == 100:
        return priority_list[TARGET_INDEX]
    target_index = int(round((random.randint(0, 100) / VOTE_PERCENT_FOR_MAIN))-1)
    return priority_list[max(0, target_index)]

def populate_creds():   
    # Read in all token creds
    with open(f"tokens_{instance_id}.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            parts = line.split(",")
            if len(line) > 0:
                all_tokens.append(parts[-1])
    
    # Read in all token creds from cred_tokens.txt
    with open(f"cred_tokens_{instance_id}.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            parts = line.split(",")
            if len(line) > 0:
                all_tokens.append(parts[-1])
    
    
    # Shuffle all tokens
    # random.shuffle(all_tokens)

async def single_async_vote(session, payload):
    global priority_list
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/vote"

    payload['username'] = get_target()
    async with session.post(url, json=payload) as response:
        data = await response.json()
        with open("logging.txt", "a") as f:
            f.write("\n")
            f.write(str(data) + str(payload["username"]))
            f.write("\n")
            f.write(str(payload["token"]))
            
async def cast_async_votes(tasks):
    global priority_list, TARGET_INDEX
    print("In cast async votes. Num Tasks:", len(tasks))

    async with aiohttp.ClientSession() as session:
        post_tasks = []

        # Get top name from ostracize list
        url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/players?type=ostracize&quantity=1&startIndex=0&reversed=true"
        top_player = requests.get(url).json()['players'][0]
        top_name = top_player['username']
        top_score = top_player['score']
        
        # priority_list = update_priority_list()
        # await asyncio.sleep(0.1)

        # if the top score is top name on our priority list move name to back of list
        if top_name == priority_list[0] and TARGET_INDEX == 0:
            name = priority_list.pop(0)
            priority_list.append(name)


        for t in tasks:
            post_tasks.append(single_async_vote(session, t))

        # Wait for website to finish updating
        awaiting_api_availability = True
        url = f"https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/playerDetails?username={top_name}"
        while awaiting_api_availability:
            num_votes = requests.get(url).json()['details']['ostracizeScore']
            if num_votes is None:
                awaiting_api_availability = False
            elif num_votes < top_score:
                awaiting_api_availability = False
            
        #TODO: If we move to a schedule we can create all these tasks before checking for availability

        # while time.time() - voting_start < DELAY_VOTES_TIME:
        #     await asyncio.sleep(0.01)
        now_string = datetime.datetime.now().strftime('%M:%S')

        # Execute all tasks at once
        # print("IN FUNCTION TIME: ", time.time() - voting_start)
        await asyncio.gather(*post_tasks)

        msg = f"Instance {instance_id} sent votes at " + now_string
        webhook = DiscordWebhook(url=WEBHOOK, content=msg)
        webhook.execute()   

if __name__ == "__main__":
    # Read the instance id from id.txt
    with open('id.txt', 'r') as f:
        instance_id = f.readline().strip('\n')
    print("Instance ID: ", instance_id)

    curr_time = datetime.datetime.now()

    # Create the running file to prevent other scripts starting up
    with open('running.txt', 'w') as f:
        f.write("Running")

    print("CLEANING PRIORITY LIST")
    update_priority_list()
    time.sleep(3)
    clean_priority_list()
    time.sleep(3)
    priority_list = clean_priority_list()

    time.sleep(random.randint(0, 10))
    # now = datetime.datetime.now()
    # webhook = DiscordWebhook(url=WEBHOOK, content=f"Rapid auto-voter {instance_id} started at " + now.strftime("%M:%S") + " with top targets " + str(priority_list[:min(len(priority_list), 3)]))
    # webhook.execute()   

    with open('logging.txt', 'w') as f:
        f.truncate()
        f.write(now.strftime("%H:%M:%S") + "\n")
    
    populate_creds()

    # Generate post tasks up until the top of the hour
    cred_count = len(all_tokens)
    vote_tasks = []

    if not RUN_TEST:
        while curr_time.minute < 58:
            curr_time = datetime.datetime.now()

    while curr_time.minute > VOTE_MINUTE or curr_time.second < VOTE_SECOND or RUN_TEST:
        curr_time = datetime.datetime.now()

        with open('recaptchas.txt', 'r') as f:
            lines = f.readlines()

            for recaptcha in lines: 
                if len(vote_tasks) >= cred_count*2:
                    # Remove oldest votes which are most likely to fail due to recaptcha
                    vote_tasks.pop(0)

                t = create_vote_task(recaptcha, "ostracize")
                if t is not None:
                    vote_tasks.append(t)
        
        with open('recaptchas.txt', 'w') as f:
            f.truncate()

        if len(all_tokens) == 0:
            populate_creds()

        if RUN_TEST and len(vote_tasks) == cred_count:
            break

    finish_time = datetime.datetime.now()

    if not RUN_TEST:
        while curr_time.minute != VOTE_MINUTE or curr_time.second < VOTE_SECOND:
            curr_time = datetime.datetime.now()

    # Cast all prepared tasks
    print("TIME TO CAST VOTES at ", curr_time.minute, ":", curr_time.second)
    
    voting_start = time.time()
    voting_time = datetime.datetime.now()
    try:
        asyncio.run(cast_async_votes(vote_tasks))
    except Exception as e:
        msg = "Instance " + instance_id + " failed during async voting due to ERROR: " + str(e)
        webhook = DiscordWebhook(url=WEBHOOK, content=msg)
        webhook.execute()  

    # Delete the running.txt file
    if os.path.exists("running.txt"):
        os.remove("running.txt")
    
    time.sleep(random.randint(10, 60)) # Delay between voting and webhook to avoid being rate-limited
    # msg = "Instance " + instance_id + " finished generating tokens at " + finish_time.strftime("%M:%S")
    # webhook = DiscordWebhook(url=WEBHOOK, content=msg)
    # webhook.execute()   

    msg = "Instance " + instance_id + " began voting on " + str(len(vote_tasks)) + " tasks at " + voting_time.strftime("%M:%S")
    webhook = DiscordWebhook(url=WEBHOOK, content=msg)
    webhook.execute()   

    duplicates = 0
    too_early = 0
    internal_error = 0
    success = 0
    general = 0
    ostracized = 0
    unknown = 0
    delete_next = False
    all_tokens = []
    populate_creds()

    # with open(f'tokens_{instance_id}.txt', 'w') as f:
    #     f.truncate()
    msg = ""
    with open('logging.txt', 'r') as f:
        for line in f.readlines():
            if line[0] != '{':
                continue
            if 'vote/userAlreadyVoted' in line:
                duplicates += 1
            elif 'vote/votingDuringProcessing' in line:
                too_early += 1
            elif 'Server' in line:
                internal_error += 1
            elif 'general/recaptcha' in line:
                general += 1
            elif 'userOstracized' in line:
                ostracized += 1
                delete_next = True
            elif "success" in line:
                success += 1
            else:
                unknown += 1
                msg += "\nUNIDENTIFIED LINE: " + line + "\n"
    

    msg += f"FARM INSTANCE {instance_id}: Attempted **{len(vote_tasks)}** votes for **{get_target()}** with **{len(all_tokens)}** accounts " +\
        f"\n**Success: {success}**\nDuplicates: {duplicates}\n" +\
            f"Too Early: {too_early}\nServer Errors: {internal_error}\nGeneral/Recaptcha: {general}\nUnknown: {unknown}\n" 

    print(msg)
    webhook = DiscordWebhook(url=WEBHOOK, content=msg)
    webhook.execute()   

 