import redis
import random
import base64
import json
import logging

class URLShortener:

    ##taking a local redis server instance 
    redis_server = None
    
    ## various variables to be used during the input and output of redis variables
    redis_shortened_url_key_fmt = 'shortened.url:%s'
    redis_global_url_list_fmt ='global:urls'
    redis_visitors_list_against_url = 'visitors:%s:url'
    redis_click_list_against_url = 'click:%s:url'

    ##configuring logging setup with root handler
    ##logging.basicConfig(filename='output.log',level=logging.DEBUG)

    ##configuring logging setup with individual instead of default root handler
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    fileHandler = logging.FileHandler("output.log")
    fileHandler.setFormatter(logging.Formatter('%(name)s:%(levelname)s:%(message)s'))
    logger.addHandler(fileHandler)
    
    ##base url which will be concatenated with the modified original URl
    base_url= 'www.manishaTinyURL/'

    def __init__(self):
        self.redis_server = redis.StrictRedis(host='localhost',port=6379,db=0)
        if self.redis_server:
            print("The redis server is running...{0}".format(self.redis_server))
        else:
            print("Go back home")
   
    ##main function used in shortening the url
    def urlshorten(self,long_url):
        url_to_shorten = list(long_url)
        random.shuffle(url_to_shorten)

        if len(url_to_shorten) > 20:
            shortened_url = url_to_shorten[-10:]
            ##print("Hello")
        else:
            shortened_url=url_to_shorten

        jumbled_url = ''.join(shortened_url)
        url_shortened = self.base_url + jumbled_url

        encoded_url = encode_base64(url_shortened)

        ## The formatting of the shortened URl has to be done in the following manner
        url_shortened_key = url_string_formatter(self.redis_shortened_url_key_fmt,encoded_url)
        ##//url_shortned_key="shortened.url:%s" + encoded_url
        ##print("the shortened url key is {0}".format(url_shortened_key))
        self.redis_server.set(url_shortened_key,long_url)
        self.redis_server.lpush(self.redis_global_url_list_fmt,encoded_url)
        ##print("the value for long url key is {0}".format(self.redis_server.get(url_shortened_key)))
        
        return url_shortened , encoded_url
    
    ## this extra facility added for getting the no of visitors and unique no of clicks on the URL
    def visit(self, shortened_url=None, ip_address = None, agent = None, referer=None):
        visitor_info = {'ip_address' : ip_address,
                        'agent' : agent ,
                        'referer' : referer }
        
        url_visitors_list = url_string_formatter(self.redis_visitors_list_against_url, shortened_url)
        self.redis_server.lpush(url_visitors_list,json.dumps(visitor_info))

        url_click_counter = url_string_formatter(self.redis_click_list_against_url,shortened_url)
        self.redis_server.incr(url_click_counter)        

    ##to retreive click value against that particular url
    def click(self, shortened_url=None):
        url_click_counter = url_string_formatter(self.redis_click_list_against_url,shortened_url)
        return self.redis_server.get(url_click_counter) 

    ##to retreive the visitors data
    def visitors_data(self,shortened_url=None):
        visitor_list = []
        url_visitors_list = url_string_formatter(self.redis_visitors_list_against_url,shortened_url)

        for visitors in self.redis_server.lrange(url_visitors_list,0,-1):
            visitor_list.append(json.loads(visitors))
    
        return visitor_list


    def expand(self,encoded_url):
        url_shortened_fmt = url_string_formatter(self.redis_shortened_url_key_fmt,encoded_url)
        result = self.redis_server.get(url_shortened_fmt)
        return result

    def short_url(self):
        return  self.redis_server.lrange(self.redis_global_url_list_fmt,0,100)


##all the utility methods

##checking for the visitor info update 
def visitor_visiting(url_shortener_service):

    print("Visitors Visiting")
    for i in range(0,5):
        print("getting URLS")
        for url in url_shortener_service.short_url():
            decoded_url = decode_base64(url)
            print("The decoded is %s:" % decoded_url)
            url_shortener_service.visit(decoded_url)

    url_shortener_service.logger.info("recent visitors")

    for url in url_shortener_service.short_url():
        expanded_url =url_shortener_service.expand(url)
        decoded_url = decode_base64(url)
        click_count = url_shortener_service.click(decoded_url)
        recent_visitor_list = url_shortener_service.visitors_data(decoded_url)

        url_shortener_service.logger.info("The visitor count and click for {0} ie {1} is {2} and {3}".
        format(decoded_url,expanded_url,len(recent_visitor_list),click_count)) 
    

##using a formatter to store data in the database
def url_string_formatter(string_fmt, string_value):
    return string_fmt % string_value

##encoding technique
def encode_base64(url):
    bytes_format = url.encode('utf-8')
    return base64.b64encode(bytes_format)

##decoding technique
def decode_base64(encoded_string):
    return base64.b64decode(encoded_string)

##utility functions to read input(urls) from a text file 
def readInputFile(file_name , url_shortener_service):
    with open(file_name, 'r') as infile:
        for line in infile:
            #for ignoring all the commented line
            if '#' not in line[0]:
                url_shortened ,encoded_url = url_shortener_service.urlshorten(line)
                url_shortener_service.logger.debug("The shortened url {0} and its encoded version is {1}".format(url_shortened,encoded_url))
                expanded_url = url_shortener_service.expand(encoded_url)
                url_shortener_service.logger.warning("The expanded url for the same is {0}".format(expanded_url))

def main():
    url_shortener_service = URLShortener()
    
    ##we want it to read the url from a file
    readInputFile('sampleURL.txt',url_shortener_service)

    ##calling teh visitors function
    visitor_visiting(url_shortener_service)

if __name__ == "__main__":
   main() 