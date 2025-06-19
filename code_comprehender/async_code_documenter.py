"""Async code documenter for parallel processing."""

import asyncio
import os
from pathlib import Path
from typing import List

from code_comprehender.async_llm_client import AsyncLLMClient
from code_comprehender.config import OUTPUT_DIR
from code_comprehender.java_parser import CodeChunk, JavaParser
from code_comprehender.llm_presets import get_default_preset, get_preset
from code_comprehender.logger import get_logger, log_warning
from code_comprehender.token_counter import TokenCounter


class AsyncCodeDocumenter:
    """Async version of code documenter for parallel processing."""

    def __init__(self, preset_name: str = None, performance_profile: str = "balanced"):
        """Initialize the async code documenter.

        Args:
            preset_name: Name of the LLM preset to use
            performance_profile: Performance profile for concurrency settings
        """
        self.logger = get_logger(self.__class__.__name__)

        # Get LLM preset
        self.preset = get_preset(preset_name) if preset_name else get_default_preset()
        self.max_tokens = self.preset.max_chunk_size

        # Store performance profile
        self.performance_profile = performance_profile

        # Initialize processors
        self.java_parser = JavaParser()
        self.token_counter = TokenCounter()



    async def process_file_async(
        self, java_file_path: str, output_dir: str = OUTPUT_DIR
    ) -> str:
        """Process a single Java file asynchronously.

        Args:
            java_file_path: Path to the Java file
            output_dir: Directory to save the documented file

        Returns:
            Path to the output file
        """
        if not os.path.exists(java_file_path):
            raise FileNotFoundError(f"Java file not found: {java_file_path}")


        # Read the Java file
        try:
            code = self.java_parser.parse_file(java_file_path)
        except Exception as e:
            raise Exception(f"Failed to read Java file: {e}")

        # Check token count and chunk if needed
        total_tokens = self.token_counter.count_tokens(code)

        if total_tokens <= self.max_tokens:
            chunks = [
                CodeChunk(
                    content=code,
                    start_line=1,
                    end_line=len(code.split("\n")),
                    chunk_type="full_file",
                    name="complete_file",
                    token_count=total_tokens,
                    imports=self.java_parser.extract_imports_from_code(code),
                    package=self.java_parser._extract_package_and_imports(code)[0],
                )
            ]
        else:
            self.logger.info(
                f"Large file ({total_tokens:,} tokens), creating {self.max_tokens:,} token chunks"
            )
            chunks = self.java_parser.extract_chunks(code, self.max_tokens)

            # Apply deduplication
            original_count = len(chunks)
            chunks = self.java_parser.deduplicate_methods(chunks)
            if len(chunks) < original_count:
                self.logger.info(
                    f"Removed {original_count - len(chunks)} duplicate chunks"
                )

        # Document the chunks asynchronously
        try:
            async_client = AsyncLLMClient(
                model_name=self.preset.model_name,
                performance_profile=self.performance_profile,
            )
            documented_chunks = await async_client.document_chunks_async(chunks)
        except Exception as e:
            raise Exception(f"Failed to document code: {e}")

        # Combine documented chunks
        if len(chunks) == 1:
            final_code = documented_chunks[0]
        else:
            final_code = self._combine_chunks_improved(chunks, documented_chunks)

        # Validate the final code
        is_valid, error_msg = self.java_parser.validate_java_syntax(final_code)
        if not is_valid:
            self.logger.warning(f"Final documented code has syntax issues: {error_msg}")
            # Try to fix common issues
            final_code = self._fix_common_syntax_issues(final_code)

        # Save to output file
        output_path = self._save_output(java_file_path, final_code, output_dir)


        return output_path

    def _combine_chunks_improved(
        self, chunks: List[CodeChunk], documented_chunks: List[str]
    ) -> str:
        """Combine documented chunks with improved merging logic.

        Args:
            chunks: Original code chunks
            documented_chunks: Documented code chunks

        Returns:
            Combined documented code
        """
        if not chunks or not documented_chunks:
            return ""

        final_parts = []

        # Extract package and imports from first chunk
        first_chunk_code = documented_chunks[0]
        package_line, imports = self.java_parser._extract_package_and_imports(
            first_chunk_code
        )

        # 1. Add package and imports
        if package_line:
            final_parts.append(package_line)
            final_parts.append("")  # Empty line after package

        if imports:
            final_parts.extend(imports)
            final_parts.append("")  # Empty line after imports

        # Categorize chunks
        class_chunks = []
        method_chunks = []

        for chunk, documented in zip(chunks, documented_chunks):
            if chunk.chunk_type in ["class", "full_file"]:
                class_chunks.append((chunk, documented))
            elif chunk.chunk_type == "method":
                method_chunks.append((chunk, documented))

        # 2. Add class definitions
        if class_chunks:
            # Use the documented class chunks directly
            for chunk, documented in class_chunks:
                # Extract just the class part (skip duplicate headers)
                class_content = self._extract_class_content(documented)
                final_parts.append(class_content)
        elif method_chunks:
            # If we only have method chunks, we need to reconstruct the class
            final_parts.append(
                self._reconstruct_class_from_methods(method_chunks, chunks[0])
            )
        else:
            # Fallback: concatenate all documented chunks
            for chunk, documented in zip(chunks, documented_chunks):
                final_parts.append(documented)

        return "\n".join(final_parts)

    def _extract_class_content(self, documented_code: str) -> str:
        """Extract class content, removing duplicate package/import headers.

        Args:
            documented_code: Documented code that may contain headers

        Returns:
            Clean class content
        """
        lines = documented_code.split("\n")
        class_started = False
        class_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip package and import lines at the beginning
            if not class_started:
                if (
                    stripped.startswith("package ")
                    or stripped.startswith("import ")
                    or stripped == ""
                    or stripped.startswith("//")
                    or stripped.startswith("/*")
                ):
                    continue
                else:
                    class_started = True

            if class_started:
                class_lines.append(line)

        return "\n".join(class_lines)

    def _reconstruct_class_from_methods(
        self, method_chunks: List[tuple], first_chunk: CodeChunk
    ) -> str:
        """Reconstruct class from method chunks.

        Args:
            method_chunks: List of (chunk, documented_code) tuples
            first_chunk: First chunk for class structure

        Returns:
            Reconstructed class code
        """
        # Extract class header from first chunk
        class_header = self._extract_class_header(first_chunk.content)

        # Combine all method bodies
        method_bodies = []
        for chunk, documented in method_chunks:
            method_body = self._extract_method_content(documented)
            if method_body.strip():
                method_bodies.append(method_body)

        # Reconstruct class
        class_parts = [class_header]
        class_parts.extend(method_bodies)
        class_parts.append("}")  # Close class

        return "\n".join(class_parts)

    def _extract_class_header(self, code: str) -> str:
        """Extract class header from code."""
        lines = code.split("\n")
        header_lines = []

        for line in lines:
            stripped = line.strip()
            header_lines.append(line)

            # Stop after class declaration
            if (
                stripped.startswith("public class ")
                or stripped.startswith("class ")
                or stripped.startswith("public abstract class ")
            ) and stripped.endswith("{"):
                break

        return "\n".join(header_lines)

    def _extract_method_content(self, documented_code: str) -> str:
        """Extract method content from documented code."""
        lines = documented_code.split("\n")
        method_lines = []
        in_method = False

        for line in lines:
            stripped = line.strip()

            # Skip package/imports at the beginning
            if not in_method:
                if (
                    stripped.startswith("package ")
                    or stripped.startswith("import ")
                    or (stripped == "" and not method_lines)
                ):
                    continue
                else:
                    in_method = True

            if in_method:
                method_lines.append(line)

        return "\n".join(method_lines)

    def _fix_common_syntax_issues(self, code: str) -> str:
        """Fix common syntax issues in the generated code.

        Args:
            code: Code with potential syntax issues

        Returns:
            Code with common issues fixed
        """
        lines = code.split("\n")
        fixed_lines = []

        # Track if we've seen Scanner import
        has_scanner_import = any("import java.util.Scanner" in line for line in lines)
        added_scanner_import = False

        for line in lines:
            # Add Scanner import if we see Scanner usage but no import
            if (
                not has_scanner_import
                and not added_scanner_import
                and "Scanner" in line
                and "import" not in line
            ):
                # Find the right place to add import (after package, before class)
                if line.strip().startswith("public class") or line.strip().startswith(
                    "class"
                ):
                    fixed_lines.append("import java.util.Scanner;")
                    fixed_lines.append("")
                    added_scanner_import = True

            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def _save_output(
        self, original_path: str, documented_code: str, output_dir: str
    ) -> str:
        """Save the documented code to output file.

        Args:
            original_path: Path to the original Java file
            documented_code: Documented code
            output_dir: Output directory

        Returns:
            Path to the saved output file
        """

        os.makedirs(output_dir, exist_ok=True)

        # Generate output filename
        original_filename = Path(original_path).name
        output_filename = original_filename
        output_path = os.path.join(output_dir, output_filename)

        # Save the documented code
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(documented_code)

        return output_path

    @staticmethod
    def process_files_parallel(
        file_paths: List[str],
        output_dir: str = OUTPUT_DIR,
        preset_name: str = None,
        performance_profile: str = "balanced",
    ) -> List[str]:
        """Process multiple files in parallel (convenience method for sync code).

        Args:
            file_paths: List of Java file paths to process
            output_dir: Output directory
            preset_name: LLM preset name
            performance_profile: Performance profile for concurrency settings

        Returns:
            List of output file paths
        """

        async def _process_all():
            documenter = AsyncCodeDocumenter(preset_name, performance_profile)

    
            tasks = []
            for file_path in file_paths:
                task = documenter.process_file_async(file_path, output_dir)
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            output_paths = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    log_warning(f"Failed to process {file_paths[i]}: {result}")
                    output_paths.append(None)
                else:
                    output_paths.append(result)

            return output_paths

        # Run the async function
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_process_all())
