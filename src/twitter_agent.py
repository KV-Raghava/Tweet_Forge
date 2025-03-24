#!/usr/bin/env python3
"""
Twitter Posting Agent - Automatically posts tweets at regular intervals.

This script connects to the Twitter API using Tweepy and posts tweets from a
predefined source file at regular intervals.
"""

import os
import time
import random
import logging
import schedule
from typing import List, Optional
import tweepy
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("twitter_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TwitterAgent:
    """Twitter posting agent that posts tweets at regular intervals."""
    
    def __init__(self, tweets_file: str = "tweets.txt"):
        """
        Initialize the Twitter agent.
        
        Args:
            tweets_file: Path to the file containing tweets to post.
        """
        # Load environment variables
        load_dotenv()
        
        # Get Twitter API credentials
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.tweet_interval = int(os.getenv("TWEET_INTERVAL_MINUTES", "60"))
        
        # Get OpenAI API key
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ai_client = None
        if self.openai_api_key:
            self.ai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OPENAI_API_KEY not found, AI tweet generation will not be available")
        
        # Check if credentials are provided
        self._validate_credentials()
        
        # Initialize Twitter API client
        self.api = self._init_twitter_api()
        
        # Load tweets from file
        self.tweets_file = tweets_file
        self.tweets = self._load_tweets()
        
        logger.info(f"TwitterAgent initialized with {len(self.tweets)} tweets")
    
    def _validate_credentials(self) -> None:
        """Validate that all required credentials are provided."""
        missing = []
        if not self.api_key:
            missing.append("TWITTER_API_KEY")
        if not self.api_secret:
            missing.append("TWITTER_API_SECRET")
        if not self.access_token:
            missing.append("TWITTER_ACCESS_TOKEN")
        if not self.access_token_secret:
            missing.append("TWITTER_ACCESS_TOKEN_SECRET")
        if not self.bearer_token:
            missing.append("TWITTER_BEARER_TOKEN")
            
        if missing:
            error_msg = f"Missing Twitter API credentials: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
    def _validate_ai_credentials(self) -> bool:
        """Validate that OpenAI API key is provided."""
        if not self.openai_api_key:
            logger.warning("OpenAI API key not provided. AI tweet generation unavailable.")
            return False
        return True
    
    def _init_twitter_api(self):
        """Initialize and return both Twitter API clients (v1.1 and v2)."""
        # Create OAuth 1.0a handler
        auth = tweepy.OAuth1UserHandler(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
        
        # Create API v1.1 instance (for some endpoints that still work)
        self.api_v1 = tweepy.API(auth)
        
        # Create API v2 client
        client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True
        )
        
        return client
    
    def _load_tweets(self) -> List[str]:
        """Load tweets from the specified file."""
        try:
            with open(self.tweets_file, "r") as f:
                tweets = [line.strip() for line in f if line.strip()]
            
            if not tweets:
                logger.warning(f"No tweets found in {self.tweets_file}")
            
            return tweets
        except FileNotFoundError:
            logger.error(f"Tweets file not found: {self.tweets_file}")
            raise
    
    def post_tweet(self) -> None:
        """Post a random tweet using the most compatible API method with rate limit handling."""
        if not self.tweets:
            logger.warning("No tweets available to post")
            return
        
        # Select a random tweet
        tweet = random.choice(self.tweets)
        used_tweets = set()
        used_tweets.add(tweet)
        
        logger.info(f"Attempting to post tweet: {tweet}")
        
        # Initialize backoff parameters
        max_retries = 5
        initial_backoff = 60  # seconds
        
        for retry in range(max_retries + 1):
            if retry > 0:
                # Calculate exponential backoff with jitter
                backoff_time = initial_backoff * (2 ** (retry - 1)) + random.uniform(0, 10)
                logger.warning(f"Rate limit hit. Retry {retry}/{max_retries} after {backoff_time:.1f} seconds")
                time.sleep(backoff_time)
                
                # Try a different tweet on retry to avoid duplicate errors
                available_tweets = [t for t in self.tweets if t not in used_tweets]
                if not available_tweets:
                    # Reset if we've used all tweets
                    used_tweets = set()
                    available_tweets = self.tweets
                
                tweet = random.choice(available_tweets)
                used_tweets.add(tweet)
                logger.info(f"Retrying with new tweet: {tweet}")
            
            # Try multiple methods to post the tweet, starting with most likely to work
            methods_tried = []
            
            # Method 1: Try API v2 with OAuth 1.0a
            try:
                methods_tried.append("API v2 (OAuth 1.0a)")
                response = self.api.create_tweet(text=tweet)
                
                if response and hasattr(response, 'data'):
                    tweet_id = response.data['id']
                    logger.info(f"Successfully posted tweet with ID {tweet_id}: {tweet}")
                    return
            except tweepy.errors.TooManyRequests as e:
                logger.warning(f"Rate limit exceeded: {e}")
                # Continue to retry loop
                continue
            except Exception as e:
                logger.warning(f"Method 1 failed: {e}")
            
            # Method 2: Try API v1.1 with OAuth 1.0a
            try:
                methods_tried.append("API v1.1 (OAuth 1.0a)")
                status = self.api_v1.update_status(tweet)
                logger.info(f"Successfully posted tweet with ID {status.id}: {tweet}")
                return
            except tweepy.errors.TooManyRequests as e:
                logger.warning(f"Rate limit exceeded: {e}")
                # Continue to retry loop
                continue
            except Exception as e:
                logger.warning(f"Method 2 failed: {e}")
            
            # If both methods failed but not due to rate limits, no need to retry
            if "TooManyRequests" not in str(e):
                break
        
        # If we've reached here, all methods and retries failed
        logger.error(f"Failed to post tweet after {max_retries} retries")
        logger.error(f"Methods tried: {', '.join(methods_tried)}")
        logger.error("Your Twitter API access level may have insufficient permissions or rate limits.")
        logger.error("Recommended actions:")
        logger.error("1. Verify 'Read and write' permissions are enabled in developer portal")
        logger.error("2. Consider upgrading to Elevated API access or a paid tier")
        logger.error("3. Increase the tweet interval (currently {self.tweet_interval} minutes)")
        logger.error("4. Check Twitter's rate limit documentation for your tier: https://developer.twitter.com/en/docs/twitter-api/rate-limits")
    
    def generate_ai_tweet(self, topic: Optional[str] = None) -> str:
        """Generate a tweet using AI based on the given topic.
        
        Args:
            topic: Optional topic to focus the tweet on. Default is CryptoXpress platform.
            
        Returns:
            AI-generated tweet text.
        """
        if not self._validate_ai_credentials() or not self.ai_client:
            logger.warning("OpenAI client not available. Using fallback tweet method.")
            return random.choice(self.tweets)
            
        try:
            # Default context about CryptoXpress
            context = """
            CryptoXpress is a cryptocurrency platform offering:
            - Simplified crypto trading
            - Decentralized finance (DeFi) solutions
            - NFT marketplace
            - Payment solutions
            - Banking services
            - Aims to make crypto accessible to regular users
            - Available on web and mobile
            - Focus on security and ease of use
            - Website: https://www.cryptoxpress.com/
            """
            
            topic_prompt = f"about {topic}" if topic else "about CryptoXpress services"
            
            # Use OpenAI to generate the tweet
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using 3.5 for cost efficiency, can use gpt-4 for higher quality
                messages=[
                    {"role": "system", "content": f"You are a marketing expert for a cryptocurrency platform called CryptoXpress. Generate ONE short, engaging tweet {topic_prompt}. The tweet must be under 280 characters, include relevant hashtags, and be written in a professional yet approachable tone. Do not use excessive emojis or hype language. Include the URL https://www.cryptoxpress.com/ only if it fits naturally. Context: {context}"},
                    {"role": "user", "content": f"Write a single marketing tweet {topic_prompt}. Must be under 280 characters."}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            tweet_text = response.choices[0].message.content.strip()
            logger.info(f"AI generated tweet: {tweet_text}")
            
            # Ensure the tweet is not too long
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
                
            return tweet_text
            
        except Exception as e:
            logger.error(f"Failed to generate AI tweet: {e}")
            # Fallback to random predefined tweet
            return random.choice(self.tweets)
    
    def post_ai_tweet(self, topic: Optional[str] = None) -> None:
        """Generate and post an AI-created tweet about CryptoXpress.
        
        Args:
            topic: Optional specific topic to focus the tweet on.
        """
        logger.info(f"Generating AI tweet{' about ' + topic if topic else ''}")
        
        # Generate the tweet
        tweet = self.generate_ai_tweet(topic)
        
        logger.info(f"Attempting to post AI-generated tweet: {tweet}")
        
        # Try multiple methods to post the tweet, starting with most likely to work
        methods_tried = []
        
        # Method 1: Try API v2 with OAuth 1.0a
        try:
            methods_tried.append("API v2 (OAuth 1.0a)")
            response = self.api.create_tweet(text=tweet)
            
            if response and hasattr(response, 'data'):
                tweet_id = response.data['id']
                logger.info(f"Successfully posted AI tweet with ID {tweet_id}: {tweet}")
                return
        except Exception as e:
            logger.warning(f"Method 1 failed: {e}")
        
        # Method 2: Try API v1.1 with OAuth 1.0a
        try:
            methods_tried.append("API v1.1 (OAuth 1.0a)")
            status = self.api_v1.update_status(tweet)
            logger.info(f"Successfully posted AI tweet with ID {status.id}: {tweet}")
            return
        except Exception as e:
            logger.warning(f"Method 2 failed: {e}")
        
        # If we've reached here, all methods failed
        logger.error(f"Failed to post AI tweet using methods: {', '.join(methods_tried)}")
    
    def run(self, use_ai: bool = False, ai_topics: List[str] = None) -> None:
        """Run the Twitter agent continuously.
        
        Args:
            use_ai: Whether to use AI-generated tweets instead of predefined ones.
            ai_topics: List of topics to cycle through for AI tweets. If None, general tweets about CryptoXpress will be generated.
        """
        logger.info(f"Starting Twitter agent, posting every {self.tweet_interval} minutes")
        logger.info(f"AI tweet generation: {'Enabled' if use_ai else 'Disabled'}")
        
        # Initialize topic rotation if AI is enabled
        if use_ai and ai_topics:
            self.ai_topics = ai_topics
            self.current_topic_index = 0
            logger.info(f"AI topics rotation enabled with topics: {', '.join(ai_topics)}")
        else:
            self.ai_topics = None
        
        # Define the function to run on schedule
        def scheduled_post():
            if use_ai:
                topic = None
                if self.ai_topics:
                    topic = self.ai_topics[self.current_topic_index]
                    self.current_topic_index = (self.current_topic_index + 1) % len(self.ai_topics)
                self.post_ai_tweet(topic)
            else:
                self.post_tweet()
        
        # Schedule the tweet posting
        schedule.every(self.tweet_interval).minutes.do(scheduled_post)
        
        # Post one tweet immediately on startup
        scheduled_post()
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    try:
        # Set a much longer interval between tweets to avoid Twitter's rate limits
        os.environ["TWEET_INTERVAL_MINUTES"] = "180"  # 3 hours between tweets
        
        agent = TwitterAgent()
        
        # Define cryptocurrency-related topics to rotate through
        crypto_topics = [
            "cryptocurrency trading",
            "DeFi solutions",
            "NFT marketplace",
            "secure crypto payments",
            "crypto banking",
            "mobile crypto app",
            "blockchain technology",
            "crypto for beginners",
            "crypto security"
        ]
        
        # For now, use regular tweets (not AI) to avoid complexity
        # Leaving the AI code in place for future use when rate limits are resolved
        agent.run(use_ai=True)
        
        # Uncomment to use AI tweets when rate limits are resolved:
        # agent.run(use_ai=True, ai_topics=crypto_topics)
    except KeyboardInterrupt:
        logger.info("Twitter agent stopped by user")
    except Exception as e:
        logger.error(f"Twitter agent failed: {e}")