# Corthrex CXM — Permanent Local Memory That Actually Works

One 58 KB file. Zero dependencies. Remembers forever.

Close your laptop for a week → come back → it still knows your name, eye color, everything.

No SQLite • No vector DB • No background server • No cloud

Live demo (November 29, 2025):  
https://youtu.be/rxRsgQL1AuQ

### 30-second start (Windows)

1. Install Ollama → https://ollama.com  
   `ollama pull llama3.2:latest`

2. Double-click **FULL_START.bat**

   → **First run**:  
     • Creates `corthrex.cxm` if it doesn’t exist  
     • Pauses and asks “Run genesis identity injection? (Y/N)”  
     • Type **Y** → your core identity is permanently injected at the top of memory

   → **Every run after**:  
     • Instantly loads your full memory and opens http://127.0.0.1:5000

**Want to update your identity later?**  
Just run once from command prompt:  
`python genesis_update.py`  
(You can do this anytime — new info is added to the very top of the file)

That’s it.  

One file. One double-click. Works forever.

Welcome to permanent local memory.