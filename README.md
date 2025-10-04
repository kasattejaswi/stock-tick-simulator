# Stock Tick Simulator

Simulates the movement of a stock price between Open, High, Low, Close based on historical data provided. This service exposes a websocket on which clients can connect. The live tick feed will be published tick by tick. 

This service is useful for developers interested in developing and testing trading algorithms on live data.

## Features

1. Clients can consume multiple symbols at once.
2. Pre define historical data in json format candle by candle. Live ticks will be published and price will oscillate between OHLC.
3. Define candle data in 1m, 5m, 15m. The lower the timeframe, better the accuracy. Higher timeframes may result inaccurate price movement as price may oscillate very differently than actual movement.
4. Time override for backtesting - Simulate historical data at any speed with timestamps matching the historical data, not real clock time.
5. Tick frequency can be modified via `tickFrequencyMs` parameter in subscription (default: 100ms). 

## Limitations

1. Since this is just a simulator, price oscillation between OHLC is randomized and may not match exact real market tick-by-tick movement.
2. The lower the candle timeframe, the better the accuracy of simulated movement.
3. Needs real historical OHLC candle data to simulate ticks. 

## Getting Started

### Create a venv

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies
```bash
pip3 install -r requirements.txt
```

### Load data

Data can be loaded in format of json file inside `data` folder. Some data is already present for a few symbols. The file format is `SYMBOL_TIMEFRAME.json`.

SYMBOL can be:
1. BANKNIFTY
2. NIFTY
3. FINNIFTY

TIMEFRAME can be:
1. 1m - Denotes 1 minute candle.
2. 5m - Denotes 5 minute candle.
3. 15m - Denotes 15 minute candle.

Ticks will oscillate between Open, High, Low and Close of these timeframes. 

### Options Data Chaining

This service supports data chaining. As an example, you may want to simulate data based on symbols that expire like BANKNIFTY FUT or BANKNIFTY at a specific strike. If multiple expiries are defined, this service will auto chain them once previous expiry is closed. 

File format for options is `OPT_SYMBOL_EXPIRY_TIMEFRAME.json`. 

Examples:

1. `OPT_BANKNIFTYFUT_28102025_1m.json`: Here the expiry is formatted as DDMMYYYY 28 Oct 2025. Hence 28102025.
2. `OPT_BANKNIFTYFUT_25112025_1m.json`: Here the expiry is formatted as DDMMYYYY 25 Nov 2025. Hence 25112025.

While consuming feed live, once `OPT_BANKNIFTYFUT_28102025_1m.json` is completed, feed will auto switch to `OPT_BANKNIFTYFUT_25112025_1m.json`.

### Data format

Data must be stored in below format in json file:
```json
[
    {
        "timestamp": "2025-07-02 09:15:00 IST",
        "open": 57558.2,
        "high": 57590.25,
        "low": 57466.75,
        "close": 57541.9,
        "volume": 0
    }
]
```

## Start the service

To start the service, run:

```bash
python3 main.py
```

## Websocket API

### Connection

Connect to: `ws://localhost:8765`

### Subscribe to feed

Define the request format:
```json
{
    "action": "SUBSCRIBE",
    "symbols": ["BANKNIFTY", "BANKNIFTYFUT"],
    "tickFrequencyMs": 100,
    "overrideTime": false,
    "responseFormat": {
        "template": {
            "NSE": {
                "CASH": {
                    "{{SYMBOL}}": {
                        "tsInMillis": "{{TIMESTAMP}}",
                        "value": "{{TICK}}"
                    }
                }
            }
        }
    }
}
```

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `action` | string | Yes | - | Action to perform. Use `"SUBSCRIBE"` to subscribe to symbols. |
| `symbols` | array of strings | Yes | - | List of symbols to subscribe to (e.g., `["BANKNIFTY", "NIFTY"]`). |
| `tickFrequencyMs` | number | No | 100 | Frequency of tick updates in milliseconds. Controls how often price updates are sent. |
| `overrideTime` | boolean | No | false | When `true`, uses timestamps from historical data. When `false`, uses current system time. |
| `responseFormat` | object | No | Default format | Custom response format template. If not provided, default format will be used. |
| `responseFormat.template` | object | No | - | JSON template defining the structure of tick responses. Use placeholders to inject tick data. |

#### Response Format Placeholders

In case you wish to modify the way how server responds, you can define your own template. There are 3 placeholders needed within the template where the server will populate the data:

1. {{SYMBOL}}: The symbol of the tick.
2. {{TIMESTAMP}}: The epoch of timestamp. The format will stay as is and cannot be changed.
3. {{TICK}}: The value of current price. It will oscillate between OHLC of data provided.

**NOTE**: Only one symbol will be responded in a single tick. If multiple ticks are subscribed, it will respond multiple times with different symbols. 

**Default tick format (if no template provided):**
```json
{
    "symbol": "BANKNIFTY",
    "timestamp": 1746174582295,
    "price": 44523.50
}
```