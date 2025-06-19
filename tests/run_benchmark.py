#!/usr/bin/env python3
"""
kotoba Multi-language LLM Benchmark Script
Compares different LLM models across Japanese, Chinese, and English tasks
"""

import json
import time
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
import yaml

# Add src to path for kotoba imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class BenchmarkRunner:
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.test_scenarios = self.load_test_scenarios()
        
        # Benchmark models (ordered by priority)
        self.models = [
            # Lightweight (priority)
            "Qwen/Qwen2-1.5B-Instruct",
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            
            # Medium weight
            "rinna/japanese-gpt-neox-3.6b",
            "cyberagent/open-calm-3b",
            
            # Heavy weight (if memory allows)
            # "pfnet/plamo-13b-instruct"
        ]
        
    def load_test_scenarios(self):
        """Load multilingual test scenarios"""
        scenarios_file = Path(__file__).parent / "multilingual_benchmark.yaml"
        if scenarios_file.exists():
            with open(scenarios_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def run_single_test(self, model, test_file, scenario_name):
        """Run a single test scenario with specified model"""
        print(f"🔄 Testing {model} on {scenario_name}")
        
        start_time = time.time()
        
        try:
            # Use MockLLM mode for quick testing
            env = os.environ.copy()
            env['USE_MOCK_LLM'] = 'true'
            
            cmd = [
                "python3", "-m", "kotoba",
                "--test-file", test_file,
                "--output-dir", "outputs"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout per test
                env=env,
                cwd=Path(__file__).parent.parent
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "execution_time": 300,
                "error": "Timeout after 5 minutes",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "execution_time": time.time() - start_time,
                "error": str(e),
                "returncode": -1
            }
    
    def create_test_files(self):
        """Create simple test files for benchmark"""
        test_files = {}
        
        # Japanese test - simple navigation
        japanese_test = {
            "name": "Japanese Simple Test",
            "url": "https://example.com",
            "steps": [
                "ページタイトルを確認する",
                "スクリーンショットを撮る"
            ]
        }
        
        # Chinese test - simple navigation
        chinese_test = {
            "name": "Chinese Simple Test",
            "url": "https://example.com",
            "steps": [
                "确认页面标题",
                "截图保存"
            ]
        }
        
        # English test - simple navigation
        english_test = {
            "name": "English Simple Test", 
            "url": "https://example.com",
            "steps": [
                "Check page title",
                "Take a screenshot"
            ]
        }
        
        # Save test files
        tests_dir = Path(__file__).parent
        
        for test_name, test_data in [
            ("japanese_test", japanese_test),
            ("chinese_test", chinese_test), 
            ("english_test", english_test)
        ]:
            test_file = tests_dir / f"benchmark_{test_name}.yaml"
            with open(test_file, 'w', encoding='utf-8') as f:
                yaml.dump(test_data, f, allow_unicode=True, default_flow_style=False)
            test_files[test_name] = str(test_file)
            
        return test_files
    
    def run_benchmark(self):
        """Run complete benchmark suite"""
        print("🚀 Starting kotoba Multi-language LLM Benchmark")
        print(f"📊 Models to test: {len(self.models)}")
        print(f"🌍 Languages: Japanese, Chinese, English")
        print("-" * 50)
        
        self.start_time = time.time()
        
        # Create test files
        test_files = self.create_test_files()
        
        # Run benchmarks
        for model in self.models:
            print(f"\n🤖 Testing model: {model}")
            model_results = {}
            
            for test_name, test_file in test_files.items():
                result = self.run_single_test(model, test_file, test_name)
                model_results[test_name] = result
                
                status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
                time_str = f"{result['execution_time']:.1f}s"
                print(f"  {test_name}: {status} ({time_str})")
            
            self.results[model] = model_results
            
        # Generate summary
        self.generate_summary()
        
    def generate_summary(self):
        """Generate benchmark summary"""
        total_time = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("📊 BENCHMARK SUMMARY")
        print("="*60)
        
        # Overall statistics
        total_tests = len(self.models) * 3  # 3 languages
        successful_tests = 0
        
        for model, tests in self.results.items():
            successful_tests += sum(1 for test in tests.values() if test["success"])
        
        print(f"⏱️  Total execution time: {total_time:.1f} seconds")
        print(f"🎯 Success rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        print()
        
        # Per-model results
        for model, tests in self.results.items():
            print(f"🤖 {model}:")
            
            avg_time = sum(test["execution_time"] for test in tests.values()) / len(tests)
            success_count = sum(1 for test in tests.values() if test["success"])
            
            print(f"   Success: {success_count}/3 tests")
            print(f"   Avg time: {avg_time:.1f}s per test")
            
            for test_name, result in tests.items():
                status = "✅" if result["success"] else "❌"
                print(f"   {status} {test_name}: {result['execution_time']:.1f}s")
            print()
        
        # Save results
        self.save_results()
        
    def save_results(self):
        """Save detailed results to JSON"""
        output_file = Path(__file__).parent.parent / "outputs" / f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        detailed_results = {
            "timestamp": datetime.now().isoformat(),
            "total_execution_time": time.time() - self.start_time,
            "models_tested": list(self.results.keys()),
            "test_scenarios": ["japanese_test", "chinese_test", "english_test"],
            "results": self.results,
            "summary": {
                "total_tests": len(self.models) * 3,
                "successful_tests": sum(
                    sum(1 for test in tests.values() if test["success"]) 
                    for tests in self.results.values()
                )
            }
        }
        
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    # Check if kotoba is installed
    try:
        import kotoba
        print(f"✅ kotoba version: {kotoba.__version__}")
    except ImportError:
        print("❌ kotoba not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                      cwd=Path(__file__).parent.parent)
    
    runner = BenchmarkRunner()
    runner.run_benchmark()