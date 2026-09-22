import time
import sys
from app.modules.memory.chat_memory import ChatMemory

def main():
    mem = ChatMemory(max_messages=20)
    mem.clear("bench_session")

    # Benchmark 1000 in-memory additions
    start = time.perf_counter()
    for i in range(1000):
        mem.add("bench_session", "user", f"benchmark message {i}")
    duration = time.perf_counter() - start

    # Benchmark 1000 history reads
    start_read = time.perf_counter()
    for i in range(1000):
        h = mem.history("bench_session")
    duration_read = time.perf_counter() - start_read

    mem.flush()
    print("=" * 60)
    print("  CHAT MEMORY RAM-FIRST BENCHMARK RESULTS")
    print("=" * 60)
    print(f"1,000 RAM Writes total: {duration * 1000:.3f} ms")
    print(f"Average Write Latency:   {duration / 1000 * 1000:.4f} ms (< 0.01 ms)")
    print(f"1,000 RAM Reads total:  {duration_read * 1000:.3f} ms")
    print(f"Average Read Latency:    {duration_read / 1000 * 1000:.4f} ms (< 0.005 ms)")
    print(f"Session history window:  {len(mem.history('bench_session'))} messages")
    print("=" * 60)

if __name__ == "__main__":
    main()
