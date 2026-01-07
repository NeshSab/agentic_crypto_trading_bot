from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any


TradeAction = Literal["BUY", "SELL", "HOLD"]
ConfidenceLevel = Literal["low", "medium", "high"]
DecisionSource = Literal["ai", "rule_override"]


class TradeDecision(BaseModel):
    """
    Final AI decision produced after evaluating a deterministic trading signal.
    This object is execution-safe and can be logged or acted upon directly.
    """

    symbol_pair: str = Field(
        ...,
        description="Cryptocurrency trading pair in BASE/QUOTE format (e.g. BTC-EUR, ETH-EUR). This is the specific asset pair being analyzed for trading.",
    )
    fast_timeframe: str = Field(
        ...,
        description="Primary timeframe where the trading signal was detected (e.g. '5m', '1h', '4h'). This represents the main chart interval used for signal generation.",
    )
    slow_timeframe: str = Field(
        ...,
        description="Longer timeframe used for trend confirmation and context (e.g. '15m', '4h', '1d'). Should be higher than fast_timeframe to validate signal direction.",
    )
    strategy: str = Field(
        ...,
        description="Name of the trading strategy or methodology that identified this opportunity (e.g. 'EMA_Strategy', 'RSI_Divergence', 'Support_Resistance'). Used for tracking strategy performance.",
    )

    signal: Literal["bullish", "bearish"] = Field(
        ...,
        description="Raw directional bias from technical analysis before AI risk assessment. 'bullish' suggests upward price movement, 'bearish' suggests downward movement.",
    )

    action: TradeAction = Field(
        ...,
        description="Final trading decision after AI analysis: 'BUY' to enter long position, 'SELL' to enter short position, or 'HOLD' to take no action due to insufficient conviction or risk.",
    )

    confidence: ConfidenceLevel = Field(
        ...,
        description="AI assessment of setup quality and conviction level: 'high' = strong confluence of factors, 'medium' = decent setup with some uncertainty, 'low' = weak or conflicting signals.",
    )

    risk_score: Optional[float] = Field(
        None, ge=0, le=1, description="Normalized risk score (0=safe, 1=very risky)"
    )

    position_size_pct: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Recommended position size as decimal fraction of available balance (e.g. 0.05 = 5%, 0.02 = 2%). Larger positions for higher confidence, smaller for uncertain setups.",
    )

    stop_loss_pct: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Protective stop-loss distance as decimal fraction from entry price (e.g. 0.03 = 3% below entry for long positions). Used to limit downside risk.",
    )

    take_profit_pct: Optional[float] = Field(
        None,
        ge=0,
        le=5,
        description="Profit target distance as decimal fraction from entry price (e.g. 0.08 = 8% above entry for long positions). Should provide favorable risk/reward ratio.",
    )

    rationale: str = Field(
        ...,
        description="Clear, concise explanation for the trading decision in 1-3 sentences. Should summarize the main technical, fundamental, or market regime factors that support the action.",
    )

    key_factors: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of critical analysis components that influenced the decision (e.g. {'RSI': 'oversold bounce', 'Volume': 'above average', 'Market_Regime': 'risk-on environment'}). Used for decision transparency and strategy refinement.",
    )

    source: DecisionSource = Field(
        default="ai",
        description="Attribution for decision origin: 'ai' for AI-generated analysis, 'rule_override' for manual rules that superseded AI recommendation. Used for performance tracking and system auditing.",
    )

    def is_executable(self) -> bool:
        """
        Whether this decision should result in an actual order.
        """
        return self.action in ("BUY", "SELL")
