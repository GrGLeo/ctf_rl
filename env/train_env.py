import time
import gymnasium as gym
import numpy as np
import socket
import struct
from packet import RoomRequestPacket, ActionPacket, decode_rle


class CtfEnv(gym.Env):
    def __init__(self, server_ip, server_port, room_type):
        super(CtfEnv, self).__init__()

        self.action_space = gym.spaces.Discrete(7)
        self.observation_space = gym.spaces.Box(
            low=0, high=7, shape=(20, 50), dtype=np.uint8
        )

        # Initialize the TCP connection
        self.server_ip = server_ip
        self.server_port = server_port
        self.room_type = room_type
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_ip, self.server_port))

        # Initialize state
        # calculate reward
        self.points = 0
        self.enemy_point = 0
        self.pos = [0, 0]  # row and col player position

        self.state = np.zeros((20, 50), dtype=np.uint8)

    def send_room_request(self):
        packet = RoomRequestPacket(self.room_type)
        self.sock.sendall(packet.serialize())

        game_start_packet = self.sock.recv(3)
        version, code, success = struct.unpack("BBB", game_start_packet)
        if code == 6 and success == 0:
            print("Game started successfully.")
        else:
            raise Exception("Failed to start game.")

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.send_room_request()
        self.state = np.zeros((20, 50), dtype=np.uint8)
        return self.state, {}

    def step(self, action):
        action_packet = ActionPacket(action)
        self.sock.sendall(action_packet.serialize())

        points = self.receive_board_packet()
        reward = 0
        done = False

        return self.state, reward, done, False, {}

    def receive_board_packet(self):
        header = self.sock.recv(2)
        version, code = struct.unpack("BB", header)
        if version != 1:
            raise ValueError("Wrong version")
        if code == 8:
            header = self.sock.recv(3)
            points = struct.unpack("BB", header[:2])
            self.point, self.enemy_point = points[0], points[1]
            length = header[2]
            encoded_board = self.sock.recv(length)
            self.state = decode_rle(encoded_board)
            return points
        elif code == 9:
            # delta packet
            header = self.sock.recv(8)
            _ = struct.unpack(">i", header[:4])[0]
            points = struct.unpack("BB", header[4:6])
            count = struct.unpack(">H", header[6:])[0]
            deltas = self.sock.recv(3*count)
            # deltas are struct of 3 byte with x, y, and value
            for i in range(0, len(deltas), 3):
                x, y, value = deltas[i], deltas[i+1], deltas[i+2]
                self.state[y][x] = value
            return points

    def render(self, mode="human"):
        print(f"State:\n{self.state}")

    def close(self):
        self.sock.close()


env = CtfEnv(server_ip="127.0.0.1", server_port=8082, room_type=0)
state, _ = env.reset()
print("Initial State:\n", state)

action = 1
next_state, reward, done, _, _ = env.step(action)
print("Next state:\n", next_state, "Reward: ", reward, "Done: ", done)
time.sleep(50/1000)
print("-----------------\n")
action = 1
next_state, reward, done, _, _ = env.step(action)
print("Next state:\n", next_state, "Reward: ", reward, "Done: ", done)
