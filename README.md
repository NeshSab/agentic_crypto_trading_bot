# Agentic Cryptocurrency Trading Bot (EU market)

An AI-powered cryptocurrency trading system that combines intelligent cryptocurrency analysis and automated trade execution. Built with LangChain agents and powered by OpenAI's GPT models with real-time market data integration for autonomous crypto trading.
<br>
- The proposed system is a hybrid AI trading agent that combines model-based reasoning with goal-directed and utility-aware decision making. The agent maintains an internal representation of market, evaluates potential actions against predefined objectives and risk constraints, and uses an LLM to synthesize qualitative information such as news and sentiment. 

<br>

**⚠️ Important: This is an experimental trading bot for educational and research purposes. Use at your own risk.**
<br>

## Table of Contents
- [Introduction](#introduction)
- [How to Navigate](#how-to-navigate-this-repository)
- [Features](#features)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [Further Improvements](#further-improvements)
- [Important Notes](#important-notes)
- [Get Help](#get-help)
- [Contribution](#contribution)
<br>

## Introduction
This application provides autonomous cryptocurrency trading capabilities through AI-powered market analysis and automated execution. The system combines comprehensive crypto fundamental analysis and real-time trading execution via OKX exchange integration. It's designed for crypto traders and developers who need intelligent automation with proper risk management and monitoring capabilities.
<br>


## How to Navigate This Repository
- `ai/`: AI agent system and trading intelligence
- `bot/`: Trading engine and execution system
- `ui/`: Streamlit web interface for monitoring and chat
- `storage/`: Database schemas and knowledge base
<br>

## Features
- **AI Trading Agent:** Intelligent trade decision making with cryptocurrency fundamental analysis, market regime classification, and Risk-On/Risk-Off assessment using comprehensive crypto analysis tools.
- **Automated Execution:** OKX exchange integration with automated order execution, position monitoring, and risk management for live cryptocurrency trading.
- **Comprehensive Analysis:** Multi-source data integration from CoinGecko API (price, fundamentals), Yahoo Finance (macro indicators), Binance (OHLC data), and development metrics (GitHub).
- **Market Intelligence:** Real-time market regime analysis, VWAP trend analysis, supply economics evaluation, and development activity tracking for informed decision making.
- **AI Desk Chat:** Interactive cryptocurrency research interface with market analysis queries, real-time data insights, and knowledge base search capabilities.
- **Middleware:** Input sanitization with prompt injection protection, comprehensive error handling, rate limiting for API calls, and automated retry logic.
- **Monitoring & Logging:** SQLite trade logging with AI decision parameters, real-time order monitoring, position tracking, and comprehensive debug logging.
- **Security Features:** Input validation, content moderation, secure API usage, and local data storage for safe operation.
<br>

## How to Run

### Prerequisites
- Python 3.12+
- Required API Keys (see setup below)

### Installation
1. Clone the repository.
2. Navigate to the project directory.
3. (Optional) Create and activate a Python virtual environment.
4. Install dependencies.
5. Set up API Keys (check for details below).
6. Navigate to storage/ and create trading.db by running init_db.py.
7. Navigate to ui/, run `streamlit run app.py` to set up configurations.

#### API Keys Setup
Create a `.env` file in the project root with the following keys:
```bash
OPENAI_API_KEY=your_openai_api_key_here

OKX_API_KEY=your_eu_okx_api_key_here
OKX_SECRET_KEY=your_eu_okx_secret_key_here
OKX_PASSPHRASE=your_eu_okx_passphrase_here

export LANGSMITH_TRACING=true
export LANGSMITH_ENDPOINT=https://api.smith.langchain.com
export LANGSMITH_API_KEY=your_langsmith_key
export LANGSMITH_PROJECT=project-name

USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
```

### Running the Application
**For Trading Bot:**
Navigate to bot/ and run 
- `python run_bot.py`
<br>

**For UI Interface:**
Navigate to ui/ and run
- `streamlit run app.py`
<br>


## Project Structure

```bash
├── ai/                             # AI agent system and trading intelligence
│   ├── ai_agent.py                 # Core agent orchestration
│   ├── chains/                     # LangChain agent configurations
│   │   ├── ai_desk.py              # Chat agent for crypto research
│   │   └── trade_advisor.py        # Trading decision agent
│   ├── tools/                      # Specialized analysis tools
│   │   ├── crypto_analysis.py      # Comprehensive crypto analysis
│   │   ├── crypto_fundamentals.py  # Fundamental analysis tool
│   │   ├── crypto_regime.py        # Market regime classification
│   │   ├── web_search.py           # Real-time news search
│   │   ├── rag_search.py           # Knowledge base search
│   │   └── registry.py             # Tool registration
│   ├── middleware/                 # Security and reliability
│   │   ├── input_sanitizer.py      # Prompt injection protection
│   │   ├── trading_error_handler.py # Error handling middleware
│   │   └── message_trimmer.py      # Context management
│   ├── utils/                      # Data processing utilities
│   │   ├── crypto_data.py          # CoinGecko API integration
│   │   ├── data_fetchers.py        # Multi-source data fetching
│   │   └── regime_analysis.py      # Market regime calculations
│   └── schemas/                    # Pydantic data models
├── bot/                            # Trading engine and execution
│   ├── run_bot.py                  # Main trading bot entry point
│   ├── trade_executor.py           # Position sizing and execution
│   ├── okx_broker.py               # OKX exchange integration
│   ├── signal_generator.py         # Trading signal processing
│   ├── order_monitor.py            # Position tracking
│   └── config_manager.py           # Trading configuration
├── ui/                             # Streamlit web interface
│   ├── app.py                      # Main UI application
│   ├── tabs/                       # Application tabs
│   │   ├── about.py                # System overview
│   │   ├── ai_desk.py              # Chat interface
│   │   ├── trades_analysis.py      # Trade monitoring
│   │   └── trading_configs.py      # Configuration management
│   └── widgets/                    # Reusable UI components
├── storage/                        # Database and knowledge base
│   ├── schema.sql                  # Database schema
│   ├── init_db.py                  # Database initialization
│   └── knowledge_base/             # Trading playbooks and references
```
<br>

## Further Improvements
- **Database Initialization:** When initializing trading.db - add default user_config and symbol_config to start with
- **Enhanced RAG Tools:** Currently AI can only read information from knowledge base, but could create tools to add, update, edit, or remove content
- **Sell Signal Execution:** Add comprehensive sell signal execution and exit strategy automation
- **Trade Analysis Tools:** Tool to read and analyze trades data for success/failure analysis and performance optimization
- **Cost Tracking Middleware:** Add tokens/price counting through middleware for usage monitoring and cost optimization
- **Crypto Regime Integration:** Fix crypto_regime tool integration with trade decision agent for better market context
- **Advanced Risk Management:** Implement stop-loss, take-profit, and position sizing optimization
- **Multi-Exchange Support:** Extend beyond OKX to support additional cryptocurrency exchanges
- **Strategy Backtesting:** Add historical backtesting capabilities for strategy validation
- **Portfolio Management:** Implement multi-asset portfolio balancing and diversification
<br>

## Important Notes

### OKX Exchange Considerations
- **EU Users:** This system is designed for OKX EU public API access
- **API Permissions:** Ensure your OKX API keys have trading permissions enabled
- **Paper Trading:** Highly recommended to test with paper trading before live deployment

### Security & Risk Management
- **Experimental Software:** This is experimental trading software - use at your own risk
- **Risk Monitoring:** Always monitor positions and have manual override capabilities
- **API Key Security:** Store API keys securely and never commit them to version control
- **Position Limits:** Set appropriate position limits to manage risk exposure

### Known Issues
- **Crypto Regime Tool:** Does not work optimally with trade decision agent as intended - requires integration improvements
- **Rate Limiting:** CoinGecko API has rate limits that may affect rapid analysis requests
<br>

## Get Help
If you encounter any issues or have questions about this project, feel free to reach out:
- **Open an Issue**: If you find a bug or have a feature request, please open an issue on GitHub
- **Email**: For personal or specific questions: agneska.sablovskaja@gmail.com
<br>

## Contribution
Contributions are welcome and appreciated! Here's how you can get involved:
1. **Reporting Bugs**: Open an issue with detailed information, steps to reproduce, and your environment details
2. **Suggesting Enhancements**: Describe your feature suggestion and provide context for why it would be useful