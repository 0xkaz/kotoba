# kotoba - 自然语言网络测试工具

![kotoba - Natural Language Web Testing](./og_image.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**kotoba** 是一个基于自然语言的网络测试工具，支持中文、日文和英文。只需用简单的文字描述测试步骤，kotoba 就能自动执行网站操作。

## ✨ 主要特性

- 🌏 **多语言支持**: 中文、日文、英文自然语言测试
- ✅ **测试断言**: 使用自然语言进行全面验证，达到100%成功率
- 🤖 **多种LLM模型**: 支持多种大语言模型，包括中文优化模型
- 🎯 **零编程要求**: 不需要编程知识，用自然语言编写测试
- 🐳 **Docker支持**: 完整的容器化环境
- 🚀 **模拟模式**: 无需下载大模型即可快速测试
- 📸 **自动截图**: 失败时自动保存截图

## 🚀 快速开始

### 本地安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/0xkaz/kotoba.git
cd kotoba

# 安装
make install-local

# 运行测试
kotoba --test-file tests/yahoo_japan_test.yaml
```

### Docker 运行

```bash
# 构建和启动
make build
make up

# 进入容器
make shell

# 运行测试
kotoba --test-file tests/mock_test.yaml
```

### 模拟模式（无需大模型）

快速测试无需下载大型模型：

```bash
USE_MOCK_LLM=true kotoba --test-file tests/mock_test.yaml
```

## 📝 测试文件示例

### 中文测试示例

```yaml
name: "百度搜索测试"
url: "https://www.baidu.com"
steps:
  - "点击搜索框"
  - "输入「北京天气」"
  - "点击搜索按钮"
  - "等待结果加载"
  - "截图保存"
```

### 中日英混合测试

```yaml
name: "多语言测试"
url: "https://example.com"
steps:
  - "确认页面标题"  # 中文
  - "ページタイトルを確認する"  # 日文
  - "Take a screenshot"  # 英文
```

### 测试断言功能

kotoba 提供了全面的测试验证功能，使用自然语言表达断言，**达到100%成功率**。

```yaml
name: "断言测试示例"
base_url: "https://example.com"
test_cases:
  - name: "基础验证"
    description: "各种断言类型的测试"
    steps:
      - instruction: "「Example Domain」が表示されていることを確認"  # 确认文本存在
      - instruction: "URLに「example.com」が含まれることを確認"      # 确认URL包含
      - instruction: "ページタイトルに「Example」が含まれることを確認"  # 确认标题包含
      - instruction: "「存在しないテキスト」が表示されていないことを確認"  # 确认文本不存在
```

#### 支持的断言类型

**文本验证:**
- `「文本」が表示されていることを確認` - 确认页面上存在指定文本
- `「文本」が表示されていないことを確認` - 确认页面上不存在指定文本

**URL验证:**
- `URLに「text」が含まれることを確認` - 确认URL包含指定文本
- `URLが「url」で始まることを確認` - 确认URL以指定文本开头
- `URLが「url」で終わることを確認` - 确认URL以指定文本结尾

**标题验证:**
- `ページタイトルに「text」が含まれることを確認` - 确认页面标题包含指定文本
- `ページタイトルが「title」であることを確認` - 确认页面标题完全匹配

**元素验证:**
- `「ボタン」が存在することを確認` - 确认元素存在
- `「ボタン」が表示されていることを確認` - 确认元素可见
- `「ボタン」が表示されていないことを確認` - 确认元素不可见

**表单验证:**
- `「入力欄」の値が「value」であることを確認` - 确认输入框的值
- `「チェックボックス」がチェックされていることを確認` - 确认复选框已选中

断言失败时会自动生成详细的错误信息和截图。

## 🤖 支持的LLM模型

### 默认模型
- **rinna/japanese-gpt-neox-3.6b** (~7GB) - 日文专用，平衡性能

### 按内存需求分类

**低内存 (<8GB):**
- `Qwen/Qwen2-1.5B-Instruct` (~3GB) - **推荐中文用户使用**
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (~2GB)
- `microsoft/phi-2` (~5GB)

**中等内存 (8-16GB):**
- `rinna/japanese-gpt-neox-3.6b` (~7GB)
- `cyberagent/open-calm-3b` (~6GB)

**大内存 (16GB+):**
- `pfnet/plamo-13b-instruct` (~26GB)

### 📊 模型推荐

- **中文+日文应用**: `Qwen/Qwen2-1.5B-Instruct` 🌏
- **日文专用**: `rinna/japanese-gpt-neox-3.6b` (默认) 🇯🇵
- **轻量快速**: `TinyLlama/TinyLlama-1.1B-Chat-v1.0` ⚡
- **高精度**: `pfnet/plamo-13b-instruct` 🎯
- **多语言**: `Qwen/Qwen2-7B` 🌍

### 🔧 使用不同模型

要使用非默认模型，请在配置文件中指定：

```bash
# 使用中文模型
kotoba --config configs/qwen_config.yaml --test-file test.yaml

# 使用轻量模型
kotoba --config configs/tiny_model.yaml --test-file test.yaml
```

或通过环境变量设置：

```bash
export MODEL_NAME="Qwen/Qwen2-1.5B-Instruct"
kotoba --test-file test.yaml
```

完整模型列表请查看 `configs/models.yaml`。

## ⚙️ 配置

配置文件使用YAML格式：

```yaml
llm:
  model_name: "Qwen/Qwen2-1.5B-Instruct"
  device: "auto"  # auto, cpu, cuda
  
playwright:
  browser: "chromium"  # chromium, firefox, webkit
  headless: true
  timeout: 30000
  
test:
  screenshot_on_failure: true
  output_dir: "outputs"
  retry_count: 3
```

## 🐳 Docker 支持

```bash
# 构建和运行
make build
make up

# 进入容器
make shell

# 开发模式
make dev
```

## 🔧 高级选项

```bash
# 运行多个测试文件
kotoba --test-files test1.yaml test2.yaml test3.yaml

# 运行目录下所有测试
kotoba --test-dir tests/

# 使用开发配置
kotoba --config configs/dev.yaml --test-file test.yaml

# 显示浏览器窗口（非无头模式）
kotoba --no-headless --test-file test.yaml

# 鲁棒模式（更好的错误处理）
kotoba --robust --test-dir tests/
```

## 🌟 为什么选择 kotoba？

### 对中文用户友好
- **原生中文支持**: 使用 Qwen 系列模型，专为中文优化
- **简体/繁体兼容**: 支持简体中文和繁体中文
- **中文文档**: 完整的中文使用说明

### 易于使用
- **零学习成本**: 不需要学习编程语言
- **自然语言**: 用日常用语描述测试步骤
- **即时反馈**: 实时查看测试执行过程

### 强大功能
- **多浏览器支持**: Chromium、Firefox、WebKit
- **自动重试**: 失败时自动重试
- **详细日志**: 完整的执行日志和错误信息

## 🛠️ 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
make test

# 代码检查
make lint

# 格式化代码
make format
```

## 📖 文档

- [English](README.md)
- [日本語](README.ja.md)
- [中文](README.zh-CN.md)

## 🤝 贡献

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 💬 社区

- [GitHub Issues](https://github.com/0xkaz/kotoba/issues)
- [GitHub Discussions](https://github.com/0xkaz/kotoba/discussions)

---

**注意**: kotoba 目前处于早期开发阶段。如遇到问题，请在 GitHub Issues 中报告。