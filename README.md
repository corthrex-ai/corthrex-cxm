# Corthrex.cxm — Ultra-Dense Append-Only File System (256-byte EAIL blocks)

**One file. Zero dependencies. Designed to survive decades.**

Current real test (Dec 1, 2025)  
- 324 records → **81.1 KB**  
- ~250 bytes per record  
- ~4 records per KB  
- Write 2,489 ops/sec — Read 22,730 ops/sec → **HYPER-EFFICIENT**

**Measured capacity (actual math, not marketing)**

| Storage            | Approx. records | Years at 2,400 records/day |
|--------------------|------------------|----------------------------|
| 64 GB thumb drive  | ~268 million     | ~300 years                 |
| 1 TB SSD           | ~4.2 billion     | ~5,000 years               |
| 8 TB HDD           | ~33.6 billion    | ~40,000 years              |

No schema. No indexes. No background server. Survives full power loss.

## The Invention Is the File Format

Everything else in this repo (Flask UI, Ollama demo) is just one possible front-end.  
The real thing is the `corthrex.cxm` file itself — a new way to store sequential data streams with almost zero overhead.

## Potential Use Cases (all unproven — just math + imagination)

- **AI Memory & Chat History**  
  Enterprise AI agents currently waste billions of dollars in storage and power on bloated vector DBs and cloud sync. 
  A single 1 TB drive using this format could hold ~5,000 years of chat history for thousands of concurrent users — 
  all local, all offline, zero recurring cost. (Demo in this repo is one tiny proof-of-concept.)

- Banking & financial ledgers (immutable append-only trail)  
- Air-traffic control event logs (survives blackouts, loads in milliseconds)  
- Robotics lifelong learning memory (swap a microSD, the robot keeps its experience)  
- IoT sensor streams (10+ years of 1 Hz data in <150 MB)  
- Personal life-logging / quantified-self archives  
- Compliance & audit trails (tamper-evident by design)  
- Embedded devices with no storage budget  
- Offline medical or scientific data collection  
- Game save systems that never bloat

Any domain that writes data in order and rarely deletes it is a candidate.

## Quick Demo (AI Memory)

The included Flask + Ollama demo shows one possible use: local AI that remembers everything forever.  
Double-click `FULL_START.bat` → talk → kill power → reboot → it still knows you.

Live demo (Nov 29, 2025): https://youtu.be/rxRsgQL1AuQ

## 30-Second Start (Windows)

1. Install Ollama → https://ollama.com  
   `ollama pull llama3.2:latest`

2. Double-click `FULL_START.bat`  
   → First run asks to inject genesis block (type **Y**)  
   → Every run after loads instantly

## Want to experiment with the file format?

```bash
python genesis_update.py   # append anything you want to the top of the file