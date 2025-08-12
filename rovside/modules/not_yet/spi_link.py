#!/usr/bin/env python3
# spi_link.py — Raspberry Pi SPI master for dual-motor control

import spidev

SYNC = 0xAA
CMD_DRIVE = 0x01
CMD_STOP  = 0x02

def crc8(data, poly=0x07, init=0x00):
    c = init
    for b in data:
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if (c & 0x80) else (c << 1) & 0xFF
    return c

class SPIDriver:
    def __init__(self, bus=0, device=0, max_hz=1_000_000, mode=0, bits=8):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = max_hz
        self.spi.mode = mode
        self.spi.bits_per_word = bits
        self.spi.cshigh = False
        self.spi.lsbfirst = False

    def _send(self, payload_bytes):
        length = len(payload_bytes)
        pkt_wo_crc = [SYNC, length] + payload_bytes
        pkt = pkt_wo_crc + [crc8(pkt_wo_crc)]
        self.spi.xfer2(pkt)

    def drive(self, left_pct, right_pct):
        # clamp to [-100, 100] and map to 0..200 (center=100)
        l = max(-100, min(100, int(left_pct))) + 100
        r = max(-100, min(100, int(right_pct))) + 100
        self._send([CMD_DRIVE, l, r])

    def stop(self):
        self._send([CMD_STOP, 0, 0])

    def close(self):
        try:
            self.stop()
        finally:
            self.spi.close()
