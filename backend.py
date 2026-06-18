import asyncio
import json
import os
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from web3 import AsyncWeb3
from web3.providers import AsyncWebSocketProvider
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuración técnica
CONTRACT_ADDRESS = "0xef3dAa5fDa8Ad7aabFF4658f1F78061fd626B8f0"
# ABI mínimo para detectar transferencias
ABI = '[{"anonymous":false,"inputs":[{"indexed":true,"name":"from","type":"address"},{"indexed":true,"name":"to","type":"address"},{"indexed":false,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"}]'
WSS_URL = os.getenv("WSS_NODE_URL", "wss://eth-mainnet.g.alchemy.com/v2/TU_KEY")

class MuzzTracker:
    def __init__(self):
        self.w3 = AsyncWeb3(AsyncWebSocketProvider(WSS_URL))
        self.contract = self.w3.eth.contract(address=CONTRACT_ADDRESS, abi=json.loads(ABI))
        self.active_connections = []

    async def broadcast(self, data):
        for connection in self.active_connections:
            await connection.send_json(data)

    async def start_monitoring(self):
        print("🚀 Monitor MuzzleToken Iniciado 24/7...")
        event_filter = await self.contract.events.Transfer.create_filter(from_block='latest')
        
        while True:
            try:
                events = await event_filter.get_new_entries()
                for event in events:
                    tx_data = {
                        "block": event['blockNumber'],
                        "from": event['args']['from'],
                        "to": event['args']['to'],
                        "value": event['args']['value'] / 10**18,
                        "type": self.identify_tx(event['args']['from'], event['args']['to'])
                    }
                    await self.broadcast(tx_data)
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

    def identify_tx(self, f, t):
        lp_address = "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f" # Uniswap LP
        if f.lower() == lp_address: return "COMPRA"
        if t.lower() == lp_address: return "VENTA"
        return "TRANSFER"

tracker = MuzzTracker()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(tracker.start_monitoring())

@app.get("/")
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    tracker.active_connections.append(websocket)
    try:
        while True: await websocket.receive_text()
    except:
        tracker.active_connections.remove(websocket)
