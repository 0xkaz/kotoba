"""Test runner module"""

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
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from .config import KotobaConfig
from .browser import BrowserManager
from .assertions import AssertionPatternMatcher, Assertion, AssertionType

# Switch between LLM and mock based on environment variable
import os
if os.getenv("USE_MOCK_LLM", "false").lower() == "true":
    from .mock_llm import MockLLMManager as LLMManager
else:
    from .llm import LLMManager

console = Console()


class TestRunner:
    """Test execution management class"""
    
    def __init__(self, config: KotobaConfig):
        self.config = config
        self.llm_manager = LLMManager(config.llm)
        self.browser_manager = BrowserManager(config.playwright)
        self.test_results: List[Dict[str, Any]] = []
        self.assertion_pattern_matcher = AssertionPatternMatcher()
        
    async def run_test_file(self, test_file_path: Path) -> Dict[str, Any]:
        """Execute test file"""
        console.print(Panel(f"[bold cyan]🧪 Starting test execution: {test_file_path.name}[/bold cyan]"))
        
        # Load test file
        test_data = self._load_test_file(test_file_path)
        console.print(f"✓ Test file loaded: [green]{test_data.get('name', 'Unnamed')}[/green]")
        
        # Load LLM model
        self.llm_manager.load_model()
        
        # Execute test
        async with self.browser_manager:
            results = await self._execute_test_suite(test_data)
        
        # Save results
        result_file = self._save_results(results, test_file_path.stem)
        
        # Display results summary
        self._display_results_summary(results)
        
        console.print(f"\n[green]✓ Test completed![/green] Results saved to: [blue]{result_file}[/blue]")
        return results
    
    async def run_interactive(self) -> None:
        """Interactive mode"""
        logger.info("Starting interactive mode")
        
        # Load LLM model
        self.llm_manager.load_model()
        
        async with self.browser_manager:
            await self._interactive_session()
    
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
    
    async def _execute_test_suite(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test suite"""
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
            await self.browser_manager.navigate(test_data["base_url"])
        
        # Execute test cases
        test_cases = test_data.get("test_cases", [])
        console.print(f"\n📝 Number of test cases: [cyan]{len(test_cases)}[/cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            for i, test_case in enumerate(test_cases):
                test_name = test_case.get('name', f'Test {i+1}')
                task = progress.add_task(f"[cyan]Test {i+1}/{len(test_cases)}: {test_name}[/cyan]", total=None)
                
                case_result = await self._execute_test_case(test_case)
                results["test_cases"].append(case_result)
                
                # Status display
                status_display = {
                    "passed": "[green]✓ Passed[/green]",
                    "failed": "[red]✗ Failed[/red]",
                    "error": "[red]⚠️  Error[/red]"
                }
                
                progress.update(task, description=f"{test_name} {status_display.get(case_result['status'], '')}", completed=True)
                
                # Update summary
                results["summary"]["total"] += 1
                if case_result["status"] == "passed":
                    results["summary"]["passed"] += 1
                elif case_result["status"] == "failed":
                    results["summary"]["failed"] += 1
                else:
                    results["summary"]["errors"] += 1
        
        results["end_time"] = datetime.now().isoformat()
        return results
    
    async def _execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual test case"""
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
                step_result = await self._execute_step(step, step_idx)
                case_result["steps"].append(step_result)
                
                if step_result["status"] == "failed":
                    case_result["status"] = "failed"
                    if self.config.test.screenshot_on_failure:
                        screenshot_path = await self._take_failure_screenshot(test_case["name"], step_idx)
                        case_result["screenshot"] = str(screenshot_path)
                    break
            
            if case_result["status"] == "running":
                case_result["status"] = "passed"
                
        except Exception as e:
            case_result["status"] = "error"
            case_result["error"] = str(e)
            logger.error(f"Test case error: {e}")
            
            if self.config.test.screenshot_on_failure:
                screenshot_path = await self._take_failure_screenshot(test_case["name"], -1)
                case_result["screenshot"] = str(screenshot_path)
        
        case_result["end_time"] = datetime.now().isoformat()
        return case_result
    
    async def _execute_step(self, step: Dict[str, Any], step_idx: int) -> Dict[str, Any]:
        """Execute individual step"""
        step_result = {
            "index": step_idx,
            "description": step.get("description", ""),
            "natural_language": step.get("instruction", ""),
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "action": None,
            "assertion_result": None,
            "error": None
        }
        
        try:
            # Parse natural language instruction
            instruction = step.get("instruction", "")
            if not instruction:
                raise ValueError("No instruction provided")
            
            logger.debug(f"Processing instruction: {instruction}")
            
            # Check if this is an assertion instruction
            assertion_info = self.assertion_pattern_matcher.parse(instruction)
            
            if assertion_info:
                # Execute as assertion
                # Convert string type back to enum if needed
                if isinstance(assertion_info["type"], str):
                    assertion_info["type"] = AssertionType(assertion_info["type"])
                assertion = Assertion(**assertion_info)
                assertion_result = await self.browser_manager.execute_assertion(assertion)
                step_result["assertion_result"] = {
                    "type": assertion.type.value,
                    "passed": assertion_result.passed,
                    "expected": assertion_result.expected_value,
                    "actual": assertion_result.actual_value,
                    "error_message": assertion_result.error_message,
                    "execution_time_ms": assertion_result.execution_time_ms
                }
                
                # Set step status based on assertion result
                step_result["status"] = "passed" if assertion_result.passed else "failed"
                if not assertion_result.passed:
                    step_result["error"] = assertion_result.error_message
                
            else:
                # Execute as regular action
                action = self.llm_manager.translate_to_actions(instruction)
                step_result["action"] = action
                
                # Execute action
                await self.browser_manager.execute_action(action)
                
                # Wait briefly (for UI updates)
                await asyncio.sleep(0.5)
                
                step_result["status"] = "passed"
            
        except Exception as e:
            step_result["status"] = "failed"
            step_result["error"] = str(e)
            logger.error(f"Step execution failed: {e}")
        
        step_result["end_time"] = datetime.now().isoformat()
        return step_result
    
    async def _take_failure_screenshot(self, test_name: str, step_idx: int) -> Path:
        """Take screenshot on failure"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_name = f"failure_{test_name}_{step_idx}_{timestamp}.png"
        screenshot_path = self.config.test.output_dir / screenshot_name
        
        try:
            await self.browser_manager.take_screenshot(str(screenshot_path))
            return screenshot_path
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return Path("screenshot_failed.png")
    
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
    
    def _display_results_summary(self, results: Dict[str, Any]) -> None:
        """Display test results summary"""
        summary = results["summary"]
        
        # Create summary table
        table = Table(title="Test Results Summary", style="cyan")
        table.add_column("Item", style="dim")
        table.add_column("Value", justify="right")
        
        table.add_row("Test Name", results["test_name"])
        table.add_row("Total", str(summary["total"]))
        table.add_row("[green]Passed[/green]", f"[green]{summary['passed']}[/green]")
        table.add_row("[red]Failed[/red]", f"[red]{summary['failed']}[/red]")
        table.add_row("[yellow]Errors[/yellow]", f"[yellow]{summary['errors']}[/yellow]")
        
        # Calculate success rate
        if summary["total"] > 0:
            success_rate = (summary["passed"] / summary["total"]) * 100
            table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        console.print("\n")
        console.print(table)
    
    async def _interactive_session(self) -> None:
        """Interactive session"""
        console.print(Panel("[bold cyan]🎮 Interactive Mode[/bold cyan]\n\nType 'exit' to quit"))
        
        # Initial page
        await self.browser_manager.navigate("about:blank")
        
        while True:
            try:
                # User input
                instruction = console.input("\n[bold cyan]📝 Instruction > [/bold cyan]").strip()
                
                if instruction.lower() in ['exit', 'quit']:
                    break
                
                if not instruction:
                    continue
                
                # Execute instruction
                console.print(f"[dim]→ Executing: {instruction}[/dim]")
                
                # Check if this is an assertion instruction
                assertion_info = self.assertion_pattern_matcher.parse(instruction)
                
                if assertion_info:
                    # Execute as assertion
                    # Convert string type back to enum if needed
                    if isinstance(assertion_info["type"], str):
                        assertion_info["type"] = AssertionType(assertion_info["type"])
                    assertion = Assertion(**assertion_info)
                    assertion_result = await self.browser_manager.execute_assertion(assertion)
                    if assertion_result.passed:
                        console.print(f"[green]✓ Assertion passed[/green]")
                    else:
                        console.print(f"[red]✗ Assertion failed: {assertion_result.error_message}[/red]")
                else:
                    # Execute as regular action
                    action = self.llm_manager.translate_to_actions(instruction)
                    await self.browser_manager.execute_action(action)
                
                # Display page information
                page_info = await self.browser_manager.get_page_info()
                console.print(f"[green]Current page: {page_info['title']}[/green]")
                console.print(f"[dim]URL: {page_info['url']}[/dim]")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
        
        console.print("\n[yellow]👋 Interactive session ended[/yellow]")
        logger.info("Interactive session ended")