"""
Assertion functionality implementation

This module provides test verification features for kotoba.
Enables natural Japanese assertion descriptions for comprehensive test validation.
"""

from enum import Enum
from typing import Optional, Union, Dict, Any, List
from pydantic import BaseModel
import re
import asyncio
from playwright.async_api import Page


class AssertionType(Enum):
    """Supported assertion types"""
    
    # Text-related assertions
    TEXT_EXISTS = "text_exists"          # Text exists on page
    TEXT_NOT_EXISTS = "text_not_exists"  # Text does not exist on page
    TEXT_EQUALS = "text_equals"          # Text exactly matches
    TEXT_CONTAINS = "text_contains"      # Text contains substring
    TEXT_MATCHES = "text_matches"        # Text matches regex pattern
    
    # Element-related assertions
    ELEMENT_EXISTS = "element_exists"    # Element exists
    ELEMENT_NOT_EXISTS = "element_not_exists"  # Element does not exist
    ELEMENT_VISIBLE = "element_visible"  # Element is visible
    ELEMENT_HIDDEN = "element_hidden"    # Element is hidden
    ELEMENT_COUNT = "element_count"      # Element count verification
    
    # Attribute-related assertions
    ATTRIBUTE_EQUALS = "attribute_equals"     # Attribute value equals
    ATTRIBUTE_CONTAINS = "attribute_contains" # Attribute value contains
    ATTRIBUTE_EXISTS = "attribute_exists"    # Attribute exists
    
    # Page-related assertions
    URL_EQUALS = "url_equals"           # URL exactly matches
    URL_CONTAINS = "url_contains"       # URL contains substring
    URL_MATCHES = "url_matches"         # URL matches regex pattern
    URL_STARTS_WITH = "url_starts_with" # URL starts with string
    URL_ENDS_WITH = "url_ends_with"     # URL ends with string
    
    TITLE_EQUALS = "title_equals"       # Title exactly matches
    TITLE_CONTAINS = "title_contains"   # Title contains substring
    TITLE_MATCHES = "title_matches"     # Title matches regex pattern
    
    # Form-related assertions
    INPUT_VALUE_EQUALS = "input_value_equals"     # Input value equals
    INPUT_VALUE_CONTAINS = "input_value_contains" # Input value contains
    CHECKBOX_CHECKED = "checkbox_checked"         # Checkbox is checked
    CHECKBOX_UNCHECKED = "checkbox_unchecked"     # Checkbox is unchecked
    
    # State-related assertions
    ELEMENT_ENABLED = "element_enabled"   # Element is enabled
    ELEMENT_DISABLED = "element_disabled" # Element is disabled


class Assertion(BaseModel):
    """Assertion definition"""
    
    type: AssertionType
    selector: Optional[str] = None
    expected: Optional[Union[str, bool, int, float]] = None
    attribute: Optional[str] = None
    timeout: int = 5000  # Timeout in milliseconds
    ignore_case: bool = False  # Ignore case sensitivity
    wait_for: bool = True  # Wait for element to appear
    
    class Config:
        # Keep enum objects instead of converting to values
        use_enum_values = False


class AssertionResult(BaseModel):
    """Assertion execution result"""
    
    passed: bool
    assertion: Assertion
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    execution_time_ms: float = 0
    
    def get_summary(self) -> str:
        """Generate result summary string"""
        status = "✅ Passed" if self.passed else "❌ Failed"
        message = f"{status}: {self.assertion.type.value}"
        
        if not self.passed and self.error_message:
            message += f" - {self.error_message}"
            
        if self.actual_value is not None:
            message += f" (actual: {self.actual_value})"
            
        return message


class AssertionPatternMatcher:
    """Parse natural language assertion instructions using pattern matching"""
    
    # Japanese pattern definitions
    PATTERNS = [
        # Text existence verification - flexible quote support and politeness levels
        (r"(.+?)が(?:表示されて|出て|見えて)?(?:いる|いること|いることを)(?:確認|チェック|検証)(?:する|します|してください|お願いします)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""](.+?)[」""]が(?:表示|存在|出現)(?:している|することを|することを確認)(?:する|します|してください|お願いします)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""](.+?)[」""]という(?:テキスト|文字|メッセージ)が(?:表示|存在)(?:している|することを確認)(?:する|します|してください|お願いします)?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # Text non-existence verification - flexible quote support and politeness levels
        (r"(.+?)が(?:表示されて|出て|見えて)?(?:いない|いないこと|いないことを)(?:確認|チェック|検証)(?:する|します|してください|お願いします)?", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        (r"[「""](.+?)[」""]が(?:表示されて|存在して)?(?:いない|いないことを確認)(?:する|します|してください|お願いします)?", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        (r"[「""](.+?)[」""]という(?:テキスト|文字|メッセージ)が(?:表示されて|存在して)?(?:いない|いないことを確認)(?:する|します|してください|お願いします)?", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        
        # Element existence verification
        (r"(.+?)(?:ボタン|リンク|フィールド|要素|項目)が(?:存在|表示|出現)(?:している|することを確認)", 
         AssertionType.ELEMENT_EXISTS, "selector"),
        (r"(.+?)が(?:見える|表示されている|存在することを確認)", 
         AssertionType.ELEMENT_VISIBLE, "selector"),
        
        # Element non-existence verification
        (r"(.+?)(?:ボタン|リンク|フィールド|要素|項目)が(?:存在して|表示されて)?(?:いない|いないことを確認)", 
         AssertionType.ELEMENT_NOT_EXISTS, "selector"),
        (r"(.+?)が(?:見えない|表示されていない|存在しないことを確認)", 
         AssertionType.ELEMENT_HIDDEN, "selector"),
        
        # URL verification - flexible quote support and politeness levels
        (r"URLが(.+?)(?:で終わる|になっている|であることを確認)(?:する|します|してください|お願いします)?", 
         AssertionType.URL_CONTAINS, "url"),
        (r"URLに[「""]?(.+?)[」""]?が含まれる(?:ことを確認)?(?:する|します|してください|お願いします)?", 
         AssertionType.URL_CONTAINS, "url"),
        (r"(?:ページの)?URLが[「""](.+?)[」""](?:と一致|であることを確認)(?:する|します|してください|お願いします)?", 
         AssertionType.URL_EQUALS, "url"),
        (r"URLが[「""]?(.+?)[」""]?で始まることを確認(?:する|します|してください|お願いします)?", 
         AssertionType.URL_STARTS_WITH, "url"),
        (r"URLが[「""]?(.+?)[」""]?で終わることを確認(?:する|します|してください|お願いします)?", 
         AssertionType.URL_ENDS_WITH, "url"),
        
        # Title verification - flexible quote support and politeness levels
        (r"(?:ページ)?タイトルが[「""](.+?)[」""](?:であることを確認|と一致)(?:する|します|してください|お願いします)?", 
         AssertionType.TITLE_EQUALS, "title"),
        (r"(?:ページ)?タイトルに[「""]?(.+?)[」""]?が含まれる(?:ことを確認)?(?:する|します|してください|お願いします)?", 
         AssertionType.TITLE_CONTAINS, "title"),
        
        # Form element verification
        (r"(.+?)(?:フィールド|入力欄)の値が「(.+?)」(?:であることを確認|と一致)", 
         AssertionType.INPUT_VALUE_EQUALS, "selector_value"),
        (r"(.+?)(?:チェックボックス|チェック)が(?:チェックされて|選択されて)(?:いる|いることを確認)", 
         AssertionType.CHECKBOX_CHECKED, "selector"),
        (r"(.+?)(?:チェックボックス|チェック)が(?:チェックされて|選択されて)?(?:いない|いないことを確認)", 
         AssertionType.CHECKBOX_UNCHECKED, "selector"),
        
        # Element count verification
        (r"(.+?)が(\d+)(?:個|件|つ)(?:表示|存在)(?:している|することを確認)", 
         AssertionType.ELEMENT_COUNT, "selector_count"),
        (r"(.+?)の(?:数が|件数が)(\d+)(?:であることを確認|と一致)", 
         AssertionType.ELEMENT_COUNT, "selector_count"),
        
        # HTML element verification
        (r"(h[1-6]|div|span|p|table|form|input|button)要素が(?:表示されて|存在して)?(?:いる|いることを確認)", 
         AssertionType.ELEMENT_EXISTS, "html_element"),
        (r"(h[1-6]|div|span|p|table|form|input|button)タグが(?:表示されて|存在して)?(?:いる|いることを確認)", 
         AssertionType.ELEMENT_EXISTS, "html_element"),
        
        # English patterns
        (r"(?:verify|check|confirm|assert)(?:\s+that)?\s+[\"'](.+?)[\"']\s+(?:is|exists?|appears?|is\s+(?:visible|displayed|present))", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:verify|check|confirm|assert)(?:\s+that)?\s+[\"'](.+?)[\"']\s+(?:is\s+not|does\s+not\s+exist|is\s+(?:not\s+visible|hidden|absent))", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        (r"(?:verify|check|confirm|assert)(?:\s+that)?\s+(?:the\s+)?url\s+contains\s+[\"'](.+?)[\"']", 
         AssertionType.URL_CONTAINS, "url"),
        (r"(?:verify|check|confirm|assert)(?:\s+that)?\s+(?:the\s+)?url\s+starts\s+with\s+[\"'](.+?)[\"']", 
         AssertionType.URL_STARTS_WITH, "url"),
        (r"(?:verify|check|confirm|assert)(?:\s+that)?\s+(?:the\s+)?url\s+ends\s+with\s+[\"'](.+?)[\"']", 
         AssertionType.URL_ENDS_WITH, "url"),
        (r"(?:verify|check|confirm|assert)(?:\s+that)?\s+(?:the\s+)?title\s+contains\s+[\"'](.+?)[\"']", 
         AssertionType.TITLE_CONTAINS, "title"),
        (r"(?:verify|check|confirm|assert)(?:\s+that)?\s+(?:the\s+)?title\s+(?:is|equals)\s+[\"'](.+?)[\"']", 
         AssertionType.TITLE_EQUALS, "title"),
        
        # Chinese patterns
        (r"(?:验证|检查|确认|断言)[\"'""](.+?)[\"'""](?:存在|显示|出现)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:验证|检查|确认|断言)[\"'""](.+?)[\"'""](?:不存在|未显示|不出现)", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        (r"(?:验证|检查|确认|断言)(?:网址|URL)包含[\"'""](.+?)[\"'""]", 
         AssertionType.URL_CONTAINS, "url"),
        (r"(?:验证|检查|确认|断言)(?:网址|URL)以[\"'""](.+?)[\"'""]开头", 
         AssertionType.URL_STARTS_WITH, "url"),
        (r"(?:验证|检查|确认|断言)(?:网址|URL)以[\"'""](.+?)[\"'""]结尾", 
         AssertionType.URL_ENDS_WITH, "url"),
        (r"(?:验证|检查|确认|断言)标题包含[\"'""](.+?)[\"'""]", 
         AssertionType.TITLE_CONTAINS, "title"),
        (r"(?:验证|检查|确认|断言)标题(?:是|等于)[\"'""](.+?)[\"'""]", 
         AssertionType.TITLE_EQUALS, "title"),
        
        # === 頻出パターン追加 ===
        
        # 口語・疑問形パターン
        (r"[「""]?(.+?)[」""]?(?:って|という(?:の|もの))(?:が|は)(?:あるか|存在するか|見えるか)(?:確認|チェック)(?:する|します|してください)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:は|が)(?:表示されて|見えて)(?:いますか|いるでしょうか|いるか)(?:？|\?)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:ちゃんと|きちんと|正しく)(?:表示|出て)(?:る|いる)(?:か|かな|だろうか)(?:確認|見る)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:表示されてる|出てる|見える)(?:よね|ね|な)(?:？|\?)?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # ビジネス・フォーマル表現
        (r"[「""]?(.+?)[」""]?(?:が|の)(?:表示状況|存在状況|可視性)(?:を|について)(?:確認|検証|チェック)(?:する|します|してください)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:について|に関して)(?:表示|存在)(?:確認|検証|チェック)(?:を行う|を実施)(?:する|します|してください)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:の|が)(?:画面表示|画面出力|レンダリング)(?:を|について)(?:確認|検証)(?:する|します|してください)?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 条件付き・仮定表現
        (r"もし[「""]?(.+?)[」""]?(?:が|って)(?:表示|存在)(?:されて|して)?(?:いる|いたら)(?:なら|場合)(?:確認|チェック)(?:する|します)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:正常に|適切に)(?:表示|出力|レンダリング)(?:されている|されてる)(?:こと|ことを)(?:確認|検証)(?:する|します)?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 感情・強調表現
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:間違いなく|確実に|絶対に)(?:表示|存在)(?:している|してる)(?:はず|だろう)(?:だから|なので)?(?:確認|チェック)(?:する|します)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:やっぱり|結局|案の定)(?:表示|出て)(?:いる|いた)(?:か|かな|だろうか)(?:確認|見る)(?:します)?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # URL関連の頻出パターン
        (r"(?:現在の|今の|このページの)?(?:URL|アドレス|リンク)(?:が|に|で)[「""]?(.+?)[」""]?(?:が|を)(?:含んで|含ま|入って)(?:いる|いること|いることを)(?:確認|チェック|検証)(?:する|します|してください)?", 
         AssertionType.URL_CONTAINS, "url"),
        (r"(?:ページの|サイトの)?(?:URL|アドレス)(?:が|は)[「""]?(.+?)[」""]?(?:から|で)(?:始まって|スタートして)(?:いる|いること|いることを)(?:確認|チェック|検証)(?:する|します|してください)?", 
         AssertionType.URL_STARTS_WITH, "url"),
        (r"(?:URL|アドレス)(?:の|が)(?:末尾|最後)(?:が|は|に)[「""]?(.+?)[」""]?(?:で|と)(?:終わって|なって)(?:いる|いること|いることを)(?:確認|チェック|検証)(?:する|します|してください)?", 
         AssertionType.URL_ENDS_WITH, "url"),
        
        # タイトル関連の頻出パターン  
        (r"(?:ページの|サイトの|この)?(?:タイトル|題名|見出し)(?:が|に|で)[「""]?(.+?)[」""]?(?:が|を)(?:含んで|含ま|入って)(?:いる|いること|いることを)(?:確認|チェック|検証)(?:する|します|してください)?", 
         AssertionType.TITLE_CONTAINS, "title"),
        (r"(?:ページの|サイトの)?(?:タイトル|題名|見出し)(?:が|は)[「""]?(.+?)[」""]?(?:と|に|で)(?:一致|同じ|マッチ)(?:している|してる|することを)(?:確認|チェック|検証)(?:する|します|してください)?", 
         AssertionType.TITLE_EQUALS, "title"),
        
        # 非存在確認の頻出パターン
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:表示されて|出て|見えて)?(?:いない|ない)(?:こと|ことを|はず)(?:を|について)?(?:確認|チェック|検証)(?:する|します|してください)?", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:画面に|ページに)(?:表示されて|出て|見えて)?(?:いない|ない|存在しない)(?:はず|だろう|と思う)(?:だから|なので)?(?:確認|チェック)(?:する|します)?", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:なんて|という)(?:テキスト|文字|メッセージ)(?:が|は)(?:表示されて|出て)?(?:いない|ない)(?:はず|だろう)(?:確認|チェック)(?:する|します)?", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        
        # より自然な英語表現
        (r"(?:make sure|ensure|verify|check)(?:\s+that)?\s+[\"'](.+?)[\"']\s+(?:is\s+(?:present|shown|displayed|visible|there)|(?:appears|exists|shows up))", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:make sure|ensure|verify|check)(?:\s+that)?\s+[\"'](.+?)[\"']\s+(?:is\s+not\s+(?:present|shown|displayed|visible|there)|(?:does\s+not\s+(?:appear|exist|show up)))", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        (r"(?:i\s+(?:should|need to|want to)\s+)?(?:see|find|locate)\s+[\"'](.+?)[\"']\s+(?:on\s+(?:the\s+)?(?:page|screen))?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:the\s+)?(?:page|screen)\s+(?:should|must|needs to)\s+(?:show|display|contain)\s+[\"'](.+?)[\"']", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 中国語の頻出パターン
        (r"(?:检查|确认|验证)[\"'""](.+?)[\"'""](?:是否|有没有)(?:显示|出现|存在)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:页面|屏幕)(?:上|中)(?:应该|必须|需要)(?:显示|包含|有)[\"'""](.+?)[\"'""]", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:确保|保证)[\"'""](.+?)[\"'""](?:在|于)(?:页面|屏幕)(?:上|中)(?:显示|出现)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # === 方言・地域表現パターン ===
        
        # 関西弁
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:出てる|見える)(?:で|やん|やんか|わ|な)(?:？|\?)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:ちゃんと|きちんと)(?:表示されてる|出てる)(?:か|やろか|やん)(?:確認|見る)(?:し|しい|してや)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:表示されとる|出とる)(?:か|やろ|わ)(?:確認|チェック)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 東北弁
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:出てる|見える)(?:べ|だべ|ぺ)(?:？|\?)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:ちゃんと|きちんと)(?:表示されてる|出てる)(?:べ|だべ)(?:か|が)(?:確認|見る)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 九州弁
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:出てる|見える)(?:と|ばい|たい)(?:？|\?)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:ちゃんと|きちんと)(?:表示されてる|出てる)(?:と|ばい)(?:確認|見る)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # === 感情表現・強調パターン ===
        
        # 驚き・発見
        (r"(?:あっ|おっ|えっ)[「""]?(.+?)[」""]?(?:が|って)(?:表示されてる|出てる|見える)(?:じゃん|やん|ね)(?:！|!)?(?:確認|チェック)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:やっぱり|案の定|思った通り)[「""]?(.+?)[」""]?(?:が|って)(?:表示されてる|出てる|見える)(?:な|ね|わ)(?:確認|チェック)?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 不安・心配
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:本当に|ちゃんと|きちんと)(?:表示されてる|出てる|見える)(?:かな|だろうか|のかしら)(?:？|\?)?(?:確認|チェック)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:正しく|適切に|問題なく)(?:表示されてる|出てる|見える)(?:か|かな)(?:不安|心配)(?:だから|なので)(?:確認|チェック)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 確信・断定
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:絶対に|間違いなく|確実に|必ず)(?:表示されてる|出てる|見える)(?:はず|に違いない|と思う)(?:確認|チェック)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:は|が)(?:当然|もちろん|当たり前に)(?:表示されてる|出てる|見える)(?:よね|でしょ|はず)(?:確認|チェック)?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # === 専門用語・業界表現 ===
        
        # IT・Web業界
        (r"[「""]?(.+?)[」""]?(?:が|の)(?:レンダリング|描画|出力)(?:が|は)(?:正常|適切|問題なし)(?:か|かどうか)(?:確認|検証|チェック)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|の)(?:DOM|HTML)(?:に|上で)(?:存在|表示)(?:している|してる)(?:か|かどうか)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:の|が)(?:UI|画面|インターフェース)(?:上|で)(?:表示|レンダリング)(?:されている|されてる)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # テスト・QA業界
        (r"[「""]?(.+?)[」""]?(?:が|の)(?:期待値|想定値|予期値)(?:通り|どおり)(?:表示|出力)(?:されている|されてる)(?:確認|検証|テスト)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:の|が)(?:表示|出力)(?:に関する|について)(?:回帰テスト|リグレッションテスト|検証)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|の)(?:アサーション|assertion)(?:として|で)(?:期待|想定)(?:されている|されてる)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # === 時制・状況表現 ===
        
        # 過去形
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:前は|以前は|昨日は)(?:表示されて|出て)(?:いた|た)(?:か|かな)(?:確認|チェック)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:さっき|先ほど|今しがた)(?:表示されて|出て)(?:いた|た)(?:はず|と思う)(?:確認|チェック)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 未来・予測
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:これから|今後|後で)(?:表示される|出る)(?:はず|だろう|と思う)(?:確認|チェック)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:きっと|おそらく|たぶん)(?:表示される|出る)(?:だろう|と思う)(?:確認|チェック)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # === 複合表現・長文パターン ===
        
        # 複数条件
        (r"(?:もし|if)[「""]?(.+?)[」""]?(?:が|って)(?:表示されて|出て)(?:いて|て)(?:、かつ|、そして|、なおかつ)(?:正常|適切|問題なし)(?:なら|であれば)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:表示されて|出て)(?:いる|る)(?:こと|の)(?:を|について)(?:前提|条件)(?:として|に)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 否定的推測
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:表示されて|出て)(?:いない|ない)(?:かも|かもしれない|可能性)(?:だから|なので)(?:確認|チェック)", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:が|って)(?:もう|既に)(?:表示されて|出て)(?:いない|ない)(?:はず|だろう|と思う)(?:確認|チェック)", 
         AssertionType.TEXT_NOT_EXISTS, "text"),
        
        # === 敬語・フォーマル表現強化 ===
        
        # 尊敬語
        (r"[「""]?(.+?)[」""]?(?:が|の)(?:表示|出力)(?:について|に関して)(?:ご確認|確認)(?:いただき|して)(?:たい|ください|お願いします)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:の|が)(?:表示状況|存在確認)(?:について|に関して)(?:お調べ|調査)(?:いただき|して)(?:たい|ください)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 謙譲語
        (r"[「""]?(.+?)[」""]?(?:が|の)(?:表示|存在)(?:について|に関して)(?:拝見|確認)(?:させて|して)(?:いただき|)(?:たい|ます)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[「""]?(.+?)[」""]?(?:の|が)(?:表示確認|存在確認)(?:を|について)(?:実施|行わ)(?:せて|して)(?:いただき|)(?:たい|ます)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # === URL/タイトル専門パターン強化 ===
        
        # URL詳細パターン
        (r"(?:現在表示中|表示されている|アクセス中)(?:の|している)(?:URL|アドレス|ページ)(?:が|に|で)[「""]?(.+?)[」""]?(?:が|を)(?:含んで|含有して|内包して)(?:いる|いること)(?:を|について)(?:確認|検証|チェック)", 
         AssertionType.URL_CONTAINS, "url"),
        (r"(?:ブラウザ|画面)(?:の|で)(?:アドレスバー|URL欄)(?:が|に|で)[「""]?(.+?)[」""]?(?:で|から)(?:開始|スタート)(?:している|してる)(?:確認|検証)", 
         AssertionType.URL_STARTS_WITH, "url"),
        (r"(?:WebページのURL|サイトアドレス)(?:が|は)[「""]?(.+?)[」""]?(?:で|にて)(?:終了|終わっ|完了)(?:している|してる)(?:確認|検証)", 
         AssertionType.URL_ENDS_WITH, "url"),
        
        # タイトル詳細パターン
        (r"(?:ブラウザ|タブ)(?:の|で)(?:タイトルバー|題名欄|ヘッダー)(?:が|に|で)[「""]?(.+?)[」""]?(?:が|を)(?:含んで|含有して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TITLE_CONTAINS, "title"),
        (r"(?:Webページ|サイト)(?:の|で)(?:メタタイトル|ページタイトル)(?:が|は)[「""]?(.+?)[」""]?(?:と|に)(?:完全一致|正確に一致)(?:している|してる)(?:確認|検証)", 
         AssertionType.TITLE_EQUALS, "title"),
        
        # === 英語表現大幅強化 ===
        
        # カジュアル英語
        (r"(?:yo|hey|ok|so),?\s*(?:is|does)\s*[\"'](.+?)[\"']\s*(?:show up|appear|display|show)(?:\s+(?:on|in)\s+(?:the\s+)?(?:page|screen))?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:can\s+(?:you|i|we)|could\s+(?:you|i|we))\s*(?:see|find|spot|locate)\s*[\"'](.+?)[\"'](?:\s+(?:on|in)\s+(?:the\s+)?(?:page|screen))?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:looks like|seems like|appears that)\s*[\"'](.+?)[\"']\s*(?:is|shows|appears|displays)(?:\s+(?:on|in)\s+(?:the\s+)?(?:page|screen))?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # ビジネス英語
        (r"(?:please\s+)?(?:validate|verify|confirm|check)\s+(?:that\s+)?(?:the\s+)?(?:text|content|element)\s+[\"'](.+?)[\"']\s+(?:is\s+)?(?:present|visible|displayed|shown)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:we\s+(?:need|must|should)\s+to\s+)?(?:ensure|verify|confirm)\s+(?:that\s+)?[\"'](.+?)[\"']\s+(?:appears|shows|displays|is\s+visible)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:it\s+is\s+)?(?:required|necessary|essential)\s+(?:that\s+)?[\"'](.+?)[\"']\s+(?:be|is)\s+(?:present|visible|displayed)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 質問形英語
        (r"(?:do\s+(?:you|we)|can\s+(?:you|we)|should\s+(?:we|i))\s+(?:see|find|verify|check)\s+(?:if\s+)?[\"'](.+?)[\"']\s+(?:is\s+)?(?:there|present|visible|shown)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:is|are|does)\s+[\"'](.+?)[\"']\s+(?:currently\s+)?(?:showing|displayed|visible|present)(?:\s+(?:on|in)\s+(?:the\s+)?(?:page|screen))?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # === 中国語表現大幅強化 ===
        
        # カジュアル中国語
        (r"(?:看看|瞅瞅|瞧瞧)[\"'""](.+?)[\"'""](?:有没有|是否)(?:显示|出现|存在)(?:了|呢|吗|嗎)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"[\"'""](.+?)[\"'""](?:应该|应当|估计|可能)(?:会|要)(?:显示|出现|存在)(?:吧|呢|了)(?:，|,)?(?:检查|确认|验证)(?:一下|下)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # ビジネス中国語
        (r"(?:请|請)(?:您|你们|大家)(?:协助|帮助|帮忙)(?:确认|检查|验证)[\"'""](.+?)[\"'""](?:的|之)(?:显示|存在|出现)(?:情况|状态|状况)", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:需要|必须|须要)(?:对|针对)[\"'""](.+?)[\"'""](?:进行|开展|实施)(?:显示|存在)(?:性|状态)(?:确认|检查|验证)", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # 疑問形中国語
        (r"[\"'""](.+?)[\"'""](?:有|在)(?:这个|这|那个|那)(?:页面|屏幕|界面)(?:上|里|中)(?:显示|出现|存在)(?:了|着|呢|嗎)(?:？|?)?", 
         AssertionType.TEXT_EXISTS, "text"),
        (r"(?:你|您|大家)(?:能|可以|会)(?:看到|找到|发现)[\"'""](.+?)[\"'""](?:在|于)(?:页面|屏幕)(?:上|中)(?:显示|出现)(?:吗|嗎|呢)(?:？|?)?", 
         AssertionType.TEXT_EXISTS, "text"),
        
        # === フォーム要素専門パターン ===
        
        # ボタン関連
        (r"[「""]?(.+?)[」""]?(?:ボタン|button|Button|按钮|按鈕)(?:が|は)(?:表示|存在|クリック可能|押せる|有効)(?:になって|で|に)(?:いる|いること)(?:を|について)?(?:確認|検証|チェック)", 
         AssertionType.ELEMENT_EXISTS, "button"),
        (r"[「""]?(.+?)[」""]?(?:を|の)(?:クリック|押す|タップ|click)(?:できる|可能)(?:か|かどうか)(?:確認|検証|チェック)", 
         AssertionType.ELEMENT_ENABLED, "button"),
        (r"[「""]?(.+?)[」""]?(?:ボタン|button)(?:が|は)(?:無効|押せない|クリックできない|disabled)(?:になって|で)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_DISABLED, "button"),
        
        # リンク関連
        (r"[「""]?(.+?)[」""]?(?:リンク|link|Link|链接|鏈接)(?:が|は)(?:表示|存在|クリック可能|有効)(?:になって|で|に)(?:いる|いること)(?:を|について)?(?:確認|検証|チェック)", 
         AssertionType.ELEMENT_EXISTS, "link"),
        (r"[「""]?(.+?)[」""]?(?:へのリンク|のリンク|へのリンク先)(?:が|は)(?:正しく|適切に)(?:設定|機能)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "link"),
        
        # 入力フィールド関連
        (r"[「""]?(.+?)[」""]?(?:入力欄|フィールド|テキストボックス|input|field)(?:が|は|に)(?:空|から|empty|blank)(?:である|になって|で)(?:いる|いること)(?:確認|検証)", 
         AssertionType.INPUT_VALUE_EQUALS, "input_empty"),
        (r"[「""]?(.+?)[」""]?(?:入力欄|フィールド|テキストボックス)(?:に|へ)(?:何か|値|データ)(?:が|を)(?:入力|設定)(?:されて|できて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.INPUT_VALUE_CONTAINS, "input_any"),
        
        # セレクトボックス関連
        (r"[「""]?(.+?)[」""]?(?:プルダウン|ドロップダウン|セレクトボックス|select)(?:で|から)[「""]?(.+?)[」""]?(?:が|を)(?:選択|選ばれて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.INPUT_VALUE_EQUALS, "select_value"),
        (r"[「""]?(.+?)[」""]?(?:の選択肢|のオプション)(?:に|で)[「""]?(.+?)[」""]?(?:が|を)(?:含まれて|存在して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "select_option"),
        
        # === ステータス・状態パターン ===
        
        # 読み込み状態
        (r"(?:ページ|画面|サイト)(?:が|の)(?:読み込み中|ローディング中|loading|載入中)(?:でない|ではない)(?:こと|ことを)(?:確認|検証)", 
         AssertionType.ELEMENT_NOT_EXISTS, "loading"),
        (r"(?:ローディング|読み込み|スピナー|spinner)(?:が|は)(?:消えて|終わって|完了して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_NOT_EXISTS, "loading"),
        
        # エラー状態
        (r"(?:エラー|error|Error|错误|錯誤)(?:メッセージ|表示|画面)(?:が|は)(?:出て|表示されて)(?:いない|ない)(?:こと|ことを)(?:確認|検証)", 
         AssertionType.TEXT_NOT_EXISTS, "error"),
        (r"(?:警告|warning|Warning|警告信息)(?:が|は)(?:表示されて|出て)(?:いない|ない)(?:こと|ことを)(?:確認|検証)", 
         AssertionType.TEXT_NOT_EXISTS, "warning"),
        
        # 成功状態
        (r"(?:成功|success|Success|成功信息)(?:メッセージ|表示)(?:が|は)(?:表示されて|出て)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "success"),
        (r"(?:完了|完成|complete|Complete)(?:メッセージ|表示|画面)(?:が|は)(?:表示されて|出て)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "complete"),
        
        # === 画像・メディアパターン ===
        
        # 画像関連
        (r"[「""]?(.+?)[」""]?(?:画像|イメージ|image|Image|图片|圖片)(?:が|は)(?:表示|ロード|読み込まれて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "image"),
        (r"(?:アイコン|icon|Icon)(?:の|で)[「""]?(.+?)[」""]?(?:が|は)(?:表示|見えて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "icon"),
        
        # 動画関連
        (r"(?:動画|ビデオ|video|Video|视频|視頻)(?:が|は)(?:再生可能|再生できる|playable)(?:な状態|で)(?:ある|いる)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "video"),
        (r"(?:動画|ビデオ|video)(?:プレイヤー|player)(?:が|は)(?:表示|ロード)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "video_player"),
        
        # === テーブル・リストパターン ===
        
        # テーブル関連
        (r"(?:テーブル|表|table|Table)(?:に|で)[「""]?(.+?)[」""]?(?:という|の)(?:データ|行|列)(?:が|は)(?:表示|含まれて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "table_data"),
        (r"(?:テーブル|表)(?:の|で)(?:行数|レコード数|件数)(?:が|は)(\d+)(?:件|行|個)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_COUNT, "table_rows"),
        
        # リスト関連
        (r"(?:リスト|一覧|list|List)(?:に|で)[「""]?(.+?)[」""]?(?:が|は)(?:含まれて|表示されて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "list_item"),
        (r"(?:リスト|一覧)(?:の|で)(?:項目数|アイテム数)(?:が|は)(\d+)(?:個|件|つ)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_COUNT, "list_items"),
        
        # === モーダル・ポップアップパターン ===
        
        # モーダル関連
        (r"(?:モーダル|ダイアログ|ポップアップ|modal|dialog|popup)(?:が|は)(?:開いて|表示されて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_VISIBLE, "modal"),
        (r"(?:モーダル|ダイアログ|ポップアップ)(?:が|は)(?:閉じて|消えて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_NOT_EXISTS, "modal"),
        
        # アラート関連
        (r"(?:アラート|alert|Alert)(?:が|は)(?:表示されて|出て)(?:いない|ない)(?:こと|ことを)(?:確認|検証)", 
         AssertionType.ELEMENT_NOT_EXISTS, "alert"),
        (r"(?:通知|notification|Notification)(?:が|は)(?:表示されて|出て)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "notification"),
        
        # === ナビゲーションパターン ===
        
        # メニュー関連
        (r"[「""]?(.+?)[」""]?(?:メニュー|menu|Menu)(?:が|は)(?:開いて|展開されて|表示されて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_VISIBLE, "menu"),
        (r"(?:ナビゲーション|navigation|nav)(?:に|で)[「""]?(.+?)[」""]?(?:が|は)(?:含まれて|表示されて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "nav"),
        
        # タブ関連
        (r"[「""]?(.+?)[」""]?(?:タブ|tab|Tab)(?:が|は)(?:選択|アクティブ|active)(?:されて|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "tab_active"),
        (r"(?:タブ|tab)(?:の|で)(?:内容|コンテンツ)(?:が|は)(?:正しく|適切に)(?:表示されて|切り替わって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_VISIBLE, "tab_content"),
        
        # === アクセシビリティパターン ===
        
        # ARIA関連
        (r"[「""]?(.+?)[」""]?(?:に|で)(?:aria-label|ariaラベル)(?:が|は)(?:設定|付与)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ATTRIBUTE_EXISTS, "aria_label"),
        (r"(?:スクリーンリーダー|screen reader)(?:で|に)(?:読み上げ可能|アクセス可能)(?:な|に)(?:なって|設定されて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ATTRIBUTE_EXISTS, "aria"),
        
        # フォーカス関連
        (r"[「""]?(.+?)[」""]?(?:に|へ)(?:フォーカス|focus)(?:が|は)(?:当たって|移動して|設定されて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "focused"),
        (r"(?:タブキー|Tab)(?:で|により)(?:正しく|適切に)(?:フォーカス移動|ナビゲーション)(?:できる|可能)(?:である|こと)(?:確認|検証)", 
         AssertionType.ELEMENT_ENABLED, "tabbable"),
        
        # === レスポンシブ・デバイスパターン ===
        
        # モバイル関連
        (r"(?:モバイル|スマホ|スマートフォン|mobile)(?:表示|ビュー|画面)(?:で|において)[「""]?(.+?)[」""]?(?:が|は)(?:正しく|適切に)(?:表示|レイアウト)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_VISIBLE, "mobile"),
        (r"(?:レスポンシブ|responsive)(?:デザイン|表示)(?:が|は)(?:正常|適切)(?:に|で)(?:動作|機能)(?:して|されて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_VISIBLE, "responsive"),
        
        # === パフォーマンス関連パターン ===
        
        # 速度関連
        (r"(?:ページ|画面)(?:が|は)(\d+)(?:秒|ミリ秒|ms)(?:以内に|未満で)(?:表示|ロード|読み込み)(?:される|完了する)(?:こと|ことを)(?:確認|検証)", 
         AssertionType.ELEMENT_VISIBLE, "performance"),
        (r"(?:レスポンス|応答|response)(?:が|は)(?:高速|速い|早い|quick|fast)(?:である|で)(?:こと|ことを)(?:確認|検証)", 
         AssertionType.ELEMENT_VISIBLE, "fast_response"),
        
        # === セキュリティ関連パターン ===
        
        # HTTPS関連
        (r"(?:HTTPS|https|SSL)(?:で|により)(?:保護|暗号化|secure)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.URL_STARTS_WITH, "https"),
        (r"(?:セキュア|secure|安全)(?:な|に)(?:接続|通信)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.URL_STARTS_WITH, "secure"),
        
        # === 特殊文字・記号パターン ===
        
        # 記号を含む表現
        (r"[「""]?(.+?)[」""]?(?:※|＊|★|☆|●|○|■|□)(?:マーク|印|記号)(?:が|は)(?:表示|付いて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "symbol"),
        (r"(?:必須|required)(?:項目|フィールド)(?:に|で)(?:※|＊|アスタリスク)(?:が|は)(?:表示|付いて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "required_mark"),
        
        # === 日付・時刻パターン ===
        
        # 日付関連
        (r"(?:日付|日時|date|Date)(?:が|は)[「""]?(.+?)[」""]?(?:と|に)(?:設定|表示)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "date"),
        (r"(?:今日|本日|today|Today)(?:の|が)(?:日付|日時)(?:が|は)(?:正しく|適切に)(?:表示|設定)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "today_date"),
        
        # 時刻関連
        (r"(?:時刻|時間|time|Time)(?:が|は)[「""]?(.+?)[」""]?(?:と|に)(?:設定|表示)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "time"),
        (r"(?:現在時刻|現在時間|current time)(?:が|は)(?:正しく|適切に)(?:表示|更新)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "current_time"),
        
        # === 価格・金額パターン ===
        
        # 価格表示
        (r"(?:価格|金額|値段|price|Price)(?:が|は)[「""]?(.+?)[」""]?(?:円|ドル|dollar|USD|JPY)(?:で|と)(?:表示|設定)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "price"),
        (r"(?:合計|総額|total|Total)(?:が|は)(?:正しく|適切に)(?:計算|表示)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "total"),
        
        # === カウント・数値パターン ===
        
        # カウント関連
        (r"(?:カウント|数|件数|count|Count)(?:が|は)(\d+)(?:に|と)(?:なって|等しく)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_CONTAINS, "count"),
        (r"(?:残り|あと|remaining)(\d+)(?:個|件|つ)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_CONTAINS, "remaining"),
        
        # === ログイン・認証パターン ===
        
        # ログイン状態
        (r"(?:ログイン|サインイン|login|sign in)(?:状態|済み|中)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "logged_in"),
        (r"(?:ログアウト|サインアウト|logout|sign out)(?:状態|済み)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_NOT_EXISTS, "logged_in"),
        
        # ユーザー情報
        (r"(?:ユーザー名|ユーザーID|username|Username)(?:が|は)[「""]?(.+?)[」""]?(?:と|で)(?:表示|設定)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "username"),
        (r"(?:アカウント|account|Account)(?:情報|名)(?:が|は)(?:正しく|適切に)(?:表示|設定)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "account"),
        
        # === ダウンロード・アップロードパターン ===
        
        # ダウンロード関連
        (r"(?:ダウンロード|download|Download)(?:ボタン|リンク)(?:が|は)(?:利用可能|有効|クリック可能)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_ENABLED, "download"),
        (r"(?:ファイル|file|File)[「""]?(.+?)[」""]?(?:が|を)(?:ダウンロード可能|取得可能)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "file_download"),
        
        # アップロード関連
        (r"(?:アップロード|upload|Upload)(?:ボタン|フォーム)(?:が|は)(?:利用可能|有効)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_ENABLED, "upload"),
        (r"(?:ファイル選択|file selection)(?:ボタン|フィールド)(?:が|は)(?:表示|利用可能)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "file_input"),
        
        # === プログレス・進捗パターン ===
        
        # 進捗表示
        (r"(?:進捗|プログレス|progress|Progress)(?:が|は)(\d+)(?:%|パーセント)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_CONTAINS, "progress"),
        (r"(?:プログレスバー|進捗バー|progress bar)(?:が|は)(?:表示|更新)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "progress_bar"),
        
        # === メッセージ・テキストパターン ===
        
        # メッセージタイプ
        (r"(?:情報|インフォ|info|Info)(?:メッセージ|表示)(?:が|は)(?:表示|出て)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "info"),
        (r"(?:ヒント|ヒント|hint|Hint|tip|Tip)(?:が|は)(?:表示|出て)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "hint"),
        
        # === バリデーション・検証パターン ===
        
        # バリデーション関連
        (r"(?:バリデーション|検証|validation|Validation)(?:エラー|メッセージ)(?:が|は)(?:表示されて|出て)(?:いない|ない)(?:こと|ことを)(?:確認|検証)", 
         AssertionType.TEXT_NOT_EXISTS, "validation_error"),
        (r"(?:入力内容|フォーム|form)(?:が|は)(?:正しい|有効|valid)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "valid_form"),
        
        # === ソート・並び替えパターン ===
        
        # ソート関連
        (r"(?:ソート|並び替え|sort|Sort)(?:が|は)(?:昇順|降順|ascending|descending)(?:に|で)(?:設定|適用)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "sorted"),
        (r"(?:項目|アイテム|items)(?:が|は)(?:正しく|適切に)(?:並んで|ソートされて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "ordered"),
        
        # === フィルター・検索パターン ===
        
        # フィルター関連
        (r"(?:フィルター|フィルタ|filter|Filter)(?:が|は)(?:適用|設定)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_EXISTS, "filter"),
        (r"(?:検索結果|search results)(?:が|は)(\d+)(?:件|個|つ)(?:表示|ヒット)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_CONTAINS, "search_results"),
        
        # === ページネーションパターン ===
        
        # ページング関連
        (r"(?:ページ|page|Page)(\d+)(?:が|を)(?:表示|選択)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_CONTAINS, "page_number"),
        (r"(?:次のページ|前のページ|next|previous)(?:ボタン|リンク)(?:が|は)(?:利用可能|クリック可能)(?:である|になって)(?:いる|いること)(?:確認|検証)", 
         AssertionType.ELEMENT_ENABLED, "pagination"),
        
        # === 言語・国際化パターン ===
        
        # 言語切替
        (r"(?:言語|language|Language)(?:が|は)[「""]?(.+?)[」""]?(?:に|で)(?:設定|切り替え)(?:されて|して)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "language"),
        (r"(?:日本語|英語|中国語|Japanese|English|Chinese)(?:表示|版)(?:に|で)(?:なって|設定されて)(?:いる|いること)(?:確認|検証)", 
         AssertionType.TEXT_EXISTS, "locale"),
        
    ]
    
    @classmethod
    def parse(cls, instruction: str) -> Optional[Dict[str, Any]]:
        """
        Extract assertion information from natural language instruction
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            Dictionary of assertion information, or None
        """
        for pattern, assertion_type, param_type in cls.PATTERNS:
            match = re.search(pattern, instruction)
            if match:
                groups = match.groups()
                
                if param_type == "text":
                    # Remove quotes if present (flexible quote support)
                    text = groups[0].strip()
                    text = text.strip('「」""''\'\'""')
                    return {
                        "type": assertion_type,
                        "expected": text,
                        "selector": None
                    }
                elif param_type == "selector":
                    return {
                        "type": assertion_type,
                        "selector": cls._text_to_selector(groups[0].strip()),
                        "expected": None
                    }
                elif param_type == "url":
                    # Remove quotes if present (flexible quote support)
                    text = groups[0].strip()
                    text = text.strip('「」""''\'\'""')
                    return {
                        "type": assertion_type,
                        "expected": text,
                        "selector": None
                    }
                elif param_type == "title":
                    # Remove quotes if present (flexible quote support)
                    text = groups[0].strip()
                    text = text.strip('「」""''\'\'""')
                    return {
                        "type": assertion_type,
                        "expected": text,
                        "selector": None
                    }
                elif param_type == "selector_value":
                    return {
                        "type": assertion_type,
                        "selector": cls._text_to_selector(groups[0].strip()),
                        "expected": groups[1].strip()
                    }
                elif param_type == "selector_count":
                    return {
                        "type": assertion_type,
                        "selector": cls._text_to_selector(groups[0].strip()),
                        "expected": int(groups[1])
                    }
                elif param_type == "html_element":
                    return {
                        "type": assertion_type,
                        "selector": groups[0].strip(),  # Direct HTML element selector
                        "expected": None
                    }
        
        return None
    
    @staticmethod
    def _text_to_selector(text: str) -> str:
        """
        Convert text description to CSS selector
        
        Args:
            text: Selector description (e.g. "ログインボタン")
            
        Returns:
            CSS selector string
        """
        # Strip quotes if present (flexible quote support)
        text = text.strip('「」""''\'\'""')
        
        # Basic conversion rules (Japanese)
        if "ボタン" in text:
            element_name = text.replace("ボタン", "").strip()
            element_name = element_name.strip('「」""''\'\'""')
            return f'button:has-text("{element_name}"), input[type="button"]:has-text("{element_name}"), input[type="submit"]:has-text("{element_name}")'
        elif "リンク" in text:
            element_name = text.replace("リンク", "").strip()
            element_name = element_name.strip('「」""''\'\'""')
            return f'a:has-text("{element_name}"):visible'
        elif "フィールド" in text or "入力欄" in text:
            element_name = text.replace("フィールド", "").replace("入力欄", "").strip()
            element_name = element_name.strip('「」""''\'\'""')
            return f'input[placeholder*="{element_name}"], input[name*="{element_name}"], label:has-text("{element_name}") + input'
        elif "チェックボックス" in text:
            element_name = text.replace("チェックボックス", "").strip()
            element_name = element_name.strip('「」""''\'\'""')
            return f'input[type="checkbox"][name*="{element_name}"], label:has-text("{element_name}") input[type="checkbox"]'
        # English patterns
        elif "button" in text.lower():
            element_name = text.lower().replace("button", "").strip()
            element_name = element_name.strip('「」""''\'\'""')
            return f'button:has-text("{element_name}"), input[type="button"]:has-text("{element_name}"), input[type="submit"]:has-text("{element_name}")'
        elif "link" in text.lower():
            element_name = text.lower().replace("link", "").strip()
            element_name = element_name.strip('「」""''\'\'""')
            return f'a:has-text("{element_name}"):visible'
        # Chinese patterns
        elif "按钮" in text or "按鈕" in text:
            element_name = text.replace("按钮", "").replace("按鈕", "").strip()
            element_name = element_name.strip('「」""''\'\'""')
            return f'button:has-text("{element_name}"), input[type="button"]:has-text("{element_name}"), input[type="submit"]:has-text("{element_name}")'
        elif "链接" in text or "連結" in text:
            element_name = text.replace("链接", "").replace("連結", "").strip()
            element_name = element_name.strip('「」""''\'\'""')
            return f'a:has-text("{element_name}"):visible'
        else:
            # Generic text-based selector
            return f':has-text("{text}")'
    
    @classmethod
    def is_assertion_instruction(cls, instruction: str) -> bool:
        """
        Determine if instruction is an assertion
        
        Args:
            instruction: Instruction text
            
        Returns:
            True if assertion instruction
        """
        # Japanese keywords
        japanese_keywords = [
            "確認", "検証", "チェック", "確かめ",
            "表示されている", "存在する", "含まれる",
            "一致する", "等しい", "同じ", "ことを確認"
        ]
        
        # English keywords
        english_keywords = [
            "verify", "check", "confirm", "assert",
            "should", "must", "expect", "ensure",
            "contains", "exists", "visible", "displayed"
        ]
        
        # Chinese keywords
        chinese_keywords = [
            "验证", "检查", "确认", "断言",
            "显示", "存在", "包含", "确保",
            "应该", "必须", "期望"
        ]
        
        all_keywords = japanese_keywords + english_keywords + chinese_keywords
        return any(keyword in instruction.lower() for keyword in all_keywords)


class AssertionExecutor:
    """Assertion execution engine"""
    
    def __init__(self, page: Page):
        self.page = page
    
    async def execute(self, assertion: Assertion) -> AssertionResult:
        """
        Execute assertion
        
        Args:
            assertion: Assertion to execute
            
        Returns:
            Execution result
        """
        import time
        start_time = time.time()
        
        try:
            result = await self._execute_assertion(assertion)
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"アサーション実行エラー: {str(e)}",
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _execute_assertion(self, assertion: Assertion) -> AssertionResult:
        """Execute actual assertion logic"""
        
        if assertion.type == AssertionType.TEXT_EXISTS:
            return await self._assert_text_exists(assertion)
        elif assertion.type == AssertionType.TEXT_NOT_EXISTS:
            return await self._assert_text_not_exists(assertion)
        elif assertion.type == AssertionType.ELEMENT_EXISTS:
            return await self._assert_element_exists(assertion)
        elif assertion.type == AssertionType.ELEMENT_NOT_EXISTS:
            return await self._assert_element_not_exists(assertion)
        elif assertion.type == AssertionType.ELEMENT_VISIBLE:
            return await self._assert_element_visible(assertion)
        elif assertion.type == AssertionType.ELEMENT_HIDDEN:
            return await self._assert_element_hidden(assertion)
        elif assertion.type == AssertionType.URL_CONTAINS:
            return await self._assert_url_contains(assertion)
        elif assertion.type == AssertionType.URL_EQUALS:
            return await self._assert_url_equals(assertion)
        elif assertion.type == AssertionType.URL_STARTS_WITH:
            return await self._assert_url_starts_with(assertion)
        elif assertion.type == AssertionType.URL_ENDS_WITH:
            return await self._assert_url_ends_with(assertion)
        elif assertion.type == AssertionType.TITLE_CONTAINS:
            return await self._assert_title_contains(assertion)
        elif assertion.type == AssertionType.TITLE_EQUALS:
            return await self._assert_title_equals(assertion)
        elif assertion.type == AssertionType.ELEMENT_COUNT:
            return await self._assert_element_count(assertion)
        elif assertion.type == AssertionType.INPUT_VALUE_EQUALS:
            return await self._assert_input_value_equals(assertion)
        elif assertion.type == AssertionType.CHECKBOX_CHECKED:
            return await self._assert_checkbox_checked(assertion)
        elif assertion.type == AssertionType.CHECKBOX_UNCHECKED:
            return await self._assert_checkbox_unchecked(assertion)
        else:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"Unimplemented assertion type: {assertion.type}"
            )
    
    async def _assert_text_exists(self, assertion: Assertion) -> AssertionResult:
        """Assert text exists on page"""
        try:
            # Try multiple selector strategies for better text matching
            selectors = [
                f'text="{assertion.expected}"',    # Exact match
                f'text=/{assertion.expected}/i',   # Case insensitive regex
                f'text*="{assertion.expected}"',   # Partial match
                f':text-is("{assertion.expected}")',  # Alternative exact match
                f':text("{assertion.expected}")',     # Contains text
            ]
            
            passed = False
            count = 0
            
            # Try each selector until one works
            for selector in selectors:
                try:
                    locator = self.page.locator(selector)
                    if assertion.wait_for:
                        # Use a shorter timeout for each attempt
                        await locator.first().wait_for(timeout=1000)
                    
                    count = await locator.count()
                    if count > 0:
                        passed = True
                        break
                except:
                    # Continue to next selector if this one fails
                    continue
            
            # If all selectors fail, try searching in page content directly
            if not passed:
                try:
                    page_content = await self.page.content()
                    if assertion.expected.lower() in page_content.lower():
                        passed = True
                        count = 1
                except:
                    pass
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=count,
                expected_value=f"テキスト '{assertion.expected}' が1つ以上存在",
                error_message=None if passed else f"テキスト '{assertion.expected}' が見つかりません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"テキスト存在確認エラー: {str(e)}"
            )
    
    async def _assert_text_not_exists(self, assertion: Assertion) -> AssertionResult:
        """テキスト非存在確認"""
        try:
            # Check using multiple strategies to ensure comprehensive search
            found = False
            
            # Try Playwright selectors
            selectors = [
                f'text="{assertion.expected}"',
                f'text=/{assertion.expected}/i',
                f'text*="{assertion.expected}"',
            ]
            
            for selector in selectors:
                try:
                    locator = self.page.locator(selector)
                    count = await locator.count()
                    if count > 0:
                        found = True
                        break
                except:
                    continue
            
            # Check page content directly if not found with selectors
            if not found:
                try:
                    page_content = await self.page.content()
                    if assertion.expected.lower() in page_content.lower():
                        found = True
                except:
                    pass
            
            passed = not found
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=1 if found else 0,
                expected_value=f"テキスト '{assertion.expected}' が存在しない",
                error_message=None if passed else f"テキスト '{assertion.expected}' が見つかりました"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"テキスト非存在確認エラー: {str(e)}"
            )
    
    async def _assert_element_exists(self, assertion: Assertion) -> AssertionResult:
        """要素存在確認"""
        try:
            locator = self.page.locator(assertion.selector)
            if assertion.wait_for:
                # Use first() to avoid strict mode violation
                await locator.first().wait_for(state="visible", timeout=assertion.timeout)
            
            count = await locator.count()
            passed = count > 0
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=count,
                expected_value=f"要素 '{assertion.selector}' が1つ以上存在",
                error_message=None if passed else f"要素 '{assertion.selector}' が見つかりません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"要素存在確認エラー: {str(e)}"
            )
    
    async def _assert_element_not_exists(self, assertion: Assertion) -> AssertionResult:
        """要素非存在確認"""
        try:
            locator = self.page.locator(assertion.selector)
            count = await locator.count()
            passed = count == 0
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=count,
                expected_value=f"要素 '{assertion.selector}' が存在しない",
                error_message=None if passed else f"要素 '{assertion.selector}' が見つかりました（{count}個）"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"要素非存在確認エラー: {str(e)}"
            )
    
    async def _assert_element_visible(self, assertion: Assertion) -> AssertionResult:
        """要素表示確認"""
        try:
            locator = self.page.locator(assertion.selector)
            if assertion.wait_for:
                await locator.wait_for(state="visible", timeout=assertion.timeout)
            
            is_visible = await locator.is_visible()
            
            return AssertionResult(
                passed=is_visible,
                assertion=assertion,
                actual_value=is_visible,
                expected_value=f"要素 '{assertion.selector}' が表示されている",
                error_message=None if is_visible else f"要素 '{assertion.selector}' が表示されていません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"要素表示確認エラー: {str(e)}"
            )
    
    async def _assert_element_hidden(self, assertion: Assertion) -> AssertionResult:
        """要素非表示確認"""
        try:
            locator = self.page.locator(assertion.selector)
            is_visible = await locator.is_visible()
            passed = not is_visible
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=is_visible,
                expected_value=f"要素 '{assertion.selector}' が非表示",
                error_message=None if passed else f"要素 '{assertion.selector}' が表示されています"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"要素非表示確認エラー: {str(e)}"
            )
    
    async def _assert_url_contains(self, assertion: Assertion) -> AssertionResult:
        """URL包含確認"""
        try:
            current_url = self.page.url
            expected_url = str(assertion.expected)
            passed = expected_url in current_url
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=current_url,
                expected_value=f"URLに '{expected_url}' が含まれる",
                error_message=None if passed else f"URLに '{expected_url}' が含まれていません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"URL包含確認エラー: {str(e)}"
            )
    
    async def _assert_url_equals(self, assertion: Assertion) -> AssertionResult:
        """URL一致確認"""
        try:
            current_url = self.page.url
            expected_url = str(assertion.expected)
            passed = current_url == expected_url
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=current_url,
                expected_value=expected_url,
                error_message=None if passed else f"URLが一致しません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"URL一致確認エラー: {str(e)}"
            )
    
    async def _assert_url_starts_with(self, assertion: Assertion) -> AssertionResult:
        """URL開始文字列確認"""
        try:
            current_url = self.page.url
            expected_start = str(assertion.expected)
            passed = current_url.startswith(expected_start)
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=current_url,
                expected_value=f"URLが '{expected_start}' で始まる",
                error_message=None if passed else f"URLが '{expected_start}' で始まっていません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"URL開始確認エラー: {str(e)}"
            )
    
    async def _assert_url_ends_with(self, assertion: Assertion) -> AssertionResult:
        """URL終了文字列確認"""
        try:
            current_url = self.page.url
            expected_end = str(assertion.expected)
            passed = current_url.endswith(expected_end)
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=current_url,
                expected_value=f"URLが '{expected_end}' で終わる",
                error_message=None if passed else f"URLが '{expected_end}' で終わっていません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"URL終了確認エラー: {str(e)}"
            )
    
    async def _assert_title_contains(self, assertion: Assertion) -> AssertionResult:
        """タイトル包含確認"""
        try:
            current_title = await self.page.title()
            expected_text = str(assertion.expected)
            passed = expected_text in current_title
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=current_title,
                expected_value=f"タイトルに '{expected_text}' が含まれる",
                error_message=None if passed else f"タイトルに '{expected_text}' が含まれていません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"タイトル包含確認エラー: {str(e)}"
            )
    
    async def _assert_title_equals(self, assertion: Assertion) -> AssertionResult:
        """タイトル一致確認"""
        try:
            current_title = await self.page.title()
            expected_title = str(assertion.expected)
            passed = current_title == expected_title
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=current_title,
                expected_value=expected_title,
                error_message=None if passed else f"タイトルが一致しません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"タイトル一致確認エラー: {str(e)}"
            )
    
    async def _assert_element_count(self, assertion: Assertion) -> AssertionResult:
        """要素数確認"""
        try:
            locator = self.page.locator(assertion.selector)
            actual_count = await locator.count()
            expected_count = int(assertion.expected)
            passed = actual_count == expected_count
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=actual_count,
                expected_value=expected_count,
                error_message=None if passed else f"要素数が一致しません（期待値: {expected_count}, 実際: {actual_count}）"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"要素数確認エラー: {str(e)}"
            )
    
    async def _assert_input_value_equals(self, assertion: Assertion) -> AssertionResult:
        """入力値一致確認"""
        try:
            locator = self.page.locator(assertion.selector)
            actual_value = await locator.input_value()
            expected_value = str(assertion.expected)
            passed = actual_value == expected_value
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=actual_value,
                expected_value=expected_value,
                error_message=None if passed else f"入力値が一致しません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"入力値確認エラー: {str(e)}"
            )
    
    async def _assert_checkbox_checked(self, assertion: Assertion) -> AssertionResult:
        """チェックボックスチェック確認"""
        try:
            locator = self.page.locator(assertion.selector)
            is_checked = await locator.is_checked()
            
            return AssertionResult(
                passed=is_checked,
                assertion=assertion,
                actual_value=is_checked,
                expected_value=True,
                error_message=None if is_checked else f"チェックボックスがチェックされていません"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"チェックボックス確認エラー: {str(e)}"
            )
    
    async def _assert_checkbox_unchecked(self, assertion: Assertion) -> AssertionResult:
        """チェックボックス未チェック確認"""
        try:
            locator = self.page.locator(assertion.selector)
            is_checked = await locator.is_checked()
            passed = not is_checked
            
            return AssertionResult(
                passed=passed,
                assertion=assertion,
                actual_value=is_checked,
                expected_value=False,
                error_message=None if passed else f"チェックボックスがチェックされています"
            )
        except Exception as e:
            return AssertionResult(
                passed=False,
                assertion=assertion,
                error_message=f"チェックボックス確認エラー: {str(e)}"
            )