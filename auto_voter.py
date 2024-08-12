from seleniumwire import webdriver
from fake_useragent import UserAgent
from discord_webhook import DiscordWebhook
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import datetime
import json
import random

now = datetime.datetime.now(datetime.UTC)

# GLOBAL VARIABLES 
VERBOSE = True
VOTED = False
LOGIN_ACTIVE = False
USER_TOKEN = ""

def update_priority_list():
    '''
    This function could be improved by hitting a different api endpoint for verifying if a player exists in the game and has not been ostracized.
    This is not currently in use, but should be modified to give feedback to a user if they tried to vote for someone that is already ostracized or doesn't exist in the game.
    '''
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/players?type=ostracize&quantity=12000&startIndex=0&reversed=true"

    payload = ""
    response = requests.request("GET", url, data=payload)
    jsonData = response.json()

    players = jsonData['players']

    livingPlayerList = []

    for player in players:
        livingPlayerList.append(player['username'])

    print("Reading Priority List")
    # Get our current priority list
    settings = json.load(os.curdir + "settings.json")
    priority_list = settings["target_list"]
    
    # Remove players that are ostracized
    for user in priority_list:
        if user not in livingPlayerList:
            if VERBOSE:
                print(f"Removing {user}")
            priority_list.remove(user)

    # TODO: add a second layer of checking by removing any names that appear in the ostracizedPlayers api.

    return priority_list

def login_to_mschf(recaptcha):    
    global LOGGED_IN, USER_TOKEN, LOGIN_ACTIVE
    LOGIN_ACTIVE = True
    settings = json.load(os.curdir + "settings.json")
    email = settings["email"]
    password = settings["password"]

    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/login"

    payload = {
        'email': email,
		'password': password,
		'recaptcha': recaptcha,
    }

    if VERBOSE:
        print("\nSending Login: ")

    response = requests.post(url, json=payload)

    data = json.loads(response.text)
    if "token" in data:
        USER_TOKEN = data['token']
        LOGGED_IN = True

    LOGIN_ACTIVE = False

def get_target():
    # If user has opted into API linking, get target from API
    settings = json.load(os.curdir + "settings.json")
    priority_list = settings["target_list"]
    target = priority_list[0]
    return target

def cast_vote(recaptcha, type="ostracize"):
    global USER_TOKEN, VOTED
    url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/vote"

    current_target = get_target()

    if current_target == "SKIP":
        return
    
    payload = {
        'type': type,
		'username': current_target,
		'recaptcha': recaptcha,
		'token':	USER_TOKEN
    }
    if VERBOSE:
        print("\nSending Vote for: ", current_target)

    response = requests.post(url, json=payload)

    data = json.loads(response.text)
    if "error" in data:
        if data['message'] == 'vote/userAlreadyVoted':
            print("THIS ACCOUNT HAS ALREADY VOTED")
            VOTED = True
        elif data['message'] == 'vote/userOstracized':
            print("THIS ACCOUNT HAS BEEN OSTRACIZED")
            VOTED = True
        else:
            print("ERROR: ", data['message'])
    elif "success" in data:
        VOTED = True
        # if user has opted into API linking, send result to API

def request_interceptor(request):
    global LOGIN_ACTIVE, LOGGED_IN
    if request.method == "GET":
        # Steal recaptcha from search for voting
        if "searchForPlayers" in request.url:
            if VERBOSE:
                print("SEARCH REQUEST: ", end = "")
            sections = request.url.split("=")
            request.abort()
            
            if not LOGGED_IN and not LOGIN_ACTIVE and len(USER_TOKEN) < 20:
                login_to_mschf(sections[1][:-len("&searchString")])
            elif not VOTED and not LOGIN_ACTIVE:
                cast_vote(sections[1][:-len("&searchString")])
            
            #TODO: Add a step the checks if we should cast and elect vote.
                


def run():
    global VOTED
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

    url = 'https://mschfplaysvenmo.com/'
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
        
        # Generate recaptcha tokens by searching for a name
        for letter in 'MSCHFREDDITVENMO': # 
            time.sleep(random.randint(1, 20)/100)
            ostracizeForm.send_keys(letter)
    except Exception as ex:
        print("ERROR INITIATING DRIVER AND NAVIGATING TO SEARCH BAR: ", ex)

        if driver:
            driver.quit()

        run()
        return
    
    # Make sure driver is quit out
    if driver:
        driver.quit()
    
    return

if __name__ == "__main__":
    while True:
        # Get user settings
        settings = json.load(os.curdir + "settings.json")
        voting_minute = settings["voting_minute"]
        
        while datetime.datetime.now().minute != voting_minute:
            time.sleep(20)

        run()
        VOTED = False
        LOGIN_ACTIVE = False