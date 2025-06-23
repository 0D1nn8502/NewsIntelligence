import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Union

import aiohttp
import feedparser
import requests
import urllib3
from pydantic import BaseModel

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 

# Configure logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

  
feeds = {
    "Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "TOI": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
    "Mint": "https://www.livemint.com/rss/politics",
    "IndianExpress": "https://indianexpress.com/section/explained/explained-economics/feed/",
    "ZeeNews": "https://zeenews.india.com/rss/india-national-news.xml",
    "UN_APAC": "https://news.un.org/feed/subscribe/en/news/region/asia-pacific/feed/rss.xml",
    "CNBC_Asia": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19832390"
}
    

models = []     


class Rss_Feed_Parser: 
    
    """ 
        Parses RSS feeds into database-friendly structure 
    
        feed : feedparser feed (https://feedparser.readthedocs.io/en/latest/common-rss-elements.html)
        
    """
    
    def __init__(self, feed, name):  
        self.feed = feed 
        self.name = name 
    
    def get_channel_elements(self):      
        if self.feed.entries: 
            return list(self.feed.entries[0].keys()) 
        
        return [] 
    

    def get_summaries(self, numSummaries : int): 
        
        for entry in self.feed.entries[:numSummaries]: 
            yield entry.get('summary', entry.get('description', entry.get('title', 'No Description')))   
        
        

    def get_news_info(self, numSummaries : int): 
        
        summs = [] 
        for i, entry in enumerate(self.feed.entries): 
            
            if i >= numSummaries: 
                break 
            
            ## Info from rss feeds ## 
            title = entry.get('title')
            summary = entry.get('summary', entry.get('description')) 
            link = entry.get('link') 
            
            if title or summary: 
                
                obj = {'title' : title, 'summary': summary}  
                
                if link: 
                    obj['link'] = link 
                
                summs.append(obj) 
            
            
        return summs 
        


class News_aggregator: 
    
    """ 
        Fetch fresh items of the various rss feeds. 

    """

    def __init__(self, feeds: Dict[str, str], timeout: int = 10, verify_ssl: bool = False): 
        self.feeds = feeds 
        self.timeout = timeout 
        self.verify_ssl = verify_ssl 
        
        
    async def fetch_feed_async(self, session: aiohttp.ClientSession, 
                             name: str, url: str) -> Optional[Rss_Feed_Parser]:
        
        """Asynchronously fetch and parse a single RSS feed"""
        try:
            async with session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse with feedparser in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    feed = await loop.run_in_executor(
                        None, feedparser.parse, content
                    )
                    
                    if feed.bozo == 0 or feed.entries:  # Valid feed or has entries despite issues
                        logger.info(f"Successfully fetched {name}: {len(feed.entries)} entries")
                        return Rss_Feed_Parser(feed, name)
                    else:
                        logger.warning(f"Invalid feed format for {name}")
           
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {name}")
        except Exception as e:
            logger.error(f"Error fetching {name}: {str(e)}")
        
        return None
        
        
    async def fetch_feeds_async(self) -> Dict[str, Rss_Feed_Parser]: 
         
        """ Asynchronously fetch and parse a single RSS feed """
        parsers = {}
        
        async with aiohttp.ClientSession() as session: 
            
             
                async with asyncio.TaskGroup() as tg: 
                    
                    ## Create fetching tasks ## 
                    tasks = {
                        name: tg.create_task(self.fetch_feed_async(session, name, link))  
                        for name, link in self.feeds.items() 
                    } 
                
                # All tasks completed successfully, collect results #    
                for name, task in tasks.items():
                    result = task.result()
                    
                    if result:
                        parsers[name] = result
                        
                    
                    # Continue with successful feeds
                    for name, task in tasks.items():
                        if task.done() and not task.exception():
                            result = task.result()
                            if result:
                                parsers[name] = result
            
        return parsers 
         
    
    async def get_aggregated_news(self, limits: Union[int, Dict[str, int]], default_limit: int = 5) -> Dict[str, List[Dict]]:   
        
        """ limits: Per source limits """ 
        
        # Fetch all feeds first
        parsers = await self.fetch_feeds_async()  
        aggregated_news = {} 
        
        for sourcename, parser in parsers.items(): 
            
            if isinstance(limits, int):
                # Single limit for all sources
                limit = limits
                
            elif isinstance(limits, dict):
                # Per-source limits
                limit = limits.get(sourcename, default_limit)
                
            else:
                limit = default_limit
            
        
            news_items = parser.get_news_info(limit)  
            aggregated_news[sourcename] = news_items 
            
            logger.info(f"Retrieved {len(news_items)} items from {sourcename} (limit: {limit})") 
            
        return aggregated_news 
    


async def main(): 
    
    # Initialize aggregator
    aggregator = News_aggregator(feeds) 
    
    print("\n=== Method 2: Per-source limits ===")
    custom_limits = {
        "Hindu": 8, 
        "TOI": 5,  
        "Mint": 5, 
        "IndianExpress": 6, 
        "UN_APAC": 10 
    } 
    
    news = await aggregator.get_aggregated_news(custom_limits, default_limit=2)
    for source, items in news.items():
        print(f"{source}: {len(items)} items") 
    
    
    
        
    
if __name__ == "__main__":
    asyncio.run(main()) 


        

    
         

        
        
        