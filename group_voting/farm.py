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
import datetime
import random
from multiprocessing import Process, Queue, set_start_method
import asyncio

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

# Reddit Server webhook
WEBHOOK = "https://discord.com/api/webhooks/1270736440543940668/tkYMqC-xRTw3Uo_Y8-sAbwHP8YWSfnkGi_uF8w3I3aDx-qf1OoK2HArye5vRSRVAYRWa"

# Below webhook is for local debugging
# WEBHOOK - "https://discord.com/api/webhooks/1266025582865547444/vwvKQJ26iNgdiaJJP-ml37d8n9JftbmRJIptYKsw4rp5VHWOmhtd1V7iNUYziuOGtxx-"

VERBOSE = True
RUN_TEST = False 

now = datetime.datetime.now(datetime.UTC)

def request_interceptor(request):
    if request.method == "GET":
        # Steal recaptcha from search for voting
        if "searchForPlayers" in request.url:
            if VERBOSE:
                print("SEARCH REQUEST: ", end = "")
            sections = request.url.split("=")
            request.abort()
            captcha = sections[1][:-len("&searchString")]

            with open("recaptchas.txt", "a") as f:
                if VERBOSE:
                    print("Captcha added")
                f.write(captcha + "\n")
                      
    elif request.method == "POST":
        if "clr" in request.url:
            if VERBOSE:
                print("Preventing catpcha clearing")
            request.abort()

def run_recaptcha_farm(depth=1):
    with open('recaptchas.txt', 'w') as f:
            f.truncate()

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

        for letter in 'adum': # 
            time.sleep(0.01)
            ostracizeForm.send_keys(letter)
    except Exception as ex:
        print("ERROR INITIATING DRIVER AND NAVIGATING TO SEARCH BAR: ", ex)
        # msg = f"ERROR WITH DRIVER IN INSTANCE {instance_id} at " + datetime.datetime.now().strftime("%M:%S") + f". UserAgent: {userAgent}"
        msg = f"instance {instance_id} resetting web driver"
        webhook = DiscordWebhook(url=WEBHOOK, content=msg)
        webhook.execute()   

        if driver:
            driver.quit()

        if depth < 4:
            run_recaptcha_farm(depth = depth + 1)
        return

    start = time.time()
    now = datetime.datetime.now(datetime.UTC)
    while now.minute < 58 and not RUN_TEST:
        now = datetime.datetime.now(datetime.UTC)

    while now.minute < 59 or now.second < 30:
        now = datetime.datetime.now(datetime.UTC)
        try:
            for _ in range(5):
                for _ in range(4):
                    ostracizeForm.send_keys(chr(random.randint(65, 90)))
                    time.sleep(random.randint(1, 15)/100)
                time.sleep(0.25)
                for _ in range(4):
                    ostracizeForm.send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)
                
            time.sleep(0.15)
                
        except Exception as ex:
            print("Failed while using search bar for creds, Exception: ", ex)     
        
        if RUN_TEST and time.time() - start > 2*60:
            break
    
    print("Shutting down driver")
    if driver:
        driver.quit()
    

if __name__ == "__main__":
    with open('id.txt', 'r') as f:
        instance_id = f.readline().strip('\n')

    curr_time = datetime.datetime.now(datetime.UTC)
    if not RUN_TEST:
        while curr_time.minute < 57 or curr_time.second < 50:
            curr_time = datetime.datetime.now(datetime.UTC)

    run_recaptcha_farm()

    # time.sleep(10)
    # msg = f"Started Farmer {instance_id} at " + curr_time.strftime("%M:%S")
    # webhook = DiscordWebhook(url=WEBHOOK, content=msg)
    # webhook.execute()   

    time.sleep(random.randint(1, 3))

    curr_time = datetime.datetime.now(datetime.UTC)
    msg = f"Finished Farmer {instance_id} at " + curr_time.strftime("%M:%S")
    webhook = DiscordWebhook(url=WEBHOOK, content=msg)
    webhook.execute()   