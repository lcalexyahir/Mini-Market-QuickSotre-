from config import Config
import psycopg2

print(f"Conectando a base de datos: {Config.DB_NAME}")

try:
    conn = psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD
    )
    print("✅ Conexión exitosa a MiniMarketOF")
    
    cursor = conn.cursor()
    cursor.execute("SELECT current_database();")
    resultado = cursor.fetchone()
    print(f"Conectado a: {resultado[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")