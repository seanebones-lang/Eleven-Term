#!/usr/bin/env python3
"""Generate performance report from benchmark JSON"""
import json
import sys
from pathlib import Path

def generate_report(benchmark_file: Path):
    """Generate human-readable performance report"""
    with open(benchmark_file) as f:
        data = json.load(f)
    
    print("=" * 60)
    print("Performance Benchmark Report")
    print("=" * 60)
    print()
    
    benchmarks = data.get("benchmarks", [])
    
    for bench in benchmarks:
        name = bench.get("name", "Unknown")
        stats = bench.get("stats", {})
        mean = stats.get("mean", 0) * 1000  # Convert to ms
        min_time = stats.get("min", 0) * 1000
        max_time = stats.get("max", 0) * 1000
        
        print(f"Benchmark: {name}")
        print(f"  Mean: {mean:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print()
    
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_performance_report.py <benchmark.json>")
        sys.exit(1)
    
    benchmark_file = Path(sys.argv[1])
    if not benchmark_file.exists():
        print(f"Error: {benchmark_file} not found")
        sys.exit(1)
    
    generate_report(benchmark_file)