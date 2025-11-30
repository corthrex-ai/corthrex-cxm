# read_mem.py
# CORTHREX LOG READER (CLI UTILITY)
# Run this from your command prompt/terminal: python read_mem.py

import os
import struct
import mmap
from datetime import datetime
from typing import Generator, Dict, Any, Optional, Tuple

# --- Configuration ---
MEMORY_FILE = 'corthrex.cxm' # <--- TARGETS THE NEW STANDARD FILE

# Constants matches eail.py
HEADER_SIZE = 64
BLOCK_SIZE = 256
RT_USER_REQUEST = 1; RT_AGENT_RESPONSE = 2; RT_INTERNAL_DEBATE = 3
RT_CONTINUATION = 6
OP_PUSH_VAL = 0x03; AT_BYTES = 0x04

# Binary Structs
RECORD_STRUCT = struct.Struct('<B B H Q Q 16s H 214s I')
CRC32C_TABLE = tuple((c := i, [c := (c >> 1) ^ 0x1EDC6F41 if c & 1 else c >> 1 for _ in range(8)], c & 0xFFFFFFFF)[2] for i in range(256))

def crc32c(data: bytes, crc: int = 0) -> int:
    crc ^= 0xFFFFFFFF
    for b in data: crc = CRC32C_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF

class CorthrexReader:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            print(f"\n[ERROR] File '{path}' not found.\n")
            print("Make sure you have run the Corthrex Chat at least once to generate the memory file.")
            exit(1)

    def scan_fast(self):
        file_size = os.path.getsize(self.path)
        with open(self.path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                pos = HEADER_SIZE
                while pos + BLOCK_SIZE <= len(mm):
                    if mm[pos] != 0x01: break # Stop at uncommitted block
                    
                    block_data = mm[pos:pos + BLOCK_SIZE]
                    payload_crc = struct.unpack_from('<I', block_data, -4)[0]
                    if crc32c(block_data[1:-4]) != payload_crc:
                        pos += BLOCK_SIZE; continue

                    _, rtype, agent_id, ts, link, _, psz = RECORD_STRUCT.unpack_from(mm, pos)[:7]
                    payload = RECORD_STRUCT.unpack_from(mm, pos)[7][:psz]
                    
                    yield {'offset': pos, 'type': rtype, 'agent_id': agent_id, 'ts': ts, 'link': link, 'pl': payload, 'psz': psz}
                    pos += BLOCK_SIZE

    def reassemble(self, head_offset):
        # Quick reassembly for display
        # Note: Ideally imports eail.py, but this is standalone for portability
        records = list(self.scan_fast())
        head = next((r for r in records if r['offset'] == head_offset), None)
        if not head: return b""
        
        chunks = [head['pl']]
        # Find continuations
        conts = sorted([r for r in records if r['type'] == RT_CONTINUATION and r['link'] == head_offset], 
                      key=lambda x: int.from_bytes(x['pl'][:2], 'little'))
        for c in conts: chunks.append(c['pl'][2:])
        return b''.join(chunks)

def decode_text(data):
    # Simplified decoder (skipping LEB128 complexity for pure display if standard format)
    try:
        # Try finding standard string marker
        if data[0] == OP_PUSH_VAL and data[1] == AT_BYTES:
            # Skip the LEB length (hacky but works for display usually)
            # Proper way needs the LEB function, but simple strings work:
            return data[3:].decode('utf-8', 'ignore') 
        return data.decode('utf-8', 'ignore').strip()
    except:
        return "[Binary Data]"

def main():
    print("\n" + "="*60)
    print(" CORTHREX LOG READER (CLI MODE)")
    print(" DO NOT RUN WHILE CHATTING TO AVOID FILE LOCKS")
    print("="*60)
    print(f"Reading: {MEMORY_FILE}\n")

    reader = CorthrexReader(MEMORY_FILE)
    count = 0

    for rec in reader.scan_fast():
        if rec['type'] == RT_CONTINUATION: continue # Skip partials
        
        count += 1
        full_data = reader.reassemble(rec['offset'])
        text = decode_text(full_data)
        
        # Cleanup artifacts for display
        text = text.replace('\x00', '').strip()
        
        # Determine Role
        role = "USER" if rec['agent_id'] == 0 else "CORTHREX"
        if rec['type'] == RT_INTERNAL_DEBATE: role = "SYSTEM_THOUGHT"
        
        ts = datetime.fromtimestamp(rec['ts'] / 1e9).strftime('%Y-%m-%d %H:%M:%S')

        print(f"[{ts}] {role}:")
        print(f"{text}")
        print("-" * 60)

    print(f"\n[End of Log. Total Records: {count}]")
    input("\nPress Enter to close...")

if __name__ == "__main__":
    main()