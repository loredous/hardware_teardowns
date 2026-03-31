#!/usr/bin/env python3
"""
WBS01 Withings Scale — USB HID diagnostic tool

Packet layout (58 bytes, output):
  [0]     Report ID = 0x01
  [1]     TotalLen  = WPP_data_len + 4
  [2]     Fragment  = 0x01 (first/only) | 0x02 (continuation)
  [3]     0x01      marker
  [4]     0x00      marker
  [5]     WPP_data_len
  [6..]   WPP data:
            [0]   type = 0x01
            [1-2] CMD_ID  (big-endian)
            [3-4] payload_len (big-endian)
            [5..] payload (inner TLVs)

Inner TLV: [TAG_HI, TAG_LO, LEN_HI, LEN_LO, data...]  (big-endian)

Identified command IDs (all require device in HID pairing mode / mode 0x03):

  --- Documented ---
  0x0101  probe          no payload        -> device identity + MAC
  0x0102  get_ip         no payload        -> current IP
  0x0104  get_wifi       no payload        -> current SSID/auth
  0x0105  status         no payload        -> pairing/sync state

  --- Undocumented (simple) ---
  0x0202  backlight      inner TAG 0x0202  -> 3 bytes: display backlight control
  0x0203  lcd            inner TAG 0x0203  -> 3 bytes: LCD display control
  0x0209  weighttest     inner TAG 0x0209  -> 8 words: weight measurement test
  0x020a  dac            inner TAG 0x020b  -> 2 bytes: DAC output
  0x020c  wl             inner TAG 0x020d  -> wireless layer direct command
  0x020e  spiflash       inner TAG 0x0210  -> 2 bytes: BCM4315 SPI flash access
  0x020f  rtc            inner TAG 0x0211  -> RTC read/set
  0x0210  dump           inner TAG 0x0213  -> 9 bytes: [type(1B), addr(4B), len(4B)]

  --- Undocumented (compound) ---
  0x0205  [compound]     inner TAG 0x0205 -> perso (device identity write)
                         inner TAG 0x020c -> weight_cal
                         inner TAG 0x0212 -> weight_verif
  0x020d  [compound]     inner TAG 0x020e -> zmeter
                         inner TAG 0x020f -> zmeter_cal

Usage examples:
  python wbs01_diag.py probe
  python wbs01_diag.py dump 0x08000000 256
  python wbs01_diag.py spiflash 0x03 0x00
  python wbs01_diag.py lcd 0x01 0x00 0x00
  python wbs01_diag.py raw 0x0210 02130009 00 08000000 00000100
  python wbs01_diag.py scan 0x0200 0x0215
"""

import sys
import time
import struct
import argparse

try:
    import hid
except ImportError:
    sys.exit("Missing dependency: pip install hid")

VENDOR_ID  = 0x1fb2
PRODUCT_ID = 0x0001
PKT_SIZE   = 58

# ---------------------------------------------------------------------------
# Packet construction
# ---------------------------------------------------------------------------

def inner_tlv(tag: int, data: bytes) -> bytes:
    """Build one inner TLV field: [TAG_HI, TAG_LO, LEN_HI, LEN_LO, data...]"""
    return struct.pack(">HH", tag, len(data)) + data


def build_packet(cmd_id: int, payload: bytes = b"", fragment: int = 0x01) -> bytes:
    """Build a 58-byte WPP HID output packet."""
    wpp = struct.pack(">BHH", 0x01, cmd_id, len(payload)) + payload
    wpp_len = len(wpp)
    total_len = wpp_len + 4
    header = bytes([0x01, total_len, fragment, 0x01, 0x00, wpp_len])
    raw = header + wpp
    return raw.ljust(PKT_SIZE, b"\x00")[:PKT_SIZE]


def build_packet_continuation(data: bytes) -> bytes:
    """Build a continuation fragment (for large commands that span packets)."""
    inner = bytes([0x02]) + data  # 0x02 = continuation marker
    total_len = len(inner) + 1
    header = bytes([0x01, total_len, 0x01])
    raw = header + inner
    return raw.ljust(PKT_SIZE, b"\x00")[:PKT_SIZE]

# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

CMD_NAMES = {
    0x0101: "probe",        0x0102: "get_ip",
    0x0103: "connect",      0x0104: "get_wifi",
    0x0105: "status",       0x0107: "wifi_ant",
    0x0108: "country",
    0x0201: "battery",      0x0202: "backlight",
    0x0203: "lcd",          0x0204: "wifi_scan_param",
    0x0205: "weight_cal",   0x0206: "wifi_ant_en",
    0x0209: "weighttest",   0x020a: "dac",
    0x020b: "ip_settings",  0x020c: "wl",
    0x020d: "zmeter_cal",   0x020e: "spiflash",
    0x020f: "rtc",          0x0210: "dump",
}


def parse_inner_tlvs(payload: bytes) -> list:
    """Walk inner TLV fields in a WPP payload."""
    fields = []
    i = 0
    while i + 4 <= len(payload):
        tag = struct.unpack(">H", payload[i:i+2])[0]
        length = struct.unpack(">H", payload[i+2:i+4])[0]
        data = payload[i+4:i+4+length]
        fields.append({"tag": tag, "length": length, "data": data, "hex": data.hex()})
        i += 4 + length
    return fields


def parse_packet(data: bytes) -> dict:
    """Parse a raw HID input report into a structured dict."""
    data = bytes(data)
    if not data:
        return {}

    report_id = data[0]

    # Report ID 2 = UART/debug text log
    if report_id == 0x02:
        text = data[3:].rstrip(b"\x00").decode("ascii", errors="replace")
        return {"type": "debug", "report_id": report_id, "text": text}

    # Report ID 3 = raw log
    if report_id == 0x03:
        text = data[1:].rstrip(b"\x00").decode("ascii", errors="replace")
        return {"type": "log", "report_id": report_id, "text": text}

    # Report ID 1 = WPP response
    if len(data) < 11 or data[3] != 0x01:
        return {"type": "unknown", "report_id": report_id, "raw": data.hex()}

    wpp_len = data[5]
    wpp = data[6:6 + wpp_len]

    if len(wpp) < 5 or wpp[0] != 0x01:
        return {"type": "bad_wpp", "raw": data.hex()}

    cmd_id = struct.unpack(">H", wpp[1:3])[0]
    pay_len = struct.unpack(">H", wpp[3:5])[0]
    payload = wpp[5:5 + pay_len]
    inner = parse_inner_tlvs(payload)

    return {
        "type":      "wpp",
        "report_id": report_id,
        "cmd_id":    cmd_id,
        "cmd_name":  CMD_NAMES.get(cmd_id, "?"),
        "payload":   payload,
        "inner":     inner,
    }


def display(parsed: dict, verbose: bool = False):
    t = parsed.get("type")
    if t == "debug":
        text = parsed["text"].strip()
        if text:
            print(f"  [DEBUG]  {text}")
    elif t == "log":
        text = parsed["text"].strip()
        if text:
            print(f"  [LOG]    {text}")
    elif t == "wpp":
        cmd_id = parsed["cmd_id"]
        name = parsed["cmd_name"]
        payload = parsed["payload"]
        print(f"  [WPP]    cmd=0x{cmd_id:04x} ({name})  payload={len(payload)}B: {payload.hex()}")
        for field in parsed["inner"]:
            data = field["data"]
            print(f"           TAG=0x{field['tag']:04x}  len={field['length']}  {data.hex()}")
            if verbose:
                _try_decode(field["tag"], data)
    elif t in ("unknown", "bad_wpp"):
        print(f"  [RAW]    {parsed.get('raw', '')}")


def _try_decode(tag: int, data: bytes):
    """Attempt a best-effort decode of known response fields."""
    try:
        if tag == 0x0201 and len(data) >= 1:
            print(f"             battery level: {data[0]}")
        elif tag == 0x0105 and len(data) >= 1:
            print(f"             status: {data[0]}")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Device I/O
# ---------------------------------------------------------------------------

def open_device() -> hid.device:
    dev = hid.device()
    try:
        dev.open(VENDOR_ID, PRODUCT_ID)
    except OSError as e:
        sys.exit(f"Cannot open device (VID=0x{VENDOR_ID:04x} PID=0x{PRODUCT_ID:04x}): {e}\n"
                 "Check that the scale is connected and you have USB HID permissions.")
    return dev


def send_recv(pkt: bytes, timeout_ms: int = 2000, verbose: bool = False) -> list:
    """Open device, send packet, collect responses until quiet, close."""
    dev = open_device()
    dev.set_nonblocking(0)

    if verbose:
        print(f"  TX: {pkt.hex()}")

    dev.write(pkt)

    responses = []
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        data = dev.read(PKT_SIZE, timeout_ms=150)
        if data:
            responses.append(data)
            deadline = time.monotonic() + 0.4  # extend on each response
    dev.close()
    return responses


def run_command(cmd_id: int, payload: bytes = b"", timeout_ms: int = 2000,
                verbose: bool = False):
    name = CMD_NAMES.get(cmd_id, f"0x{cmd_id:04x}")
    print(f"→ {name} (CMD=0x{cmd_id:04x}  payload={len(payload)}B)")
    pkt = build_packet(cmd_id, payload)
    resps = send_recv(pkt, timeout_ms=timeout_ms, verbose=verbose)
    if not resps:
        print("  (no response)")
    for r in resps:
        display(parse_packet(r), verbose=verbose)

# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def do_probe(args):
    run_command(0x0101, verbose=args.verbose)


def do_status(args):
    run_command(0x0105, verbose=args.verbose)


def do_get_wifi(args):
    run_command(0x0104, verbose=args.verbose)


def do_get_ip(args):
    run_command(0x0102, verbose=args.verbose)


def do_backlight(args):
    data = bytes([args.b1 & 0xFF, args.b2 & 0xFF, args.b3 & 0xFF])
    run_command(0x0202, inner_tlv(0x0202, data), verbose=args.verbose)


def do_lcd(args):
    data = bytes([args.b1 & 0xFF, args.b2 & 0xFF, args.b3 & 0xFF])
    run_command(0x0203, inner_tlv(0x0203, data), verbose=args.verbose)


def do_weighttest(args):
    # 26-byte wire payload: [type(1B), 6×uint32_BE, flags(1B)]
    # Confirmed by firmware: wpp_unpack_weighttest checks param_2 == 0x1a (26)
    data = struct.pack(">B6IB", 0, 0, 0, 0, 0, 0, 0, 0)
    run_command(0x0209, inner_tlv(0x0209, data), verbose=args.verbose)


def do_dac(args):
    # 8-byte wire payload: [b0, b1, b2, uint32_BE, b7]
    # Confirmed by firmware: wpp_unpack_dac checks param_2 == 8
    data = struct.pack(">BBBIB", args.b1 & 0xFF, args.b2 & 0xFF, 0, 0, 0)
    run_command(0x020a, inner_tlv(0x020b, data), verbose=args.verbose)


def do_wl(args):
    # Wire layout: [b0(1B), uint32_BE(4B), b8(1B), L(1B), data(L bytes)] = 7+L bytes
    # Confirmed from wpp_unpack_wl (0x0800fb60): size check == struct[9] + 7
    # FUN_0800fb34 reads a 1-byte length L then L bytes of data
    if args.payload_hex:
        data = bytes.fromhex(args.payload_hex)
    else:
        data = struct.pack(">BI BB", 0, 0, 0, 0)  # b0=0, uint32=0, b8=0, L=0
    run_command(0x020c, inner_tlv(0x020d, data), verbose=args.verbose)


def do_spiflash(args):
    data = bytes([args.cmd_byte & 0xFF, args.data_byte & 0xFF])
    run_command(0x020e, inner_tlv(0x0210, data), verbose=args.verbose)


def do_rtc(args):
    # 6-byte wire payload: [flags(1B), flags(1B), timestamp(4B BE)]
    # Confirmed by firmware: wpp_unpack_rtc checks param_2 == 6
    data = struct.pack(">BBI", 0, 0, 0)
    run_command(0x020f, inner_tlv(0x0211, data), verbose=args.verbose)


def do_dump(args):
    # 9-byte payload: [type(1B), addr(4B big-endian), length(4B big-endian)]
    data = struct.pack(">BII", args.access_type, args.addr, args.length)
    run_command(0x0210, inner_tlv(0x0213, data),
                timeout_ms=5000, verbose=args.verbose)


def do_perso(args):
    data = bytes.fromhex(args.payload_hex) if args.payload_hex else b"\x00"
    run_command(0x0205, inner_tlv(0x0205, data), verbose=args.verbose)


def do_weight_cal(args):
    data = bytes.fromhex(args.payload_hex) if args.payload_hex else b"\x00" * 4
    run_command(0x0205, inner_tlv(0x020c, data), verbose=args.verbose)


def do_zmeter(args):
    # 14-byte wire payload: [b0(1B), b1(1B), uint32_BE, uint32_BE, uint32_BE]
    # Confirmed by firmware: wpp_unpack_zmeter checks param_2 == 0x0e (14)
    data = bytes.fromhex(args.payload_hex) if args.payload_hex else struct.pack(">BB3I", 0, 0, 0, 0, 0)
    run_command(0x020d, inner_tlv(0x020e, data), verbose=args.verbose)


def do_zmeter_cal(args):
    # 44-byte wire payload layout (confirmed from wpp_unpack_zmeter_cal at 0x0800fa20):
    #   [0]:    1B
    #   [1-4]:  uint32_BE
    #   [5]:    count byte MUST == 3 (FUN_0800f90c asserts this); [6-17]:  3×uint32_BE
    #   [18]:   count byte MUST == 3;                              [19-30]: 3×uint32_BE
    #   [31]:   count byte MUST == 3;                              [32-43]: 3×uint32_BE
    data = (bytes.fromhex(args.payload_hex) if args.payload_hex
            else struct.pack(">BIB3IB3IB3I", 0, 0, 3, 0, 0, 0, 3, 0, 0, 0, 3, 0, 0, 0))
    run_command(0x020d, inner_tlv(0x020f, data), verbose=args.verbose)


def do_raw(args):
    cmd_id = int(args.cmd_id, 0)
    payload = bytes.fromhex(args.payload_hex) if args.payload_hex else b""
    run_command(cmd_id, payload, verbose=args.verbose)


def do_list(_args):
    print("Known command IDs:")
    for cmd_id, name in sorted(CMD_NAMES.items()):
        print(f"  0x{cmd_id:04x}  {name}")


def do_scan(args):
    start = int(args.start, 0)
    end   = int(args.end, 0)
    print(f"Scanning CMD IDs 0x{start:04x}..0x{end:04x} (no-payload probe)")
    dev = open_device()
    dev.set_nonblocking(1)
    try:
        for cmd_id in range(start, end + 1):
            pkt = build_packet(cmd_id)
            dev.write(pkt)
            time.sleep(0.35)
            responses = []
            while True:
                data = dev.read(PKT_SIZE)
                if not data:
                    break
                responses.append(data)
            tag = f"0x{cmd_id:04x}  {CMD_NAMES.get(cmd_id, ''):<16}"
            if responses:
                parsed = [parse_packet(r) for r in responses]
                summary = " | ".join(
                    f"[{p.get('type','?')}]" +
                    (f" cmd=0x{p['cmd_id']:04x}" if p.get('type') == 'wpp' else
                     f" {p.get('text','')[:40]}" if p.get('type') == 'debug' else "")
                    for p in parsed
                )
                print(f"  {tag}  RESPONSE: {summary}")
            else:
                print(f"  {tag}  (no response)")
    finally:
        dev.close()

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="WBS01 Withings Scale USB HID diagnostic tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show raw TX bytes and field decodes")
    sub = parser.add_subparsers(dest="command", required=True)

    # ── documented ──────────────────────────────────────────────────────────
    sub.add_parser("probe",    help="Probe device identity (CMD 0x0101)")
    sub.add_parser("status",   help="Get pairing/sync status (CMD 0x0105)")
    sub.add_parser("get_wifi", help="Get current WiFi config (CMD 0x0104)")
    sub.add_parser("get_ip",   help="Get current IP address (CMD 0x0102)")

    # ── undocumented simple ──────────────────────────────────────────────────
    p = sub.add_parser("backlight", help="Set display backlight (CMD 0x0202)")
    p.add_argument("b1", type=lambda x: int(x, 0), help="byte 1")
    p.add_argument("b2", type=lambda x: int(x, 0), help="byte 2")
    p.add_argument("b3", type=lambda x: int(x, 0), help="byte 3")

    p = sub.add_parser("lcd", help="LCD display command (CMD 0x0203)")
    p.add_argument("b1", type=lambda x: int(x, 0))
    p.add_argument("b2", type=lambda x: int(x, 0))
    p.add_argument("b3", type=lambda x: int(x, 0))

    sub.add_parser("weighttest", help="Trigger weight test mode (CMD 0x0209)")

    p = sub.add_parser("dac", help="Set DAC output (CMD 0x020a, 8 bytes: b0 b1 [b2 uint32 b7 zeros])")
    p.add_argument("b1", type=lambda x: int(x, 0), help="DAC command byte")
    p.add_argument("b2", type=lambda x: int(x, 0), help="DAC channel/data byte")

    p = sub.add_parser("spiflash",
                       help="BCM4315 SPI flash access (CMD 0x020e, 2 bytes)")
    p.add_argument("cmd_byte",  type=lambda x: int(x, 0),
                   help="SPI command byte (e.g. 0x03 = read)")
    p.add_argument("data_byte", type=lambda x: int(x, 0),
                   help="SPI data byte (e.g. address LSB)")

    sub.add_parser("rtc", help="Read RTC (CMD 0x020f)")

    p = sub.add_parser("wl",
                       help="Wireless layer direct command (CMD 0x020c)")
    p.add_argument("payload_hex", nargs="?", default="",
                   help="Hex payload bytes (e.g. 0100)")

    p = sub.add_parser("dump",
                       help="MCU memory dump (CMD 0x0210). "
                            "Reads arbitrary flash/SRAM over USB.")
    p.add_argument("addr",   type=lambda x: int(x, 0),
                   help="Start address (e.g. 0x08000000 for flash start)")
    p.add_argument("length", type=lambda x: int(x, 0),
                   help="Byte count to read (e.g. 256)")
    p.add_argument("--type", dest="access_type", type=lambda x: int(x, 0),
                   default=0x01,
                   help="Access type byte (default 0x01 = memory read; 0x00/0x02 return error)")

    # ── undocumented compound ────────────────────────────────────────────────
    p = sub.add_parser("perso",
                       help="Device personalization write (CMD 0x0205, TAG 0x0205)")
    p.add_argument("payload_hex", nargs="?", default="",
                   help="Hex payload (device identity/key bytes)")

    p = sub.add_parser("weight_cal",
                       help="Write weight calibration constants (CMD 0x0205, TAG 0x020c)")
    p.add_argument("payload_hex", nargs="?", default="",
                   help="Hex calibration data")

    p = sub.add_parser("zmeter",
                       help="Z-meter (bioimpedance) query (CMD 0x020d, TAG 0x020e)")
    p.add_argument("payload_hex", nargs="?", default="",
                   help="Hex payload (default: 0000)")

    p = sub.add_parser("zmeter_cal",
                       help="Z-meter calibration data (CMD 0x020d, TAG 0x020f)")
    p.add_argument("payload_hex", nargs="?", default="",
                   help="Hex payload (default: 0000)")

    # ── utility ──────────────────────────────────────────────────────────────
    p = sub.add_parser("raw",
                       help="Send an arbitrary WPP command")
    p.add_argument("cmd_id",
                   help="CMD ID in hex (e.g. 0x0210)")
    p.add_argument("payload_hex", nargs="?", default="",
                   help="Raw WPP payload as hex (e.g. 02130009 00 08000000 00000100)")

    p = sub.add_parser("scan",
                       help="Probe every CMD ID in a range and report responses")
    p.add_argument("start", help="Start CMD ID hex (e.g. 0x0200)")
    p.add_argument("end",   help="End CMD ID hex   (e.g. 0x0215)")

    sub.add_parser("list", help="List all known command IDs")

    handlers = {
        "probe":      do_probe,
        "status":     do_status,
        "get_wifi":   do_get_wifi,
        "get_ip":     do_get_ip,
        "backlight":  do_backlight,
        "lcd":        do_lcd,
        "weighttest": do_weighttest,
        "dac":        do_dac,
        "spiflash":   do_spiflash,
        "rtc":        do_rtc,
        "wl":         do_wl,
        "dump":       do_dump,
        "perso":      do_perso,
        "weight_cal": do_weight_cal,
        "zmeter":     do_zmeter,
        "zmeter_cal": do_zmeter_cal,
        "raw":        do_raw,
        "list":       do_list,
        "scan":       do_scan,
    }

    args = parser.parse_args()
    # propagate -v to subcommands that don't define it explicitly
    if not hasattr(args, "verbose"):
        args.verbose = False

    try:
        handlers[args.command](args)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
