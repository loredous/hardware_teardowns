# USB HID Interface

- **VID/PID:** 0x1fb2 / 0x0001
- **Port:** Mini-USB in battery compartment
- **Packet format:** `[ReportID(1B), Length(1B), FragmentID(1B), TLV_payload(55B)]` — 58 bytes total
- **TLV encoding (WPP — Withings Pairing Protocol):** `[tag_hi, tag_lo, len_lo, len_hi, data...]`
- **Command ID:** `(tag_hi << 8) | tag_lo`
- **Dispatch function:** `HID_CommandDispatch` at `0x0800cb28`
- **Reference client:** https://github.com/zshannon/wbs01-web

### Packet format detail

```
[0]     Report ID = 0x01
[1]     TotalLen  = WPP_data_len + 4
[2]     Fragment  = 0x01 (first/only) | 0x02 (continuation)
[3]     0x01      marker  (data[3] != 0x01 → not a WPP response packet)
[4]     0x00      marker
[5]     WPP_data_len
[6..]   WPP data:
          [0]   type = 0x01
          [1-2] CMD_ID  (big-endian)
          [3-4] payload_len (big-endian)
          [5..] payload (inner TLVs)

Inner TLV: [TAG_HI, TAG_LO, LEN_HI, LEN_LO, data...]  (big-endian)
```

### Mode lock / assertion crash

- Mode byte at `param_1+0x214`: must be `0x03` for commands to be dispatched
- Set to `0x04` on successful dispatch; reset to `0x03` by response task
- **Wrong payload size → `FUN_0803f770` assertion → HID task killed → mode stuck at 0x04**
- Recovery: unplug and replug USB (batteries do not need to be removed)

---

## Documented Commands (0x01xx Host→Device)

| CMD ID | Name | Notes |
|--------|------|-------|
| 0x0101 | Probe / Identity | Requests firmware info + MAC |
| 0x0102 | Get Identity/BSSID | 65-byte response |
| 0x0103 | WiFi Connect (compound) | Inner types: 0x104=creds, 0x105=IP, 0x109=security mode, 0x10b=WPA PSK (32B PBKDF2-SHA1), 0x10c=IP addr |
| 0x0104 | Get WiFi Config | Returns current SSID/auth |
| 0x0105 | Get Status | Returns pairing/sync state |
| 0x0107 | WiFi Enable/Antenna | Toggle antenna |
| 0x0108 | Set Country Code | 67B, includes channel list |

---

## 0x02xx Commands — Device→Host (all require mode byte == 0x03)

All 0x02xx commands are dispatched via `HID_CommandDispatch` at `0x0800cb28`.
**No authentication or pairing gating is observed** — all commands are accepted in mode 3.

### Simple commands

| CMD ID | Inner TAG | WPP Handler | Handler addr | Wire size | Confirmed | Notes |
|--------|-----------|-------------|--------------|-----------|-----------|-------|
| 0x0201 | 0x0201 | `wpp_unpack_battery_state` | — | 3 bytes | — | Battery level |
| 0x0202 | 0x0202 | `wpp_unpack_backlight` | `0x0800f5dc` | 3 bytes | ✓ | Display backlight; echoes back state |
| 0x0203 | 0x0203 | `wpp_unpack_lcd` | `0x0800f590` | 3 bytes | ✓ | LCD display control; echoes back state |
| 0x0204 | 0x0204 | `wpp_unpack_wifi_scan_param` | — | 6 bytes | — | WiFi scan params |
| 0x0206 | 0x0206 | `wpp_unpack_wifi_ant` | — | — | — | WiFi antenna/enable |
| 0x0209 | 0x0209 | `wpp_unpack_weighttest` | `0x0800f858` | **26 bytes** | ✓ | Weight measurement test |
| 0x020a | 0x020b | `wpp_unpack_dac` | `0x0800f794` | **8 bytes** | ✓ | DAC output; echoes back 8-byte payload |
| 0x020b | 0x020a | `wpp_unpack_ip` | — | — | — | IP address response |
| 0x020c | 0x020d | `wpp_unpack_wl` | `0x0800fb60` | **7+L bytes** | ✓ | Triggers BCM4315 DHD WiFi init (see below) |
| 0x020e | 0x0210 | `wpp_unpack_spiflash` | `0x0800f4e8` | 2 bytes | ✓ | BCM4315 SPI flash; returns 0xFF when not init'd |
| 0x020f | 0x0211 | `wpp_unpack_rtc` | `0x0800f748` | **6 bytes** | ✓ | RTC read/set |
| 0x0210 | 0x0213 | `wpp_unpack_dump` | `0x0800f6fc` | 9 bytes | ✓ | MCU memory read (see below) |

### Wire size corrections (firmware-confirmed)

All sizes confirmed by decompiling unpack handlers; wrong sizes trigger assertion crash.

| CMD | Inner TAG | Correct wire size | Wire layout |
|-----|-----------|-------------------|-------------|
| 0x0209 | 0x0209 | **26 bytes** | `[type(1B), 6×uint32_BE, flags(1B)]` |
| 0x020a | 0x020b | **8 bytes** | `[b0(1B), b1(1B), pad(1B), uint32_BE, b7(1B)]` |
| 0x020f | 0x0211 | **6 bytes** | `[flags(1B), flags(1B), timestamp(4B BE)]` |
| 0x020c | 0x020d | **7+L bytes** | `[b0(1B), uint32_BE, b8(1B), L(1B), data(L bytes)]` |

### Compound commands (iterate inner TLV fields)

**CMD 0x0205** — Weight calibration compound:

| Inner TAG | WPP Handler | Handler addr | Notes |
|-----------|-------------|--------------|-------|
| 0x0205 | `wpp_unpack_perso` | `0x0800fbc0` | Device personalization / identity write |
| 0x020c | `wpp_unpack_weight_cal` | `0x0800f960` | Write weight calibration to persistent store |
| 0x0212 | `wpp_unpack_weight_verif` | `0x0800f9c8` | Weight calibration verification |

**CMD 0x020d** — Z-meter calibration compound:

Requires inner TAG 0x020e (zmeter) **and** either:
- inner TAG 0x020f (zmeter_cal) also present, **or**
- byte at struct_offset+1 of zmeter payload is non-zero

Sending zmeter-only with all-zeros is silently rejected (no response, no mode change).

| Inner TAG | WPP Handler | Handler addr | Wire size | Notes |
|-----------|-------------|--------------|-----------|-------|
| 0x020e | `wpp_unpack_zmeter` | `0x0800fa88` | **14 bytes** | `[b0(1B), b1(1B), uint32_BE×3]`; b1≠0 enables zmeter-only mode |
| 0x020f | `wpp_unpack_zmeter_cal` | `0x0800fa20` | **44 bytes** | `[b0(1B), uint32_BE, {count=3,3×uint32_BE}×3]` — count bytes MUST be 3 |

---

## Command Detail

### 0x020c — Wireless Layer (`wl`)

Sends a command to the BCM4315 Dongle Host Driver (DHD). Triggers full WiFi stack init:

```
[DHD] Init Network Interface
[DHD_RTOS] Opening flash
[DHD_RTOS] Flash opened
[DHD_RTOS] Firmware version: 0000004d
[DHD_RTOS] Firmware size: 254288
```

BCM4315 WiFi firmware is 254,288 bytes (0x3E150) stored on the onboard SPI flash. Firmware version 0x4d.
Note: The `wl` command may trigger a brief USB re-enumeration if b0=0x01 is set.

### 0x0210 — Memory Dump (`dump`)

Reads arbitrary MCU memory over USB HID.

- **Wire payload:** `[access_type(1B), addr(4B BE), length(4B BE)]` = 9 bytes
- **access_type=0:** returns `TAG=0x0100 len=0` (error)
- **access_type=1:** reads memory — works for both flash (0x08000000) and SRAM (0x20000000) ✓
- **access_type=2:** returns `TAG=0x0100 len=0` (error)

**Response format:**
- Multiple `TAG=0x0207` packets: each 65 bytes = `[count(1B)=0x40][64B memory content]`
- Final `TAG=0x0100 len=0` = end of transfer
- Responses are fragmented across multiple HID packets (continuation fragments have data[3]≠0x01)

**Confirmed reads:**
- `0x08000000` (flash): first 8 bytes = `00 00 01 20 09 02 00 08` ← MSP=0x20010000, Reset=0x08000209 ✓
- `0x20000000` (SRAM): returns live SRAM contents

---

## Triggering Commands

All commands use the standard WPP TLV packet format. The device must be in mode 3 (default power-on state when connected via USB).

### Example — memory dump

```
[0x01, length, 0x01, tag_hi=0x02, tag_lo=0x10, len_lo, len_hi, 0x01, addr(4B BE), len(4B BE)]
```

### High-value targets

| CMD | Inner TAG | Why |
|-----|-----------|-----|
| 0x0210 | 0x0213 | **Memory dump** — access_type=1 reads arbitrary flash/SRAM; confirmed working |
| 0x020e | 0x0210 | **SPI flash** — 2-byte payload controls BCM4315 SPI flash; returns 0xFF when WiFi not init'd; send wl first to init |
| 0x020c | 0x020d | **Wireless layer** — triggers BCM4315 DHD init; further wl commands can interact with WiFi stack |
| 0x0205/0x0205 | 0x0205 | **Perso** — overwrites device identity/keys in persistent store (DBLIB key 1) |
| 0x0205/0x020c | 0x020c | **Weight calibration** — overwrites factory calibration constants; corrupts measurement data |
