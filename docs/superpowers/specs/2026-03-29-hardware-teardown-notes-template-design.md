# Hardware Teardown Notes Template — Design Spec

**Date:** 2026-03-29
**Status:** Approved

## Purpose

A reusable Markdown template for documenting hardware teardown and hacking projects. Covers the full arc from initial recon through active exploitation.

## Goals

- Capture both reconnaissance and exploitation notes in one document
- Minimal component inventory (chip ID, function, datasheet link)
- Physical access / disassembly notes
- Technique-specific sections: debug interfaces, firmware, wireless
- Inline image/file references (no separate gallery)
- Status and next steps tracking at the top

## Non-Goals

- Deep component documentation (register maps, CVEs, etc.)
- Side-channel / fault injection
- Cloud/API / mobile app analysis

## Template Structure

Linear, top-to-bottom document. Sections in order:

1. **Metadata** — device name, model, firmware version, acquisition date, prior research links
2. **Status & Next Steps** — current phase, bullet list of next actions
3. **Physical Access** — disassembly steps, tools, screw/clip locations, reassembly notes, inline photo references
4. **Component Inventory** — markdown table: Component | Function | Datasheet
5. **Debug Interfaces** — per interface: type, board location, pinout, speed, findings
6. **Firmware** — extraction method, memory map, dump file references, notable strings/symbols
7. **Wireless** — per radio: protocol, chip, observations, tools, findings
8. **Findings & Vulnerabilities** — consolidated actionable findings across all sections

## Output

A single file: `TEMPLATE.md` at the root of the `hardware_teardowns` repo.
