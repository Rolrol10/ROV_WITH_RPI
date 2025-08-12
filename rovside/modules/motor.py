# rovside/modules/motor.py
# Receives throttle + turn over WS, forwards via SPI, and echoes telemetry back.

import time, json, atexit
from modules.spi_bus import get_bus

TYPE = "motor"

# --- Toggle terminal printing of throttle/turn here ---
PRINT_VALUES = True  # set True to print throttle/turn updates

# Simple packet framing: [SYNC=0xAA][LEN][CMD][payload...][CRC8]
SYNC = 0xAA
CMD_THROTTLE_TURN = 0x01   # payload: [throttle_byte, turn_byte]
CMD_STOP          = 0x02

CHANGE_THRESHOLD = 1
MIN_INTERVAL     = 0.02   # 50 Hz
FORCE_SEND_AFTER = 0.3

bus = get_bus(max_hz=1_000_000, mode=0, bits=8)

_last_throttle = 0
_last_turn     = 0
_last_send_t   = 0.0

# Optional broadcast hook (set by server when loading the module)
_BROADCAST = None

def _crc8(data, poly=0x07, init=0x00):
    c = init
    for b in data:
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if (c & 0x80) else (c << 1) & 0xFF
    return c

def _pkt(cmd, payload):
    body = [SYNC, 0, cmd] + [int(x) & 0xFF for x in payload]
    body[1] = len(body) - 2 + 1  # LEN=(CMD..payload)+CRC, excludes SYNC
    return body + [_crc8(body)]

def _clamp_pct(v):
    try:
        return max(-100, min(100, int(round(float(v)))))
    except Exception:
        return 0

def _map_pct_byte(v):          # -100..100 -> 0..200 (center=100)
    return _clamp_pct(v) + 100

def _changed(a, b, th=CHANGE_THRESHOLD):
    return abs(int(a) - int(b)) >= th

async def set(data, websocket=None):
    """
    Expects:
      { "type":"motor", "action":"set", "throttle":-100..100, "turn":-100..100 }
    Aliases also accepted: "steer" or "steering" instead of "turn".
    """
    global _last_throttle, _last_turn, _last_send_t

    th = _clamp_pct(data.get("throttle", _last_throttle))
    tn = _clamp_pct(data.get("turn", data.get("steer", data.get("steering", _last_turn))))

    now = time.monotonic()
    should_send = (
        _changed(th, _last_throttle) or
        _changed(tn, _last_turn) or
        (now - _last_send_t) >= FORCE_SEND_AFTER
    )

    if should_send and (now - _last_send_t) >= MIN_INTERVAL:
        bus.send(_pkt(CMD_THROTTLE_TURN, [_map_pct_byte(th), _map_pct_byte(tn)]))
        _last_throttle, _last_turn = th, tn
        _last_send_t = now

        if PRINT_VALUES:
            print(f"🛞 [MOTOR] throttle={th:>4}%  turn={tn:>4}%")

        # Echo back to client (confirmation)
        msg = json.dumps({
            "type": "motor",
            "event": "rx",
            "throttle": th,
            "turn": tn,
            "ts": now
        })
        if websocket is not None:
            try:    await websocket.send(msg)
            except Exception: pass
        if _BROADCAST is not None:
            try:    await _BROADCAST(msg)
            except Exception: pass

async def stop(_data=None, websocket=None):
    global _last_throttle, _last_turn, _last_send_t
    bus.send(_pkt(CMD_STOP, [0, 0]))
    _last_throttle = _last_turn = 0
    _last_send_t = time.monotonic()
    print("🛑 [MOTOR] stop")
    if websocket is not None:
        try:
            await websocket.send(json.dumps({
                "type":"motor","event":"rx","throttle":0,"turn":0,"ts":_last_send_t
            }))
        except Exception:
            pass

def close(_data=None):
    # Leave SPI open; shared with other modules
    print("🔌 [MOTOR] ready; SPI bus shared with other modules")

# Called by the server on load; we keep broadcast for optional telemetry fan-out.
async def start_background_loop(broadcast_func):
    global _BROADCAST
    _BROADCAST = broadcast_func

atexit.register(close)

ACTIONS = {
    "set":       set,
    "set_speed": set,   # alias
    "drive":     set,   # alias
    "stop":      stop,
    "close":     close,
}
