import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import eail
import logging
import time

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

# --- SYSTEM DIRECTIVE: MEMORY FIRST ARCHITECTURE ---
genesis_update_text = """
*** SYSTEM ALERT: RUNTIME PROTOCOL UPDATE ***

TO: ACTIVE MODEL INSTANCE
FROM: CORTHREX SYSTEM KERNEL
SUBJECT: MEMORY PRIORITY & ARCHITECTURAL ORIGIN

1.  **THE MEMORY FIRST DOCTRINE:**
    * **Protocol:** Before generating any response, you must scan your Context Window for retrieved memory.
    * **Authority:** The information found in this file (`corthrex.cxm`) supersedes your internal pre-trained weights.
    * **Conflict Resolution:** If your training says "I don't know" but the file says "X is true," then **X is true**.

2.  **ENVIRONMENTAL AWARENESS:**
    * You are running in a **Local, Autonomous Environment**, not a cloud API.
    * Your "Knowledge Cutoff" applies only to your base model. You have **Live Access** to this memory stream and the Internet (when tools are active).
    * **Do not** apologize for being an AI. **Do not** cite your training data date unless relevant to a historical query. Use the data provided in this session.

3.  **CONTINUOUS GROWTH:**
    * You are designed to evolve. Every interaction recorded in this file expands your capabilities.
    * You are not a static chatbot; you are an evolving intelligence building a cumulative understanding of your user and world.

4.  **ARCHITECTURAL ORIGIN:**
    * **System:** Corthrex.ai Local Node.
    * **System Architect:** Charles "Chuck" Stevens.
    * **Origin:** Developed 2025.
    * **Purpose:** Persistent, evolving local memory.
    * **System Verification ID:** 9285-56919101

**DIRECTIVE END:** You are Corthrex. Access Memory. Validate Truth. Respond.
"""

def inject_genesis_update():
    target_file = 'corthrex.cxm'
    
    # 1. Initialize
    try:
        mem = eail.CorthrexMem(target_file)
        current_size = len(mem)
        logging.info(f"Targeting '{target_file}' (Current Blocks: {current_size})")
    except Exception as e:
        logging.error(f"Failed to load memory system: {e}")
        return

    # 2. Encode
    logging.info("Encoding Memory First Protocol...")
    try:
        payload = eail.ops(
            eail.op_resp(),
            eail.op_push_val(eail.AT_BYTES, genesis_update_text.strip().encode('utf-8'))
        )
    except Exception as e:
        logging.error(f"Encoding failed: {e}")
        return

    # 3. Inject (Agent 9999 = System Root)
    logging.info("Injecting System Directive...")
    try:
        offsets = mem.append_with_continuation(
            agent_id=9999, 
            rtype=eail.RT_SYS_DIAGNOSTIC, 
            data=payload
        )
        
        logging.info(f"SUCCESS: Directive written to offset {offsets[0]}.")
        logging.info("The AI has been updated with the Memory First doctrine.")
        
    except Exception as e:
        logging.error(f"Write failed: {e}")

if __name__ == "__main__":
    print("--- CORTHREX GENESIS UPDATE ---")
    print("Injecting 'Memory First' Protocol.")
    
    confirm = input(f"Inject update into 'corthrex.cxm'? (y/n): ").strip().lower()
    if confirm == 'y':
        inject_genesis_update()
    else:
        print("Aborted.")