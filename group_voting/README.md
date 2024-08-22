## The quick and dirty

To get stuff to vote at the top of the hour run the farm.py script at xx:58 minutes to generate captchas to use for voting. Run vote_tokens.py at any point prior to the top of the hour, I would recommend starting that script around thirty seconds to one minute before the hour. 

You can dig through the code to get a better idea of how it works, but basically we generate a ton of valid captchas then store them in a file. The vote_tokens.py script then reads those captchas and prepares a bunch of vote requests using those captchas. We watch for a signal after the top of the hour to tell us that the mschf api will accept votes, then we send all the votes asynchronously. 

The tokens are valid for two weeks after you login to get a token or refresh it using the api, so make sure you are on top of keeping the tokens valid. Hopefully the code is self explanatory and you can figure out how to tweak it for any of your needs.

You can check out the old birth plan I published to get a general idea of how to setup AWS to run these scripts at certain times as well as how to start and stop Ec2 instances. Feel free to ping me with any questions on how I hacked things together or if you get stuck anywhere.


The vote.py script is a slightly slower version of voting that is good to run a couple minutes after the hour. This version uses both token formatted voting creds as well as classic username and password creds.