'''
	PCPartPicker Reddit Bot
	By Prodge
	Prodge.net
	https://github.com/Prodge
	https://github.com/Prodge/PcPartPickerBot

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
  The files should be in the same directory as the script and the 
  filenames are listed below.

Todo:
- nationality support
- maybe print ttl in multiple currency will need to re-scrape for dif pricing
- add support for delete on -ve karma
- link products
- display link to build
'''

import urllib2
import praw
import time
import datetime
#	Bot Info
USERAGENT = "PcPartPickerBot 0.6 by /u/ProdigyDoo"
USERNAME = ''
PASS = ''
r=''
#	Logging Files
errorLog = 'pcPartPickerBotErrorLog.txt'
commentLog = 'pcPartPickerBotLog.txt'
#	Function Constraints
MAXPOSTS = 99
WAIT = 30
SUBREDDITS = ['buildapc', 'buildapcforme', 'buildapcsales', 'pcassembly', 'shittybattlestations',
		 'battlestations', 'gamingpc', 'hardwareswap', 'buildapc', 'pcmasterrace']
#	Statistics
repliesTotal = 0
errorCount = 0
runs = 1
startingTime = datetime.datetime.now()

#Scrapes the given PcPartPicker.com url and returns a list of prices
def scrapePartlist(url):
	page = urllib2.urlopen(url)	
	html = page.read()
	items = []
	prices = []
	suppliers = []
	stillGoing = True
	while(stillGoing):
		item = ''
		price = ''
		supplier = ''
		#Finding Item
		for i in range(len(html)):
			if html[i:i+16] == '<!-- pricing -->':
				item = html[i-400:i]
				html = html[i+20:]
				break
			if i == len(html)-1:
				stillGoing = False

		for i in range(len(item),0,-1):
			if item[i:i+4] == '</a>':		
				item = item[:i]
				break

		for i in range(len(item),0,-1):
			if item[i:i+1] == '>':		
				item = item[i+1:]
				items.append(item)
				break
		
		#Finding Supplier
		for i in range(len(html)):
			if html[i:i+15] == '<!-- delete -->':
				supplier = html[i-500:i]
				html = html[i+40:]
				break

		for i in range(len(supplier),0,-1):
			if supplier[i:i+9] == '</a></td>':		
				supplier = supplier[:i]
				price = supplier[:i]
				break

		for i in range(len(supplier),0,-1):
			if supplier[i:i+1] == '>':		
				supplier = supplier[i+1:]
				suppliers.append(supplier)
				break
		#Finding Price
		for i in range(len(price),0,-1):
			if price[i:i+9] == '</a></td>':
				price = price[:i]
				break
		
		for i in range(len(price),0,-1):
			if price[i:i+1] == '>':
				price = price[i+1:]
				prices.append(price)
				break
	return [items, prices, suppliers]

#Produces and returns a table (formatted for reddit) from the array returned from scrapePartList()
def generateComment(link):
	partList = scrapePartlist('http://pcpartpicker.com/p/' + link)
	#Checking for a clean pc part picker page (not missing any prices)
	if len(partList[0]) != len(partList[1]) != len(partList[2]) or len(partList[0]) == 0:
		return '-1'
	#Preparing Vars for commont generation
	output = ''
	newline = '\n' #its either 2 or 4 spaces for newline
	compensator = 2
	ttlPrice = sum([float(x[1:]) for x in partList[1]])
	itemWidth = max([len(x) for x in partList[0]]) + compensator
	priceWidth = max([len(str(ttlPrice)), len('price')]) + compensator
	supplierWidth = max([max([len(x) for x in partList[2]]), len('supplier')]) + compensator
	#Generating the comment output
	output += '| Item' + ''.join([' ' for i in range(itemWidth - 4)])
	output += '| Price' + ''.join([' ' for i in range(priceWidth - 5)])
	output += '| Supplier' + ''.join([' ' for i in range(supplierWidth - 8)])
	output += '|' + newline
	output += '|:' + ''.join(['-' for i in range(itemWidth)])
	output += '|:' + ''.join(['-' for i in range(priceWidth)])
	output += '|:' + ''.join(['-' for i in range(supplierWidth)])
	output += '|' + newline
	for i in range(len(partList[0])):
		output += '| ' + partList[0][i] + ''.join([' ' for l in range(itemWidth - len(partList[0][i]))])
		output += '| ' + partList[1][i] + ''.join([' ' for o in range(priceWidth - len(partList[1][i]))])
		output += '| ' + partList[2][i] + ''.join([' ' for l in range(supplierWidth - len(partList[2][i]))])
		output += '|' + newline
	output += '| ' + ''.join([' ' for i in range(itemWidth)])
	output += '| **$' + str(ttlPrice) + '**' + ''.join([' ' for o in range(priceWidth - len(str(ttlPrice)) + 1)])
	output += '| ' + ''.join([' ' for i in range(supplierWidth)])
        output += '|' + newline
	output += '^Prices ^are ^in ^USD.' + newline + newline
	output += '^This ^bot ^is ^still ^in ^beta, ^PM ^to ^report ^issues ^or ^for ^suggestions*' + newline + newline
	output += '[Source Code](https://github.com/Prodge/PcPartPickerBot)'
	return output

#Returns true if the bot hasn't previously replied to the given comment pid
def noMatch(pid):
	log = open(commentLog, "r")
	l=log.read().split()
	noMatch = True
	for line in l:
		if line == pid:
			noMatch = False
			break
	log.close()
	return noMatch

#Extracts the unique ID of the build given the comment body
def getLink(post):
	for i in range(len(post)):
		if post[i:i+19] == 'pcpartpicker.com/p/':
			return post[i+19:i+19+6]

#Returns true if the comment already contains a table
def containsTable(post):
	if 'Generated by PCPartPicker' in post or 'Type|Item|Price' in post or '[PCPartPicker part list]' in post:
		return True
	return False

#Logs the comment pid in a text file
def logComment(pid):
	loging = open(commentLog, "a")
	loging.write(pid + '\n')
	loging.close()

#Gets the most recent MAXPOSTS from the givin sub, scans them for a PcPartPicker link and replies if necessary
def scanSub(sub):
	print('--Starting Scan of "' + sub + '"')
	subreddit = r.get_subreddit(sub)
	posts = subreddit.get_comments(limit=MAXPOSTS)
	replyCount = 0
	for post in posts:
		pid = str(post.id)
		pbody = post.body
		try:
			pauthor = post.author.name
		except AttributeError:
			pauthor = '[DELETED]'
		#Check if there is a pcPartPicker.com link
		if 'pcpartpicker.com/p/' in pbody and not containsTable(pbody) and pauthor.lower() != USERNAME.lower():
			if noMatch(pid):
				link = getLink(pbody)
				comment = generateComment(link)
				if comment == '-1':
					continue
				post.reply(generateComment(link))
				logComment(str(pid))
				print('----Replied to: "' + pbody[:80] + '"...')
				replyCount += 1
	print('--Finished Scan with ' + str(replyCount) + ' Replies')
	return replyCount

#Outputs the running statistics based on the current run
def showStats():
	global startingTime
	now = datetime.datetime.now()
	elapsedTime = now - startingTime
	elapsedTimeSecs = elapsedTime.total_seconds()
	timeRunDays = elapsedTimeSecs // 60 // 60 // 24
	timeRunHours = elapsedTimeSecs // 60 // 60 % 24
	timeRunMins = elapsedTimeSecs // 60 % 60
	print("Going strong for " + str(timeRunDays) + " days, "+ str(timeRunHours) + " hours and " + str(timeRunMins) +" minutes")
	print("Scanned " + str(runs * MAXPOSTS) + " comments, made " + str(repliesTotal) + " replies and logged " + str(errorCount) + " errors \n")

#Runs the process, handles errors
def main():
	global runs
	global errorCount
	global repliesTotal
	global USERNAME
	global PASS
	global r
	#Login information input from user so its not stored in the script
	USERNAME = raw_input('Enter Bot Username: ')
	PASS = raw_input('Enter Bot Password: ')
	#Praw Setup
	r = praw.Reddit(USERAGENT)
	r.login(USERNAME, PASS)
	while True:
		if runs % 5 == 0:
			showStats()
		print("RUN: " + str(runs))
		try:
			repliesTotal += scanSub(SUBREDDITS[runs % len(SUBREDDITS)])
		except Exception as e:
			logingError = open(errorLog, "a")
			logingError.write(str(datetime.datetime.now()) + ': ' + str(e) + '\n')
			logingError.close()
			errorCount += 1
			print('An error has occured:', e)
		print('--Running again in ' + str(WAIT) + ' seconds \n')
		time.sleep(WAIT)
		runs += 1

main()
