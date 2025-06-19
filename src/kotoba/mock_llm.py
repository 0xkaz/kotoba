"""Mock LLM Manager (for testing)"""

from typing import Dict, Any
from loguru import logger


class MockLLMManager:
    """Mock for running tests without LLM model"""
    
    def __init__(self, config):
        self.config = config
        logger.info("Using Mock LLM Manager (no model loading)")
        
    def load_model(self) -> None:
        """Load model (mock)"""
        logger.info("Mock: Model loaded successfully")
    
    def translate_to_actions(self, natural_language: str) -> Dict[str, Any]:
        """Convert natural language to Playwright actions (mock)"""
        logger.info(f"Mock: Translating instruction: {natural_language}")
        
        # Simple rule-based conversion
        text_lower = natural_language.lower()
        
        # Navigation patterns: Japanese "移動" (move), "に移動" (move to), English "navigate"
        if "移動" in natural_language or "navigate" in text_lower or "に移動" in natural_language:
            # Extract URL (simplified)
            import re
            url_match = re.search(r'https?://[^\s]+', natural_language)
            url = url_match.group() if url_match else "https://example.com"
            return {"action_type": "navigate", "url": url}
            
        # Click patterns: Japanese "クリック" (click), "押す" (press), English "click"
        elif "クリック" in natural_language or "click" in text_lower or "押す" in natural_language:
            # Infer selector
            # Button patterns: Japanese "ボタン", English "button"
            if "ボタン" in natural_language or "button" in text_lower:
                selector = "button"
            # Link patterns: Japanese "リンク", English "link"
            elif "リンク" in natural_language or "link" in text_lower:
                selector = "a"
            elif "Add Element" in natural_language:
                selector = "button:has-text('Add Element')"
            elif "Login" in natural_language:
                selector = "button[type='submit'], input[type='submit']"
            elif "Delete" in natural_language:
                selector = "button:has-text('Delete')"
            else:
                # Infer selector from text content
                import re
                text_match = re.search(r'「([^」]+)」|"([^"]+)"|([A-Za-z][A-Za-z\s]+)', natural_language)
                if text_match:
                    text = text_match.group(1) or text_match.group(2) or text_match.group(3)
                    selector = f"*:has-text('{text}')"
                else:
                    selector = "button, a, input[type='submit']"
            
            return {"action_type": "click", "selector": selector}
            
        # Input patterns: Japanese "入力" (input), English "type"
        elif "入力" in natural_language or "type" in text_lower:
            # Extract input content
            import re
            
            # Infer field name
            # Username patterns: Japanese "ユーザー名", English "username"
            if "ユーザー名" in natural_language or "username" in text_lower:
                selector = "input[name='username'], input[id='username']"
            # Password patterns: Japanese "パスワード", English "password"
            elif "パスワード" in natural_language or "password" in text_lower:
                selector = "input[type='password']"
            # Search pattern: Japanese "検索" (search)
            elif "検索" in natural_language or "search" in text_lower:
                selector = "input[type='search'], input[name='q'], input[name='search'], input[placeholder*='search' i]"
            else:
                selector = "input[type='text'], input:not([type]), textarea"
            
            # Extract input text
            text_match = re.search(r'「([^」]+)」|"([^"]+)"|に\s*([^\s]+)\s*と|を\s*([^\s]+)\s*と', natural_language)
            if text_match:
                text = text_match.group(1) or text_match.group(2) or text_match.group(3) or text_match.group(4)
            else:
                text = "test input"
                
            return {"action_type": "type", "selector": selector, "text": text}
            
        # Wait patterns: Japanese "待つ" (wait), English "wait"
        elif "待つ" in natural_language or "wait" in text_lower:
            # Extract time
            import re
            # Match Japanese "秒" (seconds) or English "second(s)"
            time_match = re.search(r'(\d+)\s*(?:秒|seconds?)', natural_language)
            timeout = int(time_match.group(1)) * 1000 if time_match else 3000
            return {"action_type": "wait", "timeout": timeout}
            
        # Screenshot patterns: Japanese "スクリーンショット", English "screenshot"
        elif "スクリーンショット" in natural_language or "screenshot" in text_lower:
            return {"action_type": "screenshot", "path": "test_screenshot.png"}
            
        # Verification patterns: Japanese "確認" (confirm/verify), English "check", "verify"
        elif "確認" in natural_language or "check" in text_lower or "verify" in text_lower:
            return {"action_type": "wait", "timeout": 1000}  # Wait briefly for verification
            
        # Back navigation patterns: Japanese "戻る" (go back), English "back"
        elif "戻る" in natural_language or "back" in text_lower:
            return {"action_type": "navigate", "url": "back"}
            
        # Selection patterns: Japanese "選択" (select), English "select"
        elif "選択" in natural_language or "select" in text_lower:
            # Dropdown selection
            value_match = re.search(r'「([^」]+)」|"([^"]+)"|([A-Za-z0-9]+)', natural_language)
            value = value_match.group(1) or value_match.group(2) or value_match.group(3) if value_match else "Option 1"
            return {"action_type": "select", "selector": "select", "value": value}
            
        else:
            # Treat unknown instructions as click
            return {"action_type": "click", "selector": "*"}
    
    def unload_model(self) -> None:
        """Unload model (mock)"""
        logger.info("Mock: Model unloaded")