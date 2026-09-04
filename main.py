import asyncio
import json
import random
import asyncpg
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# PostgreSQL Baza Ulanish Satri
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/railway_db"

db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        print("✅ PostgreSQL Ma'lumotlar Bazasiga muvaffaqiyatli ulandi!")
    except Exception as e:
        print(f"❌ Bazaga ulanishda xatolik: {e}")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

@app.get("/")
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

async def fetch_trains_from_db():
    if not db_pool:
        return []
    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, type, route, cargo_type, latitude as lat, longitude as lng,
                       speed, is_moving, risk_level, status, driver, emergency
                FROM trains
            """)
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ Ma'lumotlarni olishda xatolik: {e}")
        return []

async def update_train_positions_in_db():
    if not db_pool:
        return
    try:
        async with db_pool.acquire() as conn:
            trains = await conn.fetch("SELECT id, latitude, longitude, is_moving, emergency, type FROM trains")
            for train in trains:
                if train["is_moving"] and not train["emergency"]:
                    new_lat = train["latitude"] + random.uniform(-0.002, 0.002)
                    new_lng = train["longitude"] + random.uniform(-0.002, 0.002)
                    new_speed = random.randint(140, 230) if train["type"] == "high_speed" else random.randint(50, 90)
                    
                    await conn.execute("""
                        UPDATE trains 
                        SET latitude = $1, longitude = $2, speed = $3,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $4
                    """, new_lat, new_lng, new_speed, train["id"])
    except Exception as e:
        print(f"❌ Koordinatalarni yangilashda xatolik: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await update_train_positions_in_db()
            trains_data = await fetch_trains_from_db()
            # default=str — datetime va barcha mos bo'lmagan tiplarni avto serialization qiladi
            await websocket.send_text(json.dumps(trains_data, default=str))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        print("Mijoz ulanishni uzdi")
    except Exception as e:
        print(f"WebSocket xatoligi: {e}")

@app.post("/trigger-emergency/{train_id}")
async def trigger_emergency(train_id: str):
    if not db_pool:
        return {"status": "error", "message": "Baza ulanmagan"}
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE trains
            SET emergency = true, is_moving = false, speed = 0, risk_level = 98,
                status = '🚨 FAVQULODDA AVARIYA VA XAVF!'
            WHERE id = $1
        """, train_id)
    return {"status": "success", "message": "Avariya holati bazaga saqlandi!"}

@app.post("/reset-emergency/{train_id}")
async def reset_emergency(train_id: str):
    if not db_pool:
        return {"status": "error", "message": "Baza ulanmagan"}
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE trains
            SET emergency = false, is_moving = true, speed = 50, risk_level = 15,
                status = 'Harakatlanmoqda 🟢'
            WHERE id = $1
        """, train_id)
    return {"status": "success", "message": "Xavf bekor qilindi"}