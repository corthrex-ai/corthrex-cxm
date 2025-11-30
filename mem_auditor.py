# mem_auditor.py
# Corthrex Integrity Auditor (Chat Compatible)

import os
import shutil
import time
import struct
import sys
import io
import contextlib

# Ensure eail is found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import eail
except ImportError:
    pass # Handled by main script usually

class MemAuditor:
    def __init__(self, ark_path='corthrex.cxm'):
        self.ark_path = ark_path
        self.backup_path = ''
        self.stats = {
            'start_time': time.time(),
            'original_size': 0, 'final_size': 0,
            'total_records_scanned': 0, 'valid_records_found': 0,
            'corrupt_records_found': 0, 'corrupt_offsets': []
        }
        # Buffer to capture output for Chat UI
        self.log_buffer = io.StringIO()

    def log(self, message):
        """Writes to both console (for debug) and buffer (for chat UI)"""
        print(message)
        self.log_buffer.write(message + "\n")

    def _create_backup(self):
        if not os.path.exists(self.ark_path):
            self.log(f"[WARNING] Memory file not found at '{self.ark_path}'.")
            return False

        self.stats['original_size'] = os.path.getsize(self.ark_path)
        timestamp = time.strftime("%Y-%m-%d-%H%M%S")
        self.backup_path = f"{self.ark_path}.{timestamp}.bak"
        
        try:
            shutil.copy2(self.ark_path, self.backup_path)
            self.log(f"[INFO] Backup secured: {os.path.basename(self.backup_path)}")
            return True
        except Exception as e:
            self.log(f"[FATAL] Backup failed: {e}")
            return False

    def audit_and_repair(self):
        self.log("🔎 **CORTHREX INTEGRITY SCAN**")
        self.log("--------------------------------")

        if not self._create_backup(): return self.log_buffer.getvalue()

        valid_records_data = []
        temp_ark_path = self.ark_path + ".tmp"

        try:
            with open(self.ark_path, 'rb') as f:
                header = f.read(eail.HEADER_SIZE)
                if not header or len(header) < eail.HEADER_SIZE:
                    self.log("[FATAL] Header corrupted.")
                    return self.log_buffer.getvalue()
                valid_records_data.append(header)

                while True:
                    block_offset = f.tell()
                    block_data = f.read(eail.BLOCK_SIZE)
                    if not block_data: break

                    self.stats['total_records_scanned'] += 1

                    if len(block_data) == eail.BLOCK_SIZE:
                        stored_crc = struct.unpack_from('<I', block_data, eail.BLOCK_SIZE - 4)[0]
                        calculated_crc = eail.crc32c(block_data[1:-4])
                        commit_byte = block_data[0]

                        if commit_byte == 0x01 and stored_crc == calculated_crc:
                            self.stats['valid_records_found'] += 1
                            valid_records_data.append(block_data)
                        else:
                            self.stats['corrupt_records_found'] += 1
                            self.stats['corrupt_offsets'].append(block_offset)
                    else:
                        self.stats['corrupt_records_found'] += 1
                        self.stats['corrupt_offsets'].append(block_offset)

            if self.stats['corrupt_records_found'] > 0:
                self.log(f"[WARN] Found {self.stats['corrupt_records_found']} corrupt records.")
                self.log("[ACTION] Rebuilding memory file...")
                with open(temp_ark_path, 'wb') as temp_f:
                    for data in valid_records_data: temp_f.write(data)
                
                os.remove(self.ark_path)
                os.rename(temp_ark_path, self.ark_path)
                self.log("[SUCCESS] Rebuild complete.")
            else:
                self.log(f"[OK] scanned {self.stats['total_records_scanned']} blocks.")
                self.log("[OK] Structure Integrity: 100%")

        except Exception as e:
            self.log(f"[FATAL] Audit Error: {e}")
        
        return self.log_buffer.getvalue()

def run_audit_return_text():
    auditor = MemAuditor()
    return auditor.audit_and_repair()

if __name__ == "__main__":
    run_audit_return_text()