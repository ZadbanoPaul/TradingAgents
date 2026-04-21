// Stałe UI — zsynchronizuj z plików Python: indicators_catalog, analysis_horizon.

export const INVESTMENT_HORIZONS = [
  { id: "intraday", label: "Intraday (sesja / godziny)" },
  { id: "swing_short", label: "Swing krótki (dni)" },
  { id: "swing_medium", label: "Swing średni (tygodnie)" },
  { id: "position", label: "Pozycja (miesiące)" },
  { id: "long_term", label: "Długoterminowy (lata)" },
] as const;

export const INDICATOR_OPTIONS: { id: string; label: string }[] = [
  { id: "close_10_ema", label: "EMA(10)" },
  { id: "rsi", label: "RSI" },
  { id: "macd", label: "MACD" },
  { id: "macds", label: "MACD Signal" },
  { id: "macdh", label: "MACD Histogram" },
  { id: "boll", label: "Bollinger środek" },
  { id: "boll_ub", label: "Bollinger góra" },
  { id: "boll_lb", label: "Bollinger dół" },
  { id: "atr", label: "ATR" },
  { id: "close_50_sma", label: "SMA(50)" },
  { id: "close_200_sma", label: "SMA(200)" },
  { id: "vwma", label: "VWMA" },
  { id: "mfi", label: "MFI" },
];
