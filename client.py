import socket
import sys
import threading
import json

class NimClient:
    def __init__(self, server_ip, port):
        self.server_ip = server_ip
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_id = None
        self.running = True

    def connect(self):
        self.client_socket.connect((self.server_ip, self.port))
        print("Connected to server.")

        #Sunucudan gelen ID mesajını al ve oyuncu ID'sini ata
        id_msg = json.loads(self.client_socket.recv(1024).decode())
        if id_msg['type'] == 'id':
            self.player_id = id_msg['id']
            print(f"Your player ID is {self.player_id}.")

        #Serverdan gelen mesajları dinle
        threading.Thread(target=self.listen_to_server, daemon=True).start()

        while self.running:
            user_input = input()
            if user_input.lower() == 'state':
                self.send({"type": "state"})
                continue

            try:
                pile, count = map(int, user_input.strip().split())
                self.send({"type": "move", "pile": pile, "count": count})
            except:
                print("Invalid input format. Use: <pile_index> <num_objects>")

    def listen_to_server(self):
        while True:
            try:
                data = self.client_socket.recv(2048)
                if not data:
                    break
                messages = json.loads(data.decode())
                self.handle_message(messages)
            except Exception as e:
                print("Connection closed or error:", e)
                break

        self.running = False
        self.client_socket.close()

    #Serverdan gelen mesajları yönet ve işleme al
    def handle_message(self, msg):
        msg_type = msg.get("type")

        if msg_type == "start":
            self.print_piles(msg["piles"])
            if msg["turn"] == self.player_id:
                print("Game started. Your turn!")
            else:
                print(f"Game started. Player {msg['turn']}'s turn.")

        elif msg_type == "state":
            self.print_piles(msg["piles"])
            print(msg["turn_msg"])

        elif msg_type == "update":
            self.print_piles(msg["piles"])
            if msg["turn"] == self.player_id:
                print("Your turn!")
            else:
                print(f"Waiting for Player {msg['turn']}'s move.")

        elif msg_type == "error":
            print("Server says:", msg["msg"])

        elif msg_type == "win":
            if msg["winner"] == self.player_id:
                print("You won! Congratulations!")
            else:
                print("You lost. Better luck next time!")
            self.running = False

    def send(self, message):
        try:
            self.client_socket.sendall(json.dumps(message).encode())
        except:
            print("Failed to send message to server.")

    #Oyunun pile durumunu ekrana yazdır
    def print_piles(self, piles):
        print("Current pile state:")
        for i, count in enumerate(piles):
            print(f"Pile {i}: {'*' * count}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_ip> <port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    port = int(sys.argv[2])

    client = NimClient(server_ip, port)
    client.connect()
