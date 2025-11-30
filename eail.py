# eail.py
# Corthrex Extended AI Log Protocol
# Version: 2.4.1

import os
import struct
import time
import mmap
import secrets
import logging
from typing import Generator, Dict, Any, List, Optional, Tuple

# Setup library logging (silenced by default)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ---------------------------
# Configuration
# ---------------------------
FILE_TAG = b'CRTX'
HEADER_SIZE = 64
BLOCK_SIZE = 256
RT_USER_REQUEST    = 1; RT_AGENT_RESPONSE  = 2; RT_INTERNAL_DEBATE = 3
RT_SYS_DIAGNOSTIC  = 4; RT_FACT_CORRECTION = 5; RT_CONTINUATION    = 6; RT_BLOB_REF = 7
OP_REQ = 0x06; OP_RESP = 0x07; OP_END = 0x09; OP_PUSH_KEY = 0x02
OP_PUSH_VAL = 0x03; OP_BIND = 0x04; OP_ASSERT = 0x05
AT_INT = 0x00; AT_BYTES = 0x04; AT_DICTID = 0x05; AT_TEXTID = 0x07

_CRC32C_TABLE = tuple(
    (c := i, [c := (c >> 1) ^ 0x1EDC6F41 if c & 1 else c >> 1 for _ in range(8)], c & 0xFFFFFFFF)[2]
    for i in range(256)
)

def crc32c(data: bytes, crc: int = 0) -> int:
    crc ^= 0xFFFFFFFF
    for b in data: crc = _CRC32C_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return (crc ^ 0xFFFFFFFF) & 0xFFFFFFFF

HEADER_STRUCT = struct.Struct('<4s H H Q 48x')
RECORD_STRUCT = struct.Struct('<B B H Q Q 16s H 214s I')

# ---------------------------
# CorthrexMem Class
# ---------------------------
class CorthrexMem:
    __slots__ = ('path', '_file_size', 'continuation_map')
    
    def __init__(self, path: str = 'corthrex.cxm'):
        self.path = path
        self._file_size = 0
        self.continuation_map = {} 
        self._ensure_file()
        self._rebuild_index()

    def _ensure_file(self):
        if not os.path.exists(self.path) or os.path.getsize(self.path) < HEADER_SIZE:
            with open(self.path, 'wb') as f: f.write(HEADER_STRUCT.pack(FILE_TAG, 1, BLOCK_SIZE, 0))
        self._file_size = os.path.getsize(self.path)

    def _rebuild_index(self):
        self.continuation_map = {}
        for record in self.scan_fast():
            if record['type'] == RT_CONTINUATION:
                link = record['link']
                if link not in self.continuation_map:
                    self.continuation_map[link] = []
                self.continuation_map[link].append(record)
        
        for head in self.continuation_map:
            self.continuation_map[head].sort(key=lambda r: int.from_bytes(r['payload'][:2], 'little'))

    def __len__(self):
        return (os.path.getsize(self.path) - HEADER_SIZE) // BLOCK_SIZE

    def __getitem__(self, idx: int) -> Optional[Dict[str, Any]]:
        total = len(self)
        if idx < 0: idx += total
        if idx < 0 or idx >= total: raise IndexError("Index out of range")
        return self.get_record_by_id(idx)

    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        offset = HEADER_SIZE + (record_id * BLOCK_SIZE)
        if offset + BLOCK_SIZE > os.path.getsize(self.path): return None
        
        try:
            with open(self.path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    block_data = mm[offset : offset + BLOCK_SIZE]
                    stored_crc = struct.unpack_from('<I', block_data, -4)[0]
                    calc_crc = crc32c(block_data[1:-4])
                    if calc_crc != stored_crc: return None 
                    
                    _, rtype, agent_id, ts, link, semh, psz = RECORD_STRUCT.unpack_from(block_data, 0)[:7]
                    payload = RECORD_STRUCT.unpack_from(block_data, 0)[7][:psz]
                    
                    return {
                        'id': record_id,
                        'offset': offset, 'type': rtype, 'agent_id': agent_id, 
                        'timestamp': ts, 'link': link, 'semhash16': semh, 
                        'payload_size': psz, 'payload': payload
                    }
        except ValueError: return None

    def scan_fast(self) -> Generator[Dict[str, Any], None, None]:
        self._file_size = os.path.getsize(self.path)
        if self._file_size < HEADER_SIZE + BLOCK_SIZE: return
        
        with open(self.path, 'rb') as f:
            if self._file_size == 0: return
            try:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    pos = HEADER_SIZE
                    record_counter = 0 
                    while pos + BLOCK_SIZE <= len(mm):
                        if mm[pos] != 0x01: break
                        block_data = mm[pos:pos + BLOCK_SIZE]
                        stored_crc = struct.unpack_from('<I', block_data, -4)[0]
                        calc_crc = crc32c(block_data[1:-4])
                        if calc_crc != stored_crc: break
                        _, rtype, agent_id, ts, link, semh, psz = RECORD_STRUCT.unpack_from(mm, pos)[:7]
                        payload = RECORD_STRUCT.unpack_from(mm, pos)[7][:psz]
                        yield {
                            'id': record_counter,
                            'offset': pos, 'type': rtype, 'agent_id': agent_id, 
                            'timestamp': ts, 'link': link, 'semhash16': semh, 
                            'payload_size': psz, 'payload': payload
                        }
                        pos += BLOCK_SIZE
                        record_counter += 1
            except ValueError: return

    def scan(self, filter_type: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        for record in self.scan_fast():
            if filter_type is None or record['type'] == filter_type:
                yield record

    def get_tail_offset(self) -> int:
        self._file_size = os.path.getsize(self.path)
        return HEADER_SIZE + ((self._file_size - HEADER_SIZE) // BLOCK_SIZE) * BLOCK_SIZE

    def _append_record_fast(self, agent_id: int, rtype: int, payload: bytes, semhash: bytes, link_offset: int = 0) -> int:
        tail = self.get_tail_offset()
        record_data = RECORD_STRUCT.pack(0x00, rtype, agent_id, time.time_ns(), link_offset, semhash, len(payload), payload.ljust(214, b'\x00'), 0)
        crc = crc32c(record_data[1:-4])
        final_block = b'\x01' + record_data[1:-4] + struct.pack('<I', crc)
        with open(self.path, 'r+b') as f:
            f.seek(tail); f.write(final_block); f.flush(); os.fsync(f.fileno())
        return tail

    def append_with_continuation(self, agent_id: int, rtype: int, data: bytes, link_offset: int = 0) -> List[int]:
        semhash16 = secrets.token_bytes(16)
        if len(data) <= 214: return [self._append_record_fast(agent_id, rtype, data, semhash16, link_offset)]
        offsets, head_payload = [], data[:214]
        head_offset = self._append_record_fast(agent_id, rtype, head_payload, semhash16, link_offset)
        offsets.append(head_offset)
        self.continuation_map[head_offset] = []
        for seq, i in enumerate(range(214, len(data), 212), 1):
            chunk = data[i:i + 212]
            cont_payload = seq.to_bytes(2, 'little') + chunk
            cont_offset = self._append_record_fast(agent_id, RT_CONTINUATION, cont_payload, semhash16, head_offset)
            offsets.append(cont_offset)
            self.continuation_map[head_offset].append({'offset': cont_offset, 'payload': cont_payload})
        return offsets

    def reassemble_payload(self, head_offset: int) -> Optional[bytes]:
        try:
            with open(self.path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    if head_offset + BLOCK_SIZE > len(mm): return None
                    _, _, _, _, _, _, psz = RECORD_STRUCT.unpack_from(mm, head_offset)[:7]
                    head_payload = RECORD_STRUCT.unpack_from(mm, head_offset)[7][:psz]
                    if psz < 214: return head_payload
                    if head_offset in self.continuation_map:
                        chunks = [head_payload]
                        for rec in self.continuation_map[head_offset]:
                            chunks.append(rec['payload'][2:]) 
                        return b''.join(chunks)
                    return head_payload
        except Exception: return None

def _decode_leb128(data: bytes) -> Tuple[Optional[int], int]:
    result, shift, bytes_read = 0, 0, 0
    for i, byte in enumerate(data):
        bytes_read += 1; result |= (byte & 0x7F) << shift
        if not (byte & 0x80): return result, bytes_read
        shift += 7
        if shift >= 64: return None, bytes_read
    return None, bytes_read

def leb128_encode_fast(n: int) -> bytes:
    if n == 0: return b'\x00'
    result = bytearray()
    while True:
        byte = n & 0x7F; n >>= 7
        if (n == 0 and not (byte & 0x40)) or (n == -1 and (byte & 0x40)):
            result.append(byte); break
        result.append(byte | 0x80)
    return bytes(result)

def encode_atom_fast(tag: int, val) -> bytes:
    if tag == AT_BYTES:
        data = val if isinstance(val, bytes) else str(val).encode('utf-8')
        return bytes([AT_BYTES]) + leb128_encode_fast(len(data)) + data
    elif tag == AT_INT:
        return bytes([AT_INT]) + leb128_encode_fast(int(val))
    raise ValueError(f'Unsupported atom tag: {tag}')

def op_req(): return bytes([OP_REQ])
def op_resp(): return bytes([OP_RESP])
def op_end(): return bytes([OP_END])
def op_push_key(kid: int): return bytes([OP_PUSH_KEY]) + kid.to_bytes(2, 'little')
def op_push_val(tag: int, val): return bytes([OP_PUSH_VAL]) + encode_atom_fast(tag, val)
def ops(*op_bytes: bytes): return b''.join(op_bytes)

def extract_text_fast(eail_data: bytes) -> str:
    try:
        i = 0
        while i < len(eail_data):
            if eail_data[i] == OP_PUSH_VAL and i + 1 < len(eail_data) and eail_data[i+1] == AT_BYTES:
                length, bytes_read = _decode_leb128(eail_data[i+2:])
                if length is not None:
                    start = i + 2 + bytes_read
                    return eail_data[start : start + length].decode('utf-8', 'ignore')
            i += 1
        return eail_data.decode('utf-8', 'ignore').strip()
    except Exception:
        return "Binary data"