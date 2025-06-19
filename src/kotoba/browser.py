"""Playwright Web browser management module"""

import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from .config import PlaywrightConfig
from .assertions import AssertionExecutor, AssertionResult, Assertion

console = Console()


class BrowserManager:
    """Playwright browser management class"""
    
    def __init__(self, config: PlaywrightConfig):
        self.config = config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.assertion_executor: Optional[AssertionExecutor] = None
        
    async def start(self) -> None:
        """Start browser (with progress display)"""
        try:
            console.print(f"[bold cyan]🌎 Starting browser...[/bold cyan]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                
                # Initialize Playwright
                task = progress.add_task("🎭 Initializing Playwright...", total=None)
                self.playwright = await async_playwright().start()
                progress.update(task, completed=True)
                
                # Select browser type
                if self.config.browser == "chromium":
                    browser_type = self.playwright.chromium
                    browser_icon = "🌐"
                elif self.config.browser == "firefox":
                    browser_type = self.playwright.firefox
                    browser_icon = "🦊"
                elif self.config.browser == "webkit":
                    browser_type = self.playwright.webkit
                    browser_icon = "🍎"
                else:
                    raise ValueError(f"Unsupported browser: {self.config.browser}")
                
                # Launch browser
                task = progress.add_task(f"{browser_icon} Launching {self.config.browser}...", total=None)
                
                mode = "[dim]Headless mode[/dim]" if self.config.headless else "[yellow]Display mode[/yellow]"
                console.print(f"  {mode}")
                
                self.browser = await browser_type.launch(
                    headless=self.config.headless,
                    args=['--no-sandbox', '--disable-dev-shm-usage'] if self.config.headless else []
                )
                progress.update(task, completed=True)
                
                # Create context
                task = progress.add_task("🎲 Creating context...", total=None)
                self.context = await self.browser.new_context(
                    viewport=self.config.viewport
                )
                progress.update(task, completed=True)
                
                # Create page
                task = progress.add_task("📄 Creating new page...", total=None)
                self.page = await self.context.new_page()
                self.page.set_default_timeout(self.config.timeout)
                progress.update(task, completed=True)
                
                # Initialize assertion executor
                task = progress.add_task("✅ Initializing assertion engine...", total=None)
                self.assertion_executor = AssertionExecutor(self.page)
                progress.update(task, completed=True)
            
            console.print(f"[bold green]✨ Browser started![/bold green]")
            console.print(f"[dim]  Viewport: {self.config.viewport['width']}x{self.config.viewport['height']}[/dim]")
            console.print(f"[dim]  Timeout: {self.config.timeout}ms[/dim]")
            logger.info("Browser started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    async def navigate(self, url: str) -> None:
        """Navigate to specified URL"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            if url == "back":
                console.print("[yellow]← Going back to previous page[/yellow]")
                await self.page.go_back()
            else:
                console.print(f"[cyan]🚀 Navigating to: {url}[/cyan]")
                await self.page.goto(url)
                await self.page.wait_for_load_state("networkidle")
            
            # Display current page information
            title = await self.page.title()
            console.print(f"[green]✓ Page title: {title}[/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Navigation failed: {e}[/red]")
            logger.error(f"Navigation failed: {e}")
            raise
    
    async def execute_action(self, action: Dict[str, Any]) -> Any:
        """Execute action (with display)"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        action_type = action.get("action_type")
        
        try:
            if action_type == "click":
                selector = action.get("selector", "")
                console.print(f"[blue]🕹️  Click: {selector}[/blue]")
                await self.page.click(selector)
                logger.info(f"Clicked: {selector}")
                
            elif action_type == "type":
                selector = action.get("selector", "")
                text = action.get("text", "")
                console.print(f"[blue]⌨️  Type: '{text}' → {selector}[/blue]")
                await self.page.fill(selector, text)
                logger.info(f"Typed '{text}' into: {selector}")
                
            elif action_type == "wait":
                timeout = action.get("timeout", 3000)
                await self.page.wait_for_timeout(timeout)
                logger.info(f"Waited: {timeout}ms")
                
            elif action_type == "navigate":
                url = action.get("url", "")
                await self.navigate(url)
                
            elif action_type == "screenshot":
                path = action.get("path", "screenshot.png")
                await self.page.screenshot(path=path)
                logger.info(f"Screenshot saved: {path}")
                
            elif action_type == "scroll":
                await self.page.mouse.wheel(0, 500)
                logger.info("Scrolled down")
                
            elif action_type == "wait_for_selector":
                selector = action.get("selector", "")
                timeout = action.get("timeout", self.config.timeout)
                await self.page.wait_for_selector(selector, timeout=timeout)
                logger.info(f"Waited for selector: {selector}")
                
            elif action_type == "get_text":
                selector = action.get("selector", "")
                text = await self.page.text_content(selector)
                logger.info(f"Got text from {selector}: {text}")
                return text
                
            elif action_type == "get_attribute":
                selector = action.get("selector", "")
                attribute = action.get("attribute", "")
                value = await self.page.get_attribute(selector, attribute)
                logger.info(f"Got attribute {attribute} from {selector}: {value}")
                return value
                
            elif action_type == "select":
                selector = action.get("selector", "select")
                value = action.get("value", "")
                await self.page.select_option(selector, value)
                logger.info(f"Selected '{value}' in {selector}")
                
            else:
                logger.warning(f"Unknown action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            raise
    
    async def execute_assertion(self, assertion: Assertion) -> AssertionResult:
        """
        Execute assertion
        
        Args:
            assertion: Assertion to execute
            
        Returns:
            AssertionResult
        """
        if not self.assertion_executor:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            console.print(f"[yellow]✅ Assertion: {assertion.type.value}[/yellow]")
            if assertion.expected:
                console.print(f"[dim]   Expected: {assertion.expected}[/dim]")
            if assertion.selector:
                console.print(f"[dim]   Selector: {assertion.selector}[/dim]")
            
            result = await self.assertion_executor.execute(assertion)
            
            if result.passed:
                console.print(f"[green]✓ Assertion passed[/green]")
            else:
                console.print(f"[red]✗ Assertion failed: {result.error_message}[/red]")
                if result.actual_value is not None:
                    console.print(f"[dim]   Actual: {result.actual_value}[/dim]")
            
            logger.info(f"Assertion result: {result.get_summary()}")
            return result
            
        except Exception as e:
            logger.error(f"Assertion execution failed: {e}")
            raise
    
    async def take_screenshot(self, path: Optional[str] = None) -> str:
        """Take screenshot"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        if not path:
            path = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
        
        try:
            await self.page.screenshot(path=path, full_page=True)
            logger.info(f"Screenshot saved: {path}")
            return path
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get page information"""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        try:
            return {
                "title": await self.page.title(),
                "url": self.page.url,
                "viewport": await self.page.viewport_size(),
            }
            
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            raise
    
    async def close(self) -> None:
        """Close browser"""
        try:
            console.print("[yellow]🌙 Closing browser...[/yellow]")
            
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            console.print("[green]✓ Browser closed[/green]")
            logger.info("Browser closed")
            
        except Exception as e:
            console.print(f"[red]✗ Failed to close browser: {e}[/red]")
            logger.error(f"Failed to close browser: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager"""
        await self.close()