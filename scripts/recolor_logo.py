# -*- coding: utf-8 -*-
"""
Перекрашивает белый логотип в тёмно-синий (#324266), сохраняя прозрачность.
Создаёт frontend/public/images/logo-dark.png из frontend/public/images/logo.png.

Работает без сторонних библиотек: читает PNG-чанки, распаковывает IDAT,
применяет фильтры строк, заменяет RGB (сохраняя альфу), собирает PNG обратно.
"""
import struct
import zlib
import os
import sys

NAVY = (0x32, 0x42, 0x66)  # --navy из style.css


def read_png(path):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a png'
    pos = 8
    chunks = []
    idat = b''
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        cdata = data[pos + 8:pos + 8 + length]
        chunks.append((ctype, cdata))
        if ctype == b'IDAT':
            idat += cdata
        pos += 12 + length
    return chunks, idat


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def unfilter(raw, w, h, bpp):
    stride = w * bpp
    out = bytearray(h * stride)
    pos = 0
    prev = bytearray(stride)
    for y in range(h):
        ftype = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + stride])
        pos += stride
        if ftype == 0:
            pass
        elif ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                up = prev[i]
                ul = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + paeth(left, up, ul)) & 0xFF
        else:
            raise ValueError('bad filter %d' % ftype)
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return out


def refilter(px, w, h, bpp):
    stride = w * bpp
    raw = bytearray()
    prev = bytearray(stride)
    for y in range(h):
        line = bytearray(px[y * stride:(y + 1) * stride])
        filt = bytearray(b'\x00')  # filter type 0 (None) — компрессия справится
        raw += filt + line
        prev = line
    return bytes(raw)


def main():
    src = os.path.join('frontend', 'public', 'images', 'logo.png')
    dst = os.path.join('frontend', 'public', 'images', 'logo-dark.png')

    chunks, idat = read_png(src)
    meta = {}
    for ctype, cdata in chunks:
        if ctype == b'IHDR':
            w, h, depth, ctype_, comp, filt, interlace = struct.unpack('>IIBBBBB', cdata)
            meta = dict(w=w, h=h, depth=depth, ctype=ctype_, interlace=interlace)
    assert meta['depth'] == 8, 'ожидается 8 бит на канал'
    assert meta['ctype'] == 6, 'ожидается RGBA'
    assert meta['interlace'] == 0, 'ожидается без interlace'

    w, h = meta['w'], meta['h']
    bpp = 4
    px = unfilter(zlib.decompress(idat), w, h, bpp)

    for i in range(0, len(px), bpp):
        r, g, b = px[i], px[i + 1], px[i + 2]
        # белый/почти белый -> navy
        if r > 235 and g > 235 and b > 235:
            px[i], px[i + 1], px[i + 2] = NAVY

    compressed = zlib.compress(bytes(refilter(px, w, h, bpp)), 9)

    out = bytearray(b'\x89PNG\r\n\x1a\n')
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    for ctype, cdata in [(b'IHDR', ihdr), (b'IDAT', compressed), (b'IEND', b'')]:
        out += struct.pack('>I', len(cdata)) + ctype + cdata
        out += struct.pack('>I', zlib.crc32(ctype + cdata) & 0xFFFFFFFF)

    with open(dst, 'wb') as f:
        f.write(out)
    print('OK: %s (%dx%d)' % (dst, w, h))


if __name__ == '__main__':
    sys.exit(main())
