CREATE TABLE IF NOT EXISTS user_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ai_persona TEXT NOT NULL,
    fast_window INTEGER NOT NULL,
    slow_window INTEGER NOT NULL,
    confirmation_indicator_window INTEGER NOT NULL,
    atr_window INTEGER NOT NULL,
    atr_multiplier REAL NOT NULL,
    usage INTEGER DEFAULT 0,
    added_at DATETIME,
    discontinued_at DATETIME
);

CREATE TABLE IF NOT EXISTS symbol_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_pair TEXT NOT NULL,
    max_allocation REAL NOT NULL,
    usage INTEGER DEFAULT 0,
    added_at DATETIME,
    discontinued_at DATETIME
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_pair TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    price REAL NOT NULL,
    ema_metrices TEXT NOT NULL,
    confirmation_metrices TEXT NOT NULL,
    strategy TEXT NOT NULL,
    detected_at DATETIME,
    processed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ai_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id INTEGER NOT NULL,
    user_configs_id INTEGER,
    symbol_pair TEXT NOT NULL,
    fast_timeframe TEXT NOT NULL,
    slow_timeframe TEXT NOT NULL,
    strategy TEXT NOT NULL,
    signal TEXT NOT NULL, 
    action TEXT NOT NULL, 
    confidence TEXT NOT NULL,
    risk_score REAL,
    position_size_pct REAL,
    stop_loss_pct REAL,
    take_profit_pct REAL,
    rationale TEXT NOT NULL,
    key_factors TEXT, 
    source TEXT NOT NULL DEFAULT 'ai',
    model_name TEXT,
    tools_used TEXT NOT NULL,
    created_at DATETIME,
    FOREIGN KEY (signal_id) REFERENCES signals(id),
    FOREIGN KEY (user_configs_id) REFERENCES user_config(id)
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_order_id TEXT,
    signal_id INTEGER,
    ai_decision_id INTEGER,
    user_config_id INTEGER,
    symbol_pair TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    entry_price REAL NOT NULL,
    initial_stop_loss REAL,
    opened_at DATETIME,
    entry_fill_price REAL NOT NULL,
    entry_fill_quantity REAL,
    exit_algo_id TEXT,
    exit_order_id TEXT,
    amended_stop_loss REAL,
    exit_fill_price REAL,
    exit_fill_quantity REAL,
    closed_at DATETIME,
    order_status TEXT NOT NULL,
    FOREIGN KEY (signal_id) REFERENCES signals(id),
    FOREIGN KEY (ai_decision_id) REFERENCES ai_decisions(id),
    FOREIGN KEY (user_config_id) REFERENCES user_config(id)
);