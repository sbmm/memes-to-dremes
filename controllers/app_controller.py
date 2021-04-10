from __future__ import annotations

from typing import cast, Any, Dict, Optional, Tuple

from tweepy import Stream

from .base_controller import BaseController
from models.app_model import AppModel
from models.influencers_tweet_model import InfluencersTweetDAO
from models.influencers_model import InfluencersDAO
from ShaunsWork.sentimentanalysis import SentimentAnalysis


class AppController(BaseController):
    MONTH_MAP = {
        'Jan': '01',
        'Feb': '02',
        'Mar': '03',
        'Apr': '04',
        'May': '05',
        'Jun': '06',
        'Jul': '07',
        'Aug': '08',
        'Sep': '09',
        'Oct': '10',
        'Nov': '11',
        'Dec': '12'
    }

    def __init__(self, model) -> None:
        super().__init__(model)

        self._influencersDAO = InfluencersDAO()
        self._influencersTweetDAO = InfluencersTweetDAO()
        self._sentimentAnalysis = SentimentAnalysis()
        # TODO: add instance of twitter api class for making calls to api

        self._twitterStream: Stream = Optional[Stream]

    @property
    def twitterStream(self) -> Stream:
        return self._twitterStream

    @twitterStream.setter
    def twitterStream(self, value) -> None:
        self._twitterStream = value

    @property
    def influencersDAO(self) -> InfluencersDAO:
        return self._influencersDAO

    @property
    def sentimentAnalysis(self) -> SentimentAnalysis:
        return self._sentimentAnalysis

    @property
    def influencersTweetDAO(self) -> InfluencersTweetDAO:
        return self._influencersTweetDAO

    def startStream(self) -> None:
        # TODO: get followers and filters
        keywords = ["bitcoin", "btc"]
        influencers = ["1309965256286973955"]
        self.twitterStream.influencers = influencers
        self.twitterStream.filter(track=keywords, follow=influencers, is_async=True)

    def restartStream(self) -> None:
        self.twitterStream.disconnect()
        self.startStream()

    def changeBtnText(self, value):
        cast(AppModel, self.model).btnText = value

    def addInfluencer(self, twitterHandle: str) -> None:
        # Step 1: Get influencer data from twitter.
        userID, name, account = self._getUserData(twitterHandle)

        # Step 2: Add influencer to database.
        # TODO: use updated method that takes in userID as well.
        self.influencersDAO.add_influencer(name, account)

        # Step 3: Get historic tweets for influencer.
        rawTweets: List[Dict[str, Any]] = self._getUserTweets(twitterHandle)

        # Step 4: Perform sentiment analysis on historic data.
        # TODO: figure out return type of sentiment analysis method
        tweets = self._performSentimentAnalysis(rawTweets)

        # Step 5: Add tweets to database alongside their sentiment score.
        # TODO: insert results into database
        for tweet in tweets:
            self.addTweet(tweet)

        # TODO: automatically update influencer / coin lists
        # Step 6: Restart streamer so it picks up new influencer to follow.
        self.restartStream()

        # TODO: find a way to update model with data so it works and triggers UI update.
        # Step 7: Update UI with new data
        cast(AppModel, self.model).tweetHistory = tweets

    # TODO: use class for api calls to retrieve user data.
    def _getUserData(self, twitterHandle: str) -> Tuple[str, str, str]:
        pass

    # TODO: use class for api calls to retrieve user tweet history.
    def _getUserTweets(self, twitterHandle: str) -> List[Dict[str, Any]]:
        pass

    # TODO: use class for sentiment analysis to perform analysis on tweets.
    def _performSentimentAnalysis(self, tweets: List[Dict[str, Any]]):
        pass

    def updateTweetHistory(self) -> None:
        # get tweets from database
        # pass tweets to model
        pass

    def addTweet(self, tweet_data, crypto_ticker) -> None:
        # run SentinmentAnalysis, score the tweet, append to tweet data
        sentiment_score = self.sentimentAnalysis.get_tweet_sentiment(tweet_data)

        # add tweet to database - running the DAO method to add to the database
        influencer_twitter_acc = tweet_data['user']['screen_name']
        tweet_ID = tweet_data['id']
        tweet_text = tweet_data['text']

        # convert tweet date-time to ISO-8601 format before adding to database
        tweet_date_time_list = tweet_data['created_at'].split()
        tweet_year = tweet_date_time_list[5]

        tweet_month = self.MONTH_MAP[tweet_date_time_list[1]]
        tweet_day = tweet_date_time_list[2]
        tweet_time = tweet_date_time_list[3]
        tweet_date_time = tweet_year + '-' + tweet_month + '-' + tweet_day + ' ' + tweet_time

        tweetDAO = InfluencersTweetDAO()
        tweetDAO.add_influencer_tweet(
            influencer_twitter_acc, tweet_ID, tweet_text, tweet_date_time, crypto_ticker, sentiment_score
        )
        # pass tweet to model
        # manually trigger signal here
        model: AppModel = cast(AppModel, self.model)
        model.btnText = str(sentiment_score)