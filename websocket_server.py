import asyncio
import json
import websockets
from datetime import datetime
from data_loader import DataLoader
from tick_generator import TickGenerator
from response_formatter import ResponseFormatter


class WebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.data_loader = DataLoader()
        self.clients = {}
        
    async def handle_client(self, websocket, path):
        """Handle a client connection."""
        client_id = id(websocket)
        print(f"Client {client_id} connected")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get("action", "").upper()
                    
                    if action == "SUBSCRIBE":
                        await self.handle_subscribe(websocket, client_id, data)
                    else:
                        await websocket.send(json.dumps({
                            "error": "Unknown action. Use 'SUBSCRIBE'."
                        }))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "error": "Invalid JSON format"
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        "error": f"Error processing request: {str(e)}"
                    }))
        except websockets.exceptions.ConnectionClosed:
            print(f"Client {client_id} disconnected")
        finally:
            if client_id in self.clients:
                self.clients[client_id]["active"] = False
                del self.clients[client_id]
    
    async def handle_subscribe(self, websocket, client_id, data):
        """Handle subscription request from client."""
        symbols = data.get("symbols", [])
        tick_frequency_ms = data.get("tickFrequencyMs", 100)
        override_time = data.get("overrideTime", False)
        response_format = data.get("responseFormat", {})
        template = response_format.get("template", None)
        
        if not symbols:
            await websocket.send(json.dumps({
                "error": "No symbols provided"
            }))
            return
        
        symbol_generators = {}
        for symbol in symbols:
            candles = self.data_loader.load_symbol_data(symbol)
            if not candles:
                await websocket.send(json.dumps({
                    "error": f"No data found for symbol: {symbol}"
                }))
                continue
            
            ticks_per_candle = max(10, int(60000 / tick_frequency_ms))
            generator = TickGenerator(candles, ticks_per_candle)
            symbol_generators[symbol] = generator
        
        if not symbol_generators:
            await websocket.send(json.dumps({
                "error": "No valid symbols found"
            }))
            return
        
        self.clients[client_id] = {
            "websocket": websocket,
            "symbol_generators": symbol_generators,
            "tick_frequency_ms": tick_frequency_ms,
            "override_time": override_time,
            "formatter": ResponseFormatter(template),
            "active": True
        }
        
        await self.send_ticks(client_id)
    
    async def send_ticks(self, client_id):
        """Send ticks to a specific client based on their subscription."""
        client = self.clients.get(client_id)
        if not client:
            return
        
        websocket = client["websocket"]
        symbol_generators = client["symbol_generators"]
        tick_frequency_ms = client["tick_frequency_ms"]
        override_time = client["override_time"]
        formatter = client["formatter"]
        
        try:
            while client.get("active", False):
                active_symbols = [s for s, g in symbol_generators.items() if g.has_more_data()]
                
                if not active_symbols:
                    await websocket.send(json.dumps({
                        "status": "completed",
                        "message": "All symbol data has been processed"
                    }))
                    break
                
                for symbol in active_symbols:
                    generator = symbol_generators[symbol]
                    if generator.should_advance_candle():
                        generator.advance_candle()
                
                for symbol in active_symbols:
                    generator = symbol_generators[symbol]
                    
                    if not generator.has_more_data():
                        continue
                    
                    tick_price = generator.generate_tick()
                    
                    if tick_price is None:
                        continue
                    
                    if override_time:
                        timestamp_dt = generator.get_current_timestamp()
                        timestamp_ms = int(timestamp_dt.timestamp() * 1000)
                    else:
                        timestamp_ms = int(datetime.now().timestamp() * 1000)
                    
                    response = formatter.format_response(symbol, timestamp_ms, tick_price)
                    await websocket.send(json.dumps(response))
                
                await asyncio.sleep(tick_frequency_ms / 1000.0)
        
        except websockets.exceptions.ConnectionClosed:
            print(f"Client {client_id} connection closed during tick streaming")
        except Exception as e:
            print(f"Error sending ticks to client {client_id}: {e}")
            try:
                await websocket.send(json.dumps({
                    "error": f"Error streaming ticks: {str(e)}"
                }))
            except:
                pass
    
    async def start(self):
        """Start the WebSocket server."""
        print(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()
