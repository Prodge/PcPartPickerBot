PcPartPickerBot
===============

A Reddit comment bot that replies to PcPartPicker.com links with a table of parts and pricing.

See it in action: http://www.reddit.com/user/PcPartPickerBot


From pcPartBot.py:

Info:
- This bot uses Praw to access the Reddit API.
- The bot searches relevent subreddits for pcpartpicker.com links.
- When a match is found urllib2 is used to get the html from that page.
- The html is then processed to find the Pc Parts, price and supplier.
- A comment is generated from this information and is posted in response.

Dependencies:
- PRAW: https://praw.readthedocs.org/en/v2.1.16/
- Errors and comments are logged in text files that are not automatically 
  generated and so they will have to be created before running this script.
  The required txt files for logging are in this repo (name sensitive)


Feel free to copy this code, a comment with a link to this repo may help others or you in the future
