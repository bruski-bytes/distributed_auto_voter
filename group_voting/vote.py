from seleniumwire import webdriver
from fake_useragent import UserAgent
from discord_webhook import DiscordWebhook
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import requests
import asyncio
import random
import datetime
import json

'''
ARGUMENTS:
VOTE_PERCENT_FOR_MAIN: a number from 50 to 100 specifying what percentage of votes should go toward the main target.
                        The remaining percentage of votes go to another name on our priority list.

TRACK_SECOND: A boolean value that is set by the presence of 'track_second.txt' in the repo directory. 
              If True -> we will use the variables mentioned above to determine our voting behaviour.
              If False -> we ignore the above logic and only cast votes for our targets.
'''

# Reddit Server webhook
WEBHOOK = "<YOUR WEBHOOK HERE>"

# Below webhook is for local debugging

VERBOSE = True

now = datetime.datetime.now(datetime.UTC)
# random.seed(now.hour)
print(now.hour)
VOTE_PERCENT_FOR_MAIN = 100 # if now.minute <= 20 else 50
print("RUNNING VOTING WITH {} PERCENT FOR MAIN".format(VOTE_PERCENT_FOR_MAIN))
TRACK_SECOND = False

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

renewed_tokens = []

# Setup chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--window-size=1100,1000")
options.add_argument("--disable-dev-ahm-usage")
options.add_argument("--no-sandbox")
options.add_argument('--headless')
options.add_argument('--disable-dev-shm-usage')  
options.add_argument('--log-level=3')
options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
options.add_experimental_option('useAutomationExtension', False)
# options.binary_location = "/opt/google/chrome/google-chrome"

# GLOBAL VARIABLES 
all_emails = []
all_passwords = []
all_tokens = []
priority_list = []
email_token_lookup = {}
new_email_token_lookup = {}
LOGIN_ACTIVE = False

def update_priority_list():
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/players?type=ostracize&quantity=12000&startIndex=0&reversed=true"

    payload = ""
    response = requests.request("GET", url, data=payload)
    jsonData = response.json()

    players = jsonData['players']

    livingPlayerList = []

    first_place_score = players[0]['score']
    first_place = players[0]['username']

    second_place = players[1]['username']
    second_place_score = players[1]['score']

    for player in players:
        livingPlayerList.append(player['username'])

    # print("Reading Priority List")
    # Get our current priority list
    with open('priority_list.txt', 'r') as f:
        priority_list = f.read().splitlines()
        # print("Current Priority List: ", priority_list)  
    
    # Remove players that are ostracized
    for user in priority_list:
        if user not in livingPlayerList:
            if VERBOSE:
                print(f"Removing {user}")
            priority_list.remove(user)

    with open('priority_list.txt', 'w') as f:
        f.write('\n'.join(priority_list))

    if VERBOSE:
        print("Current Gap: ", first_place_score - second_place_score)

    gap = first_place_score - second_place_score
    
    return priority_list, gap, first_place, second_place

def login_to_mschf(recaptcha):    
    global all_emails, all_passwords, all_tokens, LOGIN_ACTIVE
    LOGIN_ACTIVE = True
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/login"

    current_email = all_emails.pop(0)
    current_password = all_passwords.pop(0)
    payload = {
        'email': current_email,
		'password': current_password,
		'recaptcha': recaptcha,
    }
    if VERBOSE:
        print("\nSending Login: ", current_email)
    response = requests.post(url, json=payload)

    data = json.loads(response.text)
    if "token" in data:
        # all_tokens.append(data['token'])
        # cred_tokens.add(data['token'])
        # new_email_token_lookup[current_email] = data['token']
        with open('login_results.txt', 'a') as f:
            f.write(f"{current_email}, success, {data['token']}\n")
    else:
        if data['message'] == "login/wrongPassword":
            bad_passwords.add(current_email)
            with open('login_results.txt', 'a') as f:
                f.write(f"{current_email}, bad pw\n")
        elif data['message'] == "login/noUser":
            bad_emails.add(current_email)
            with open('login_results.txt', 'a') as f:
                f.write(f"{current_email}, bad email\n")
        else:
            print("Error: ", data)
            with open('login_results.txt', 'a') as f:
                f.write(f"{current_email}, error\n")
            #TODO: Add logging of error to discord
    LOGIN_ACTIVE = False

def get_target():
    global priority_list, TARGET_INDEX, TRACK_SECOND, VOTE_PERCENT_FOR_MAIN

    priority_list, gap, first_place, second_place = update_priority_list()
    return priority_list[0]
    if random.randint(0, 100) <= VOTE_PERCENT_FOR_MAIN:
        target = priority_list[TARGET_INDEX]
    else:
        target = priority_list[TARGET_INDEX+1]

    if TRACK_SECOND:
        # Default to continue voting to maintain lead in first place
        if first_place in priority_list:
            target = first_place

        # If second place is a target, voting will either help us create a tie, or catch up to first place
        if second_place in priority_list:
            # Try to create a tie
            if gap != 0:
                target = second_place
            else:
                target = "SKIP"

    return target

def renew_token(recaptcha):
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/token"

    current_token = all_tokens.pop(0)

    data = {
        'token': current_token,
        'recaptcha': recaptcha,
    }

    response = requests.post(url, json=data)
    print(response.text)
    renewed_tokens.append(response.json()['token'])

def cast_vote(recaptcha, type="ostracize"):
    global all_tokens
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/vote"

    current_target = get_target()

    if current_target == "SKIP":
        return
    
    current_token = all_tokens.pop(0)

    payload = {
        'type': type,
		'username': current_target,
		'recaptcha': recaptcha,
		'token':	current_token
    }
    if VERBOSE:
        print("\nSending Vote: ", current_target, current_token)
    # response = requests.post(url, headers=headers, json=payload)
    time.sleep(random.randint(5, 20))
    response = requests.post(url, json=payload)
    # TODO: Analyze response message for logging
    data = json.loads(response.text)
    if "error" in data:
        if data['message'] == 'vote/userAlreadyVoted':
            if current_token in new_email_token_lookup:
                duplicate_votes.add(new_email_token_lookup[current_token])
            else:
                duplicate_tokens.add(current_token)
            print("DUPLICATE VOTE")
        elif data['message'] == 'vote/userOstracized':
            if current_token in new_email_token_lookup:
                ostracized_votes.add(new_email_token_lookup[current_token])
            else:
                ostracized_tokens.add(current_token)
        else:
            # TODO: Send discord webhook to log error
            print("ERROR: ", data['message'])
    elif "success" in data:
        print("SUCCESSFUL VOTE")
        successful_votes.add(current_token)

def request_interceptor(request):
    global all_tokens, all_emails
    if request.method == "GET":
        # Steal recaptcha from search for voting
        if "searchForPlayers" in request.url:
            if VERBOSE:
                print("SEARCH REQUEST: ", end = "")
            sections = request.url.split("=")
            request.abort()
            if len(all_tokens) > 0:
                if VERBOSE:
                    print("Voting Token")
                cast_vote(sections[1][:-len("&searchString")])
                # renew_token(sections[1][:-len("&searchString")])
            elif len(all_emails) > 0:
                if VERBOSE:
                    print("LOGGING IN")
                login_to_mschf(sections[1][:-len("&searchString")])
            else:
                pass


def run():
    global all_emails, LOGIN_ACTIVE
    url = 'https://mschfplaysvenmo.com/'
    count = 0
    ua = UserAgent()
    userAgent = ua.random
    print("\nRunning with ", userAgent)
    try:
        options.add_argument("--user-agent=" + userAgent)

        driver = webdriver.Chrome(options=options)
        driver.request_interceptor = request_interceptor

        driver.get(url)
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, '#__layout > div > div > div > div.content__inner__panels > div.center-panel.show-secondary-screen > div.center-panel__inner > div.secondary-screen.center-panel__inner__secondary-screen > div > div > div.screen__inner__inner > div > div > div.choose-vote-type-container__choices.small-caps > div > button:nth-child(1)').click()
        time.sleep(1)
        WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#searchpageostracize > div > div > div > div.pixelated-container__inner.filled.large.row.inverted > div > div.search-bar__container__inner__bottom.ostracize > form > input"))).click()
        time.sleep(1)
        ostracizeForm = driver.find_element(By.CSS_SELECTOR, '#searchpageostracize > div > div > div > div.pixelated-container__inner.filled.large.row.inverted > div > div.search-bar__container__inner__bottom.ostracize > form > input')
        for letter in 'adam': # 
            time.sleep(0.01)
            ostracizeForm.send_keys(letter)
    except Exception as ex:
        print("ERROR INITIATING DRIVER AND NAVIGATING TO SEARCH BAR: ", ex)
    
    error = False

    start = time.time()
    while len(all_emails) > 0 or len(all_tokens) > 0 or LOGIN_ACTIVE:
        try:
            for i in range(25):
                time.sleep(0.02)
                ostracizeForm.send_keys(Keys.BACKSPACE)
                time.sleep(0.02)
                ostracizeForm.send_keys('m')
        except Exception as ex:
            print("Failed while using search bar for creds, Exception: ", ex)
            error = True
            break  
        time.sleep(0.5)

        if len(all_tokens) == 0:
            print("cast all initial token votes in ", time.time() - start)

    print("Cast votes in ", time.time() - start)
    # Make sure driver is quit out
    if driver:
        driver.quit()
    
    if error:
        run()
    return

if __name__ == "__main__":
    curr_time = datetime.datetime.now()
    
    # Read the instance id from id.txt
    with open('id.txt', 'r') as f:
        instance_id = f.readline().strip('\n')
    print("Instance ID: ", instance_id)

    time.sleep(random.randint(0, 10))
    now = datetime.datetime.now()
    webhook = DiscordWebhook(url=WEBHOOK, content=f"Slow auto-voter {instance_id} started at " + now.strftime("%M:%S"))
    webhook.execute()   

    update_priority_list()
    
    with open('priority_list.txt', 'r') as f:
        priority_list = f.read().splitlines()  

    # Create the running file to prevent other scripts starting up
    with open('running.txt', 'w') as f:
        f.write("Running")

    # Read in all email-password creds
    with open(f"creds_{instance_id}.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            parts = line.split(" ")
            all_emails.append(parts[0])
            all_passwords.append(parts[-1])
            print("parts", parts)
    
    # Read in all token creds
    with open(f"tokens_{instance_id}.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            parts = line.split(",")
            if len(line) > 0:
                all_tokens.append(parts[0])
    
    
    # Read in all token creds from cred_tokens.txt
    with open(f"cred_tokens_{instance_id}.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            parts = line.split(",")
            if len(line) > 0:
                all_tokens.append(parts[1])
    
    # with open(f"reserved_tokens.txt", "r") as f:
    #     lines = f.readlines()
    #     for line in lines:
    #         line = line.strip("\n")
    #         parts = line.split(",")
    #         if len(line) > 0:
    #             all_tokens.append(parts[1])
    
    
    # Create a new file to log login results
    with open('login_results.txt', 'w') as f:
        f.write('')
    

    logged_already = False
    totalRuns = 0
    super_start = time.time()
    run()

    # Filter out bad emails and passwords and rewrite creds.txt
    filtered_emails = []
    filtered_passwords = []
    with open(f"creds.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            parts = line.split(" ")
            # print("lower_parts", parts)
            email = parts[0]
            password = parts[-1]
            if email not in bad_emails and password not in bad_passwords and email not in ostracized_votes:
                filtered_emails.append(email)
                filtered_passwords.append(password)

    with open(f"creds.txt", "w") as f:
        for email, password in zip(filtered_emails, filtered_passwords):
            f.write(email + " " + password + "\n")

    with open("bad_creds.txt", "w") as f:
        for email, password in zip(filtered_emails[len(filtered_emails) - len(bad_emails):], filtered_passwords[len(filtered_passwords) - len(bad_passwords):]):
            f.write(email + " " + password + "\n")
    
    filtered_tokens = []
    with open(f"tokens.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip("\n")
            if len(line) > 0:
                if line not in ostracized_tokens:
                    filtered_tokens.append(line)
    
    with open("renewed_tokens.txt", "w") as f:
        for token in renewed_tokens:
            f.write(token + "\n")

    with open(f"tokens.txt", "w") as f:
        f.write('\n'.join(filtered_tokens))
    
    with open(f"cred_tokens.txt", "w") as f:
        for email in new_email_token_lookup:
            if new_email_token_lookup[email] not in ostracized_tokens:
                f.write(email + " " + new_email_token_lookup[email] + "\n")
        
        for email in email_token_lookup:
            if email not in new_email_token_lookup and email_token_lookup[email] not in ostracized_tokens:
                f.write(email + " " + email_token_lookup[email] + "\n")
        

    msg = f"INSTANCE {instance_id} SUCCESFULL VOTES FOR {priority_list[TARGET_INDEX]}: **" + str(len(successful_votes)) + "**\nCreds\n"+ "Ostracized: " + str(len(ostracized_votes)) + "\nDuplicate: " + str(len(duplicate_votes)) +\
        "\nInvalid Emails: " + str(bad_emails) + "\nInvalid Passwords: " + str(bad_passwords)

    print(msg)
    webhook = DiscordWebhook(url=WEBHOOK, content=msg)
    webhook.execute()

    # msg = "TOKENS\n"+ "Num Ostracized: " + str(len(ostracized_tokens)) + "\nNum Duplicate: " + str(len(duplicate_tokens)-len(duplicate_votes)) +\
    #     "\nNum Invalid: " + str(len(invalid_tokens))
    # print(msg)
    # webhook = DiscordWebhook(url=WEBHOOK, content=msg)
    # webhook.execute()

        
    # TODO: Add a step for casting elect votes, read in all good tokens and try to cast an elect vote for them
    # TODO: track down how to handle double counting between tokens and creds
    # Delete running file
    if os.path.exists("running.txt"):
        os.remove("running.txt")

    print("Entire program lasted: ", time.time() - super_start)

    # CODE FOR RUNNING ON A SCHEDULE
    # with open('priority_list.txt', 'w') as f:
    #     f.write('\n'.join(priority_list[1:]))