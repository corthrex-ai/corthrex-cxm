# debug_index.py — run this once, right now
import eail

mem = eail.CorthrexMem("corthrex.cxm")

print(f"Total blocks in file: {len(mem)}")
print("\nLast 15 raw text extracts:\n" + "="*50)

count = 0
for rec in mem.scan():
    if rec["type"] in (eail.RT_USER_REQUEST, eail.RT_AGENT_RESPONSE):
        text = eail.extract_text_fast(rec["payload"])
        role = "USER" if rec["type"] == eail.RT_USER_REQUEST else "CORTHREX"
        print(f"{rec['timestamp']} [{role}] {text[:120]}...")
        count += 1
        if count >= 15:
            break