from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio

app = FastAPI()

# O'zbekiston temir yo'llari xaritasi uchun asosiy liniyalar va stansiyalar
MAP_ROUTES = {
    "tashkent_bukhara": [[41.2995, 69.2401], [40.4897, 68.7842], [40.1158, 67.8422], [39.6542, 66.9597], [40.0844, 65.3792], [39.7747, 64.4286]],
    "vodiy_line": [[41.2995, 69.2401], [40.5433, 70.9381], [40.3864, 71.7864], [40.7821, 72.3442]],
    "south_line": [[39.6542, 66.9597], [38.8605, 65.7890], [37.2242, 67.2783]],
    "west_line": [[39.7747, 64.4286], [41.5503, 60.6317], [41.4689, 59.6134], [43.0417, 58.8500]]
}

# GPS bilan jihozlangan poyezdlar ro'yxati (Simulyatsiya telemetriyasi)
trains_gps_data = [
    {"id": "TR-101", "name": "Afrosiyob #762", "route": "Toshkent - Buxoro", "lat": 40.1158, "lng": 67.8422, "speed": 180, "status": "moving", "is_emergency": False},
    {"id": "TR-204", "name": "Yo'lovchi #010", "route": "Toshkent - Termiz", "lat": 38.8605, "lng": 65.7890, "speed": 75, "status": "moving", "is_emergency": False},
    {"id": "TR-502", "name": "Yuk Poyezdi #401", "route": "Navoiy - Qo'ng'irot", "lat": 41.5503, "lng": 60.6317, "speed": 0, "status": "stopped", "is_emergency": False},
    {"id": "TR-999", "name": "Yuk Poyezdi #909", "route": "Qarshi - Samarqand", "lat": 39.1000, "lng": 66.2000, "speed": 0, "status": "emergency", "is_emergency": True}
]

@app.get("/")
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/routes")
async def get_routes():
    return MAP_ROUTES

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # GPS koordinatalarini real vaqtda harakatlantirish
            for train in trains_gps_data:
                if train["status"] == "moving":
                    train["lat"] += 0.001
                    train["lng"] += 0.001
            await websocket.send_text(json.dumps(trains_gps_data))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass