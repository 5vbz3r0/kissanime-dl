# /*$vbZ3r0*/ #

import re, os, sys, cfscrape, argparse
from bs4 import BeautifulSoup as bs
from time import time, sleep
from base64 import b64decode
from urllib.request import urlopen, URLopener
from urllib.parse import urlparse
try:
	from resumable import urlretrieve
except:
	from urllib.request import urlretrieve

def stream_url(url, title, quality, verbose=False):
	page = bs(cfscrape.create_scraper().get(url).content, 'lxml')
	quality_selector = page.find(id='selectQuality')
	if quality_selector is None:
		print("No downloadable video present")
		return None
	available_qualities = [i.split('">')[-1] for i in str(quality_selector).split("</option>")][:-1]
	if quality not in available_qualities:
		print("{} not availble.. Trying best available quality ({})".format(quality, available_qualities[0]))
		quality = available_qualities[0]
	option = quality_selector.find(text=re.compile(quality)).parent
	encoded_url = option['value']
	decoded_url = b64decode(encoded_url).decode()
	if verbose:
		print('Stream URL: {}'.format(decoded_url))
	return decoded_url

def download_episode(url, title, folder, quality):
	trial = 1
	title = re.sub(r"[^a-zA-Z0-9\-\.\(\)\' ]", '_', title)
	filename = title + '.mp4'
	filename = '{}/{}'.format(folder, filename)
	err = None
	while True:
		if os.path.exists(filename):
				return
		file = filename
		filename += '.part'
		print('Downloading {}'.format(title))
		surl = stream_url(url, title, quality)
		while surl is not None:
			try:
				URLopener.version = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
				headers = urlretrieve(surl, filename=filename, reporthook=dlProgress)
				print("\ndone\n")
				os.rename(filename,file)
				return
			except Exception as e:
				err = e
				print("\nUnable to download..\n"+str(err))
				if 'Forbidden' in str(e):
					trial+=1
					if trial > 10:
						return
					print("Trying again..\nTry: " + str(trial))
					continue
				else:
					break
		trial += 1
		if trial > 10:
			return
		print("\nUnable to download..\n" + str(err))
		print("Trying again..\nTry: " + str(trial))
		filename = file

def dlProgress(count, blockSize, totalSize):
	percent = count*blockSize*100/totalSize
	if totalSize-count*blockSize<=40000:
		percent = 100
	n = int(percent//4)
	dl, dls = unitsize(count*blockSize)
	tdl, tdls = unitsize(totalSize)
	l = len(tdl)-len(dl)
	sys.stdout.write("\r" + "   {:.2f}".format(percent) + "% |" + "#"*n + " "*(25-n) + "| " + " "*(l+1) + dl  + "/" + tdl)
	sys.stdout.flush()

def unitsize(size):
	B = 'B'
	unit = ''
	if size<1024:
		unit = B + ' '
	elif (size/1024) < 1024:
		size /= 1024.0
		unit = 'k' + B
	elif (size/1024) < 1024**2:
		size /= 1024.0**2
		unit = 'M' + B
	else:
		size /= 1024.0**3
		unit = 'G' + B
	return ("{:.2f}".format(size), unit)

def get_anime_name(download_location, anime_name):
	url = "https://kissanime.to/Anime/"
	folder = download_location
	if "kissanime" in anime_name:
		url = anime_name
		anime_name = url.split('/')[-1]
	else:
		anime_name = '-'.join([i for i in map(str.capitalize,anime_name.split())])
		url += anime_name
	if folder.split('/')[-1] != anime_name:
		folder += '/' + anime_name
	return folder, url

def get_arguments():
	class join(argparse.Action):
		def __call__(self, parser, namespace, values, option_string=None):
			if option_string is None:
				values = ' '.join(values)
				if values in ['-h','--help']: parser.print_help()
			elif '--eps' in option_string:
				if '~' in values: values = [-(int(values.split('~')[-1]))]
				elif ',' in values: values = [i-1 for i in map(int, values.split(','))]
				elif '-' in values:
					start, end = [i for i in map(int, values.split('-'))]
					values = [i for i in range(start-1, end)]
				values.sort()
			setattr(namespace, self.dest, values)
	episodes_help = '''
					Enter the episodes as comma seperated values (without any spaces)
					or as start-end.
					Possible usage: --ep 1,2,3,6 or 
									--ep 3-10 or 
									--ep -200 or 
									--ep 100-
					'''
	parser = argparse.ArgumentParser(description='A command line script to download videos from KissAnime')
	parser.add_argument('-o', default=os.getcwd(), metavar='Download Folder')
	parser.add_argument('--quality', choices=['1080p', '720p', '360p'], default='1080p')
	parser.add_argument('--eps', default='~1', help=episodes_help, type=str, action=join)
	parser.add_argument('url', nargs=argparse.REMAINDER, action=join, help='URL/Anime name')
	args = parser.parse_args()
	if args.url is '':
		print("Please enter anime name/url")
		parser.print_help()
		exit()
	return args.o, args.url, args.quality, args.eps

folder, url, quality, eps = get_arguments()
folder, url = get_anime_name(folder, url)
if not os.path.exists(folder): os.makedirs(folder)
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36','Accept-Encoding':'identity'}
url_base = '{url.scheme}://{url.netloc}'.format(url=urlparse(url))
page = bs(cfscrape.create_scraper().get(url).content,'lxml')
urls = page.find('table', {'class': 'listing'}).find_all('a')
ret = []
for a in reversed(urls):
	if a['href'].startswith('http'):
		urlep = a['href']
	else:
		urlep = url_base + a['href']
	ret.append((urlep, a.string.strip()))
for i in eps:
	u, title = ret[i]
	download_episode(u, title, folder, quality)

# implement dl speed, eta