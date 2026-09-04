import asyncio
import random
import json
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app = FastAPI(title="O'zbekiston Temir Yo'llari - FVV & TY Real-time Monitoring")

USE_REAL_API = False  
OTY_API_URL = "https://api.railway.uz/v1/trains/live-gps"
OTY_API_TOKEN = "YOUR_OFFICIAL_API_TOKEN_HERE"            

INITIAL_TRAINS = [
    {"id": "TR-101", "name": "Afrosiyob 762", "type": "Yo'lovchi", "route": "Toshkent - Samarqand", "cargo_type": "Yo'lovchilar", "lat": 40.0, "lng": 66.9, "speed": 180, "risk_level": 10, "status": "Harakatlanmoqda 🟢", "driver": "A. Karimov", "emergency": False},
    {"id": "TR-202", "name": "Nasaf 004", "type": "Yo'lovchi", "route": "Toshkent - Qarshi", "cargo_type": "Yo'lovchilar", "lat": 38.8, "lng": 65.7, "speed": 120, "risk_level": 15, "status": "Harakatlanmoqda 🟢", "driver": "B. Rahimov", "emergency": False},
    {"id": "TR-505", "name": "Qamchiq Ekspress", "type": "Yuk", "route": "Angren - Pop", "cargo_type": "Neft va Kimyo", "lat": 41.1, "lng": 70.5, "speed": 60, "risk_level": 25, "status": "Dovonda harakatlanmoqda ⚠️", "driver": "S. Tursunov", "emergency": False},
    {"id": "TR-909", "name": "Surxon Trans", "type": "Yuk", "route": "Termiz - Toshkent", "cargo_type": "Qishloq xo'jaligi", "lat": 37.2, "lng": 67.2, "speed": 0, "risk_level": 80, "status": "To'xtab turibdi 🟡", "driver": "O. Abdullayev", "emergency": False}
]

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

def fetch_from_oty_real_api():
    try:
        headers = {"Authorization": f"Bearer {OTY_API_TOKEN}"}
        response = requests.get(OTY_API_URL, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

async def train_monitoring_loop():
    while True:
        if USE_REAL_API:
            real_data = fetch_from_oty_real_api()
            if real_data:
                await manager.broadcast(json.dumps(real_data))
        else:
            for train in INITIAL_TRAINS:
                if not train["emergency"] and train["speed"] > 0:
                    train["lat"] += random.uniform(-0.002, 0.002)
                    train["lng"] += random.uniform(-0.002, 0.002)
                    train["speed"] = max(30, min(220, train["speed"] + random.randint(-3, 3)))
            
            await manager.broadcast(json.dumps(INITIAL_TRAINS))
        
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(train_monitoring_loop())

@app.get("/")
async def get():
    return FileResponse("index.html")

@app.post("/trigger-emergency/{train_id}")
async def trigger_emergency(train_id: str):
    for train in INITIAL_TRAINS:
        if train["id"] == train_id:
            train["emergency"] = True
            train["status"] = "🚨 AVARIYA HOLATI!"
            train["risk_level"] = 95
            train["speed"] = 0
    return {"status": "success", "message": f"{train_id} da avariya yoqildi"}

@app.post("/reset-emergency/{train_id}")
async def reset_emergency(train_id: str):
    for train in INITIAL_TRAINS:
        if train["id"] == train_id:
            train["emergency"] = False
            train["status"] = "Harakatlanmoqda 🟢"
            train["risk_level"] = 10
            train["speed"] = 80
    return {"status": "success", "message": f"{train_id} da xavf bekor qilindi"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)