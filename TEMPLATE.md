# [Device Name] Teardown Notes

> **Usage:** Copy this file into a new device subdirectory to start a teardown: `cp TEMPLATE.md <device_name>/NOTES.md`

## Metadata

| Field | Value |
|---|---|
| Device | [e.g. Withings Body+ Smart Scale] |
| Model / Part Number | [e.g. WBS05] |
| Firmware Version | [e.g. unknown / dumped] |
| Started | [YYYY-MM-DD] |

---

## Worklog

**2026-03-28**
- Physical hardware teardown

## Status & Next Steps

**Current Phase:**
- [ ] Recon
- [ ] Active
- [ ] Done

**Next Steps:**
- [ ] ...
- [ ] ...

---

## Physical Access

### Disassembly

**Tools needed:** [e.g. T5 Torx, plastic pry tool]

**Steps:**
1. ...
2. ...
3. ...

**Notes / gotchas:** [e.g. ribbon cable attached to lid — lift carefully]

**Reassembly notes:** [anything non-obvious about putting it back together]

**Photos:**
- ![Board overview](images/board_top.jpg)
- [add more inline as needed]

---

## Component Inventory

| Component | Function | Datasheet |
|---|---|---|
| [e.g. STM32F103VD] | [e.g. Primary MCU] | [link or filename] |

---

## Debug Interfaces

### [Interface Type — e.g. UART]

- **Location on board:** [e.g. J3 header, top-left near MCU]
- **Pinout:** [e.g. Pin 1: VCC, Pin 2: TX, Pin 3: RX, Pin 4: GND]
- **Speed / settings:** [e.g. 115200 8N1]
- **Findings:** [what you got — boot log, shell, nothing, etc.]
- **Files:** [inline links to captures/logs, e.g. [boot.log](outputs/boot.log)]

### [Interface Type — e.g. SWD / JTAG]

- **Location on board:**
- **Pinout:**
- **Speed / settings:**
- **Findings:**
- **Files:**

---

## Firmware

- **Extraction method:** [e.g. SWD memory read via OpenOCD, UART xmodem, chip-off]
- **Tool / command:** [e.g. `openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "program dump.bin 0x08000000 0x80000 verify exit"`]
- **Memory map:**

| Region | Start | End | Notes |
|---|---|---|---|
| [e.g. Flash Bank 0] | [e.g. 0x08000000] | [e.g. 0x0807FFFF] | |

- **Dump files:** [e.g. [stm32_bank_0_dump.bin](outputs/stm32_bank_0_dump.bin)]
- **Strings / symbols of interest:**
  - `[e.g. "AT+CWJAP" — WiFi credentials sent in plaintext]`
  - `[e.g. "/etc/passwd" — hints at Linux userspace]`

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

_Free-form. Dead ends, half-formed observations, questions to revisit._

_[your notes here]_
