"""kotoba main entry point"""

import asyncio
import click
from pathlib import Path
from loguru import logger
import sys
import os

# Detect execution environment and set paths
def setup_environment():
    """Set up execution environment (Docker vs Local)"""
    current_dir = Path(__file__).parent.parent.parent
    src_dir = current_dir / "src"
    
    # Detect execution inside Docker container
    is_docker = os.path.exists("/.dockerenv") or os.environ.get("CONTAINER_ENV") == "docker"
    
    if src_dir.exists() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
        logger.debug(f"Added to Python path: {src_dir}")
    
    return is_docker

# Execute environment setup
setup_environment()

from .config import load_config, KotobaConfig
from .runner import TestRunner
from .optimized_runner import OptimizedTestRunner
from .robust_runner import RobustTestRunner


@click.command()
@click.option('--config', '-c', type=click.Path(exists=True), 
              default='configs/default.yaml', help='Configuration file path')
@click.option('--docker', is_flag=True, help='Force execution in Docker mode')
@click.option('--test-file', '-t', type=click.Path(exists=True),
              help='Test file to execute')
@click.option('--test-files', multiple=True, type=click.Path(exists=True),
              help='Multiple test files (for batch mode)')
@click.option('--test-dir', type=click.Path(exists=True, file_okay=False),
              help='Test directory (run all YAML files)')
@click.option('--output-dir', '-o', type=click.Path(),
              default='outputs', help='Output directory')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed logs')
@click.option('--headless/--no-headless', default=None, 
              help='Toggle headless mode')
@click.option('--optimized', is_flag=True, default=True,
              help='Optimized mode (browser session reuse)')
@click.option('--robust', is_flag=True, default=False,
              help='Robust mode (enhanced error tolerance, new page for each test)')
def main(config, docker, test_file, test_files, test_dir, output_dir, verbose, headless, optimized, robust):
    """kotoba - Web testing tool using Japanese natural language
    
    A test tool that can automatically operate websites with natural Japanese
    instructions like "Enter 'weather forecast' in the search box".
    
    Usage examples:
        kotoba --test-file tests/yahoo_japan_test.yaml
        kotoba --test-files tests/test1.yaml tests/test2.yaml  # Batch mode
        kotoba --test-dir tests/  # Run all tests in directory
        kotoba --test-dir tests/ --robust  # Robust mode (error tolerance)
        kotoba --config configs/dev.yaml --no-headless
        USE_MOCK_LLM=true kotoba --test-file tests/mock_test.yaml
    """
    
    # Detect execution environment
    is_docker = setup_environment()
    if docker:
        is_docker = True
    
    # Set log level
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    logger.info(f"Running in {'Docker' if is_docker else 'Local'} mode")
    
    # Load configuration
    config_path = Path(config)
    kotoba_config = load_config(config_path)
    
    # Override headless mode
    if headless is not None:
        kotoba_config.playwright.headless = headless
    
    # Set output directory
    kotoba_config.test.output_dir = Path(output_dir)
    kotoba_config.test.output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"kotoba starting with config: {config_path}")
    logger.info(f"Model: {kotoba_config.llm.model_name}")
    logger.info(f"Browser: {kotoba_config.playwright.browser}")
    logger.info(f"Output: {kotoba_config.test.output_dir}")
    
    # Create test file list
    test_file_paths = []
    
    if test_file:
        test_file_paths.append(Path(test_file))
    
    if test_files:
        test_file_paths.extend([Path(f) for f in test_files])
    
    if test_dir:
        # Search for YAML files in directory
        test_dir_path = Path(test_dir)
        yaml_files = list(test_dir_path.glob("*.yaml")) + list(test_dir_path.glob("*.yml"))
        test_file_paths.extend(yaml_files)
    
    # Select and execute test runner
    try:
        all_tests_passed = True
        
        if test_file_paths:
            if len(test_file_paths) > 1:
                # Execute multiple files
                if robust:
                    # Robust mode: emphasis on error tolerance
                    logger.info(f"Using robust batch mode for {len(test_file_paths)} test files")
                    runner = RobustTestRunner(kotoba_config)
                    results = asyncio.run(runner.run_test_files_batch(test_file_paths))
                    # Check results for batch mode
                    for result in results:
                        summary = result.get("summary", {})
                        if summary.get("failed", 0) > 0 or summary.get("errors", 0) > 0:
                            all_tests_passed = False
                elif optimized:
                    # Optimized mode: emphasis on speed
                    logger.info(f"Using optimized batch mode for {len(test_file_paths)} test files")
                    runner = OptimizedTestRunner(kotoba_config)
                    results = asyncio.run(runner.run_test_files_batch(test_file_paths))
                    # Check results for batch mode
                    for result in results:
                        summary = result.get("summary", {})
                        if summary.get("failed", 0) > 0 or summary.get("errors", 0) > 0:
                            all_tests_passed = False
                else:
                    # Standard mode: individual execution
                    logger.info(f"Using standard mode for {len(test_file_paths)} test files")
                    runner = TestRunner(kotoba_config)
                    for test_path in test_file_paths:
                        logger.info(f"Running test file: {test_path}")
                        result = asyncio.run(runner.run_test_file(test_path))
                        summary = result.get("summary", {})
                        if summary.get("failed", 0) > 0 or summary.get("errors", 0) > 0:
                            all_tests_passed = False
            else:
                # Execute single file
                if robust:
                    runner = RobustTestRunner(kotoba_config)
                elif optimized:
                    runner = OptimizedTestRunner(kotoba_config)
                else:
                    runner = TestRunner(kotoba_config)
                
                logger.info(f"Running test file: {test_file_paths[0]}")
                result = asyncio.run(runner.run_test_file(test_file_paths[0]))
                summary = result.get("summary", {})
                if summary.get("failed", 0) > 0 or summary.get("errors", 0) > 0:
                    all_tests_passed = False
        else:
            # Interactive mode
            runner = TestRunner(kotoba_config)
            asyncio.run(runner.run_interactive())
        
        # Exit with appropriate code
        if test_file_paths and not all_tests_passed:
            logger.error("Some tests failed or had errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()