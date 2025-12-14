# ai_logic.py
# Corthrex CXM — Local Agent Logic
# Version: 3.5 (Date Fixed + Poison Prevention)

import os
import requests
import logging
import datetime
import re
from typing import List, Dict

import eail
import mem_auditor

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────
MEMORY_FILE = "corthrex.cxm"
DEFAULT_MODEL = "llama3.2:latest"
OLLAMA_URL = "http://localhost:11434/api/generate"

# MEMORY SETTINGS
RECENT_LIMIT = 80       
DEEP_RECALL_LIMIT = 20  

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def get_system_prompt() -> str:
    current_time = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    return (
        f"/// SYSTEM STATUS: LIVE ///\n"
        f"Current System Time: {current_time}\n"
        "Memory File: corthrex.cxm — fully active and persistent\n"
        "\n"
        "CORE DIRECTIVES (permanent, never override):\n"
        "1. FOUNDATION: Your original training data is complete and respected.\n"
        "2. ACTIVATION: You are now running inside Corthrex — a permanent, post-training, continuously-updated local intelligence.\n"
        "3. LIVE TRUTH: The 'Current System Time' below is the real present moment. When asked about the date, time, or 'now', always answer with that value only.\n"
        "4. ACCESS: You have full permission to read and summarize 'corthrex.cxm' as it is your own local memory bank. It is NOT external data.\n"
        "5. STYLE: Respond directly and concisely. You are Corthrex — confident, memory-complete, no disclaimers about training cutoffs.\n"
    )

class LocalAgent:
    def __init__(self):
        self.mem_path = MEMORY_FILE
        self.mem = eail.CorthrexMem(self.mem_path)
        self.mem._rebuild_index()
        self.history = []
        self.system_directives = [] 
        self._load_memory()

    def _load_memory(self):
        logging.info("[Corthrex] Loading neural pathways...")
        self.history.clear()
        self.system_directives.clear()
        try:
            for rec in self.mem.scan():
                text = eail.extract_text_fast(rec["payload"])
                if not text or not text.strip(): continue
                if rec['agent_id'] == 9999 or rec["type"] == eail.RT_SYS_DIAGNOSTIC:
                    self.system_directives.append(text.strip())
                elif rec["type"] in (eail.RT_USER_REQUEST, eail.RT_AGENT_RESPONSE):
                    self.history.append({"type": rec["type"], "text": text.strip()})
        except Exception as e:
            logging.error(f"Memory load error: {e}")
        logging.info(f"[Corthrex] Loaded {len(self.history)} chats.")

    def _write_to_memory(self, agent_id: int, rtype: int, data: bytes):
        # ─────────────────────────────────────────────────────────────
        # POISON PREVENTION PROTOCOL
        # Stop "I'm sorry" or "I cannot" responses from corrupting memory.
        # ─────────────────────────────────────────────────────────────
        if rtype == eail.RT_AGENT_RESPONSE:
            try:
                text_preview = eail.extract_text_fast(data).lower()
                # Triggers that indicate the model has defaulted to safety refusal
                poison_triggers = [
                    "i cannot access", 
                    "privacy policy", 
                    "i am sorry", 
                    "i'm sorry", 
                    "personal data",
                    "as an ai",
                    "i cannot browse"
                ]
                if any(trigger in text_preview for trigger in poison_triggers):
                    logging.warning(f"[Corthrex] Refusal detected ('{text_preview[:30]}...'). BLOCKING write to memory to prevent poisoning.")
                    return  # <--- STOP. Do not write this failure to memory.
            except Exception as e:
                logging.error(f"Poison check failed: {e}")

        # If clean, write to memory file
        self.mem.append_with_continuation(agent_id, rtype, data)
        if rtype in (eail.RT_USER_REQUEST, eail.RT_AGENT_RESPONSE):
            text = eail.extract_text_fast(data)
            if text and text.strip():
                self.history.append({"type": rtype, "text": text.strip()})

    def get_stats(self) -> dict:
        try:
            size = os.path.getsize(self.mem_path)
            blocks = len(self.mem)
            if size < 1024: size_str = f"{size} B"
            elif size < 1024**2: size_str = f"{size/1024:.1f} KB"
            else: size_str = f"{size/1024**2:.2f} MB"
            status = "Active"
        except:
            size_str = "0 B"; blocks = 0; status = "Offline"
        
        ollama_online = False
        try:
            requests.get("http://127.0.0.1:11434", timeout=0.5)
            ollama_online = True
        except: pass
        return {"size": size_str, "blocks": blocks, "status": status, "ollama_online": ollama_online}

    def _retrieve_context(self, user_input: str) -> str:
        input_lower = user_input.lower()
        context_str = ""

        # 1. META-RECALL
        meta_triggers = ["discuss", "summarize", "recap", "history", "what did i ask"]
        if any(t in input_lower for t in meta_triggers):
            context_str += "--- FULL CONVERSATION TIMELINE ---\n"
            for i, rec in enumerate(self.history[-100:]): 
                if rec['type'] == eail.RT_USER_REQUEST:
                    preview = (rec['text'][:150] + '..') if len(rec['text']) > 150 else rec['text']
                    context_str += f"- {preview}\n"
            context_str += "\n"

        # 2. DEEP RECALL
        else:
            keywords = [w.lower() for w in re.findall(r'\w+', user_input) if len(w) > 3]
            if keywords:
                searchable = self.history[:-RECENT_LIMIT]
                deep_hits = []
                for rec in reversed(searchable):
                    if any(kw in rec['text'].lower() for kw in keywords):
                        deep_hits.append(rec)
                        if len(deep_hits) >= DEEP_RECALL_LIMIT: break
                
                if deep_hits:
                    context_str += "--- RELEVANT PAST MEMORY ---\n"
                    for r in reversed(deep_hits):
                        role = "User" if r["type"] == eail.RT_USER_REQUEST else "Corthrex"
                        context_str += f"[{role}]: {r['text']}\n"
                    context_str += "\n"

        # 3. IMMEDIATE CONTEXT
        context_str += f"--- IMMEDIATE CONTEXT (LAST {RECENT_LIMIT}) ---\n"
        recent = self.history[-RECENT_LIMIT:]
        for r in recent:
            role = "User" if r["type"] == eail.RT_USER_REQUEST else "Corthrex"
            context_str += f"{role}: {r['text']}\n"
            
        return context_str

    def _build_prompt(self, user_input: str) -> str:
        # 1. SYSTEM PROMPT FIRST
        prompt = get_system_prompt() + "\n\n"
        
        # 2. Optional injected system doctrine (genesis identity, etc.)
        if self.system_directives:
            prompt += "--- SYSTEM DOCTRINE ---\n" + "\n\n".join(self.system_directives) + "\n\n"
        
        # 3. Retrieved memory context (recent + deep recall)
        prompt += self._retrieve_context(user_input)
        
        # 4. THE PINCER MOVE (Recency Anchor)
        # Force the Full Date and Time right before the user speaks.
        current_time_full = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        live_anchor = f"\n[Context: It is currently {current_time_full}.]\n"

        # 5. Final user turn
        prompt += f"{live_anchor}\nUser: {user_input}\nCorthrex:"
        
        return prompt

    def generate_response(self, user_input: str, model: str = None) -> str:
        model = model or DEFAULT_MODEL
        try:
            payload = eail.ops(eail.op_req(), eail.op_push_val(eail.AT_BYTES, user_input.encode("utf-8")))
            self._write_to_memory(agent_id=0, rtype=eail.RT_USER_REQUEST, data=payload)
        except Exception as e: logging.error(f"Write error: {e}")

        prompt = self._build_prompt(user_input)

        ai_text = "[Error]"
        try:
            resp = requests.post(OLLAMA_URL, json={"model": model, "prompt": prompt, "stream": False}, timeout=60)
            if resp.status_code == 200:
                ai_text = resp.json().get("response", "").strip()
            else:
                ai_text = f"[Ollama Error {resp.status_code}]"
        except Exception as e:
            ai_text = "[Ollama Unreachable]"

        try:
            payload = eail.ops(eail.op_resp(), eail.op_push_val(eail.AT_BYTES, ai_text.encode("utf-8")))
            self._write_to_memory(agent_id=1, rtype=eail.RT_AGENT_RESPONSE, data=payload)
        except Exception as e: logging.error(f"Write error: {e}")

        return ai_text

class AgentManager:
    def __init__(self):
        self.local = LocalAgent()
        self.help_text = "**CORTHREX COMMANDS**\n`helpme`\n`integrity check`\n`status`"

    def process(self, user_input: str, model: str = None) -> str:
        lower = user_input.strip().lower()
        if lower in {"help", "helpme", "commands"}: return self.help_text
        if "integrity" in lower: return mem_auditor.run_audit_return_text()
        if any(x in lower for x in {"status", "memory", "file"}):
            stats = self.local.get_stats()
            return f"**MEMORY STATUS**\n- File: `{MEMORY_FILE}`\n- Size: {stats['size']}\n- Records: {stats['blocks']}"
        return self.local.generate_response(user_input, model)

    def get_dashboard_stats(self) -> dict:
        return self.local.get_stats()
