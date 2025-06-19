"""LLM model management module"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from typing import Optional, Dict, Any
from loguru import logger
from tqdm import tqdm
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
import time
from .config import LLMConfig

console = Console()


class LLMManager:
    """LLM model management class"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.pipeline: Optional[pipeline] = None
        
    def load_model(self) -> None:
        """Load model (with progress display)"""
        try:
            console.print(f"[bold cyan]🤖 Starting LLM model load: {self.config.model_name}[/bold cyan]")
            
            # Device configuration
            if self.config.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.config.device
                
            console.print(f"[yellow]⚙️  Device: {device}[/yellow]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                
                # Load tokenizer
                task = progress.add_task("📖 Downloading tokenizer...", total=100)
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.config.model_name,
                    trust_remote_code=True
                )
                progress.update(task, advance=100)
                
                # Load model
                task = progress.add_task("🧞 Downloading model...", total=100)
                
                # Display model size in advance
                model_size = self._estimate_model_size()
                if model_size:
                    console.print(f"[dim]Estimated size: {model_size}[/dim]")
                
                # Download start time
                start_time = time.time()
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.config.model_name,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    device_map="auto" if device == "cuda" else None,
                    trust_remote_code=True
                )
                
                # Display download time
                elapsed = time.time() - start_time
                progress.update(task, advance=100)
                console.print(f"[green]✓ Model download complete ({elapsed:.1f} seconds)[/green]")
                
                # Create pipeline
                task = progress.add_task("🔧 Building pipeline...", total=100)
                
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=0 if device == "cuda" else -1,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32
                )
                progress.update(task, advance=100)
            
            console.print("[bold green]✨ Model loading complete![/bold green]")
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text"""
        if not self.pipeline:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Default parameters
        generation_kwargs = {
            "max_length": self.config.max_length,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "do_sample": True,
            "pad_token_id": self.tokenizer.eos_token_id,
            "return_full_text": False,
        }
        
        # Override with user-specified parameters
        generation_kwargs.update(kwargs)
        
        try:
            result = self.pipeline(prompt, **generation_kwargs)
            generated_text = result[0]["generated_text"]
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise
    
    def translate_to_actions(self, natural_language: str) -> Dict[str, Any]:
        """Convert natural language to Playwright actions"""
        prompt = f"""
Convert the following natural language instruction into executable Playwright actions.
Output in JSON format, including action_type (click, type, wait, navigate, screenshot, etc.) and parameters.

Natural language instruction: {natural_language}

Conversion result (JSON format):
"""
        
        try:
            response = self.generate_text(prompt, max_length=256)
            
            # Attempt simple JSON parsing (more robust parsing needed in actual implementation)
            import json
            import re
            
            # Extract JSON portion
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                action_data = json.loads(json_match.group())
                return action_data
            else:
                # Fallback: basic action estimation
                return self._fallback_action_parsing(natural_language)
                
        except Exception as e:
            logger.warning(f"LLM action conversion failed: {e}")
            return self._fallback_action_parsing(natural_language)
    
    def _fallback_action_parsing(self, text: str) -> Dict[str, Any]:
        """Fallback parsing when LLM fails"""
        text_lower = text.lower()
        
        if "click" in text_lower or "press" in text_lower or "tap" in text_lower:
            return {"action_type": "click", "selector": "button"}
        elif "type" in text_lower or "input" in text_lower or "enter" in text_lower:
            return {"action_type": "type", "selector": "input", "text": ""}
        elif "wait" in text_lower or "pause" in text_lower:
            return {"action_type": "wait", "timeout": 3000}
        elif "navigate" in text_lower or "go to" in text_lower or "open" in text_lower:
            return {"action_type": "navigate", "url": ""}
        else:
            return {"action_type": "unknown", "original_text": text}
    
    def _estimate_model_size(self) -> Optional[str]:
        """Estimate model size"""
        model_sizes = {
            "rinna/japanese-gpt-neox-3.6b": "~7GB",
            "cyberagent/open-calm-3b": "~6GB",
            "pfnet/plamo-13b": "~26GB",
            "pfnet/plamo-13b-instruct": "~26GB",
            "Qwen/Qwen2-1.5B-Instruct": "~3GB",
            "microsoft/phi-2": "~5GB",
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0": "~2GB",
        }
        return model_sizes.get(self.config.model_name)
    
    def unload_model(self) -> None:
        """Unload model and free memory"""
        console.print("[yellow]🧠 Unloading model...[/yellow]")
        
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        console.print("[green]✓ Memory freed[/green]")
        logger.info("Model unloaded and memory cleared")