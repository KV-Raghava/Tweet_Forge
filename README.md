# Twitter Marketing Agent

A robust, automated Twitter posting tool designed to publish scheduled tweets for marketing campaigns. This agent can use both predefined tweets and AI-generated content focused on marketing for cryptocurrency platforms.

## Features

- **Automated Tweet Posting**: Schedule tweets at customizable intervals
- **Multiple Posting Methods**: Uses both Twitter API v1.1 and v2 for maximum compatibility
- **Rate Limit Handling**: Implements exponential backoff with jitter for reliable operation
- **AI-Powered Content**: Optional OpenAI integration to generate dynamic, context-aware tweets
- **Topic Rotation**: Cycles through predefined topics for varied content
- **Robust Error Handling**: Comprehensive error detection and recovery
- **Detailed Logging**: Complete visibility into agent operations

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd marketing_tweets
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the project root with the following variables:
   ```
   # Twitter API Credentials
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
   TWITTER_BEARER_TOKEN=your_bearer_token
   
   # Optional: OpenAI API key for AI tweet generation
   OPENAI_API_KEY=your_openai_api_key
   
   # Posting interval in minutes (default: 180)
   TWEET_INTERVAL_MINUTES=180
   ```

2. Customize the tweets in `tweets.txt`, with one tweet per line.

## Twitter Developer Setup

1. Create a Twitter Developer account at [developer.twitter.com](https://developer.twitter.com)
2. Create a new project and app
3. Configure app permissions:
   - Set "User authentication settings" to "Read and write"
   - Enable OAuth 1.0a and OAuth 2.0
4. Generate API keys and access tokens
5. Add them to your `.env` file

## Usage

### Basic Usage

Run the Twitter agent with predefined tweets:

```bash
python src/twitter_agent.py
```

### Advanced Configuration

You can modify settings in the `src/twitter_agent.py` script:

#### Adjust Posting Interval

```python
# Set a longer interval to avoid rate limits
os.environ["TWEET_INTERVAL_MINUTES"] = "360"  # 6 hours
```

#### Enable AI Tweet Generation

```python
# Define cryptocurrency-related topics
crypto_topics = [
    "cryptocurrency trading",
    "DeFi solutions",
    "NFT marketplace"
    # Add more topics as needed
]

# Enable AI tweet generation with topic rotation
agent.run(use_ai=True, ai_topics=crypto_topics)
```

## AI Tweet Generation

When AI tweet generation is enabled, the agent uses OpenAI to create dynamic, engaging tweets about the specified topics. Each tweet is focused on marketing for CryptoXpress and includes:

- Professional marketing language
- Relevant hashtags
- Specific focus on the current topic in rotation
- Adherence to Twitter's 280 character limit

## Troubleshooting

### Rate Limiting Issues

If you encounter rate limit errors:
1. Increase the `TWEET_INTERVAL_MINUTES` value
2. Check your Twitter API access level (Basic, Elevated, or Premium)
3. Verify that your app has the correct permissions

### API Authentication Errors

If you see authentication errors:
1. Regenerate your tokens in the Twitter Developer Portal
2. Ensure OAuth 1.0a is enabled
3. Verify your app has "Read and write" permissions

### OpenAI Integration Issues

If AI tweet generation is failing:
1. Check your OpenAI API key is valid
2. Verify you have sufficient credits in your OpenAI account
3. Try using a different model by modifying the `model` parameter in `generate_ai_tweet()`

## License

[MIT License](LICENSE)

## Credits

Developed by CryptoXpress Team