#!/usr/bin/python
"""Crawls the web looking for quantitative information about bitcoin popularity.

	Examples (require Internet connection):
	# this will find and gedit a text file containing the indicated search terms
	>>> bitcrawl.py # takes about a minute
	329
	>>> bitcrawl.py # takes a sec
	329
	
	Dependencies:
		argparse -- ArgumentParser
		urllib
		urllib2

	TODO:
	1. Add option to filter out some common red herrings like .bash_history (or hobs's .bash_history_forever)
	2. Add option to provide colorized/highlighted search result text abstracts like 
	   recoll or google desktop, and select on to launch
	3. add quiet and verbose options
	4. deal with csv: http://www.google.com/trends/?q=bitcoin&ctab=0&geo=us&date=ytd&sort=0 , 
	      <a href='/trends/viz?q=bitcoin&date=ytd&geo=us&graph=all_csv&sort=0&scale=1&sa=N'>
	      other examples in comments below
	5. poll domain name registries to determine the number of domain names with "bitcoin" in them or beginning with "bit" or having "bit" and "coin" in them 
	6. build website and REST to share bitcoin trend info, several domain names saved at bustaname under shopper@tg username 
	      pairbit, bitpair, coinpair, paircoin, coorbit, bitcorr, bitcoinarbitrage, etc

	Copyright:
	((c) Hobson Lane dba TotalGood)

"""

FILENAME='/home/hobs/Notes/notes_repo/bitcoin trend data.json'

def parse_args():
	# TODO: "meta-ize" this by only requiring number format specification in some common format 
	#       like sprintf or the string input functions of C or python, and then convert to a good regex
	# TODO: add optional units and suffix patterns
	URLs={'http://bitcoincharts.com/about/markets-api/': 
			{ 'blocks':
				[r'<td class="label">Blocks</td><td>',          # (?<= ... )\s*
				 r'[0-9]{1,9}'                               ],  # (...)
			  'total_btc': # total money supply of BTC
				[r'<td class="label">Total BTC</td><td>',
				 r'[0-9]{0,2}[.][0-9]{1,4}[MmKkGgBb]' ], 
			  'difficulty':
				[r'<td class="label">Difficulty</td><td>',
				 r'[0-9]{1,10}' ], 
			  'estimated': # total money supply of BTC
				[r'<td class="label">Estimated</td><td>',
				 r'[0-9]{1,10}' ] ,
			  'blocks':     # total money supply of BTC blocks
				[r'<td class="label">Estimated</td><td>\s*[0-9]{1,10}\s*in',
				 r'[0-9]{1,10}' ] ,
			  'hash_rate':     # THash/s on the entire BTC network
				[r'<td class="label">Network total</td><td>',
				 r'[0-9]{0,2}[.][0-9]{1,4}' ],
			  'block_rate':     # blocks/hr on the entire BTC network
				[r'<td class="label">Blocks/hour</td><td>',
				 r'[0-9]{0,3}[.][0-9]{1,4}' ] } ,
		'https://en.bitcoin.it/wiki/Trade': {
			'traffic':
				[r'accessed\s',
				 r'([0-9],)?[0-9]{3},[0-9]{3}'  ] }, 
		'https://mtgox.com':                {
			'price':
			[r'Weighted Avg:<span>',             # (?<= ... )\s*
			 r'\$[0-9]{1,2}[.][0-9]{3,5}',]  } , # (...)
		}
	from argparse import ArgumentParser
	p = ArgumentParser(description=__doc__.strip())
	p.add_argument(
		'-b','--bitfloor','--bf',
		type    = int,
		nargs   = '?',
		default = 0,
		help    = 'Retrieve N prices from the order book at bitfloor.',
		)
	p.add_argument(
		'-u','--urls','--url',
		type    = str,
		nargs   = '*',
		default = URLs,
		help    = 'URL to scape data from.',
		)
	p.add_argument(
		'-p','--prefix',
		type    = str,
		nargs   = '*',
		default = '', 
		help    = 'HTML that preceeds the desired numerical text.',
		)
	p.add_argument(
		'-r','--regex','--regexp','--re',
		type    = str,
		nargs   = '*',
		default = '',
		help    = 'Python/Perl regular expression to capture numerical string only.',
		)
	p.add_argument(
		'-v','--verbose',
		action  = 'store_true',
		default = False,
		help    = 'Output an progress information.',
		)
	p.add_argument(
		'-q','--quiet',
		action  = 'store_true',
		default = False,
		help    = "Don't output anything to stdout, not even the numerical value scraped from the page. Overrides verbose.",
		)
	p.add_argument(
		'-t','--tab',
		action  = 'store_true',
		default = 'false',
		help    = "In the output file, precede numerical data with a tab (column separator).",
		)
	p.add_argument(
		'-n','--newline',
		action  = 'store_true',
		default = 'false',
		help    = "In the output file, after outputing the numerical value, output a newline.",
		)
	p.add_argument(
		'-s','--separator','-c','--column-separator',
		metavar = 'SEP',
		type    = str,
		default = '',
		help    = "In the output file, precede numberical data with the indicated string as a column separator.",
		)
	p.add_argument(
		'-m','--max','--max-results',
		metavar = 'N',
		type=int,
		default = 1,
		help    = 'Limit the maximum number of results.',
		)
	p.add_argument(
		'-f','--path','--filename',
		type    = str,
		#nargs  = '*', # other options '*','+', 2
		default = FILENAME,
		help    = 'File to append the numerical data to (after converting to a string).',
		)
	return p.parse_args()

#Historic Trade Data
#Trade data is available as CSV, delayed by approx. 15 minutes.
#http://bitcoincharts.com/t/trades.csv?symbol=SYMBOL[&start=UNIXTIME][&end=UNIXTIME]
#returns CSV:
#unixtime,price,amount
#Without start or end set it'll return the last few days (this might change!).
#Examples
#Latest mtgoxUSD trades:
#http://bitcoincharts.com/t/trades.csv?symbol=mtgoxUSD
#All bcmPPUSD trades:
#http://bitcoincharts.com/t/trades.csv?symbol=bcmPPUSD&start=0
#btcexYAD trades from a range:
#http://bitcoincharts.com/t/trades.csv?symbol=btcexYAD&start=1303000000&end=1303100000
#Telnet interface
#There is an experimental telnet streaming interface on TCP port 27007.
#This service is strictly for personal use. Do not assume this data to be 100% accurate or write trading bots that rely on it.

COOKIEFILE='/home/hobs/tmp/wget_cookies.txt'
#REFERRERURL='http://google.com'
#USERAGENT='Mozilla'

#!/usr/bin/env python

import urllib
import urllib2

class Bot:
	"""A browser session that follows redirects and maintains cookies."""
	def __init__(self):
		self.response    = ''
		self.params      = ''
		self.url         = ''
		redirecter  = urllib2.HTTPRedirectHandler()
		cookies     = urllib2.HTTPCookieProcessor()
		self.opener = urllib2.build_opener(redirecter, cookies)
#		build_opener creates an object that already handles 404 errors, etc, right?
#			except urllib2.HTTPError, e:
#				print "HTTP error: %d" % e.code
#			except urllib2.URLError, e:
#				print "Network error: %s" % e.reason.args[1]
	def GET(self, url):
		self.response = self.opener.open(url).read()
		return self.response
	def POST(self, url, params):
		self.url    = url
		self.params = urllib.urlencode(parameters)
		self.response = self.opener.open(url, self.params ).read()
		return self.response

def get_page(url):
	try:
		return urllib.urlopen(url).read()
	except:
		return ''

def get_next_target(page):
	start_link = page.find('<a href=')
	if start_link == -1: 
		return None, 0
	start_quote = page.find('"', start_link)
	end_quote = page.find('"', start_quote + 1)
	url = page[start_quote + 1:end_quote]
	return url, end_quote

def union(p,q):
	for e in q:
		if e not in p:
			p.append(e)

def get_all_links(page):
	links = []
	while True:
		url,endpos = get_next_target(page)
		if url:
			links.append(url)
			page = page[endpos:]
		else:
			break
	return links # could use set() to filter out duplicates

# TODO: set default url if not url
# TODO: tries to browse to weird URLs and bookmarks, e.g. "href=#Printing"
# TODO: need to count stats like how many are local and how many unique second and top level domain names there are
def get_links(url='https://en.bitcoin.it/wiki/Trade',max_depth=1,max_breadth=1e6,max_links=1e6,verbose=False):
	import datetime
	from tg.tz import Local
	tocrawl = [url]
	crawled = []
	depthtocrawl = [0]*len(tocrawl)
	depth = 0
	page = tocrawl.pop()
	depth = depthtocrawl.pop()
	links = 0
	if verbose:
		print 'Counting links by crawling URL "'+url+'" to a depth of '+str(max_depth)+'...'
	while depth<=max_depth and links<max_links:
		links += 1
		if page not in crawled:
			i0=len(tocrawl)
			link_urls = set(get_all_links(get_page(page))) # set() makes sure all links are unique
			union(tocrawl, link_urls)
			if verbose:
				print 'Retrieved '+str(len(link_urls))+' links at "'+ page + '"'
			crawled.append(page)
			for i in range(i0,len(tocrawl)):
				depthtocrawl.append(depth+1)
		if not tocrawl: break
		page  = tocrawl.pop(0) # FIFO to insure breadth first search
		depth = depthtocrawl.pop(0) # FIFO
	dt = datetime.datetime.now(tz=Local)
	return {url:{'datetime':str(dt),'links':len(crawled),'depth':max_depth}}

# TODO: set default url if not url
def rest_json(url='https://api.bitfloor.com/book/L2/1',verbose=False):
	import json, datetime
	from tg.tz import Local
	if verbose:
		print 'Getting REST data from URL "'+url+'" ...'
	data_str = Bot().GET(url)
	dt = datetime.datetime.now(tz=Local)
	if verbose:
		print 'Retrieved a '+str(len(data_str))+'-character JSON string at '+ str(dt)
	dat     = json.loads( data_str )
	dat['datetime']=str(dt)
	return {url:dat}

# TODO: set default url if not url
def bitfloor_book(url='https://api.bitfloor.com/book/L2/1',bids=None,asks=None,verbose=False):
	return rest_json(url=url,verbose=verbose) 

# TODO: set default url if not url
def mine_data(url='',prefixes=r'',regexes=r'',verbose=False):
	import datetime
	from tg.tz import Local
	if verbose:
		print 'Mining URL "'+url+'" ...'
	if not url: 
	    return None
	page=Bot().GET(u)
	dt = datetime.datetime.now(tz=Local)
	dat = {'datetime':str(dt)}
	if verbose:
		print 'Retrieved '+str(len(page))+' characters/bytes at '+ str(dt)
	if isinstance(prefixes,list):
		for i,[prefix,regex] in enumerate(prefixes):
			r = re.compile(r'(?:'+prefix+r')\s*'+r'(?P<quantity>'+regex+r')') # lookbehind group NOT required: r'(?<=...)'
			mo = r.search(page)
			if mo:
				q = mo.group(mo.lastindex)
				dat[i]=q
	elif isinstance(prefixes,dict):
		for name,[prefix,regex] in prefixes.items():
			r = re.compile(r'(?:'+prefix+r')\s*'+r'(?P<quantity>'+regex+r')') # lookbehind group NOT required: r'(?<=...)'
			mo = r.search(page)
			if mo:
				q = mo.group(mo.lastindex)
				dat[name]=q
	return dat

if __name__ == "__main__":
	import re
	o = parse_args()
	#bitcoin_url = "https://en.bitcoin.it/wiki/Trade"
	#bifloor_url = 'https://api.bitfloor.com/book/L2/1'

#	data = rest_json()
#	print type(data)
#	print data

#	example bot usage
#	signin_results   = bot.POST('https://example.com/authenticator', {'passwd':'foo'})
#	singoff_results  = bot.POST('https://example.com/deauthenticator',{})

	dat = dict()
	if type(o.urls)==dict:
		for u,r in o.urls.items():
			dat[u]=mine_data(u,r,verbose=not o.quiet)
#	elif type(o.urls)==list and len(o.urls)==len(o.prefix)==len(o.regex):
#		for i,u in enumerate(o.urls):
#			mine_data(u,o.prefix[i],o.regex[i],verbose=not o.quiet)
#	elif type(o.urls)==type(o.prefix)==type(o.regex)==str and len(o.urls)>1 and len(o.regex)>0 and len(o.prefix)>0:
#		mine_data(o.urls,o.prefix,o.regex,verbose=not o.quiet)
	else:
		raise ValueError('Invalid URL, prefix, or regex argument.')
	
	if o.verbose:
		import pprint
		pprint.pprint(dat)
	bfdat = bitfloor_book(verbose=not o.quiet)
	if o.verbose:
		pprint.pprint(bfdat)
	links = get_links(max_depth=0,verbose=not o.quiet)
	with open(o.path,'r+') as f: # 'a+' and 'w+' don't work
		# pointer should be at the end already due to append mode, but it's not,
		f.seek(0,2)  # go to position 0 relative to 2=EOF (1=current, 0=begin)
		if f.tell()>3:
			f.seek(-3,2) # if you do this before seek(0,2) on a "a+" or "w+" file you get "[Errno 22] Invalid argument"
			#terms=f.read()
			#if terms=='\n]\n':
			#f.seek(-3,2)
			f.write(",\n") # to allow continuation of the json array/list
		else:
			f.write('[\n')  # start a new json array/list
		import json
		f.write(json.dumps(dat,indent=2))
		f.write(",\n") # delimit records/object-instances within an array with commas
		f.write(json.dumps(bfdat,indent=2))
		f.write(",\n") # delimit records/object-instances within an array with commas
		f.write(json.dumps(links,indent=2))
		f.write("\n]\n") #  terminate array brackets and add an empty line
		if o.verbose:
			print 'Appended json records to "'+o.path+'"'

