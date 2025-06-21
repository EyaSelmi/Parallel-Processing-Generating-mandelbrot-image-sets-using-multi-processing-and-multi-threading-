class Bitmap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = [0] * (width * height)

    def get(self, x, y):
        return self.data[y * self.width + x]

    def set(self, x, y, value):
        self.data[y * self.width + x] = value

    def reset(self, value):
        for i in range(len(self.data)):
            self.data[i] = value

    def width_(self):
        return self.width

    def height_(self):
        return self.height

    def data_(self):
        return self.data

def make_rgba(r, g, b, a=255):
    return ((a << 24) | (r << 16) | (g << 8) | b)

def get_red(rgba):
    return (rgba >> 16) & 0xff

def get_green(rgba):
    return (rgba >> 8) & 0xff

def get_blue(rgba):
    return rgba & 0xff

import struct

def save_bitmap_as_bmp(bitmap, filename):
    width, height = bitmap.width, bitmap.height
    row_padded = (width * 3 + 3) & ~3
    filesize = 54 + row_padded * height
    bmp_header = bytearray([
        0x42, 0x4D,  # Signature 'BM'
        *struct.pack('<I', filesize),
        0, 0, 0, 0,  # Reserved
        54, 0, 0, 0,  # Offset to pixel data
        40, 0, 0, 0,  # DIB header size
        *struct.pack('<i', width),
        *struct.pack('<i', height),
        1, 0,        # Planes
        24, 0,       # Bits per pixel
        0, 0, 0, 0,  # Compression
        0, 0, 0, 0,  # Image size (can be 0 for BI_RGB)
        0, 0, 0, 0,  # X pixels per meter
        0, 0, 0, 0,  # Y pixels per meter
        0, 0, 0, 0,  # Total colors
        0, 0, 0, 0   # Important colors
    ])
    with open(filename, 'wb') as f:
        f.write(bmp_header)
        for y in range(height - 1, -1, -1):
            row = bytearray()
            for x in range(width):
                color = bitmap.get(x, y)
                r = get_red(color)
                g = get_green(color)
                b = get_blue(color)
                row.extend([b, g, r])
            row.extend([0] * (row_padded - width * 3))
            f.write(row)
