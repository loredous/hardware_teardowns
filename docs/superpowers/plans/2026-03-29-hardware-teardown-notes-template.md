# Hardware Teardown Notes Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `TEMPLATE.md` at the repo root — a reusable Markdown notes template for hardware teardown and hacking projects.

**Architecture:** Single Markdown file with 9 sections in linear order, filled with placeholder text and inline usage guidance. No code, no tooling — just the template itself.

**Tech Stack:** Markdown

---

### Task 1: Create TEMPLATE.md

**Files:**
- Create: `TEMPLATE.md`

- [ ] **Step 1: Create the file**

Create `/home/jbanker/code/hardware_teardowns/TEMPLATE.md` with the following content:

```markdown
# [Device Name] Teardown Notes

> **Usage:** Copy this file into a new device subdirectory to start a teardown: `cp TEMPLATE.md <device_name>/NOTES.md`

## Metadata

| Field | Value |
|---|---|
| Device | [e.g. Withings Body+ Smart Scale] |
| Model / Part Number | [e.g. WBS05] |
| Firmware Version | [e.g. unknown / dumped] |
| Acquired | [YYYY-MM-DD] |
| Prior Research | [links to relevant prior work, or "none found"] |

---

## Status & Next Steps

**Current Phase:** `[ ] Recon  [ ] Active  [ ] Done`

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
| | | |

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

-
```

- [ ] **Step 2: Verify the file renders correctly**

Open `TEMPLATE.md` in a Markdown viewer and visually confirm:
- All 9 sections are present in order
- Tables render correctly (Metadata, Component Inventory, Memory Map)
- Checkboxes render as checkboxes
- No broken Markdown syntax

- [ ] **Step 3: Commit**

```bash
git add TEMPLATE.md
git commit -m "add hardware teardown notes template"
```

---

### Task 2: Update spec status

**Files:**
- Modify: `docs/superpowers/specs/2026-03-29-hardware-teardown-notes-template-design.md`

- [ ] **Step 1: Mark spec as Approved**

Change line 4 from `**Status:** Draft` to `**Status:** Approved`.

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-03-29-hardware-teardown-notes-template-design.md
git commit -m "mark hardware teardown template spec as approved"
```
