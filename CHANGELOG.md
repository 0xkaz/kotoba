# Changelog

All notable changes to kotoba will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.0.1] - 2025-06-20

### Initial Release
- Web test execution using natural language (Japanese/English)
- Browser automation through Playwright integration
- Test case definition in YAML format
- Support for multiple LLM models
  - Japanese-optimized: rinna, cyberagent, pfnet
  - Multilingual: Qwen, Phi, TinyLlama
- Both Docker and local environment support
- MockLLM mode (testing without LLM models)
- HuggingFace model caching
- Basic test runner implementation