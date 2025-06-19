"""設定管理のユニットテスト"""

import pytest
import yaml
from pathlib import Path

from kotoba.config import (
    LLMConfig, PlaywrightConfig, TestConfig, KotobaConfig,
    load_config, save_config
)


def test_llm_config_defaults():
    """LLM設定のデフォルト値テスト"""
    config = LLMConfig()
    
    assert config.model_name == "rinna/japanese-gpt-neox-3.6b"
    assert config.device == "auto"
    assert config.max_length == 512
    assert config.temperature == 0.7
    assert config.top_p == 0.9


def test_playwright_config_defaults():
    """Playwright設定のデフォルト値テスト"""
    config = PlaywrightConfig()
    
    assert config.browser == "chromium"
    assert config.headless is True
    assert config.timeout == 30000
    assert config.viewport == {"width": 1280, "height": 720}


def test_test_config_defaults():
    """テスト設定のデフォルト値テスト"""
    config = TestConfig()
    
    assert config.base_url == ""
    assert config.screenshot_on_failure is True
    assert config.output_dir == Path("outputs")
    assert config.retry_count == 3


def test_kotoba_config_defaults():
    """kotoba設定のデフォルト値テスト"""
    config = KotobaConfig()
    
    assert isinstance(config.llm, LLMConfig)
    assert isinstance(config.playwright, PlaywrightConfig)
    assert isinstance(config.test, TestConfig)
    assert config.log_level == "INFO"


def test_load_config_file_not_exists():
    """存在しない設定ファイルの読み込みテスト"""
    config = load_config(Path("nonexistent.yaml"))
    
    # デフォルト設定が返される
    assert isinstance(config, KotobaConfig)
    assert config.llm.model_name == "rinna/japanese-gpt-neox-3.6b"


def test_load_config_valid_file(tmp_path):
    """有効な設定ファイルの読み込みテスト"""
    config_file = tmp_path / "test_config.yaml"
    config_data = {
        "llm": {
            "model_name": "test-model",
            "temperature": 0.5
        },
        "playwright": {
            "browser": "firefox",
            "headless": False
        },
        "log_level": "DEBUG"
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f)
    
    config = load_config(config_file)
    
    assert config.llm.model_name == "test-model"
    assert config.llm.temperature == 0.5
    assert config.playwright.browser == "firefox"
    assert config.playwright.headless is False
    assert config.log_level == "DEBUG"


def test_save_config(tmp_path):
    """設定ファイル保存テスト"""
    config = KotobaConfig(
        llm=LLMConfig(model_name="custom-model", temperature=0.8),
        playwright=PlaywrightConfig(browser="webkit", headless=False),
        log_level="WARNING"
    )
    
    config_file = tmp_path / "saved_config.yaml"
    save_config(config, config_file)
    
    # ファイルが作成されていることを確認
    assert config_file.exists()
    
    # 保存された内容を確認
    loaded_config = load_config(config_file)
    assert loaded_config.llm.model_name == "custom-model"
    assert loaded_config.llm.temperature == 0.8
    assert loaded_config.playwright.browser == "webkit"
    assert loaded_config.playwright.headless is False
    assert loaded_config.log_level == "WARNING"


def test_config_validation():
    """設定値の検証テスト"""
    # 正常なケース
    config = LLMConfig(
        model_name="valid-model",
        temperature=0.5,
        top_p=0.9
    )
    assert config.temperature == 0.5
    
    # 異常なケース（pydanticが型チェックする）
    with pytest.raises(ValueError):
        LLMConfig(temperature="invalid")  # 文字列は不正