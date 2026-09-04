from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio

app = FastAPI()

# Rasmdagi sxemaga mos asosiy stansiyalar va magistrallar
STATIONS = [
    {"name": "Toshkent-Markaziy", "lat": 41.2995, "lng": 69.2401, "type": "hub"},
    {"name": "Guliston", "lat": 40.4897, "lng": 68.7842, "type": "station"},
    {"name": "Jizzax", "lat": 40.1158, "lng": 67.8422, "type": "station"},
    {"name": "Samarqand", "lat": 39.6542, "lng": 66.9597, "type": "hub"},
    {"name": "Navoiy", "lat": 40.0844, "lng": 65.3792, "type": "hub"},
    {"name": "Buxoro-1", "lat": 39.7747, "lng": 64.4286, "type": "hub"},
    {"name": "Qarshi", "lat": 38.8605, "lng": 65.7890, "type": "hub"},
    {"name": "Termiz", "lat": 37.2242, "lng": 67.2783, "type": "station"},
    {"name": "Qo'qon", "lat": 40.5433, "lng": 70.9381, "type": "station"},
    {"name": "Andijon-1", "lat": 40.7821, "lng": 72.3442, "type": "station"},
    {"name": "Urganch", "lat": 41.5503, "lng": 60.6317, "type": "station"},
    {"name": "Nukus", "lat": 41.4689, "lng": 59.6134, "type": "station"},
    {"name": "Qo'ng'irot", "lat": 43.0417, "lng": 58.8500, "type": "station"}
]

# Temir yo'l yo'nalishlari ko'ordinatalari
RAILWAY_NETWORKS = {
    "tashkent_bukhara": [
        [41.2995, 69.2401], [40.4897, 68.7842], [40.1158, 67.8422], 
        [39.6542, 66.9597], [40.0844, 65.3792], [39.7747, 64.4286]
    ],
    "vodiy_line": [
        [41.2995, 69.2401], [40.5433, 70.9381], [40.3864, 71.7864], [40.7821, 72.3442]
    ],
    "south_line": [
        [39.6542, 66.9597], [38.8605, 65.7890], [37.2242, 67.2783]
    ],
    "west_line": [
        [39.7747, 64.4286], [41.5503, 60.6317], [41.4689, 59.6134], [43.0417, 58.8500]
    ]
}

# Turlar bo'yicha poyezdlar (Afrosiyob, Yo'lovchi, Yuk)
active_trains = [
    {"id": "AF-762", "name": "Afrosiyob 762", "type": "afrosiyob", "route": "Toshkent - Buxoro", "lat": 40.1158, "lng": 67.8422, "speed": 210, "is_emergency": False},
    {"id": "AF-764", "name": "Afrosiyob 764", "type": "afrosiyob", "route": "Buxoro - Toshkent", "lat": 39.7747, "lng": 64.4286, "speed": 195, "is_emergency": False},
    {"id": "PASS-010", "name": "Sharq Express", "type": "passenger", "route": "Toshkent - Termiz", "lat": 38.8605, "lng": 65.7890, "speed": 85, "is_emergency": False},
    {"id": "PASS-060", "name": "Vodiy Express", "type": "passenger", "route": "Andijon - Toshkent", "lat": 40.5433, "lng": 70.9381, "speed": 75, "is_emergency": False},
    {"id": "CARGO-401", "name": "Yuk Poyezdi #401", "type": "cargo", "route": "Navoiy - Qo'ng'irot", "lat": 41.5503, "lng": 60.6317, "speed": 50, "is_emergency": False},
    {"id": "CARGO-909", "name": "Yuk Poyezdi #909", "type": "cargo", "route": "Qarshi - Samarqand", "lat": 39.1000, "lng": 66.2000, "speed": 0, "is_emergency": True}
]

@app.get("/")
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/map-data")
async def get_map_data():
    return {"stations": STATIONS, "routes": RAILWAY_NETWORKS}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            for train in active_trains:
                if not train["is_emergency"]:
                    train["lat"] += 0.0015
                    train["lng"] += 0.0015
            await websocket.send_text(json.dumps(active_trains))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass