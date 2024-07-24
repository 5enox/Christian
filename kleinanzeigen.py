import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.crawler import CrawlerProcess
from scrapy.exporters import CsvItemExporter
import json
import re
import csv
import configparser
import urllib.parse



class KleinanzeigenSpider(CrawlSpider):
    name = 'kleinanzeigenspider'
    headers = {
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            # 'accept-encoding':'gzip, deflate, br',
            'accept-language':'en-US,en;q=0.9,en-GB;q=0.8,id;q=0.7',
            'sec-ch-ua':'"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile':'?0',
            'sec-ch-ua-platform':'"Chrome OS"',
            'sec-fetch-dest':'document',
            'sec-fetch-mode':'navigate',
            'sec-fetch-site':'same-origin',
            'sec-fetch-user':'?1',
            'upgrade-insecure-requests':'1',
            'user-agent':'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            }
    def start_requests(self):
        urlTemplate = 'https://www.kleinanzeigen.de/s-buecher-zeitschriften/sortierung:preis/preis:0:5/#bookTitle#/k0c76'
        start_urls = []
        with open("awin_feed_clean.csv", "r", encoding="utf8") as csvfile:   
            lines = csv.reader(csvfile, delimiter=',')
            for line in lines:
                bookTitle = urllib.parse.quote(line[1])
                urlToBook = re.sub('#bookTitle#', bookTitle, urlTemplate)
                start_urls.append(urlToBook + '|' + line[2] + '|' + line[0])


        for start_url in start_urls:
            metains = {
                'bookprice':start_url.split('|')[1], 
                'awinurl': start_url.split('|')[2]
                }
            yield scrapy.Request(start_url.split('|')[0], headers=self.headers,callback=self.parse,dont_filter=True,meta=metains)

    def parse(self, response):
        p = {
            'AwinURL': response.meta['awinurl'],
            'Price':'',
            'Title':'',
            'URL':'url',
        }
        listings = response.xpath("//*[@class='aditem']")
        for listing in listings:
            title = listing.xpath(".//a[@class='ellipsis']/text()").get()
            price = listing.xpath(".//*[@class='aditem-main--middle--price-shipping--price']/text()").get()
            try:
                price = price.strip()
                price = price.replace(" ","")
                if(',' not in price):
                    price = price.split('€')[0]
            except:break
            
            try:
                if float(price) > float(response.meta['bookprice']):break
            except ValueError:break
            
            url = response.request.url
            
            p['Price'] = price
            p['Title'] = title
            p['URL'] = url
        if p['Title'] == '': pass
        else:yield(p)
        
        
c = CrawlerProcess(
    settings={
        "FEEDS":{
            "kleinanzeigen.csv" : {"format" : "csv",
                                "overwrite":True,
                                "encoding": "utf-8-sig"
                            }},
        "CONCURRENT_REQUESTS":100, # default 16
        "CONCURRENT_REQUESTS_PER_DOMAIN":200, # default 8 
        "CONCURRENT_ITEMS":1000, # default 100
        "DOWNLOAD_DELAY": 1,
        "DEPTH_PRIORITY":1,
        "FEED_EXPORTERS":{
            'csv':'exporters.CsvCustomSeperator'
        },
        # "DEPTH_LIMIT":0, # how many pages down to go in pagination
        # "JOBDIR":'crawls/post_crawler',
        "DUPEFILTER_DEBUG":False, # don't rescrape a page
        # "RETRY_HTTP_CODES":[500, 503, 504, 400, 408, 307, 403,429],
        "HTTPERROR_ALLOW_ALL":True,
        "ROBOTSTXT_OBEY":False,
        # "LOG_LEVEL":"INFO",
        "COOKIES_ENABLED":True,
        "USER_AGENT":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 OPR/86.0.4363.64',
        # "DEFAULT_REQUEST_HEADERS":{
        #     'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        #     # 'accept-encoding':'gzip, deflate, br',
        #     'accept-language':'en-US,en;q=0.9',
        #     'sec-ch-ua':'" Not A;Brand";v="99", "Chromium";v="98", "Opera GX";v="84"',
        #     'sec-ch-ua-mobile':'?0',
        #     'sec-ch-ua-platform':'"Windows"',
        #     'sec-fetch-dest':'document',
        #     'sec-fetch-mode':'navigate',
        #     'sec-fetch-site':'none',
        #     'sec-fetch-user':'?1',
        #     'upgrade-insecure-requests':'1',
        #     'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 OPR/86.0.4363.64',
        #     }
    }
)
c.crawl(KleinanzeigenSpider)
c.start()