import asyncio
from websocket_server import WebSocketServer


def main():
    """
    Main entry point for the stock tick simulator.
    """
    server = WebSocketServer(host="localhost", port=8765)
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")


if __name__ == "__main__":
    main()
