import json
import os
import glob
from datetime import datetime
from dateutil import parser


class DataLoader:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        
    def load_symbol_data(self, symbol):
        """Load data for a given symbol. Handles regular symbols and options chaining."""
        if symbol.startswith("OPT_"):
            return self._load_options_chain(symbol)
        else:
            return self._load_regular_symbol(symbol)
    
    def _load_regular_symbol(self, symbol):
        """Load regular symbol data."""
        timeframes = ["1m", "5m", "15m"]
        
        for timeframe in timeframes:
            file_pattern = os.path.join(self.data_dir, f"{symbol}_{timeframe}.json")
            files = glob.glob(file_pattern)
            
            if files:
                return self._load_json_file(files[0])
        
        return []
    
    def _load_options_chain(self, symbol):
        """Load options data with expiry chaining."""
        parts = symbol.split("_", 1)
        if len(parts) < 2:
            return []
        
        base_symbol = parts[1]
        file_pattern = os.path.join(self.data_dir, f"OPT_{base_symbol}_*_*.json")
        files = glob.glob(file_pattern)
        
        if not files:
            return []
        
        file_expiry_map = []
        for file_path in files:
            filename = os.path.basename(file_path)
            parts = filename.replace(".json", "").split("_")
            if len(parts) >= 3:
                expiry_str = parts[2]
                try:
                    expiry_date = datetime.strptime(expiry_str, "%d%m%Y")
                    file_expiry_map.append((expiry_date, file_path))
                except ValueError:
                    continue
        
        if not file_expiry_map:
            return []
        
        file_expiry_map.sort(key=lambda x: x[0])
        
        all_candles = []
        for expiry_date, file_path in file_expiry_map:
            candles = self._load_json_file(file_path)
            all_candles.extend(candles)
        
        return all_candles
    
    def _load_json_file(self, file_path):
        """Load candles from JSON file and parse timestamps."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for candle in data:
                if 'timestamp' in candle:
                    candle['datetime'] = parser.parse(candle['timestamp'])
            
            return data
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return []
    
    def get_available_symbols(self):
        """Get list of all available symbols in the data directory."""
        symbols = set()
        
        for file_path in glob.glob(os.path.join(self.data_dir, "*_*.json")):
            filename = os.path.basename(file_path)
            if filename.startswith("OPT_"):
                parts = filename.replace(".json", "").split("_")
                if len(parts) >= 3:
                    symbols.add(f"OPT_{parts[1]}")
            else:
                parts = filename.replace(".json", "").split("_")
                if len(parts) >= 2:
                    symbols.add(parts[0])
        
        return list(symbols)
