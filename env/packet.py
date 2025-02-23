import struct
import numpy as np


class RoomRequestPacket:
    def __init__(self, room_type):
        self.version = 1
        self.code = 2
        self.room_type = room_type

    def serialize(self):
        return struct.pack('BBB', self.version, self.code, self.room_type)


class ActionPacket:
    def __init__(self, action):
        self.version = 1
        self.code = 7
        self.action = action

    def serialize(self):
        return struct.pack('BBB', self.version, self.code, self.action)


def decode_rle(rle):
    rle_string = rle.decode("utf-8")
    parts = rle_string.split("|")
    decoded = list()
    print(rle)
    print(rle_string)

    for part in parts:
        sub_parts = part.split(":")
        if len(sub_parts) != 2:
            raise ValueError("Failed to decode RLE")
        print(sub_parts)
        value = int(sub_parts[0])
        count = int(sub_parts[1])

        decoded.extend([value]*count)

    if len(decoded) != 20 * 50:
        raise ValueError("Decoded date does not match expected size")
    grid = np.array(decoded).reshape(20, 50)
    return grid
