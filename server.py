import socket
import threading
import sys
import json
import random

class NimServer:
    def __init__(self, port, piles):
        self.host = '0.0.0.0'
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []
        self.piles = piles
        self.current_turn = None
        self.lock = threading.Lock()

    def start_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        print(f"Server listening on port {self.port}...")

        while len(self.clients) < 2:
            conn, addr = self.server_socket.accept()
            player_id = len(self.clients)
            self.clients.append((conn, player_id))
            print(f"Client connected from {addr}, assigned ID={player_id}")
            threading.Thread(target=self.handle_client, args=(conn, player_id), daemon=True).start()

        self.current_turn = random.randint(0, 1)
        print(f"Game started with piles: {self.piles}")
        self.broadcast({"type": "start", "piles": self.piles, "turn": self.current_turn})

    def handle_client(self, conn, player_id):
        conn.sendall(json.dumps({"type": "id", "id": player_id}).encode())

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode())

                if message['type'] == 'move':
                    self.process_move(player_id, message['pile'], message['count'])
                elif message['type'] == 'state':
                    self.send_state(conn, player_id)
            except Exception as e:
                print(f"Error with player {player_id}: {e}")
                break

        conn.close()

    def send_state(self, conn, player_id):
        turn_msg = "Your turn!" if self.current_turn == player_id else f"Player {self.current_turn}'s turn."
        conn.sendall(json.dumps({
            "type": "state",
            "piles": self.piles,
            "turn_msg": turn_msg
        }).encode())

    def process_move(self, player_id, pile, count):
        with self.lock:
            if self.current_turn != player_id:
                self.send_to(player_id, {"type": "error", "msg": "Not your turn."})
                return

            if pile >= len(self.piles) or pile < 0:
                self.send_to(player_id, {"type": "error", "msg": "Invalid pile index."})
                return

            if count <= 0 or count > self.piles[pile]:
                self.send_to(player_id, {"type": "error", "msg": "Invalid number of objects."})
                return

            self.piles[pile] -= count
            print(f"Player {player_id} removed {count} from pile {pile}. Piles: {self.piles}")

            if all(p == 0 for p in self.piles):
                self.broadcast({"type": "win", "winner": player_id})
                return

            self.current_turn = 1 - self.current_turn
            self.broadcast({"type": "update", "piles": self.piles, "turn": self.current_turn})

    def send_to(self, player_id, message):
        conn, _ = self.clients[player_id]
        conn.sendall(json.dumps(message).encode())

    def broadcast(self, message):
        for conn, _ in self.clients:
            try:
                conn.sendall(json.dumps(message).encode())
            except:
                continue


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python server.py <port> [<pile1> <pile2> ...]")
        sys.exit(1)

    port = int(sys.argv[1])
    piles = list(map(int, sys.argv[2:])) if len(sys.argv) > 2 else [5, 7, 9]

    server = NimServer(port, piles)
    server.start_server()
