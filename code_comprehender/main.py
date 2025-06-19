"""Main CLI application for Code Comprehender."""

import sys
from pathlib import Path

import click

from code_comprehender.code_documenter import CodeDocumenter
from code_comprehender.code_visualizer import CodeVisualizer
from code_comprehender.config import OUTPUT_DIR
from code_comprehender.llm_client import LLMClient
from code_comprehender.llm_presets import get_default_preset, get_preset
from code_comprehender.logger import (
    get_logger,
    log_error,
    log_success,
    log_warning,
    set_log_level,
)
from code_comprehender.repository_processor import RepositoryProcessor

logger = get_logger()


@click.command()
@click.argument(
    "java_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
)  # This is just for testing
@click.option(
    "--preset", "-p", default=None, help="LLM preset to use (default: gpt-4o-mini)"
)
@click.option(
    "--output-dir",
    "-o",
    default=OUTPUT_DIR,
    help=f"Output directory (default: {OUTPUT_DIR})",
)
@click.option(
    "--visualize", "-v", is_flag=True, help="Create architecture visualization"
)
@click.option("--github", "-g", help="GitHub repository URL to analyze")
@click.option(
    "--docs-only", is_flag=True, help="Only create documentation (skip visualization)"
)
@click.option("--test-connection", is_flag=True, help="Test LLM connection and exit")
@click.option(
    "--sequential",
    is_flag=True,
    help="Use sequential processing instead of parallel (slower)",
)
@click.option(
    "--performance-profile",
    default="balanced",
    type=click.Choice(["conservative", "balanced", "aggressive"]),
    help="Performance profile: conservative (safe), balanced (default), aggressive (fast for large repos)",
)
def cli(
    java_file: Path,
    preset: str,
    output_dir: str,
    visualize: bool,
    github: str,
    docs_only: bool,
    test_connection: bool,
    sequential: bool,
    performance_profile: str,
):
    """Code Comprehender - Add comprehensive documentation or create architecture visualizations for code files using LLM.

    JAVA_FILE: Path to the Java file to process (not needed when using --github)

    \b
    Examples:
        # Add documentation to a Java file
        uv code-comprehender MyClass.java

        # Create architecture visualization for a single file
        uv code-comprehender --visualize MyClass.java

        # Analyze a GitHub repository (both docs and viz by default, parallel processing)
        uv code-comprehender --github github_url

        # Analyze GitHub repo with only documentation
        uv code-comprehender --github github_url --docs-only

        # Analyze GitHub repo with only visualization
        uv code-comprehender --github github_url --visualize

        # Use specific LLM preset
        uv code-comprehender --preset gpt-4 --github github_url

        # Use sequential processing (slower but more stable)
        uv code-comprehender --github github_url --sequential

        # Use aggressive performance profile for large repos
        uv code-comprehender --github github_url --performance-profile aggressive

        # Use performance profiles for different repository sizes
        uv code-comprehender --github github_url --performance-profile aggressive

        # Test LLM connection
        uv code-comprehender --test-connection
    """
    try:
        # Set up logging level
        set_log_level("INFO")

        # Handle test connection first (before validation)
        if test_connection:
            logger.info("Testing LLM connection...")
            # Get preset and create LLM client directly
            llm_preset = get_preset(preset) if preset else get_default_preset()
            llm_client = LLMClient(llm_preset.model_name)
            if llm_client.test_connection():
                log_success("Connection successful!")
                sys.exit(0)
            else:
                log_error("Connection failed!")
                sys.exit(1)

        # Check for GitHub repository analysis
        if github:
            # Determine what to process
            if docs_only and visualize:
                # Both flags specified - do both operations
                process_docs = True
                process_viz = True
            elif docs_only:
                # Only documentation requested
                process_docs = True
                process_viz = False
            elif visualize:
                # Only visualization requested
                process_docs = False
                process_viz = True
            else:
                # Default: create both documentation and visualization
                process_docs = True
                process_viz = True

            # Initialize repository processor with performance profile
            repo_processor = RepositoryProcessor(
                preset, performance_profile=performance_profile
            )

            # Log performance settings
            logger.info(f"Using performance profile: {performance_profile}")

            # Process GitHub repository
            use_parallel = not sequential
            results = repo_processor.process_github_repository(
                github, output_dir, process_docs, process_viz, use_parallel
            )

            # Display results summary
            summary = results.get("summary", {})
            log_success("GitHub repository processing completed!")
            logger.info(
                f"Repository: {results.get('repository_info', {}).get('name', 'Unknown')}"
            )
            logger.info(f"Total files: {summary.get('total_files', 0)}")
            logger.info(f"Successfully processed: {summary.get('successful_files', 0)}")
            logger.info(f"Failed: {summary.get('failed_files', 0)}")

            if results.get("errors"):
                log_warning(
                    "Some files failed to process. Check the processing report for details."
                )

            logger.info(f"Results saved to: {results.get('output_directory')}")

            return

        # Require Java file for single file operations
        if not java_file:
            log_error(
                "Please provide a Java file path or use --github for repository analysis"
            )
            sys.exit(1)

        # Handle visualization mode
        if visualize:
            visualizer = CodeVisualizer(preset)

            # Create architecture visualization
            viz_path, json_path = visualizer.process_file(str(java_file), output_dir)
            log_success("Successfully created architecture visualization!")
            logger.info(f"Visualization saved to: {viz_path}")
            logger.info(f"Analysis data saved to: {json_path}")
        else:
            # Handle documentation mode (original functionality)
            documenter = CodeDocumenter(preset)

            # Process the Java file
            output_path = documenter.process_file(str(java_file), output_dir)
            log_success("Successfully documented code file!")
            logger.info(f"Output saved to: {output_path}")

    except FileNotFoundError as e:
        log_error(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        log_error(f"Configuration Error: {e}")
        logger.info("Make sure to set your OPENAI_API_KEY environment variable")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
