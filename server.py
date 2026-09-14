import asyncio
import websockets
import os

# Получаем порт от Render
PORT = int(os.environ.get("PORT", 10000))

admin_conn = None
client_conn = None

async def http_handler(path, request_headers):
    """Эта функция отвечает кодом 200 OK роботу Render, когда он проверяет порт как сайт"""
    # Если робот пришел проверять порт по HTTP
    if path == "/":
        # Возвращаем правильный HTTP-ответ, чтобы Render перешел в статус LIVE
        return websockets.http.Status.OK, [("Content-Type", "text/plain")], b"OK"

async def handle_connection(websocket, path):
    """Эта функция обрабатывает подключения Пульта и Клиента"""
    global admin_conn, client_conn
    try:
        # Читаем приветственное сообщение от подключившегося устройства
        auth_data = await websocket.recv()
        auth_data = auth_data.strip()
        
        # ЕСЛИ ПОДКЛЮЧИЛСЯ ПУЛЬТ
        if auth_data == "IAM_ADMIN":
            admin_conn = websocket
            print("[+] Пульт управления подключен к облаку!")
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
                print("[-] Пульт отключился.")
                
        # ЕСЛИ ПОДКЛЮЧИЛСЯ КЛИЕНТ
        elif auth_data == "IAM_CLIENT":
            client_conn = websocket
            print("[+] Управляемый ПК подключен к облаку!")
            try:
                async for message in websocket:
                    if admin_conn:
                        await admin_conn.send(message)
            except:
                pass
            finally:
                client_conn = None
                print("[-] Клиент отключился.")
                
    except Exception as e:
        print(f"Ошибка сокета: {e}")

async def main():
    # Запускаем один сервер, который умеет одновременно обрабатывать и HTTP (process_request),
    # и входящие веб-сокет соединения на одном порту! Конфликта портов больше не будет.
    async with websockets.serve(handle_connection, "0.0.0.0", PORT, process_request=http_handler):
        print(f"[*] Облачный моно-сервер запущен на порту {PORT}")
        await asyncio.Future() # Держит сервер активным

if __name__ == "__main__":
    asyncio.run(main())
