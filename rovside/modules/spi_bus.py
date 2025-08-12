# rovside/modules/spi_bus.py
# Shared SPI bus for ALL rovside modules. Import get_bus() anywhere.

import os
import time
import atexit
import threading

class _DummySPI:
    def xfer2(self, data):
        print(f"⚠️ [ROV SPI:DUMMY] xfer2({data})")
        return [0] * len(data)
    def close(self):
        print("🔌 [ROV SPI:DUMMY] closed")

class SPIBus:
    def __init__(self, bus=None, dev=None, *, max_hz=1_000_000, mode=0, bits=8, debug=False):
        self.bus = int(os.environ.get("ROV_SPI_BUS", 0 if bus is None else bus))
        self.dev = int(os.environ.get("ROV_SPI_DEV", 0 if dev is None else dev))
        self.max_hz = max_hz
        self.mode = mode
        self.bits = bits
        self.debug = bool(int(os.environ.get("ROV_SPI_DEBUG", "0" if not debug else "1")))
        self._lock = threading.Lock()

        try:
            import spidev
            spi = spidev.SpiDev()
            spi.open(self.bus, self.dev)
            spi.max_speed_hz = self.max_hz
            spi.mode = self.mode
            spi.bits_per_word = self.bits
            spi.cshigh = False
            spi.lsbfirst = False
            time.sleep(0.01)
            self._spi = spi
            print(f"✅ [ROV SPI] open bus={self.bus} dev={self.dev} @ {self.max_hz/1000:.0f} kHz")
        except Exception as e:
            print(f"⚠️ [ROV SPI] Falling back to dummy: {e}")
            self._spi = _DummySPI()

    def xfer(self, bytes_list):
        """Full-duplex transfer; returns list of bytes read."""
        payload = [int(b) & 0xFF for b in bytes_list]
        with self._lock:
            if self.debug:
                print(f"📤 [ROV SPI] TX {payload}")
            rx = self._spi.xfer2(payload)
            if self.debug:
                print(f"📥 [ROV SPI] RX {rx}")
            return rx

    def send(self, bytes_list):
        """Write-only convenience (still clocks out via xfer)."""
        self.xfer(bytes_list)

    def close(self):
        try:
            self._spi.close()
        except Exception:
            pass

# -------- Singleton access --------
_BUS = None
def get_bus(**kwargs) -> SPIBus:
    global _BUS
    if _BUS is None:
        _BUS = SPIBus(**kwargs)
        atexit.register(_BUS.close)
    return _BUS
