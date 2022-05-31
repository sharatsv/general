import tweepy
import pdb
import re
import matplotlib.pyplot as plt


from common import WfClient, convert_time_to_epoch_msec
from datetime import datetime
from nltk.corpus import stopwords          # Help remove stop-words like ['a', 'the', 'and' ..]
from nltk.tokenize import word_tokenize    # Help tokenize sentences
from nltk.sentiment import SentimentIntensityAnalyzer

from pymongo import MongoClient
from wordcloud import WordCloud



# Secret keys
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

# Fetch tweets based on hash-tags
HASH_TAGS = ['#vmware', '#tanzu', '#wavefront']
MAX_RESULTS = 5000

proxy_ip = '192.168.4.196'
sia = SentimentIntensityAnalyzer()


class MongoOps(object):
    """
    Objects in Mongo: db, collection->table, document->data/rows
    """
    def __init__(self, db_name, collection_name):
        # Connect to a mongo-db instance, create a db/collection
        client = MongoClient('localhost', 27017)
        self.collection_name = collection_name
        self.db = client[db_name]
        self.collection = self.db[collection_name]

    def collection_exists(self):
        for collection in self.db.list_collection_names():
            if collection == self.collection_name:
                print('Collection/Table %s exists' % collection)
                return True
        return False

    def insert_docs(self, docs):
        # Insert tweets into Mongo-DB
        self.collection.insert_many(docs)

    def stats(self):
        # Check for content in Mongo-db/collection
        print('Number of documents: {0}'.format(self.collection.count_documents({})))
        for doc in self.collection.find()[:10]:
            print(doc)

    def drop_collection(self, collection_name):
        for collection in self.db.list_collection_names():
            if collection == self.collection_name:
                print('Found collection/table %s. Removing it!' % collection)
                self.collection.drop()
                break


# login to Twitter with extended rate limiting
# must be used with the Tweepy Cursor to wrap the search and enact the waits
def appauth_login():
    # get the authorization from Twitter and save in the Tweepy package
    auth = tweepy.AppAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    # apparently no need to set the other access tokens
    tweepy_api = tweepy.API(auth, wait_on_rate_limit=True)

    # if a null api is returned, give error message
    if not tweepy_api:
        print('Problem Connecting to API with AppAuth')

    # return the Twitter api object that allows access for the Tweepy api functions
    return tweepy_api


def filter_words(orig_sentence):
    # Initialize punctuations
    punctuation_marks = ['!', '(', ')', '-', '[', ']', '{', '}', ';', ':', '\\', '"',
                         '<', '>', '.', '?', '@', '$', '%', '^', '&', '*', '~', '#']

    # Create a stop_words list for English, Spanish etc.
    stop_words = stopwords.words('english')

    tokens = word_tokenize(orig_sentence)
    filter_sentence = [w for w in tokens if w.isascii() and
                       w.lower() not in stop_words and
                       w not in punctuation_marks]
    return filter_sentence


def get_sentiment(tweet):
    score = sia.polarity_scores(tweet)['compound']
    if int(score) == 0:
        sentiment = 'Neutral'
    elif score > 0:
        sentiment = 'Positive'
    elif score < 0:
        sentiment = 'Negative'
    return sentiment


if __name__ == '__main__':
    wf_client = WfClient(proxy_ip)
    # Clean-up old records
    # mongo_old = MongoOps('tweets', 'tweet_info')
    # mongo_old.drop_collection('tweet_info')

    mongo = MongoOps('tweets', 'tweet_info')

    if not mongo.collection_exists():
        api = appauth_login()
        print("Twitter AppAuthorization: ", api)
        # Use the tweepy to fetch tweets from tweeter and insert into Mongo-DB
        search_results = []
        for hash_tag in HASH_TAGS:
            res = [status for status in tweepy.Cursor(api.search_tweets, q=hash_tag).items(MAX_RESULTS)]
            search_results.extend(res)

        tweets = [res._json for res in search_results]
        tweet_docs = []
        for tweet in tweets:
            sentiment = get_sentiment(tweet['text'])
            tweet_docs.append({'time': tweet['created_at'],
                               'tweet': tweet['text'],
                               'user': tweet['user']['name'],
                               'retweeted': tweet['retweeted'],
                               'retweet_count': tweet['retweet_count'],
                               'sentiment': sentiment})
        print(tweet_docs[:10])

        mongo.insert_docs(tweet_docs)

    # Get stats of the db/collection
    mongo.stats()

    # Get stats of sentiment
    for sentiment in ['Neutral', 'Positive', 'Negative']:
        my_query = {'sentiment': sentiment}
        data = mongo.collection.find(my_query)
        data_len = len([item for item in data])
        now = datetime.now()
        now_msec = convert_time_to_epoch_msec(now.strftime("%Y-%m-%d %H:%M:%S"))
        tags_dict = {'sentiment': sentiment}
        wf_client.send_metric(name='my.twitter.sentiment', value=data_len,
                              timestamp=now_msec, tags=tags_dict)

    # Tokenize words, filter them and create a map for hash tags
    final_words = {}
    for document in mongo.collection.find():
        word_tokens = filter_words(document['tweet'])
        for hash_tag in HASH_TAGS:
            tag = re.sub('#', '', hash_tag)
            if tag in word_tokens:
                if tag in final_words.keys():
                    final_words[tag].extend(word_tokens)
                else:
                    final_words[tag] = word_tokens

    # Plot word-clouds
    for hash_tag in final_words:
        fil_words_str = ''  # For word-cloud we need the words to be in a str format
        for word in final_words[hash_tag]:
            fil_words_str += word + " "
        # Plot a word-cloud
        word_cloud = WordCloud(width=600, height=600,
                               background_color='white',
                               min_font_size=10,
                               collocations=False).generate(fil_words_str)

        # Using matplotlib plt visualize the word-cloud
        plt.figure(figsize=(8, 8), facecolor=None)
        plt.imshow(word_cloud)
        plt.axis("off")
        plt.tight_layout(pad=0)

        # plt.show()


pdb.set_trace()
