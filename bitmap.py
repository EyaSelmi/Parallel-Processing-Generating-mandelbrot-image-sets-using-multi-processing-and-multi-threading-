import struct

class Bitmap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = [0] * (width * height)

def make_rgba(r, g, b, a=255):
    return (r << 24) | (g << 16) | (b << 8) | a

def bitmap_load(filename):
    with open(filename, 'rb') as f:
        header_field = f.read(2)
        if header_field != b'BM':
            print('bitmap: not a BMP file')
            return None
        f.seek(18)
        width, height = struct.unpack('<ii', f.read(8))
        f.seek(2, 1)  # skip planes
        bits = struct.unpack('<H', f.read(2))[0]
        compression = struct.unpack('<I', f.read(4))[0]
        if compression != 0 or bits != 24:
            print('bitmap: sorry, I only support 24-bit uncompressed bitmaps.')
            return None
        # Skip to pixel data offset
        f.seek(54)
        m = Bitmap(width, height)
        row_padded = (width * 3 + 3) & (~3)
        for y in range(height):
            row = f.read(row_padded)
            for x in range(width):
                i = (height - 1 - y) * width + x
                b, g, r = row[x*3:x*3+3]
                if b == 0 and g == 0 and r == 0:
                    m.data[i] = 0
                else:
                    m.data[i] = make_rgba(r, g, b, 255)
        return m

