# benchmark_corthrex.py
import time, os, eail, random, string
TEST_FILE = "benchmark_test.cxm"
ITERATIONS = 5000

def generate_random_payload(size=50):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode('utf-8')

def run_benchmark_return_stats():
    if os.path.exists(TEST_FILE): os.remove(TEST_FILE)
    mem = eail.CorthrexMem(TEST_FILE)
    
    start_write = time.perf_counter()
    for i in range(ITERATIONS):
        rtype = eail.RT_USER_REQUEST if i % 2 == 0 else eail.RT_AGENT_RESPONSE
        payload = eail.ops(eail.op_req(), eail.op_push_val(eail.AT_BYTES, generate_random_payload()))
        mem.append_with_continuation(agent_id=0, rtype=rtype, data=payload)
    write_time = time.perf_counter() - start_write
    write_iops = int(ITERATIONS / write_time)
    
    start_read = time.perf_counter()
    count = 0
    for rec in mem.scan_fast():
        mem.reassemble_payload(rec['offset']); count += 1
    read_time = time.perf_counter() - start_read
    read_iops = int(count / read_time) if read_time > 0 else 0
    
    try: os.remove(TEST_FILE)
    except: pass
    
    return {"write_speed": f"{write_iops:,} OPS", "read_speed": f"{read_iops:,} OPS", "status": "HYPER-EFFICIENT"}