import socket
import threading

PORT = 65432
admin_conn = None
client_conn = None

def handle_connection(conn, addr):
    global admin_conn, client_conn
    try:
        conn.settimeout(5.0)
        auth_data = conn.recv(1024).decode('utf-8').strip()
        conn.settimeout(None)
        
        if auth_data == "IAM_ADMIN":
            admin_conn = conn
            print(f"[+] Пульт управления подключен! IP: {addr}")
            while True:
                data = conn.recv(4096)
                if not data: break
                if client_conn:
                    client_conn.sendall(data)
                else:
                    conn.sendall(b"error:Klient seychas vne seti!")
                    
        elif auth_data == "IAM_CLIENT":
            client_conn = conn
            print(f"[+] Управляемый ПК подключен! IP: {addr}")
            while True:
                data = conn.recv(65536)
                if not data: break
                if admin_conn:
                    admin_conn.sendall(data)
        else:
            conn.close()
            
    except Exception as e:
        print(f"[-] Ошибка устройства {addr}: {e}")
    finally:
        if conn == admin_conn: admin_conn = None
        elif conn == client_conn: client_conn = None

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', PORT))
        s.listen(5)
        print(f"[*] Центральный сервер успешно запущен на порту {PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
