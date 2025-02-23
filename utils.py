import socket
import time
import struct
import threading

class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.listening = False

    def connect(self):
        try:
            # Create a socket object
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to the server
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Connection error: {e}")
            self.close()

    def send_packet(self, packet):
        try:
            if self.client_socket:
                # Serialize the packet to bytes and send it
                serialized_packet = packet.serialize()
                if serialized_packet:
                    self.client_socket.sendall(serialized_packet)
                    print(f"Sent packet: {packet}")
        except Exception as e:
            print(f"Send error: {e}")

    def receive_game_start_packet(self):
        try:
            if self.client_socket:
                # Receive the GameStartPacket
                data = self.client_socket.recv(12)  # Assuming 3 integers of 4 bytes each
                if len(data) == 12:
                    packet = GameStartPacket.from_bytes(data)
                    if packet:
                        print(f"Received GameStartPacket: {packet}")
                        if packet.version == 1 and packet.code == 6:
                            return packet.success == 1
                    else:
                        print("Failed to decode GameStartPacket")
                else:
                    print("Failed to receive complete GameStartPacket")
        except Exception as e:
            print(f"Receive error: {e}")
        return False

    def receive_board_packet(self):
        try:
            if self.client_socket:
                # Receive the header (version, code, points)
                header = self.client_socket.recv(16)
                if len(header) == 16:
                    packet = BoardPacket.from_bytes(header)
                    if packet:
                        print(f"Received BoardPacket: {packet}")
                        if packet.version == 1 and packet.code == 8:
                            # Receive the encoded board
                            encoded_board_length = packet.points[1]  # Assuming points[1] contains the length
                            encoded_board = self.client_socket.recv(encoded_board_length)
                            packet.encoded_board = encoded_board
                            # Decode the encoded board
                            decoded_board = decode_rle(packet.encoded_board.decode('utf-8'))
                            if decoded_board:
                                for row in decoded_board:
                                    print(row)
                        else:
                            print("Invalid version or code")
                    else:
                        print("Failed to decode BoardPacket header")
                else:
                    print("Failed to receive complete header")
        except Exception as e:
            print(f"Receive error: {e}")

    def listen_for_packets(self):
        self.listening = True
        try:
            while self.listening:
                self.receive_board_packet()
        except Exception as e:
            print(f"Listening error: {e}")
        finally:
            self.listening = False

    def start_listening(self):
        # Start listening in a separate thread
        threading.Thread(target=self.listen_for_packets).start()

    def stop_listening(self):
        self.listening = False

    def close(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            print("Connection closed.")

class LoginPacket:
    def __init__(self, username="", password="", version=1, code=0):
        self.version = version
        self.code = code
        self.username = username
        self.password = password

    def serialize(self):
        try:
            # Encode strings to bytes
            username_bytes = self.username.encode('utf-8')
            password_bytes = self.password.encode('utf-8')

            # Create a binary representation of the packet
            packet = bytearray()
            packet.append(self.version)
            packet.append(self.code)

            # Pack the lengths of the username and password as uint16
            packet.extend(struct.pack('!H', len(username_bytes)))
            packet.extend(username_bytes)
            packet.extend(struct.pack('!H', len(password_bytes)))
            packet.extend(password_bytes)

            return bytes(packet)
        except Exception as e:
            print(f"Serialization error: {e}")
            return None

    def __repr__(self):
        return (f"LoginPacket(version={self.version}, code={self.code}, "
                f"username='{self.username}', password='{self.password}')")

class RoomRequestPacket:
    def __init__(self, room_type, version=1, code=2):
        self.version = version
        self.code = code
        self.room_type = room_type

    def serialize(self):
        try:
            # Create a binary representation of the packet
            packet = bytearray()
            packet.append(self.version)
            packet.append(self.code)
            packet.append(self.room_type)
            return bytes(packet)
        except Exception as e:
            print(f"Serialization error: {e}")
            return None

    def version(self):
        return self.version

    def code(self):
        return self.code

    def __repr__(self):
        return (f"RoomRequestPacket(version={self.version}, code={self.code}, "
                f"room_type={self.room_type})")

class GameStartPacket:
    def __init__(self, version=1, code=6, success=0):
        self.version = version
        self.code = code
        self.success = success

    @staticmethod
    def from_bytes(data):
        try:
            # Unpack the version, code, and success from the binary data
            version, code, success = struct.unpack('!3i', data)
            return GameStartPacket(version=version, code=code, success=success)
        except Exception as e:
            print(f"Decoding error: {e}")
            return None

    def __repr__(self):
        return (f"GameStartPacket(version={self.version}, code={self.code}, "
                f"success={self.success})")

class BoardPacket:
    def __init__(self, version=1, code=8, points=(0, 0), encoded_board=b''):
        self.version = version
        self.code = code
        self.points = points
        self.encoded_board = encoded_board

    @staticmethod
    def from_bytes(data):
        try:
            # Unpack the version, code, and points from the binary data
            version, code, point1, point2 = struct.unpack('!4i', data[:16])
            points = (point1, point2)

            return BoardPacket(version=version, code=code, points=points)
        except Exception as e:
            print(f"Decoding error: {e}")
            return None

    def __repr__(self):
        return (f"BoardPacket(version={self.version}, code={self.code}, "
                f"points={self.points}, encoded_board={self.encoded_board})")

def decode_rle(rle):
    try:
        # Split the RLE data into parts
        parts = rle.split('|')
        decoded = []

        # Process each part
        for part in parts:
            sub_parts = part.split(':')
            if len(sub_parts) != 2:
                raise ValueError("Failed to decode RLE")

            value = int(sub_parts[0])
            count = int(sub_parts[1])

            # Append the value 'count' times to the decoded list
            decoded.extend([value] * count)

        # Create a 20x50 grid
        grid = [[0] * 50 for _ in range(20)]

        # Fill the grid with the decoded values
        for i in range(20):
            grid[i][:] = decoded[i * 50:(i + 1) * 50]

        return grid

    except Exception as e:
        print(f"Decoding error: {e}")
        return None

# Example usage
client = TCPClient('127.0.0.1', 8082)
client.connect()

login_packet = LoginPacket("user123", "pass456")
client.send_packet(login_packet)
time.sleep(1)

room_request_packet = RoomRequestPacket(room_type=0)
client.send_packet(room_request_packet)

# Wait for GameStartPacket
if client.receive_game_start_packet():
    # Start listening for incoming BoardPackets
    client.start_listening()

    # Keep the main thread alive to receive packets
    try:
        while True:
            pass
    except KeyboardInterrupt:
        client.stop_listening()
        client.close()
else:
    print("Failed to start game or invalid GameStartPacket")
    client.close()

