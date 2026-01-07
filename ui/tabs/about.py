"""
About tab UI component for application information and setup.

This module renders the about page for the Cryptocurrency Trading Bot,
providing users with application overview and system capabilities.

"""

import streamlit as st


def render() -> None:
    """
    Render the About tab content.

    Displays trading bot information, AI capabilities, and
    system overview for users.
    """

    st.header("🤖 Cryptocurrency Trading Bot")

    st.markdown(
        """
    **AI-powered cryptocurrency trading system** that combines intelligent 
    market analysis, automated trade execution, and comprehensive risk management
    to provide autonomous trading capabilities.
    """
    )
    st.subheader("🚀 System Architecture")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **🤖 AI Trading Agent**
        - Intelligent trade decision making
        - Cryptocurrency fundamental analysis
        - Market regime classification
        - Risk-on/Risk-off assessment
        
        **📊 Data Sources**
        - CoinGecko API (price, fundamentals)
        - Yahoo Finance (macro indicators)
        - Binance (daily data)
        - OKX API (OHLC data)
        """
        )

    with col2:
        st.markdown(
            """
        **🔄 Trading Engine**
        - OKX exchange integration
        - Automated order execution
        - Position monitoring
        - Risk management
        
        **💬 AI Desk Chat**
        - Interactive crypto research
        - Market analysis queries
        - Real-time data insights
        - Knowledge base search
        """
        )

    st.subheader("💡 AI Desk Capabilities")

    with st.expander("📈 **Cryptocurrency Analysis**", expanded=False):
        st.markdown(
            """
        - *"Analyze BTC fundamentals and current market regime"*
        - *"What's the current Risk-On/Risk-Off environment for crypto?"*
        - *"Compare ETH development activity to other major coins"*
        - *"Explain the relationship between DXY and crypto markets"*
        - *"How does Bitcoin dominance affect altcoin performance?"*
        """
        )

    with st.expander("🔍 **Market Research**", expanded=False):
        st.markdown(
            """
        - *"Search for recent crypto regulation news"*
        - *"What are the macro drivers affecting crypto prices?"*
        - *"Analyze VWAP trends for SOL over the past week"*
        - *"Find information about upcoming crypto events"*
        - *"Research institutional crypto adoption trends"*
        """
        )

    with st.expander("⚡ **Trading Intelligence**", expanded=False):
        st.markdown(
            """
        - *"Should I take this BTC long position based on current regime?"*
        - *"What's the risk-reward for ETH at current levels?"*
        - *"Explain the current crypto market regime score"*
        - *"How does volume analysis support this trade idea?"*
        """
        )

    st.subheader("⚙️ Technical Components")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
        **🛠️ AI Tools:**
        - Comprehensive crypto analysis
        - Market regime classification
        - Web search & news gathering
        - RAG knowledge base
        - Wikipedia integration
        """
        )

    with col2:
        st.markdown(
            """
        **🔧 Trading Infrastructure:**
        - OKX API integration
        - SQLite trade logging
        - Real-time order monitoring
        - Position size calculation
        - Error handling & retries
        """
        )

    st.subheader("🔒 Security & Risk Management")
    st.markdown(
        """
    - **Input Sanitization**: Prompt injection protection for AI interactions
    - **Error Handling**: Comprehensive middleware for API failures
    - **Rate Limiting**: Built-in delays to respect API rate limits
    - **Local Storage**: Trade data stored in local SQLite database
    """
    )

    st.subheader("⚠️ Important Notes")
    st.markdown(
        """
    This is an **experimental trading bot** for educational and research purposes.
    
    - **Use at your own risk** - cryptocurrency trading involves substantial risk
    - **Paper trading recommended** before live deployment
    - **API keys required** - see README for setup instructions
    - **Monitor positions** - automated trades require supervision
    """
    )

    st.markdown("---")
    st.caption(
        "Cryptocurrency Trading Bot • Built with LangChain & Streamlit • "
        "AI-Powered Trade Execution"
    )
