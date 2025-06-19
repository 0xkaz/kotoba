"""Configuration management module"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import yaml
from pathlib import Path


class LLMConfig(BaseModel):
    """LLM model configuration"""
    model_name: str = Field(default="rinna/japanese-gpt-neox-3.6b")
    device: str = Field(default="auto")
    max_length: int = Field(default=512)
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)


class PlaywrightConfig(BaseModel):
    """Playwright configuration"""
    browser: str = Field(default="chromium")
    headless: bool = Field(default=True)
    timeout: int = Field(default=30000)
    viewport: Dict[str, int] = Field(default={"width": 1280, "height": 720})


class TestConfig(BaseModel):
    """Test execution configuration"""
    base_url: str = Field(default="")
    screenshot_on_failure: bool = Field(default=True)
    output_dir: Path = Field(default=Path("outputs"))
    retry_count: int = Field(default=3)


class KotobaConfig(BaseModel):
    """Overall kotoba tool configuration"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    playwright: PlaywrightConfig = Field(default_factory=PlaywrightConfig)
    test: TestConfig = Field(default_factory=TestConfig)
    log_level: str = Field(default="INFO")


def load_config(config_path: Path) -> KotobaConfig:
    """Load configuration file"""
    if not config_path.exists():
        return KotobaConfig()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    return KotobaConfig(**config_data)


def save_config(config: KotobaConfig, config_path: Path) -> None:
    """Save configuration file"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False, allow_unicode=True)