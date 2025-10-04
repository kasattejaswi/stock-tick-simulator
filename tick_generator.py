import random
from datetime import datetime, timedelta


class TickGenerator:
    def __init__(self, candles, ticks_per_candle=10):
        """
        Initialize tick generator with candle data.
        
        Args:
            candles: List of candle dictionaries with open, high, low, close, datetime
            ticks_per_candle: Number of ticks to generate per candle before advancing
        """
        self.candles = candles
        self.current_candle_index = 0
        self.current_candle = None
        self.ticks_per_candle = max(4, ticks_per_candle)
        self.current_tick_count = 0
        self.tick_interval_seconds = 0
        self.tick_sequence = []
        self.sequence_index = 0
        self.candle_duration_seconds = 60
        self.next_candle_boundary = None
        
        if self.candles:
            self.current_candle = self.candles[0]
            self._calculate_tick_interval()
            self._generate_tick_sequence()
            self._calculate_next_boundary()
    
    def _calculate_tick_interval(self):
        """Calculate the time interval between ticks based on candle timeframe."""
        if len(self.candles) >= 2:
            self.candle_duration_seconds = (self.candles[1]['datetime'] - self.candles[0]['datetime']).total_seconds()
        else:
            self.candle_duration_seconds = 60
        
        self.tick_interval_seconds = self.candle_duration_seconds / self.ticks_per_candle
    
    def _calculate_next_boundary(self):
        """Calculate the next candle boundary based on wall-clock time."""
        now = datetime.now()
        
        if self.candle_duration_seconds == 60:
            seconds_into_minute = now.second + now.microsecond / 1000000.0
            seconds_to_boundary = 60 - seconds_into_minute
        elif self.candle_duration_seconds == 300:
            minutes_into_5min = now.minute % 5
            seconds_into_5min = minutes_into_5min * 60 + now.second + now.microsecond / 1000000.0
            seconds_to_boundary = 300 - seconds_into_5min
        elif self.candle_duration_seconds == 900:
            minutes_into_15min = now.minute % 15
            seconds_into_15min = minutes_into_15min * 60 + now.second + now.microsecond / 1000000.0
            seconds_to_boundary = 900 - seconds_into_15min
        else:
            seconds_to_boundary = self.candle_duration_seconds
        
        self.next_candle_boundary = now + timedelta(seconds=seconds_to_boundary)
    
    def _generate_tick_sequence(self):
        """Generate a realistic tick sequence with gradual price movement."""
        if not self.current_candle:
            self.tick_sequence = []
            return
        
        open_price = self.current_candle['open']
        high_price = self.current_candle['high']
        low_price = self.current_candle['low']
        close_price = self.current_candle['close']
        
        sequence = [open_price]
        
        direction = 1 if close_price > open_price else -1
        price_range = high_price - low_price
        
        if price_range == 0:
            self.tick_sequence = [open_price] * self.ticks_per_candle
            self.sequence_index = 0
            return
        
        tick_size = price_range * 0.05
        
        keypoints = [open_price]
        
        if direction > 0:
            keypoints.append(low_price)
            keypoints.append(high_price)
            keypoints.append(close_price)
        else:
            keypoints.append(high_price)
            keypoints.append(low_price)
            keypoints.append(close_price)
        
        ticks_remaining = self.ticks_per_candle - 1
        segment_ticks = max(1, ticks_remaining // (len(keypoints) - 1))
        
        current_price = open_price
        
        for i in range(1, len(keypoints)):
            target_price = keypoints[i]
            
            if i == len(keypoints) - 1:
                segment_length = ticks_remaining
            else:
                segment_length = min(segment_ticks, ticks_remaining)
            
            for j in range(segment_length):
                if j == segment_length - 1:
                    current_price = target_price
                else:
                    progress = (j + 1) / segment_length
                    base_price = sequence[-1] + (target_price - sequence[-1]) * progress
                    
                    noise_factor = random.uniform(-0.3, 0.3)
                    noise = tick_size * noise_factor
                    current_price = base_price + noise
                    current_price = max(low_price, min(high_price, current_price))
                
                sequence.append(current_price)
            
            ticks_remaining -= segment_length
        
        while len(sequence) < self.ticks_per_candle:
            sequence.append(close_price)
        
        self.tick_sequence = [round(p, 2) for p in sequence[:self.ticks_per_candle]]
        self.sequence_index = 0
    
    def has_more_data(self):
        """Check if there are more candles to process."""
        return self.current_candle_index < len(self.candles)
    
    def should_advance_candle(self):
        """Check if we've reached the next candle boundary."""
        if self.next_candle_boundary is None:
            return False
        return datetime.now() >= self.next_candle_boundary
    
    def get_current_timestamp(self):
        """Get the timestamp of the current tick within the candle."""
        if self.current_candle and 'datetime' in self.current_candle:
            base_time = self.current_candle['datetime']
            offset = timedelta(seconds=self.current_tick_count * self.tick_interval_seconds)
            return base_time + offset
        return datetime.now()
    
    def generate_tick(self):
        """Generate a single tick from the sequence."""
        if not self.tick_sequence:
            return None
        
        tick_price = self.tick_sequence[self.sequence_index]
        self.sequence_index = (self.sequence_index + 1) % len(self.tick_sequence)
        self.current_tick_count += 1
        
        return tick_price
    
    def advance_candle(self):
        """Move to the next candle."""
        self.current_candle_index += 1
        
        if self.current_candle_index < len(self.candles):
            self.current_candle = self.candles[self.current_candle_index]
            if self.current_candle_index + 1 < len(self.candles):
                self.candle_duration_seconds = (self.candles[self.current_candle_index + 1]['datetime'] - 
                                          self.current_candle['datetime']).total_seconds()
                self.tick_interval_seconds = self.candle_duration_seconds / self.ticks_per_candle
            self._generate_tick_sequence()
            self.next_candle_boundary = datetime.now() + timedelta(seconds=self.candle_duration_seconds)
            self.current_tick_count = 0
            return True
        else:
            self.current_candle = None
            self.tick_sequence = []
            return False
