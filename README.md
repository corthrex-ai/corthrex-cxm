# Corthrex CXM — Permanent local AI memory that survives full shutdowns

**One file. Zero dependencies. Actually works.**

- Current real-world size (after ~300 messages): **73 KB**  
- Average message pair (user + assistant): **~250 bytes**  
- Measured cold storage efficiency: **~4 messages per KB**

**Real capacity (measured, not theoretical):**

| Storage          | Approx. messages | Years of daily heavy use* |
|------------------|------------------|---------------------------|
| 64 GB thumb drive| 268 million      | ~300 years                |
| 1 TB SSD         | 4.2 billion      | ~5,000 years              |
| 8 TB HDD         | 33.6 billion     | ~40,000 years             |

\* ~2,400 messages per day (very heavy user) — measured on real hardware.

No other open-source local memory system even comes close.  
Everything else uses SQLite + vectors + background servers that forget on restart.  
This one doesn’t.

KEEP IN MIND - The UI and Memory Logic of this project is ongoing project - I have been working on the LOGIC 
the main thing is the corthrex.cxm born from subpar storage file systems not made for AI memory.

→ Double-click FULL_START.bat → talk → kill power → reboot → it still remembers. Forever.

Live demo (Nov 29, 2025): https://youtu.be/rxRsgQL1AuQ
Live demo (November 29, 2025): https://youtu.be/rxRsgQL1AuQ  

## 30-second start (Windows)

1. Install Ollama → https://ollama.com  
   `ollama pull (at leaset 1 chat model)`

2. Double-click `FULL_START.bat`  
   → First run:  
   • Creates `corthrex.cxm` if missing  
   • Asks “Run genesis identity injection? (Y/N)” → type **Y**  
   • Injects permanent core identity (via `genesis_update.py`)  
   → Every run after: instantly loads full history and opens http://127.0.0.1:5000

## What’s new as of November 30, 2025 (v3.3)

- Real system clock is now injected on every turn → AI always knows the correct date/time  
- No more unprompted recaps — only summarizes when you explicitly say “catch me up”, “summarize”, etc.  
- Memory context is strictly ordered so old hallucinations can’t win  
- Genesis identity block is now baked in from first run (and can be re-run anytime)

The magic is still the same single `corthrex.cxm` file and the 256-byte EAIL protocol.

## Want to update or add to your identity later?

```bash
python genesis_update.py
Runs in 2 seconds, appends new directives to the very top of memory.
That’s it.
One file. One double-click. Works forever.
More improvements, tools, and model support coming — this project is actively developed.
Welcome to permanent local memory.