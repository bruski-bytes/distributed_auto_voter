# Distributed Auto Voter
## Putting power back in the hands of the people. Brought to you by the RedditMSCHFVenmo Discord Server

### Join our group
Want to join our group for MSCHF Plays Venmo? Join our Discord! Make sure your Discord nickname and username do not match your venmo username. Also remove any linked accounts you may have on your discord. People will go to great lengths to find you and vote you out. 

https://discord.gg/NFStWDjt

Don't want to worry about changing your discord profile but still want to join our group? Send an email to lilbumpkin0@gmail.com and we will get you onboarded! 

### Setting up an auto-voter
To set up your own auto-voter using this code base you can follow the video tutorial (COMING SOON). We also have a document [here](setup.md) that follows along with the video and provides all the commands you need to copy and paste while setting up your auto-voter. The entire process should take 10-20 minutes to get your auto-voter running for free in the cloud 24/7.

### Development Game Plan
We want to make the use of this auto-voter as easy as possible. Downstream that may mean making it into an executable that people can run on their local machine or in an AWS EC2 instance. In the short term it would look like people downloading and using this code base. Ideally, they just need to change a settings file to add their credentials and the list of names that they want to vote on for ostracize and elect.

#### Features to Implement
- Allow the users to automate elect votes. 
- Allow users to specify the minute of the hour to cast their ostracize vote
- Allow users to specify hour of the day to cast elect vote
- Add a 'random target' option for ostracize and elect, they auto-voter will cast a vote for a random target if no target is specified and this option is turned on.
- Add a 'create ties'option. This option will prioritize making 2nd place and 1st place tie over voting for the specified target.

#### Non-Code work to do
- Make a tutorial on using the codebase
- Make a tutorial on setting up a free tier AWS account and hosting the code in an EC2 instance so it can run 24/7 without requiring your local machine.

#### BUGS
- For some reason the headless chrome instance stays alive after shutdown sometimes. This can eat up a lot of a computer's resources and is hard to detect without using task manager. 

#### Features for Consideration
- API field that can be filled in for pulling targets directly from our groups target list instead of manually updating a local target list
- API field for posting the auto-voter's status back to the group, to verify who is voting in harmony with the group for determining who is eligible for a payout at the end of the game.
- Discord webhook field, people can make their own server and create a webhook where the auto-voter can send messages if something fails, or just to confirm that it ran.
