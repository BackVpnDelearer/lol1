import asyncio
import websockets
import os
import http.server
import threading

# Render сам выдает порт через переменную среды, если ее нет — ставим 10000
PORT = int(os.environ.get("PORT", 10000))

admin_conn = None
client_conn = None

# --- КОСТЫЛЬ ДЛЯ ОБХОДА ТАЙМ-АУТА RENDER ---
def run_dummy_http():
    """Запускает простейший веб-сервер, чтобы Render думал, что это сайт"""
    server_address = ('0.0.0.0', PORT)
    # Создаем заглушку, которая на любой запрос отвечает кодом 200 OK
    class SimpleHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"OK")
        def log_message(self, format, *args):
            return # Отключаем лишние логи в консоль
            
    httpd = http.server.HTTPServer(server_address, SimpleHandler)
    print(f"[*] HTTP-заглушка запущена на порту {PORT}")
    httpd.serve_forever()

async def handle_connection(websocket, path):
    global admin_conn, client_conn
    try:
        auth_data = await websocket.recv()
        auth_data = auth_data.strip()
        
        if auth_data == "IAM_ADMIN":
            admin_conn = websocket
            print("[+] Пульт управления подключен!")
            try:
                async for message in websocket:
                    if client_conn:
                        await client_conn.send(message)
                    else:
                        await websocket.send("error:Klient seychas vne seti!")
            except:
                pass
            finally:
                admin_conn = None
                
        elif auth_data == "IAM_CLIENT":
            client_conn = websocket
            print("[+] Управляемый ПК подключен!")
            try:
                async for message in websocket:
                    if admin_conn:
                        await admin_conn.send(message)
            except:
                pass
            finally:
                client_conn = None
                
    except Exception as e:
        print(f"Ошибка сокета: {e}")

async def main():
    # Запускаем HTTP-заглушку в отдельном потоке, чтобы она не мешала веб-сокетам
    threading.Thread(target=run_dummy_http, daemon=True).start()
    
    # Запускаем наш основной сервер управления на том же порту
    # Веб-сокеты умеют работать на одном порту вместе с HTTP
    async with websockets.serve(handle_connection, "0.0.0.0", PORT):
        print(f"[*] Облачный сервер управления готов.")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
