"""テストランナーのユニットテスト"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from kotoba.config import KotobaConfig, LLMConfig, PlaywrightConfig, TestConfig
from kotoba.runner import TestRunner


@pytest.fixture
def mock_config():
    """テスト用設定"""
    return KotobaConfig(
        llm=LLMConfig(model_name="test-model"),
        playwright=PlaywrightConfig(headless=True),
        test=TestConfig(output_dir=Path("/tmp/test_output"))
    )


@pytest.fixture
def mock_runner(mock_config):
    """テスト用ランナー"""
    return TestRunner(mock_config)


@pytest.mark.asyncio
async def test_execute_step_success(mock_runner):
    """ステップ実行成功テスト"""
    # LLMとブラウザをモック
    mock_runner.llm_manager.translate_to_actions = MagicMock(
        return_value={"action_type": "click", "selector": "button"}
    )
    mock_runner.browser_manager.execute_action = AsyncMock()
    
    step = {
        "instruction": "ボタンをクリックする",
        "description": "テストボタンクリック"
    }
    
    result = await mock_runner._execute_step(step, 0)
    
    assert result["status"] == "passed"
    assert result["natural_language"] == "ボタンをクリックする"
    assert result["action"]["action_type"] == "click"


@pytest.mark.asyncio
async def test_execute_step_failure(mock_runner):
    """ステップ実行失敗テスト"""
    # LLMは成功、ブラウザ操作で失敗
    mock_runner.llm_manager.translate_to_actions = MagicMock(
        return_value={"action_type": "click", "selector": "button"}
    )
    mock_runner.browser_manager.execute_action = AsyncMock(
        side_effect=Exception("Element not found")
    )
    
    step = {
        "instruction": "存在しないボタンをクリックする",
        "description": "失敗テスト"
    }
    
    result = await mock_runner._execute_step(step, 0)
    
    assert result["status"] == "failed"
    assert "Element not found" in result["error"]


def test_load_test_file_yaml(mock_runner, tmp_path):
    """YAMLテストファイル読み込みテスト"""
    test_file = tmp_path / "test.yaml"
    test_content = """
name: "Test Suite"
test_cases:
  - name: "Test Case 1"
    steps:
      - instruction: "テスト指示1"
"""
    test_file.write_text(test_content, encoding='utf-8')
    
    result = mock_runner._load_test_file(test_file)
    
    assert result["name"] == "Test Suite"
    assert len(result["test_cases"]) == 1
    assert result["test_cases"][0]["name"] == "Test Case 1"


def test_load_test_file_json(mock_runner, tmp_path):
    """JSONテストファイル読み込みテスト"""
    test_file = tmp_path / "test.json"
    test_content = '''
{
  "name": "JSON Test Suite",
  "test_cases": [
    {
      "name": "JSON Test Case",
      "steps": [
        {"instruction": "JSON指示1"}
      ]
    }
  ]
}
'''
    test_file.write_text(test_content, encoding='utf-8')
    
    result = mock_runner._load_test_file(test_file)
    
    assert result["name"] == "JSON Test Suite"
    assert len(result["test_cases"]) == 1


def test_load_test_file_unsupported_format(mock_runner, tmp_path):
    """サポートされていないファイル形式テスト"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("invalid content")
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        mock_runner._load_test_file(test_file)


@pytest.mark.asyncio
async def test_take_failure_screenshot(mock_runner):
    """失敗時スクリーンショットテスト"""
    mock_runner.browser_manager.take_screenshot = AsyncMock(return_value="screenshot.png")
    
    result = await mock_runner._take_failure_screenshot("test_case", 1)
    
    assert result.name.startswith("failure_test_case_1_")
    assert result.suffix == ".png"
    mock_runner.browser_manager.take_screenshot.assert_called_once()


@pytest.mark.asyncio
async def test_take_failure_screenshot_error(mock_runner):
    """スクリーンショット失敗テスト"""
    mock_runner.browser_manager.take_screenshot = AsyncMock(
        side_effect=Exception("Screenshot failed")
    )
    
    result = await mock_runner._take_failure_screenshot("test_case", 1)
    
    assert result.name == "screenshot_failed.png"