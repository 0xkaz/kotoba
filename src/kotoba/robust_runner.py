"""Robust test runner module"""

import asyncio
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint

from .config import KotobaConfig
from .browser import BrowserManager

# Switch between LLM and mock based on environment variable
import os
if os.getenv("USE_MOCK_LLM", "false").lower() == "true":
    from .mock_llm import MockLLMManager as LLMManager
else:
    from .llm import LLMManager

console = Console()


class RobustTestRunner:
    """Robust test execution management class"""
    
    def __init__(self, config: KotobaConfig):
        self.config = config
        self.llm_manager = LLMManager(config.llm)
        self.browser_manager = BrowserManager(config.playwright)
        self.test_results: List[Dict[str, Any]] = []
        self._browser_started = False
        
    async def run_test_files_batch(self, test_file_paths: List[Path]) -> List[Dict[str, Any]]:
        """Execute multiple test files in batch (with robust browser session management)"""
        if not test_file_paths:
            return []
            
        console.print(Panel(f"[bold cyan]🚀 Starting robust batch test execution: {len(test_file_paths)} files[/bold cyan]"))
        
        # Load LLM model only once
        console.print("[yellow]🤖 Loading LLM model...[/yellow]")
        self.llm_manager.load_model()
        
        # Start browser only once
        console.print("[yellow]🌎 Starting browser session...[/yellow]")
        await self.browser_manager.start()
        self._browser_started = True
        
        batch_results = []
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                
                overall_task = progress.add_task(
                    f"[cyan]Batch test in progress...[/cyan]", 
                    total=len(test_file_paths)
                )
                
                for i, test_file_path in enumerate(test_file_paths):
                    console.print(f"\n[bold blue]📋 Test {i+1}/{len(test_file_paths)}: {test_file_path.name}[/bold blue]")
                    
                    try:
                        # Create new page for each test
                        result = await self._run_single_test_robust(test_file_path)
                        batch_results.append(result)
                        
                        progress.update(overall_task, advance=1)
                        
                    except Exception as e:
                        logger.error(f"Test file {test_file_path} failed: {e}")
                        error_result = {
                            "test_name": test_file_path.name,
                            "status": "error",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }
                        batch_results.append(error_result)
                        progress.update(overall_task, advance=1)
        
        finally:
            # Close browser session
            if self._browser_started:
                console.print("[yellow]🌙 Closing browser session...[/yellow]")
                try:
                    await self.browser_manager.close()
                except Exception as e:
                    logger.warning(f"Browser close warning: {e}")
                self._browser_started = False
        
        # Display batch result summary
        self._display_batch_summary(batch_results)
        
        return batch_results
    
    async def _run_single_test_robust(self, test_file_path: Path) -> Dict[str, Any]:
        """Execute single test file robustly (run in new page)"""
        # Load test file
        test_data = self._load_test_file(test_file_path)
        console.print(f"  ✓ Test data loaded: [green]{test_data.get('name', 'Unnamed')}[/green]")
        
        # Create new page and execute
        page = None
        try:
            page = await self.browser_manager.context.new_page()
            page.set_default_timeout(self.browser_manager.config.timeout)
            
            # Temporarily switch page
            original_page = self.browser_manager.page
            self.browser_manager.page = page
            
            # Execute test
            results = await self._execute_test_suite_robust(test_data)
            
            # Restore original page
            self.browser_manager.page = original_page
            
            # Save results
            result_file = self._save_results(results, test_file_path.stem)
            console.print(f"  ✓ Results saved: [dim]{result_file}[/dim]")
            
            return results
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            raise
        finally:
            # Close used page
            if page and not page.is_closed():
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"Page close warning: {e}")
    
    async def _execute_test_suite_robust(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test suite robustly"""
        results = {
            "test_name": test_data.get("name", "Unknown"),
            "start_time": datetime.now().isoformat(),
            "base_url": test_data.get("base_url", ""),
            "test_cases": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0
            }
        }
        
        # Set base URL
        if test_data.get("base_url"):
            try:
                await self.browser_manager.navigate(test_data["base_url"])
            except Exception as e:
                logger.error(f"Base URL navigation failed: {e}")
                results["summary"]["errors"] += 1
                results["end_time"] = datetime.now().isoformat()
                return results
        
        # Execute test cases
        test_cases = test_data.get("test_cases", [])
        console.print(f"  📝 Number of test cases: [cyan]{len(test_cases)}[/cyan]")
        
        for i, test_case in enumerate(test_cases):
            test_name = test_case.get('name', f'Test {i+1}')
            console.print(f"    ⚡ {test_name}")
            
            try:
                case_result = await self._execute_test_case_robust(test_case)
                results["test_cases"].append(case_result)
                
                # Update summary
                results["summary"]["total"] += 1
                if case_result["status"] == "passed":
                    results["summary"]["passed"] += 1
                    console.print(f"    [green]✓ Success[/green]")
                elif case_result["status"] == "failed":
                    results["summary"]["failed"] += 1
                    console.print(f"    [red]✗ Failed[/red]")
                else:
                    results["summary"]["errors"] += 1
                    console.print(f"    [red]⚠️  Error[/red]")
                    
            except Exception as e:
                logger.error(f"Test case {test_name} crashed: {e}")
                error_case = {
                    "name": test_name,
                    "status": "error",
                    "error": str(e),
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat()
                }
                results["test_cases"].append(error_case)
                results["summary"]["total"] += 1
                results["summary"]["errors"] += 1
                console.print(f"    [red]💥 Crash[/red]")
        
        results["end_time"] = datetime.now().isoformat()
        return results
    
    async def _execute_test_case_robust(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual test case robustly"""
        case_result = {
            "name": test_case.get("name", "Unknown"),
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "steps": [],
            "error": None,
            "screenshot": None
        }
        
        try:
            # Execute steps
            steps = test_case.get("steps", [])
            for step_idx, step in enumerate(steps):
                try:
                    step_result = await self._execute_step_robust(step, step_idx)
                    case_result["steps"].append(step_result)
                    
                    if step_result["status"] == "failed":
                        case_result["status"] = "failed"
                        break
                        
                except Exception as e:
                    logger.error(f"Step {step_idx} crashed: {e}")
                    error_step = {
                        "index": step_idx,
                        "status": "error",
                        "error": str(e),
                        "start_time": datetime.now().isoformat(),
                        "end_time": datetime.now().isoformat()
                    }
                    case_result["steps"].append(error_step)
                    case_result["status"] = "error"
                    break
            
            if case_result["status"] == "running":
                case_result["status"] = "passed"
                
        except Exception as e:
            case_result["status"] = "error"
            case_result["error"] = str(e)
            logger.error(f"Test case error: {e}")
        
        case_result["end_time"] = datetime.now().isoformat()
        return case_result
    
    async def _execute_step_robust(self, step: Dict[str, Any], step_idx: int) -> Dict[str, Any]:
        """Execute individual step robustly"""
        step_result = {
            "index": step_idx,
            "description": step.get("description", ""),
            "natural_language": step.get("instruction", ""),
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "action": None,
            "error": None
        }
        
        try:
            # Check page state
            if not self.browser_manager.page or self.browser_manager.page.is_closed():
                raise RuntimeError("Page is closed or unavailable")
            
            # Parse natural language and convert to action
            instruction = step.get("instruction", "")
            if not instruction:
                raise ValueError("No instruction provided")
            
            logger.debug(f"Processing instruction: {instruction}")
            action = self.llm_manager.translate_to_actions(instruction)
            step_result["action"] = action
            
            # Execute action (with timeout handling)
            try:
                await asyncio.wait_for(
                    self.browser_manager.execute_action(action),
                    timeout=self.browser_manager.config.timeout / 1000
                )
            except asyncio.TimeoutError:
                raise RuntimeError(f"Action timed out: {action}")
            
            # Short wait (for UI update)
            await asyncio.sleep(0.2)
            
            step_result["status"] = "passed"
            
        except Exception as e:
            step_result["status"] = "failed"
            step_result["error"] = str(e)
            logger.error(f"Step execution failed: {e}")
        
        step_result["end_time"] = datetime.now().isoformat()
        return step_result
    
    def _load_test_file(self, file_path: Path) -> Dict[str, Any]:
        """Load test file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    return json.load(f)
                elif file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")
                    
        except Exception as e:
            logger.error(f"Failed to load test file: {e}")
            raise
    
    def _save_results(self, results: Dict[str, Any], test_name: str) -> Path:
        """Save test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.config.test.output_dir / f"result_{test_name}_{timestamp}.json"
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            return result_file
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    def _display_batch_summary(self, batch_results: List[Dict[str, Any]]) -> None:
        """Display batch test result summary"""
        console.print(f"\n[bold cyan]📊 Robust Batch Test Completion Summary[/bold cyan]")
        
        # Overall statistics
        total_tests = len(batch_results)
        total_cases = sum(len(result.get("test_cases", [])) for result in batch_results)
        total_passed = sum(result.get("summary", {}).get("passed", 0) for result in batch_results)
        total_failed = sum(result.get("summary", {}).get("failed", 0) for result in batch_results)
        total_errors = sum(result.get("summary", {}).get("errors", 0) for result in batch_results)
        
        # Create summary table
        table = Table(title="Robust Batch Test Results", style="cyan")
        table.add_column("Test File", style="dim")
        table.add_column("Cases", justify="right")
        table.add_column("Passed", justify="right")
        table.add_column("Failed", justify="right")
        table.add_column("Errors", justify="right")
        table.add_column("Success Rate", justify="right")
        
        for result in batch_results:
            name = result.get("test_name", "Unknown")
            summary = result.get("summary", {})
            total = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            errors = summary.get("errors", 0)
            
            success_rate = (passed / total * 100) if total > 0 else 0
            
            table.add_row(
                name,
                str(total),
                f"[green]{passed}[/green]",
                f"[red]{failed}[/red]",
                f"[yellow]{errors}[/yellow]",
                f"{success_rate:.1f}%"
            )
        
        # Add total row
        table.add_row("", "", "", "", "", style="dim")
        overall_success_rate = (total_passed / total_cases * 100) if total_cases > 0 else 0
        table.add_row(
            f"[bold]Total ({total_tests} files)[/bold]",
            f"[bold]{total_cases}[/bold]",
            f"[bold green]{total_passed}[/bold green]",
            f"[bold red]{total_failed}[/bold red]",
            f"[bold yellow]{total_errors}[/bold yellow]",
            f"[bold]{overall_success_rate:.1f}%[/bold]"
        )
        
        console.print("\n")
        console.print(table)
        
        # Display robustness improvement effects
        console.print(f"\n[bold green]🛡️  Robustness Improvement Effects:[/bold green]")
        console.print(f"• Create new page for each test file (ensure independence)")
        console.print(f"• Improved error tolerance (continue execution even if one test fails)")
        console.print(f"• Safely executed {total_tests} test files")

    # Keep traditional run_test_file for compatibility with existing methods
    async def run_test_file(self, test_file_path: Path) -> Dict[str, Any]:
        """Execute single test file (legacy compatible)"""
        return (await self.run_test_files_batch([test_file_path]))[0]