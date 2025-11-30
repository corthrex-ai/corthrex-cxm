# mem_doctor.py
# Corthrex Memory Cleaner & Safety System (Turbo Mode)
# Usage: python mem_doctor.py

import os
import shutil
import time
import requests
import sys

# Ensure eail is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import eail
except ImportError:
    print("[FATAL] eail.py not found.")
    sys.exit(1)

# --- Configuration ---
MEMORY_FILE = "corthrex.cxm"
MODEL_NAME = "phi4-q5:latest"
OLLAMA_URL = "http://localhost:11434/api/generate"
SAFE_DELETE_THRESHOLD = 0.25 

class MemDoctor:
    def __init__(self, mem_path=MEMORY_FILE):
        self.mem_path = mem_path
        self.quarantine_path = 'corthrex.quarantine'
        
        # Hard filters - Instant Trash
        self.trash_triggers = [
            "as an ai language model", "i cannot browse", "i do not have access", 
            "cutoff of 2023", "openai", "cannot fulfill", "sorry, i cannot"
        ]

    def _is_garbage_fast(self, text):
        """
        Returns: 'TRASH', 'KEEP', or 'CHECK' (ask LLM)
        """
        if not text or len(text) < 3: return 'TRASH'
        text_lower = text.lower()

        # 1. CPU Check: Instant Trash
        if any(ref in text_lower for ref in self.trash_triggers):
            return 'TRASH'

        # 2. CPU Check: Instant Keep (Long + Clean)
        # If it's over 100 chars and passed the trash check, it's likely valid memory.
        if len(text) > 100:
            return 'KEEP'

        # 3. Ambiguous: Ask LLM (Short messages that might be junk)
        return 'CHECK'

    def _ask_llm_is_garbage(self, text):
        system_prompt = (
            "Analyze this memory log.\n"
            "Reply 'TRASH' if it contains AI refusals, glitches, or gibberish.\n"
            "Reply 'KEEP' if it is a valid conversation or fact.\n"
            "Reply ONLY with 'TRASH' or 'KEEP'."
        )
        try:
            payload = {
                "model": MODEL_NAME,
                "prompt": f"{system_prompt}\n\nLOG:\n{text}",
                "stream": False
            }
            # Fast timeout
            response = requests.post(OLLAMA_URL, json=payload, timeout=2)
            result = response.json().get('response', '').strip().upper()
            return "TRASH" in result
        except:
            return False 

    def _extract_text(self, mem, offset):
        try:
            payload = mem.reassemble_payload(offset)
            if not payload: return ""
            return eail.extract_text_fast(payload)
        except: return ""

    def start_cleaning_cycle(self):
        print("\n" + "="*60)
        print(" CORTHREX MEMORY DOCTOR (TURBO)")
        print("="*60)
        
        if not os.path.exists(self.mem_path):
            print(f"[ERROR] Target file '{self.mem_path}' not found.")
            return

        # 1. SAFETY BACKUP
        backup_path = f"{self.mem_path}.{int(time.time())}.bak"
        try:
            shutil.copy2(self.mem_path, backup_path)
            print(f"[SAFETY] Backup created: {os.path.basename(backup_path)}")
        except Exception as e:
            print(f"[FATAL] Could not create backup: {e}")
            return

        mem = eail.CorthrexMem(self.mem_path)
        all_records = list(mem.scan_fast())
        total = len(all_records)
        
        print(f"[INFO] Scanning {total} neural blocks...")
        
        keep = []
        trash = []
        llm_checks = 0

        # Scan loop
        start_time = time.time()
        for i, rec in enumerate(all_records):
            if i % 500 == 0: 
                print(f"\r -> Analyzed {i}/{total} (LLM Calls: {llm_checks})...", end="")

            # Always keep system messages
            if rec['agent_id'] == 9999 or rec['type'] == eail.RT_SYS_DIAGNOSTIC:
                keep.append(rec); continue

            # Skip continuations
            if rec['type'] == eail.RT_CONTINUATION: continue

            text = self._extract_text(mem, rec['offset'])
            
            # FAST CHECK
            verdict = self._is_garbage_fast(text)
            
            if verdict == 'TRASH':
                trash.append(rec)
            elif verdict == 'KEEP':
                keep.append(rec)
            else:
                # Only use GPU for the tricky ones
                llm_checks += 1
                if self._ask_llm_is_garbage(text):
                    trash.append(rec)
                else:
                    keep.append(rec)

        duration = time.time() - start_time
        print(f"\r -> Analyzed {total}/{total}. Done in {duration:.2f}s.      ")
        
        trash_count = len(trash)
        
        print(f"\n[RESULTS]")
        print(f" - Healthy Records: {len(keep)}")
        print(f" - Corrupt/Trash:   {trash_count}")
        print(f" - LLM Validations: {llm_checks} (Optimized)")

        if trash_count == 0:
            print("\n[OK] System is clean.")
            return

        # Safety Valve
        ratio = trash_count / total
        if ratio > SAFE_DELETE_THRESHOLD:
            print(f"\n[🚨 ABORT] Safety Triggered! Attempted to delete {ratio*100:.1f}% of memory.")
            return

        print("\n[ACTION] performing surgery...")
        
        # Rewrite Logic
        temp_path = self.mem_path + ".clean"
        try:
            with open(temp_path, 'wb') as f_out:
                f_out.write(eail.HEADER_STRUCT.pack(eail.FILE_TAG, 1, eail.BLOCK_SIZE, 0))
                with open(self.mem_path, 'rb') as f_in:
                    for rec in keep:
                        f_in.seek(rec['offset'])
                        data = f_in.read(eail.BLOCK_SIZE)
                        f_out.write(data)
            
            os.replace(temp_path, self.mem_path)
            print(f"[SUCCESS] Removed {trash_count} blocks. Optimization complete.")
            
        except Exception as e:
            print(f"[ERROR] Rebuild failed: {e}")
            if os.path.exists(temp_path): os.remove(temp_path)

if __name__ == "__main__":
    doc = MemDoctor()
    doc.start_cleaning_cycle()