# Scraping and Analyzing Twitter Data on Thai Politics

This project is an attempt to collect and analyze data on how Twitter users react to important political events in Thailand in February 2019. Please check out [my blog post](https://naponjatusripitak.github.io/2019-02-12-TwitterAnalysis/) where I provide a brief overview of the project and the results.

I draw inspiration from Alexander Galea's [tutorial](https://galeascience.wordpress.com/2016/03/18/collecting-twitter-data-with-python/) on using Tweepy to collect data from Twitter Search API. 

I've made some adjustments to his code by using application-only authorization and cursor method, thereby speeding up the entire process.

### Dependencies

You will need access to the Twitter API which means you must have a personal account. Also, please import the following libraries:

```python
# Import modules
import json
import tweepy
import csv
import json
import pandas as pd
import numpy as np
import pickle
from IPython.display import display
import matplotlib.pyplot as plt
import seaborn as sns
import fileinput
import pickle
from pandas import Series
import datetime
import pytz
from tqdm import tqdm
```

### Scraping data from Twitter
First, we'll need a place to store our credentials (consumer key, consumer secret, access key and access secret) for communicating with the API. It's a good idea to store this in your working directory rather than in your codes.

```python
# Create a dictionary to store your twitter credentials

twitter_cred = dict()

# Enter your own consumer_key, consumer_secret, access_key and access_secret
# Replacing the stars ("********")

twitter_cred['CONSUMER_KEY'] = '("********")'
twitter_cred['CONSUMER_SECRET'] = '("********")'
twitter_cred['ACCESS_KEY'] = '("********")'
twitter_cred['ACCESS_SECRET'] = '("********")'

# Save the information to a json so that it can be reused in code without exposing
# the secret info to public

with open('twitter_credentials.json', 'w') as secret_info:
    json.dump(twitter_cred, secret_info, indent=4, sort_keys=True)
```
Use this function to recall these credentials which we have stored in a JSON file in our working directory.

```python
def load_api():
    with open('twitter_credentials.json') as cred_data:
        info = json.load(cred_data)
        consumer_key = info['CONSUMER_KEY']
        consumer_secret = info['CONSUMER_SECRET']
        access_key = info['ACCESS_KEY']
        access_secret = info['ACCESS_SECRET']
    auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
    # load the twitter API via tweepy
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    if (not api):
        print ("Can't Authenticate")
        sys.exit(-1)
    return api
```

Normally, for standard search api with user authentication, there is a rate limit of 180 requests per 15 minutes. Using application-only authorization speeds up that process to 450 requests per 15 minutes.
I found this info from [here](https://bhaskarvk.github.io/2015/01/how-to-use-twitters-search-rest-api-most-effectively./)

These are the functions which we'll use.

First, we need a function for sending requests to the Twitter search API.

```python
# Function for searching tweets    
def tweet_search(api, query, max_tweets, max_id, since_id):
    searched_tweets = []
    try:
        new_tweets = []
        for tweet in tweepy.Cursor(api.search,q=query, count=100, since_id=str(since_id), max_id=str(max_id-1)).items(max_tweets):
            new_tweets.append(tweet)
        print('found',len(new_tweets),'tweets', api.rate_limit_status()['resources']['search'])
        if not new_tweets:
            print('no tweets found')
            return searched_tweets, max_id
        else:
            searched_tweets.extend(new_tweets)
            max_id = new_tweets[-1].id
    except tweepy.TweepError:
        print('exception raised, waiting 15 minutes')
        print('(until:', dt.datetime.now()+dt.timedelta(minutes=15), ')')
        time.sleep(15*60)      
    return searched_tweets, max_id
```

Second, we will use a function that searches for an id associated with the oldest tweet, which we will be using as the starting point for our scraping.

```python
def get_tweet_id(api, date='', days_ago=9, query='a'):
    ''' Function that gets the ID of a tweet. This ID can then be
        used as a 'starting point' from which to search. The query is
        required and has been set to a commonly used word by default.
        The variable 'days_ago' has been initialized to the maximum
        amount we are able to search back in time (9).'''

    if date:
        # return an ID from the start of the given day
        td = date + dt.timedelta(days=1)
        tweet_date = '{0}-{1:0>2}-{2:0>2}'.format(td.year, td.month, td.day)
        tweet = api.search(q=query, count=1, until=tweet_date)
    else:
        # return an ID from __ days ago
        td = dt.datetime.now() - dt.timedelta(days=days_ago)
        tweet_date = '{0}-{1:0>2}-{2:0>2}'.format(td.year, td.month, td.day)
        # get list of up to 10 tweets
        tweet = api.search(q=query, count=10, until=tweet_date)
        print('search limit (start/stop):',tweet[0].created_at)
        # return the id of the first tweet in the list
        return tweet[0].id
```

Third, we need a function to store the data we've collected in our working directory.
        
```python
def write_tweets(tweets, filename):
    ''' Function that appends tweets to a file. '''

    with open(filename, 'a') as f:
        for tweet in tweets:
            json.dump(tweet._json, f)
            f.write('\n')      
 ```
 
 Lastly, we need a main function for looping over all the search terms
 
 ```python

def main():
    ''' This is a script that continuously searches for tweets
        that were created over a given number of days. The search
        dates and search phrase can be changed below. '''



    ''' search variables: '''
    search_phrases = ['#ไทยรักษาชาติ', '#ทรงพระสเลนเดอร์', '#เลือกตั้ง62',
    '#เลือกตั้งปี62', '#แม่มาแล้วธานอส', '#พระราชโองการ', '#ทรงพระสแลนด์เดอร์']
    
    time_limit = 240                          # runtime limit in hours
    max_tweets = 10000                           # number of tweets per search (will be
                                               # iterated over) - maximum is 100
    min_days_old, max_days_old = 2, 4          # search limits e.g., from 7 to 8
                                               # gives current weekday from last week,
                                               # min_days_old=0 will search from right now
    #USA = '39.8,-95.583068847656,2500km'       # this geocode includes nearly all American
                                               # states (and a large portion of Canada)
    

    # loop over search items,
    # creating a new file for each
    for search_phrase in search_phrases:

        print('Search phrase =', search_phrase)

        ''' other variables '''
        name = search_phrase.split()[0]
        json_file_root = name + '/'  + name
        os.makedirs(os.path.dirname(json_file_root), exist_ok=True)
        read_IDs = False
        
        # open a file in which to store the tweets
        if max_days_old - min_days_old == 1:
            d = dt.datetime.now() - dt.timedelta(days=min_days_old)
            day = '{0}-{1:0>2}-{2:0>2}'.format(d.year, d.month, d.day)
        else:
            d1 = dt.datetime.now() - dt.timedelta(days=max_days_old-1)
            d2 = dt.datetime.now() - dt.timedelta(days=min_days_old)
            day = '{0}-{1:0>2}-{2:0>2}_to_{3}-{4:0>2}-{5:0>2}'.format(
                  d1.year, d1.month, d1.day, d2.year, d2.month, d2.day)
        json_file = json_file_root + '_' + day + '.json'
        if os.path.isfile(json_file):
            print('Appending tweets to file named: ',json_file)
            read_IDs = True
        
        # authorize and load the twitter API
        api = load_api()
        
        # set the 'starting point' ID for tweet collection
        if read_IDs:
            # open the json file and get the latest tweet ID
            with open(json_file, 'r') as f:
                lines = f.readlines()
                max_id = json.loads(lines[-1])['id']
                print('Searching from the bottom ID in file')
        else:
            # get the ID of a tweet that is min_days_old
            if min_days_old == 0:
                max_id = -1
            else:
                max_id = get_tweet_id(api, days_ago=(min_days_old-1))
        # set the smallest ID to search for
        since_id = get_tweet_id(api, days_ago=(max_days_old-1))
        print('max id (starting point) =', max_id)
        print('since id (ending point) =', since_id)
        


        ''' tweet gathering loop  '''
        start = dt.datetime.now()
        end = start + dt.timedelta(hours=time_limit)
        count, exitcount = 0, 0
        while dt.datetime.now() < end:
            count += 1
            print('count =',count)
            # collect tweets and update max_id
            tweets, max_id = tweet_search(api, search_phrase, max_tweets,
                                          max_id=max_id, since_id=since_id)
            # write tweets to file in JSON format
            if tweets:
                write_tweets(tweets, json_file)
                exitcount = 0
            else:
                exitcount += 1
                if exitcount == 3:
                    if search_phrase == search_phrases[-1]:
                        sys.exit('Maximum number of empty tweet strings reached - exiting')
                    else:
                        print('Maximum number of empty tweet strings reached - breaking')
                        break


if __name__ == "__main__":
    main()
```
### Parsing JSON data to Pandas

After we have collected all of our data, the next step is to transform them into a pandas dataframe for analysis. We can select only relvevent types of info such as id, created_at, text ฯลฯ

But first, we need a function for storing the hashtags in each tweet into a list so that we won't have to do a string search for them later.

```python
# Function for extracting hashtags into lists
def hash_parse(tweet):
    hashes = list()
    for hashtag in tweet:
        text = hashtag['text']
        hashes.append(text)
    return hashes
```

Instead of loading all of the files into python and appending the info into a list, I would recommend processing the data line by line by writing them into csv and then reading them into pandas. Seems like a roundabout way to do things, but this is actually much faster than processing a large list.

```python
# Load JSON files, go through each line, extract data, and write to csv 
tweet_files = ['#ทรงพระสเลนเดอร์/#ทรงพระสเลนเดอร์_2019-02-07_to_2019-02-08.json',
               '#ทรงพระแคนเซิล/#ทรงพระแคนเซิล_2019-02-07_to_2019-02-08.json',
               '#ไทยรักษาชาติ/#ไทยรักษาชาติ_2019-02-07_to_2019-02-08.json',
               '#พระราชโองการ/#พระราชโองการ_2019-02-07_to_2019-02-08.json',
               '#เลือกตั้ง62/#เลือกตั้ง62_2019-02-07_to_2019-02-08.json',
               '#เลือกตั้งปี62/#เลือกตั้งปี62_2019-02-07_to_2019-02-08.json',
               '#แม่มาแล้วธานอส/#แม่มาแล้วธานอส_2019-02-07_to_2019-02-08.json'
              ]
f = open('tweets.csv', 'w')
writer = csv.writer(f)
for file in tweet_files:
    print(file)
    with open(file, 'r') as f:
        for line in tqdm(f.readlines()):
            tweets = []
            data = json.loads(line)
            tweets.extend([data['id'], data['created_at'], data['user']['screen_name'], data['user']['id'],
                           data['text'], data['retweet_count'], data['favorite_count'], data['in_reply_to_status_id'],
                           data['in_reply_to_user_id'], data['user']['location'], data['place']['full_name']
                           if data['place'] != None else '',
                           hash_parse(data['entities']['hashtags']), data['place']['country_code']
                           if data['place'] != None else '', data['coordinates']['coordinates'][0]
                           if data['coordinates'] != None else 'NaN',
                           data['coordinates']['coordinates'][1]
                            if data['coordinates'] != None else 'NaN'
                          ])
            writer.writerow(tweets)            
f.close()
```
### Analysis and Visualization

First, we read in the csv files.

```python
# Applying the function
keys =  ['id', 'created_at', 'user_name', 'user_id', 'text', 'retweet_count', 'favorite_count', 'in_reply_to_status_id',
              'in_reply_to_user_id', 'user_location', 'place', 'hashtags', 'country_code', 'long', 'latt']
df= pd.read_csv('tweets.csv', names = keys, converters={'hashtags': eval}) # use eval in order to retain list type object for hashtags

```
Drop the duplicates.

```python
# Drop duplicates. This is an important step since a single tweet may contain multiple hashtags and we use the search api with hashtags as our query.
df = df.drop_duplicates(subset='id')
```

Create a function for counting hashtags.

```python
# Function for counting hashtags
def count_hashtags(df):
    hashtag_list = []                          #CREATE EMPTY LIST 
    for i in df.hashtags:    #LOOP OVER EVERY CELL IN ENTITIES_HASHTAGS
        j = ', '.join(i)
        if pd.notnull(j):                      #IF CELL NOT EMPTY
            tags = j.split()                   #SPLIT EACH CELL INTO SEPARATE HASHTAGS
            for t in tags:                     #FOR EACH TAG IN THE CELL
                t = "#"+t                      #ADD '#' SYMBOL TO BEGINNING OF EACH TAG
                t = t.replace(',', '')         #REMOVE COMMAS FROM END OF TAGS
                t = t.lower()                  #MAKE TAG LOWER CASE
                hashtag_list.append(t)         #ADD TAG TO OUR LIST
    top = pd.DataFrame(Series(hashtag_list).value_counts(), columns=['count'])
    return(top)
```
Count all the hashtags and select only the top 10

```python
# Count hashtags and store a list of top hashtags in tags
df_top = count_hashtags(df)
tags = df_top[0:10].index.tolist()
print(tags)
```

    ['#ไทยรักษาชาติ', '#ทรงพระสเลนเดอร์', '#เลือกตั้ง62', '#เลือกตั้งปี62', '#อนาคตใหม่', '#แม่มาแล้วธานอส', '#พระราชโองการ', '#ทรงพระสแลนด์เดอร์', '#พรรคอนาคตใหม่', '#เลือกตั้ง2562']

Create new columns from the top hashtags, if a tweet contains a given hashtag = 1, if not = 0

```python
# Generating columns of hashtags
for tag in tags:
    df[tag] = df.hashtags.apply(lambda x: 1 if tag[1:] in x else 0)
```
ทำการนับความถี่ของ hashtag ต่อนาที

```python
# Counting hashtags per minute
df['time'] = pd.DatetimeIndex(df['created_at'])
grouper = df.groupby([pd.Grouper(key='time', freq = '1Min')])
df1 = grouper[[s for s in tags]].sum()
```
Convert from wide to long formate and deal with the time zone.

```python
# Convert from wide to long format & adjust for time difference
df1.reset_index(level=0, inplace=True)
df1 = df1.melt(id_vars='time')
df1['time'] = pd.to_datetime(df1['time'], format='%Y-%b-%d %H:%M:%S.%f').dt.tz_localize('UTC').dt.tz_convert('Asia/Bangkok')
```

```python
# Remove timezone just in case
df1['time'] = df1['time'].dt.tz_localize(None)
```
Plotting with Plotly

```python
# Log in with plotly credentials
import plotly 
import plotly.plotly as py
import plotly.graph_objs as go
key= ''
plotly.tools.set_credentials_file(username='taozaze', api_key=key)
```


```python
# Generate the data for plotly
d={}
data = []
for tag in tags:
        d["trace_{0}".format(tag)]= go.Scatter(
            x = df1[df1.variable == tag]['time'],
            y = df1[df1.variable == tag]['value'],
            mode = 'lines',
            name = tag
        )
        data.append(d["trace_{0}".format(tag)])

```


```python
# Layout and plot
layout = dict(title = 'Tweet Time Distribution by Hashtag',
              xaxis = dict(title = 'Time'),
              yaxis = dict(title = 'Tweets Per Minute'),
              )

py.iplot(go.Figure(data=data, layout=layout), filename = 'basic-line', auto_open=True)
```




<iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="https://plot.ly/~taozaze/7.embed" height="525px" width="100%"></iframe>




```python
# Creat bar plot for top hashtags

top_hash = df_top.reset_index()[0:10]
data = [
    go.Bar(
        x=top_hash['index'], # assign x as the dataframe column 'x'
        y=top_hash['count']
    )
]

# Layout and plot
layout = dict(title = 'Top Hashtags',
              xaxis = dict(title = 'Hashtag'),
              yaxis = dict(title = 'Hashtag Frequency'),
              )

py.iplot(go.Figure(data=data, layout=layout), filename = 'pandas-bar-chart', auto_open=True)
```

<iframe id="igraph" scrolling="no" style="border:none;" seamless="seamless" src="https://plot.ly/~taozaze/9.embed" height="525px" width="100%"></iframe>
