"""Code documentation functionality for Java files."""

import os
from pathlib import Path
from typing import List

from code_comprehender.config import OUTPUT_DIR
from code_comprehender.java_parser import CodeChunk, JavaParser
from code_comprehender.llm_client import LLMClient
from code_comprehender.llm_presets import get_default_preset, get_preset
from code_comprehender.logger import get_logger
from code_comprehender.token_counter import TokenCounter


class CodeDocumenter:
    """Main class for code documentation."""

    def __init__(self, preset_name: str = None):
        self.logger = get_logger(self.__class__.__name__)

        # Get the preset configuration
        if preset_name:
            self.preset = get_preset(preset_name)
        else:
            self.preset = get_default_preset()

        # Use preset settings directly
        self.max_tokens = self.preset.max_chunk_size

        # Initialize components with preset settings
        self.java_parser = JavaParser()
        self.llm_client = LLMClient(self.preset.model_name)
        self.token_counter = TokenCounter(self.preset.model_name)

        # Remove verbose preset logging

    def process_file(self, java_file_path: str, output_dir: str = OUTPUT_DIR) -> str:
        """Process a single Java file.

        Args:
            java_file_path: Path to the Java file
            output_dir: Directory to save the documented file

        Returns:
            Path to the output file
        """
        if not os.path.exists(java_file_path):
            raise FileNotFoundError(f"Java file not found: {java_file_path}")

        self.logger.info(f"Processing: {java_file_path}")

        # Read the Java file
        try:
            code = self.java_parser.parse_file(java_file_path)
        except Exception as e:
            raise Exception(f"Failed to read Java file: {e}")

        # Validate original code syntax
        # is_valid, error_msg = self.java_parser.validate_java_syntax(code)
        # if not is_valid:
        #     self.logger.warning(f"Original code has syntax issues: {error_msg}")

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
            # print('chunks: ', chunks)
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

        # Document the chunks
        try:
            documented_chunks = self.llm_client.document_chunks(chunks)
        except Exception as e:
            raise Exception(f"Failed to document code: {e}")

        # Combine documented chunks with improved merging
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
        self.logger.info(f"Documented code saved to: {output_path}")

        return output_path

    def _combine_chunks_improved(
        self, chunks: List[CodeChunk], documented_chunks: List[str]
    ) -> str:
        """Combine multiple documented chunks into a single file with improved logic.

        Args:
            chunks: Original chunks
            documented_chunks: Documented chunk contents

        Returns:
            Combined documented code
        """
        if not chunks or not documented_chunks:
            return ""

        # If we have a single full file chunk, return it directly
        if len(chunks) == 1 and chunks[0].chunk_type == "full_file":
            return documented_chunks[0]

        # Separate different types of chunks
        package_import_chunks = []
        class_chunks = []
        method_chunks = []
        other_chunks = []

        for i, chunk in enumerate(chunks):
            if chunk.chunk_type == "package_imports":
                package_import_chunks.append((chunk, documented_chunks[i]))
            elif chunk.chunk_type == "class":
                class_chunks.append((chunk, documented_chunks[i]))
            elif chunk.chunk_type in ["method", "large_method"]:
                method_chunks.append((chunk, documented_chunks[i]))
            else:
                other_chunks.append((chunk, documented_chunks[i]))

        # Build the final code systematically
        final_parts = []

        # 1. Add package and imports (from first chunk if available)
        if chunks[0].package:
            final_parts.append(chunks[0].package)
            final_parts.append("")

        if chunks[0].imports:
            final_parts.extend(chunks[0].imports)
            final_parts.append("")

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
        self, method_chunks: List[tuple], reference_chunk: CodeChunk
    ) -> str:
        """Reconstruct a class from individual method chunks.

        Args:
            method_chunks: List of (chunk, documented_content) tuples
            reference_chunk: Reference chunk for class structure

        Returns:
            Reconstructed class
        """
        if not method_chunks:
            return ""

        # Start with a basic class structure
        class_lines = []

        # Extract class name from the first method chunk
        first_method_name = method_chunks[0][0].name
        class_name = (
            first_method_name.split(".")[0]
            if "." in first_method_name
            else "GeneratedClass"
        )

        class_lines.append(f"public class {class_name} {{")
        class_lines.append("")

        # Add each method
        processed_methods = set()
        for chunk, documented in method_chunks:
            method_content = self._extract_method_from_documented_chunk(documented)
            if method_content and chunk.name not in processed_methods:
                class_lines.append("    " + method_content.replace("\n", "\n    "))
                class_lines.append("")
                processed_methods.add(chunk.name)

        class_lines.append("}")

        return "\n".join(class_lines)

    def _extract_method_from_documented_chunk(self, documented_chunk: str) -> str:
        """Extract method code from a documented chunk with improved logic.

        Args:
            documented_chunk: Documented chunk containing class header + method

        Returns:
            Just the method part
        """
        lines = documented_chunk.split("\n")
        method_lines = []
        in_method = False
        brace_count = 0

        for line in lines:
            stripped = line.strip()

            # Look for method signatures (improved detection)
            if not in_method:
                # Skip class declaration, package, imports
                if (
                    stripped.startswith("package ")
                    or stripped.startswith("import ")
                    or stripped.startswith("public class ")
                    or stripped.startswith("class ")
                    or stripped == ""
                    or stripped.startswith("//")
                    or stripped.startswith("/*")
                ):
                    continue

                # Look for method signature
                if (
                    (
                        "public " in stripped
                        or "private " in stripped
                        or "protected " in stripped
                    )
                    and "(" in stripped
                    and ")" in stripped
                    and not stripped.startswith("class")
                ):
                    in_method = True

            if in_method:
                method_lines.append(line)
                brace_count += line.count("{") - line.count("}")
                if brace_count <= 0 and "{" in "".join(method_lines):
                    break

        return "\n".join(method_lines) if method_lines else documented_chunk

    def _fix_common_syntax_issues(self, code: str) -> str:
        """Fix common syntax issues in generated code.

        Args:
            code: Java code that may have syntax issues

        Returns:
            Code with common issues fixed
        """
        lines = code.split("\n")
        fixed_lines = []

        # Track imports to avoid duplicates
        seen_imports = set()
        imports_section = True

        for line in lines:
            stripped = line.strip()

            # Handle imports
            if imports_section and stripped.startswith("import "):
                if stripped not in seen_imports:
                    seen_imports.add(stripped)
                    fixed_lines.append(line)
                continue
            elif (
                stripped
                and not stripped.startswith("package ")
                and not stripped.startswith("//")
            ):
                imports_section = False

            # Add missing Scanner import if Scanner is used but not imported
            if (
                "Scanner" in line
                and "new Scanner" in line
                and "import java.util.Scanner;" not in seen_imports
            ):
                fixed_lines.insert(-1, "import java.util.Scanner;")
                seen_imports.add("import java.util.Scanner;")

            fixed_lines.append(line)

        # Ensure Scanner import is present if needed
        code_content = "\n".join(fixed_lines)
        if (
            "Scanner" in code_content
            and "import java.util.Scanner;" not in code_content
        ):
            # Find the right place to insert the import
            final_lines = []
            inserted_import = False

            for line in fixed_lines:
                if not inserted_import and (
                    line.strip().startswith("public class")
                    or (
                        line.strip()
                        and not line.strip().startswith("package")
                        and not line.strip().startswith("import")
                    )
                ):
                    final_lines.append("import java.util.Scanner;")
                    final_lines.append("")
                    inserted_import = True
                final_lines.append(line)

            return "\n".join(final_lines)

        return "\n".join(fixed_lines)

    def _save_output(
        self, java_file_path: str, documented_code: str, output_dir: str
    ) -> str:
        """Save the documented code to an output file.

        Args:
            java_file_path: Original Java file path
            documented_code: Documented Java code
            output_dir: Output directory

        Returns:
            Path to the saved output file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate output file path
        file_name = Path(java_file_path).name
        output_path = os.path.join(output_dir, file_name)

        # Write the documented code
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(documented_code)

        return output_path
