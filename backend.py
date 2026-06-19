import asyncio
import os
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permitir CORS para que tu PWA en GitHub Pages conecte sin bloqueos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MuzzTracker:
    def __init__(self):
        self.active_connections = []
        # Aquí puedes inicializar tus variables de la blockchain o Web3 si las usas

    async def start_monitoring(self):
        print("[BOT] Iniciando monitoreo de la blockchain...")
        block_count = 100000  # Bloque simulado inicial o base
        
        while True:
            try:
                # -------------------------------------------------------------
                # TU LÓGICA DE MONITOREO VA AQUÍ
                # Ejemplo simulado para el feed en vivo:
                # -------------------------------------------------------------
                block_count += 1
                tx_data = {
                    "block": block_count,
                    "type": "COMPRA" if (block_count % 2 == 0) else "VENTA",
                    "from": "0xef3dA0000000000000000000000000000000B8f0",
                    "to": "0x71C7656EC7ab88b098defB751B7401B5f6d1476B",
                    "value": "1500.50"
                }
                
                # Enviar los datos a todas las PWAs conectadas
                await self.broadcast(tx_data)
                
                # CONTROL CRÍTICO: Pausa obligatoria para liberar el Event Loop
                await asyncio.sleep(5)  
                
            except Exception as e:
                print(f"[ERROR BOT]: {e}")
                await asyncio.sleep(10)

    async def broadcast(self, data: dict):
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        # Hacer una copia de la lista para evitar errores si alguien se desconecta en medio del envío
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

tracker = MuzzTracker()

# USAR EL EVENTO STARTUP CORRECTAMENTE SIN BLOQUEAR
@app.on_event("startup")
async def startup_event():
    # asyncio.ensure_future o create_task desliga la tarea del flujo principal inmediatamente
    asyncio.ensure_future(tracker.start_monitoring())
    print("[SERVER] Tarea de monitoreo enviada a segundo plano con éxito.")

@app.get("/")
async def get_root():
    # Esta es la ruta que tu Cron-Job externa y el Health Check de Render van a tocar
    return {"status": "MuzzStudio Backend Online", "bot_running": True}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    tracker.active_connections.append(websocket)
    print(f"[WS] Nueva PWA conectada. Total: {len(tracker.active_connections)}")
    try:
        while True:
            # Mantiene el socket abierto escuchando actividad de la PWA
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        if websocket in tracker.active_connections:
            tracker.active_connections.remove(websocket)
        print("[WS] PWA desconectada.")
