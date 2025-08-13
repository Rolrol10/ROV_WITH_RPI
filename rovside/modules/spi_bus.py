# Shared SPI bus for ALL rovside modules. Import get_bus() anywhere.

import os, time, atexit, threading

class _DummySPI:
    def xfer2(self, data):
        print(f"⚠️ [ROV SPI:DUMMY] xfer2({data})")
        return [0] * len(data)
    def close(self):
        print("🔌 [ROV SPI:DUMMY] closed")

class SPIBus:
    def __init__(self, bus=None, dev=None, *, max_hz=500000, mode=0, bits=8, debug=True):
        self.bus = int(os.environ.get("ROV_SPI_BUS", 0 if bus is None else bus))
        self.dev = int(os.environ.get("ROV_SPI_DEV", 0 if dev is None else dev))
        self.max_hz = max_hz
        self.mode = mode
        self.bits = bits
        self.debug = bool(int(os.environ.get("ROV_SPI_DEBUG", "0" if not debug else "1")))
        self._lock = threading.Lock()

        # Optional manual CS (BCM pin). If set, we’ll toggle this instead of relying on CE0/CE1 wiring.
        self._manual_cs_bcm = os.environ.get("ROV_SPI_MANUAL_CS")
        self._gpio = None
        if self._manual_cs_bcm is not None:
            try:
                self._manual_cs_bcm = int(self._manual_cs_bcm)
                import RPi.GPIO as GPIO
                self._gpio = GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                GPIO.setup(self._manual_cs_bcm, GPIO.OUT, initial=GPIO.HIGH)  # idle high
                print(f"🔧 [ROV SPI] Manual CS on BCM{self._manual_cs_bcm}")
            except Exception as e:
                print(f"⚠️ [ROV SPI] Manual CS requested but GPIO init failed: {e}")
                self._manual_cs_bcm = None

        try:
            import spidev
            spi = spidev.SpiDev()
            spi.open(self.bus, self.dev)
            spi.max_speed_hz = self.max_hz
            spi.mode = self.mode           # CPOL=0, CPHA=0  → mode 0
            spi.bits_per_word = self.bits  # 8 bits
            spi.cshigh = False             # active-low
            spi.lsbfirst = False
            # Optional: spi.threewire = False
            time.sleep(0.01)
            self._spi = spi
            print(f"✅ [ROV SPI] open bus={self.bus} dev={self.dev} @ {self.max_hz/1000:.0f} kHz")
        except Exception as e:
            print(f"⚠️ [ROV SPI] Falling back to dummy: {e}")
            self._spi = _DummySPI()

    def _cs_low(self):
        if self._gpio and self._manual_cs_bcm is not None:
            self._gpio.output(self._manual_cs_bcm, 0)

    def _cs_high(self):
        if self._gpio and self._manual_cs_bcm is not None:
            self._gpio.output(self._manual_cs_bcm, 1)

    def xfer(self, bytes_list):
        """Full-duplex transfer; returns list of bytes read."""
        payload = [int(b) & 0xFF for b in bytes_list]
        with self._lock:
            if self.debug:
                print(f"📤 [ROV SPI] TX {payload}")
            # If manual CS is used, assert it just before the transfer
            if self._manual_cs_bcm is not None:
                self._cs_low()
                # tiny setup delay so STM32 EXTI sees CS before first clock
                time.sleep(0.000005)  # 5 µs
            try:
                rx = self._spi.xfer2(payload)
            finally:
                if self._manual_cs_bcm is not None:
                    # tiny hold time then deassert
                    time.sleep(0.000002)  # 2 µs
                    self._cs_high()
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
        try:
            if self._gpio and self._manual_cs_bcm is not None:
                self._cs_high()
                self._gpio.cleanup(self._manual_cs_bcm)
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
