import asyncio
import websockets
import json
from datetime import datetime


async def test():
    uri = "ws://localhost:8765"
    
    print("Connecting to server...")
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        
        # Subscribe
        request = {
            "action": "SUBSCRIBE",
            "symbols": ["BANKNIFTY"],
            "tickFrequencyMs": 200,
            "overrideTime": True
        }
        
        await websocket.send(json.dumps(request))
        print(f"Subscribed to BANKNIFTY")
        print()
        
        start_time = datetime.now()
        print(f"Started at: {start_time.strftime('%H:%M:%S')}")
        print(f"Next minute will be at: {start_time.minute + 1}:00")
        print()
        
        current_candle = None
        tick_count = 0
        candle_count = 0
        
        # Collect ticks for 70 seconds or until 2 candles seen
        i = 0
        while i < 400 and candle_count < 2:
            response = await websocket.recv()
            data = json.loads(response)
            
            if 'price' not in data:
                print(f"Error: {data}")
                continue
            
            timestamp = data['timestamp']
            price = data['price']
            now = datetime.now()
            
            # Track candle changes
            candle_id = timestamp // 60000
            if current_candle != candle_id:
                if current_candle is not None:
                    elapsed = (now - start_time).total_seconds()
                    print(f"\n>>> CANDLE SWITCHED at {now.strftime('%H:%M:%S')} (second: {now.second})")
                    print(f"    Elapsed time: {elapsed:.1f}s")
                    print(f"    Previous candle had {tick_count} ticks")
                    print()
                    candle_count += 1
                    tick_count = 0
                current_candle = candle_id
            
            tick_count += 1
            i += 1
            
            # Print every 5th tick to reduce spam
            if i % 5 == 0:
                elapsed = (now - start_time).total_seconds()
                print(f"Tick {i}: price={price}, time={now.strftime('%H:%M:%S')}, elapsed={elapsed:.1f}s")
        
        print(f"\nTotal candles seen: {candle_count + 1}")
        print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test())
