# [Device Name] Teardown Notes

> **Usage:** Copy this file into a new device subdirectory to start a teardown: `cp TEMPLATE.md <device_name>/NOTES.md`

## Metadata

| Field | Value |
|---|---|
| Device | WiThings Connected Scale |
| Model / Part Number | WBS01 |
| Firmware Version | Unknown |
| Started | 2026-03-28 |

---
## Worklog

**2026-03-28**
- Physical hardware teardown
- UART Access
**2026-03-29**
- JTAG access
- Firmware dumped as `stm32_bank_0_dump.bin`

## Status & Next Steps

**Current Phase:**
- [X] Recon
- [ ] Active
- [ ] Done

**Next Steps:**
- [ ] Decompile firmware
- [ ] Enumerate USB HID commands
- [ ] Inspect Wifi reporting protocol

---

## Physical Access

### Disassembly

**Tools needed:**
- Sturdy shim
- Pry tool
- Phillips screwdriver
- Pliers

**Steps:**
1. Use pry tool and shim to detatch foam tape ring at each corner (Between glass and bottom case)
2. Lift glass plate
3. Unscrew 2xPH2 screws holding screen in place
4. Unscrew 2xPH2 screws holding board in place
5. Remove battery terminals to allow board to be removed

**Notes / gotchas:** 
Glass to case fit is tight to begin with. Became much easier after cutting first foam tape ring

**Reassembly notes:**
Will need to replace foam tape

**Photos:**
- ![Board Overview](images/board_overview.jpg)

---

## Component Inventory

| Component | Function | Datasheet |
|---|---|---|
| STM32F103VDT6 | Primary MCU | [Datasheet](datasheets/stm32f103vd.pdf) |
| BCM4315KFFBG | Wifi + Bluetooth Controller | No Datasheet Found |
| 74HC4052D | Analog Multiplexer | [Datasheet](datasheets/74HC_HCT4052.pdf) |
| TS974I | OpAmp | [Datasheet](datasheets/ts971.pdf) 



---

## Debug Interfaces

### UART

- **Location on board:** JP2 Header (20 pin)
- **Pinout:** 
  1. Ground
  2. Device RX
  3. Device TX
  4. VCC
- **Speed / settings:** 115200 8N1
- **Findings:**
  - Only outputs basic debug logging

### JTAG

- **Location on board:** J16 Header (20 pin)
- **Pinout:** Standard ARM JTAG - VCC at pin 1, Pins closer to edge are live, others are ground
- **Speed / settings:** Standard ARM JTAG
- **Findings:**
  - Memory dump allowed, no read protection
- **Files:**
  - [Memory Bank 0 Dump](outputs/stm32_bank_0_dump.bin)

---

## Firmware

- **Extraction method:** Read via JTAG
- **Tool / command:** `openocd -f interface/ch347.cfg -f target/stm32f1x.cfg"` | `flash read_bank 0 stm32_bank_0_dump.bin`
- **Memory map:**

See STM32 

- **Build date:** lundi 1 août 2011, 18:25:06 (UTC+0200)
- **Dump files:** [stm32_bank_0_dump.bin](outputs/stm32_bank_0_dump.bin)
- **Embedded libraries:** lwIP TCP/IP stack + libcurl
- **Strings / symbols of interest:**
  - `Start wifi test mode` Indicates test modes exist
  - `http://%s/%s` Potential indicator that all data is non-encrypted
  - `cgi-bin/measure` Path used for web app?
  - Query Params - Good indicator of data format
    - `action=store&sessionid=%s&macaddress=%s`
    - `&userid=%d`
    - `&meastime=%u`
    - `&devtype=%d`
    - `&attribstatus=%d&measures=`
  - `/home/gfaussard/work/tags/bodyscale-imped/**` Several paths from original dev system perhaps?
  - Calibration screen contents hint at calibration mode
    - `PRESS BUTTON`
    - `FOR Z CALIB`
    - `OK PLS WAIT`
  - Hardcoded network params
    - `scalews.withings.net` — cloud backend endpoint
    - `208.67.222.222` — hardcoded OpenDNS server
    - `00:24:e4:03:f3:22` — hardcoded Broadcom WiFi MAC
    - `2ce84b84e6833d5c` — hardcoded 32-hex device identifier
---

## Wireless

### [Protocol — e.g. Bluetooth LE]

- **Chip:** [e.g. EMW3239]
- **Observations:** [what traffic / behavior was seen]
- **Tools used:** [e.g. Wireshark + nRF Sniffer, bettercap]
- **Files:** [inline links to captures]
- **Findings:** [anything actionable]

### [Protocol — e.g. WiFi 802.11]

- **Chip:**
- **Observations:**
- **Tools used:**
- **Files:**
- **Findings:**

---

## Findings

_Consolidated actionable findings. What was found and what it enables — no severity ratings or CVE format needed._

- **[Finding title]:** [description + what it enables, e.g. "Unauthenticated UART shell: full root shell accessible without disassembly via J3 header"]

---

## Notes / Scratch

- Mini-USB port in battery area is used for intial setup
  - Presents as USB HID device
  - https://github.com/zshannon/wbs01-web
  - Possible to fuzz command structure?

