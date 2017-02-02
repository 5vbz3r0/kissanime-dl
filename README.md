
# kissanime-dl
**Command-line script to download videos from KissAnime**
  
  
This script requires [`cfscrape`](https://github.com/Anorov/cloudflare-scrape), `requests` and `BeautifulSoup4` to work.   
Install using pip:  

`pip install -U cfscrape requests beautifulsoup4`  
  

##USAGE:
`kissanimedl.py [-o DL_LOCATION] [--quality DL_QUALITY] [--eps EPISODES] URL`  
where  
`DL_LOCATION` is where you want the file to be downloaded  
`DL_QUALITY` is one of `1080p`, `720p`, `480p` and `360p`  
`EPISODES` is of the format `start-end`, or `list,of,episodes,to,be,downloaded`, or `episode_number`  
`URL` is either the `url_of_the_anime's_page_in_KissAnime` or `the_anime's_name_as_it_appears_in_KissAnime`
