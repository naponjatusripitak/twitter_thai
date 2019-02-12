# -*- coding: utf-8 -*-
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

# Def

def hash_parse(tweet):
    hashes = list()
    for hashtag in tweet:
        text = hashtag['text']
        hashes.append(text)
    return hashes
    
# Load JSON files
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
