# /*$vbZ3r0*/ #

import re, os, sys, argparse, time
import cfscrape
import requests
from bs4 import BeautifulSoup as bs
from base64 import b64decode
from urllib.parse import urlparse

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

def download(url, filename, reporthook=None):
	blocksize = 4096
	trial = 0
	try:
		dl_length = os.path.getsize(filename)
		count = dl_length // blocksize
	except FileNotFoundError:
		dl_length = 0
		count = 0
	code = -1
	s = requests.Session()
	headers =  {'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
				'connection':'keep-alive', 'range':'bytes={}-'.format(dl_length)}
	s.headers.update(headers)
	try:
		r = s.get(url, stream=True, timeout=10)
	except requests.exceptions.Timeout:
		print('\nTimeout\n')
		s.close()
		return 3
	if r.status_code == requests.codes.forbidden:
		raise requests.exceptions.HTTPError('{}'.format(r.status_code))
	if r.status_code == requests.codes.partial:
		write_code = 'ab'
	elif r.status_code == requests.codes.ok and count != 0:
		print("Unable to resume download. Redownloading entire file.")
		write_code = 'wb'
	final_ext = r.headers['content-type'].split('/')[1]
	final_filename = '{}.{}'.format('.'.join(filename.split('.')[:-1]), final_ext)
	if os.path.exists(final_filename):
		code = 0
		return code
	totalsize = int(r.headers['Content-Length']) + dl_length
	try:
		with open(filename, write_code) as f:
			for chunk in r.iter_content(chunk_size=blocksize):
				v = f.write(chunk)
				if reporthook is not None: reporthook(count, blocksize, totalsize)
				count += 1
	except requests.exceptions.Timeout:
		write_code = 'ab'
		print('\nTimeout\n')
		code = 2
	except requests.exceptions.ConnectionError:
		write_code = 'ab'
		print('\nConnection error\n')
		code = 2
	except requests.exceptions.StreamConsumedError:
		write_code = 'ab'
		print('\nConnection error\n')
		code = 2
	except Exception as err:
		print(err)
	else:
		os.rename(filename, final_filename)
		code = 1
	finally:
		s.close()
		return code

def download_episode(url, title, folder, quality):
	trial = 1
	title = re.sub(r"[^a-zA-Z0-9\-\.\(\)\' ]", '_', title)
	filename = title + '.part'
	filename = '{}/{}'.format(folder, filename)
	err = None
	while True:
		if os.path.exists(filename): print('Continuing download of {}'.format(title))
		else: print('Downloading {}'.format(title))
		surl = stream_url(url, title, quality)
		while surl is not None:
			try:
				dl_complete = download(surl, filename=filename, reporthook=dlProgress)
			except requests.exceptions.HTTPError as e:
				err = e
				print("\nUnable to download..\n"+str(err))
				if '403' in str(e):
					trial+=1
					if trial > 10:
						return
					print("Trying again..\nTry: " + str(trial))
					continue
				else:
					break
			else:
				if dl_complete == 0: print('\nFile already exists. Skipping download.\n')
				elif dl_complete == 1: print("\nDownload complete\n")
				elif dl_complete == 2: print("\nUnable to complete download due to bad connection\n")
				elif dl_complete == 3: print("\nUnable to connect to the server\n")
				return
		trial += 1
		if trial > 10:
			return
		print("\nUnable to download..\n" + str(err))
		print("Trying again..\nTry: " + str(trial))

def dlProgress(count, blockSize, totalSize):
	global init_count
	global time_history
	try:
		time_history.append(time.monotonic())
	except NameError:
		time_history = [time.monotonic()]
	try:
		init_count
	except NameError:
		init_count = count
	percent = count*blockSize*100/totalSize
	if totalSize-count*blockSize <= 40000:
		percent = 100
	dl, dlu = unitsize(count*blockSize)
	tdl, tdlu = unitsize(totalSize)
	count -= init_count
	if count > 0:
		n = 1000
		_count = n if count > n else count
		time_history = time_history[-_count:]
		time_weights = list(range(1,len(time_history)-1))
		time_diff = [(i-j)*k for i, j, k in zip(time_history[1:], time_history[:-1], time_weights)]
		try:
			speed = blockSize*(sum(time_weights)) / sum(time_diff)
		except:
			speed = 0
	else: speed = 0
	n = int(percent//4)
	try:
		eta = format_time((totalSize-blockSize*(count+init_count+1))//speed)
	except:
		eta = '>1 day'
	speed, speedu = unitsize(speed, True)
	l = len(tdl)-len(dl)
	sys.stdout.write("\r" + "   {:.2f}".format(percent) + "% |" + "#"*n + " "*(25-n) + "| " + " "*(l+1) + dl + dlu  + "/" + tdl + tdlu + speed + speedu + " " + eta)
	sys.stdout.flush()

def unitsize(size, speed=False):
	B = 'B' if not speed else 'B/s'
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
	if speed: t = "{:4}".format(int(size))+'.'+"{:02}".format(int((size%1)*100))
	else: t = "{:.2f}".format(size)
	return t, unit

def format_time(t):
	sec = t = int(t)
	mn, hr = 0, 0
	if t>=60:
		sec=int(t%60)
		if sec<0: sec=0
		t //= 60
	else: return ("{:2}".format(hr)+":"+"{:02}".format(mn)+":"+"{:02}".format(sec))
	mn = t
	if t>=60:
		mn=int(t%60)
		t //= 60
	else: return ("{:2}".format(hr)+":"+"{:02}".format(mn)+":"+"{:02}".format(sec))
	hr = t
	if t>=24:
		hr=int(t%24)
		t //= 24
	else: return ("{:2}".format(hr)+":"+"{:02}".format(mn)+":"+"{:02}".format(sec))
	return '>1 day  '

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
				else: values = [int(values)-1]
				values.sort()
			setattr(namespace, self.dest, values)
	episodes_help = '''
					Enter the episodes as comma seperated values (without any spaces)
					or as start-end.
					Possible usage: --ep 1,2,3,6 or 
									--ep 3-10 or 
									--ep 200
					'''
	parser = argparse.ArgumentParser(description='A command line script to download videos from KissAnime')
	parser.add_argument('-o', default=os.getcwd(), metavar='Download Folder')
	parser.add_argument('--quality', choices=['1080p', '720p', '360p'], default='1080p')
	parser.add_argument('--eps', default=[-1], help=episodes_help, type=str, action=join)
	parser.add_argument('url', nargs=argparse.REMAINDER, action=join, help='URL/Anime name')
	args = parser.parse_args()
	if args.url is '':
		print("Please enter anime name/url")
		parser.print_help()
		exit()
	return args.o, args.url, args.quality, args.eps

def get_episode_list(url):
	url_base = '{url.scheme}://{url.netloc}'.format(url=urlparse(url))
	page = bs(cfscrape.create_scraper().get(url).content,'lxml')
	urls = page.find('table', {'class': 'listing'}).find_all('a')
	ep_list = []
	for a in reversed(urls):
		urlep = a['href'] if a['href'].startswith('http') else url_base + a['href']
		ep_list.append((urlep, a.string.strip()))
	return ep_list
	

def main():
	folder, url, quality, eps = get_arguments()
	folder, url = get_anime_name(folder, url)
	if not os.path.exists(folder): os.makedirs(folder)
	ep_list = get_episode_list(url)
	for i in eps:
		u, title = ep_list[i]
		download_episode(u, title, folder, quality)

if __name__ == '__main__':
	main()
