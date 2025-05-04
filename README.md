# TruthLens: Misinformation Surveillance Platform

TruthLens is a Model Context Protocol (MCP) server that provides AI assistants with tools to detect, analyze, and verify potential misinformation. Built with Python and the MCP framework, it enables automated fact-checking and misinformation monitoring capabilities.

## 📋 Features

- **Web Content Ingestion**: Extract content from URLs and news sources
- **Claim Extraction**: Automatically identify factual claims in text using Google's Gemini AI
- **Claim Verification**: Assess the veracity of claims using AI and external knowledge sources
- **News Monitoring**: Search for and analyze news content for misinformation
- **Trend Analysis**: Track and report on trending misinformation by topic

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    TruthLens MCP Server                   │
├───────────────┬───────────────────────┬───────────────────┤
│  Data Sources │      Core Tools       │  External APIs    │
├───────────────┼───────────────────────┼───────────────────┤
│               │                       │                   │
│  Web Content  │   ingest_url()        │   Google Gemini   │
│  News Sites   │   extract_claims()    │   NewsAPI         │
│  Social Media │   verify_claim()      │   Wikipedia API   │
│  Wikipedia    │   search_news()       │   Reddit API      │
│  Fact-check   │   analyze_source()    │   Fact Check API  │
│  Databases    │   get_trending_info() │                   │
│               │   setup_monitor()     │                   │
│               │                       │                   │
└───────────────┴───────────────────────┴───────────────────┘
                          │
                          ▼
┌───────────────────────────────────────────────────────────┐
│                    MCP Clients / AI Models                 │
└───────────────────────────────────────────────────────────┘
```

### Data Flow:

1. AI assistant or MCP client requests information about a claim or URL
2. TruthLens server ingests content from web sources or receives direct text
3. Claims are extracted using pattern matching or Gemini AI
4. Each claim is verified using multiple sources (Wikipedia, fact-check databases)
5. Results are returned to the client with evidence and confidence scores

## 🚀 Setup and Installation

### Prerequisites

- Python 3.10 or higher
- API keys for external services:
  - Google Gemini API (required)
  - NewsAPI (optional)
  - Reddit API (optional)

### Installation with UV (Recommended)

[UV](https://github.com/astral-sh/uv) is a fast Python package installer and resolver. To install and run TruthLens using UV:

1. **Install UV** (if not already installed)
   ```bash
   pip install uv
   ```

2. **Clone this repository**
   ```bash
   git clone <repository-url>
   cd MCP\ Build
   ```

3. **Create and activate a virtual environment**
   ```bash
   uv venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

5. **Set up API keys**
   - Create a new file named `.env` in the root directory
   - Add your API keys using the following format:

   ```
   # TruthLens API Keys
   # Replace placeholder values with your actual API keys
   
   # Google Gemini API Key (required for LLM-based claim extraction and verification)
   # Get it from: https://aistudio.google.com/app/apikey
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # NewsAPI Key (used for fetching news articles)
   # Get it from: https://newsapi.org/
   NEWSAPI_KEY=your_newsapi_key_here
   
   # Reddit API Credentials (optional, for production use)
   # Get from: https://www.reddit.com/prefs/apps
   # Instructions:
   #  1. Click "Create App" button at the bottom
   #  2. Select "script" for personal use
   #  3. Fill in name (e.g., "TruthLens")
   #  4. For redirect URI, use: http://localhost:8000 (even though this app doesn't use it)
   #  5. After creation, you'll receive a client ID and secret
   REDDIT_CLIENT_ID=your_reddit_client_id_here
   REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
   REDDIT_USER_AGENT=TruthLens/0.1 (by /u/YourUsername)
   
   # Google Fact Check Tools API Key (optional, for production use)
   # Get from: https://developers.google.com/fact-check/tools/api/
   FACTCHECK_API_KEY=your_factcheck_api_key_here
   ```

   **Important Notes:**
   - At minimum, you need the `GEMINI_API_KEY` for AI-powered analysis
   - If API keys are missing, the system will fall back to pattern matching and demo data
   - Never commit your `.env` file to version control

6. **Run the server**
   ```bash
   python run_server.py
   ```

### Alternative Installation with pip

If you don't have UV installed, you can use pip:

```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python run_server.py
```

## 🧪 Testing

Test the server by sending requests to its MCP endpoints:

1. **Basic demo resource**
   ```
   truthlens://demo
   ```

2. **Tool examples**
   ```
   ingest_url(url="https://en.wikipedia.org/wiki/COVID-19_vaccine")
   extract_claims(text="Vaccines are effective at preventing serious illness.")
   verify_claim(claim_text="Climate change is caused by human activities.")
   ```

## 📚 API Keys

The following API keys are used in this project:

1. **Google Gemini API** - Required for AI-based claim extraction and verification
   - Get from: https://aistudio.google.com/app/apikey

2. **NewsAPI** - For news search functionality
   - Get from: https://newsapi.org/

3. **Reddit API** - For social media content monitoring (optional)
   - Get from: https://www.reddit.com/prefs/apps

## ⚠️ Limitations

- The current implementation uses in-memory storage and is not suitable for production
- Pattern matching fallback has limited accuracy compared to AI-powered analysis
- Web scraping may be subject to rate limits and terms of service restrictions

## 📝 License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.