A video walkthrough of this guide will be coming soon and will be linked at the top of this document!

## Step 1: Set up your free AWS account
Open a new tab and go to [https://aws.amazon.com/](https://aws.amazon.com/). Use the 'Create an AWS Account' button in the top right to start creating an account. AWS offers a free 12-month trial on some of its products, but it requires payment information as they will charge you after the 12 month period if you continue using their services. We recommend setting a reminder somewhere to shut down your account within 12 months so you don't get charged for anything. 

Enter all the requested information then navigate to the AWS Management Console. From the Console Home you will go to the top left and select 'Services > Compute > EC2'. This will take you to the EC2 Dashboard.

### Creating the EC2 instances

We are going to create a small EC2 instance that is included in the AWS free tier. Click the orange 'Launch instance' button, then follow the steps below. This EC2 instance will be a private computer that lives in the cloud and runs your auto-voter for you.

1) Give your instance a name, anything will do.

2) Select Ubuntu as the OS and leave all the default settings. 

The default settings will be 24.04 LTS image, t2.micro instance type, 8 GiB gp3 storage.

3) Click 'Launch instance'

4) Select 'Proceed without key pair' then launch the instance.

## Step 2: Setting up the EC2 instance

From the EC2 Dashboard we can connect to our instance by clicking on 'Instances' then clicking on the instance id of the instance we have running. This will take us to an instance summary, where we can click 'Connect' in the top right to access our EC2 instance. 

Once you are connected you will be in the terminal of your EC2 instance. If you are unfamiliar with the terminal, it is basically how we can navigate and do things in a computer without a screen. Having no display to a screen allows the computer to be more lightweight and less expensive. You will copy and paste the following lines into the terminal one at a time and press enter after each line to run the command. When copying and pasting with the terminal you should either right click with your mouse, or use ctrl+shift+c/v instead of just ctrl+c/v.

The bottom of this document includes some tips for using the terminal.

1.  **Get google chrome downloaded and installed** by running the following commands in the terminal
    
    - 'sudo apt-get update'
    - 'sudo apt-get install libxss1 libappindicator1 libindicator7'
    - 'sudo wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb'
    - 'sudo apt install ./google-chrome*.deb'
    - 'sudo apt-get install -f'
    
2. **Setup the python virtual environment** by running these commands in terminal
    - 'sudo apt install python3.12-venv'
    - 'python3 -m venv venv'
    - 'source venv/bin/activate'
    
3. **Get the GitHub repo setup**
    - 'git clone https://github.com/bruski-bytes/distributed_auto_voter.git'

4. **Install necessary python packages**
    1. type 'cd distributed_auto_voter' into the EC2 terminal and press enter. This moves you into the folder where the auto_voter lives.
    2. use 'pip install -r requirements.txt' to install all the needed python packages

5. **Run your auto-voter**
    1. You need to setup your settings file. To make sure it isn't overwritten with updates we keep it separate from the codebase.
        a. Run 'cp example_settings.json settings.json' to make an individual copy of the settings file
        b. Run 'nano settings.json' to open up a text editor to modify the settings file. Add your email and password here, as well as any targets you want to vote for. Everything should have parentheses around it as in the example file. Names in the target list should be separated by commas, and stay within the square brackets.
        c. To save your settings us CTRL+X, then press Y to confirm the changes, then press enter to save the file.
    2. Test that the code is setup correctly and able to cast a vote for you by using the command `python auto_voter.py`
    3. Once you confirm the auto-voter is ready, run the command `nohup python -u auto_voter.py > output.log &`. This will run the program in the background in AWS, so it will continue running even after you disconnect. 
    4. you can check that it is running with 'cat output.log' to see the program's output, or 'ps -ef | grep python' to see if the process is running.

## HOW TO UPDATE
We will occasionally push updates to this codebase. If you want to update your version of the code to match the latest version you just need to sign in to your aws account, connect to your EC2 instance and follow these steps:
1) Kill your old code process:
    - run 'ps -ef | grep python' and note the PID (process ID) on the line with auto_voter.py
    - run 'kill -9 7551' but replace 7551 with your process ID.
    - 

## TERMINAL INFO
You should be able to get the auto-voter up and running just by copying and pasting the commands in the guide and following along with the video. However, if you wanted to play around in the terminal, or know what the different commands above do, here are some tips.
- **Navigation**: You can think of the terminal as a bunch of folders (directories) nested inside each other. By default when you connect you start in the ubuntu folder inside the home folder inside the root folder (/home/ubuntu). You can navigate around from here by using 'cd directory_name' to go into a directory in your current directory. 'cd ..' takes you one step up out of the current directory you are in.
    - The 'ls' command lists everything inside your current directory. Just type 'ls' then press enter.
- **Tab complete**: When using commands to navigate between folders or that use a file you can press the tab key to complete the command for you if there is only one possible option. Ex: I want to navigate to the distributed_auto_voter folder, I can type 'cd d' then push tab and the terminal will finish the command as 'cd distributed_auto_voter' for me, because there is only the one directory that starts with a d.
- **Sudo**: We put 'sudo' in front of a command to run the command with elevated permissions, this basically tells the computer that we are allowed to do what we are requesting to do.
- **Repeating commands**: You can use the up and down arrow keys to cycle through the previous commands you have run, so if you want to repeat a command you recently ran you can push up on your arrow key to find it.
