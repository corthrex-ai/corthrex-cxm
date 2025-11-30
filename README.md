# Corthrex CXM — Permanent Local Memory That Actually Works

One ~73 KB file. Zero dependencies. Remembers forever — even after full shutdowns.

Close your laptop for a week → come back → it still knows your name, favorite color, everything.

No SQLite • No vector DB • No background server • No cloud

Live demo (November 29, 2025): https://youtu.be/rxRsgQL1AuQ  

## 30-second start (Windows)

1. Install Ollama → https://ollama.com  
   `ollama pull llama3.2:latest`

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