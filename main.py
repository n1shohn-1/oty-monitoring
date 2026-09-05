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

# Initial poyezdlar ro'yxati (Baza bo'sh bo'lsa avto-yuklanadi)
INITIAL_TRAINS = [
    ('AFR-01', 'Afrosiyob Express', 'high_speed', 'Toshkent - Samarqand - Buxoro', 'Yo''lovchi', 40.5000, 68.2000, 210, True, 5, 'Harakatlanmoqda 🟢', 'O. Zokirov', False),
    ('AFR-02', 'Afrosiyob Tezkor', 'high_speed', 'Buxoro - Samarqand - Toshkent', 'Yo''lovchi', 39.8500, 64.6000, 195, True, 8, 'Harakatlanmoqda 🟢', 'A. Karimov', False),
    ('SHQ-101', 'Sharq Poezdi', 'passenger', 'Toshkent - Qarshi', 'Yo''lovchi', 39.3500, 66.8000, 85, True, 12, 'Harakatlanmoqda 🟢', 'M. Rahimov', False),
    ('SHQ-102', 'Sharq Express', 'passenger', 'Qarshi - Toshkent', 'Yo''lovchi', 38.8605, 65.7890, 0, False, 2, 'Bekatda to''xtagan 🟡', 'S. Narzullayev', False),
    ('NFT-909', 'Sanoat Neft Tarkibi', 'freight', 'Buxoro - Farg''ona', 'Neft Mahsulotlari (Xavfli)', 41.0500, 70.0500, 62, True, 45, 'Harakatlanmoqda 🟢', 'E. Axmedov', False),
    ('YUK-301', 'O''zbekiston Kon-Metall', 'freight', 'Olmaliq - Navoiy', 'Ruda va Metall', 40.8000, 69.1000, 55, True, 15, 'Harakatlanmoqda 🟢', 'B. Qodirov', False),
    ('YUK-302', 'Qishloq Xo''jaligi Yuk', 'freight', 'Andijon - Toshkent', 'Bug''doy va Paxta', 40.8800, 71.5000, 48, True, 10, 'Harakatlanmoqda 🟢', 'D. Umarov', False),
    ('PAS-501', 'Toshkent - Marg''ilon', 'passenger', 'Toshkent - Farg''ona', 'Yo''lovchi', 41.1500, 69.8000, 72, True, 18, 'Harakatlanmoqda 🟢', 'X. G''ofurov', False),
    ('PAS-502', 'Termiz Yo''lovchi', 'passenger', 'Toshkent - Termiz', 'Yo''lovchi', 38.2000, 67.2000, 68, True, 22, 'Harakatlanmoqda 🟢', 'N. Tojiyev', False),
    ('YUK-303', 'Tranzit Konteyner', 'freight', 'Nukus - Buxoro', 'Konteynerlar', 41.8000, 61.2000, 60, True, 8, 'Harakatlanmoqda 🟢', 'J. Rasulov', False)
]

@app.on_event("startup")
async def startup():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        print("✅ PostgreSQL Bazasiga muvaffaqiyatli ulandi!")
        
        # Jadval yaratish va 10 ta poyezdni avtomatik joylash
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trains (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100),
                    type VARCHAR(50),
                    route VARCHAR(100),
                    cargo_type VARCHAR(100),
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    speed INT,
                    is_moving BOOLEAN,
                    risk_level INT,
                    status VARCHAR(100),
                    driver VARCHAR(100),
                    emergency BOOLEAN,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Agar baza bo'sh bo'lsa, poyezdlarni qo'shadi
            count = await conn.fetchval("SELECT COUNT(*) FROM trains;")
            if count == 0:
                for t in INITIAL_TRAINS:
                    await conn.execute("""
                        INSERT INTO trains (id, name, type, route, cargo_type, latitude, longitude, speed, is_moving, risk_level, status, driver, emergency)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """, *t)
                print("✅ Bazaga 10 ta dastlabki poyezdlar kiritildi!")

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
            SET emergency = true, is_moving = false, speed = 0, risk_level = 99,
                status = '🚨 FAVQULODDA AVARIYA / TO''XTASH!'
            WHERE id = $1
        """, train_id)
    return {"status": "success", "message": "Avariya holati saqlandi"}

@app.post("/reset-emergency/{train_id}")
async def reset_emergency(train_id: str):
    if not db_pool:
        return {"status": "error", "message": "Baza ulanmagan"}
    async with db_pool.acquire() as conn:
        await conn.execute("""
            UPDATE trains
            SET emergency = false, is_moving = true, speed = 60, risk_level = 10,
                status = 'Harakatlanmoqda 🟢'
            WHERE id = $1
        """, train_id)
    return {"status": "success", "message": "Xavf bekor qilindi"}