"""Code parsing and chunking utilities."""

from dataclasses import dataclass
from typing import List, Tuple

import javalang

from code_comprehender.logger import get_logger
from code_comprehender.token_counter import TokenCounter


@dataclass
class CodeChunk:
    """Represents a chunk of Java code with metadata."""

    content: str
    start_line: int
    end_line: int
    chunk_type: str  # 'class', 'method', 'field', 'import', 'package'
    name: str
    token_count: int
    imports: List[str] = None  # Store required imports
    package: str = None  # Store package declaration


class JavaParser:
    """Handles parsing and chunking of Java source code."""

    def __init__(self):
        """Initialize the Java parser."""
        self.token_counter = TokenCounter()
        self.logger = get_logger(self.__class__.__name__)

    def parse_file(self, file_path: str) -> str:
        """Read and return the content of a Java file.

        Args:
            file_path: Path to the Java file

        Returns:
            The content of the Java file

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Java file not found: {file_path}")
        except IOError as e:
            raise IOError(f"Error reading Java file {file_path}: {e}")

    def parse_java_code(self, code: str) -> javalang.tree.CompilationUnit:
        """Parse Java code using javalang.

        Args:
            code: Java source code string

        Returns:
            Parsed compilation unit
        """
        try:
            return javalang.parse.parse(code)
        except Exception as e:
            raise ValueError(f"Failed to parse Java code: {e}")

    def extract_chunks(self, code: str, max_tokens: int) -> List[CodeChunk]:
        """Extract logical chunks from Java code with improved boundaries.

        Args:
            code: Java source code string
            max_tokens: Maximum tokens per chunk

        Returns:
            List of code chunks
        """

        # If too large, parse and chunk by logical units
        try:
            tree = self.parse_java_code(code)
            chunks = []
            lines = code.split("\n")

            # Extract package and imports
            package, imports = self._extract_package_and_imports(code)
            package_imports_header = self._build_header(package, imports)

            # Extract classes and their methods with improved boundaries
            for class_decl in tree.types:
                if isinstance(class_decl, javalang.tree.ClassDeclaration):
                    class_chunks = self._extract_class_chunks_improved(
                        class_decl,
                        lines,
                        package_imports_header,
                        max_tokens,
                        package,
                        imports,
                    )
                    chunks.extend(class_chunks)

            return chunks

        except Exception as e:
            self.logger.warning(f"Parsing failed, using fallback chunking: {e}")
            # If parsing fails, fall back to improved text chunking
            return self._fallback_chunk_improved(code, max_tokens)

    def _extract_package_and_imports(self, code: str) -> Tuple[str, List[str]]:
        """Extract package declaration and import statements.

        Args:
            code: Java source code

        Returns:
            Tuple of (package_name, list_of_imports)
        """
        lines = code.split("\n")
        package = None
        imports = []

        for line in lines:
            line = line.strip()
            if line.startswith("package "):
                package = line
            elif line.startswith("import "):
                imports.append(line)
            elif line and not line.startswith("//") and not line.startswith("/*"):
                # Stop at first non-comment, non-import, non-package line
                break

        return package, imports

    def _build_header(self, package: str, imports: List[str]) -> str:
        """Build the header with package and imports.

        Args:
            package: Package declaration
            imports: List of import statements

        Returns:
            Complete header string
        """
        header_parts = []

        if package:
            header_parts.append(package)
            header_parts.append("")  # Empty line

        if imports:
            header_parts.extend(imports)
            header_parts.append("")  # Empty line

        return "\n".join(header_parts)

    def _extract_class_chunks_improved(
        self,
        class_decl: javalang.tree.ClassDeclaration,
        lines: List[str],
        header: str,
        max_tokens: int,
        package: str,
        imports: List[str],
    ) -> List[CodeChunk]:
        """Extract chunks from a class declaration with improved logic.

        Args:
            class_decl: Class declaration node
            lines: Source code lines
            header: Package and import header
            max_tokens: Maximum tokens per chunk
            package: Package name
            imports: Import statements

        Returns:
            List of chunks for the class
        """
        chunks = []

        # Get class boundaries using improved detection
        start_line = class_decl.position.line - 1
        end_line = self._find_class_end_line_improved(class_decl, lines)

        # Try to include the entire class in one chunk
        class_content = header + "\n".join(lines[start_line : end_line + 1])
        class_tokens = self.token_counter.count_tokens(class_content)

        if class_tokens <= max_tokens:
            chunks.append(
                CodeChunk(
                    content=class_content,
                    start_line=start_line + 1,
                    end_line=end_line + 1,
                    chunk_type="class",
                    name=class_decl.name,
                    token_count=class_tokens,
                    imports=imports,
                    package=package,
                )
            )
        else:
            # Split class into method chunks with improved boundaries
            method_chunks = self._extract_method_chunks_improved(
                class_decl, lines, header, max_tokens, package, imports
            )
            chunks.extend(method_chunks)

        return chunks

    def _extract_method_chunks_improved(
        self,
        class_decl: javalang.tree.ClassDeclaration,
        lines: List[str],
        header: str,
        max_tokens: int,
        package: str,
        imports: List[str],
    ) -> List[CodeChunk]:
        """Extract method-level chunks with improved boundaries and context.

        Args:
            class_decl: Class declaration node
            lines: Source code lines
            header: Package and import header
            max_tokens: Maximum tokens per chunk
            package: Package name
            imports: Import statements

        Returns:
            List of method chunks
        """
        chunks = []

        # Extract class header (up to opening brace)
        class_start = class_decl.position.line - 1
        class_header_end = self._find_class_header_end(lines, class_start)
        class_header_lines = lines[class_start : class_header_end + 1]

        # Build class context for methods
        class_context = header + "\n".join(class_header_lines)

        # Extract each method as a separate chunk
        processed_methods = set()  # Track processed methods to avoid duplicates

        for member in class_decl.body or []:
            if isinstance(member, javalang.tree.MethodDeclaration):
                method_name = f"{class_decl.name}.{member.name}"

                # Skip if already processed (deduplication)
                if method_name in processed_methods:
                    self.logger.warning(f"Skipping duplicate method: {method_name}")
                    continue

                processed_methods.add(method_name)

                method_start = member.position.line - 1
                method_end = self._find_method_end_line_improved(
                    member, lines, method_start
                )

                method_lines = lines[method_start : method_end + 1]
                method_content = (
                    class_context
                    + "\n\n    // Method implementation\n"
                    + "\n".join(["    " + line for line in method_lines])
                    + "\n}"
                )

                method_tokens = self.token_counter.count_tokens(method_content)

                chunk_type = "method" if method_tokens <= max_tokens else "large_method"

                chunks.append(
                    CodeChunk(
                        content=method_content,
                        start_line=method_start + 1,
                        end_line=method_end + 1,
                        chunk_type=chunk_type,
                        name=method_name,
                        token_count=method_tokens,
                        imports=imports,
                        package=package,
                    )
                )

        return chunks

    def _find_class_header_end(self, lines: List[str], class_start: int) -> int:
        """Find the end of class header (where opening brace is).

        Args:
            lines: Source code lines
            class_start: Class start line index

        Returns:
            Line index where class header ends
        """
        for i in range(class_start, len(lines)):
            if "{" in lines[i]:
                return i
        return class_start + 1  # Fallback

    def _find_class_end_line_improved(
        self, class_decl: javalang.tree.ClassDeclaration, lines: List[str]
    ) -> int:
        """Find the end line of a class declaration with improved logic.

        Args:
            class_decl: Class declaration node
            lines: Source code lines

        Returns:
            End line index (0-based)
        """
        start_line = class_decl.position.line - 1
        brace_count = 0
        found_opening_brace = False

        for i in range(start_line, len(lines)):
            line = lines[i]

            # Count braces more carefully
            for char in line:
                if char == "{":
                    brace_count += 1
                    found_opening_brace = True
                elif char == "}":
                    brace_count -= 1

                    # If we've found the opening brace and count reaches 0, we've found the end
                    if found_opening_brace and brace_count == 0:
                        return i

        return len(lines) - 1

    def _find_method_end_line_improved(
        self,
        method_decl: javalang.tree.MethodDeclaration,
        lines: List[str],
        start_line: int,
    ) -> int:
        """Find the end line of a method declaration with improved logic.

        Args:
            method_decl: Method declaration node
            lines: Source code lines
            start_line: Start line index (0-based)

        Returns:
            End line index (0-based)
        """
        brace_count = 0
        found_opening_brace = False

        for i in range(start_line, len(lines)):
            line = lines[i]

            # Count braces more carefully, ignoring string literals
            in_string = False
            in_char = False
            escape_next = False

            for char in line:
                if escape_next:
                    escape_next = False
                    continue

                if char == "\\":
                    escape_next = True
                    continue

                if char == '"' and not in_char:
                    in_string = not in_string
                elif char == "'" and not in_string:
                    in_char = not in_char
                elif not in_string and not in_char:
                    if char == "{":
                        brace_count += 1
                        found_opening_brace = True
                    elif char == "}":
                        brace_count -= 1

                        if found_opening_brace and brace_count == 0:
                            return i

        return len(lines) - 1

    def _fallback_chunk_improved(self, code: str, max_tokens: int) -> List[CodeChunk]:
        """Improved fallback chunking strategy when parsing fails.

        Args:
            code: Java source code
            max_tokens: Maximum tokens per chunk

        Returns:
            List of text chunks with better boundaries
        """
        lines = code.split("\n")
        chunks = []
        current_chunk = []
        current_tokens = 0

        package, imports = self._extract_package_and_imports(code)
        header = self._build_header(package, imports)
        header_tokens = self.token_counter.count_tokens(header)

        for i, line in enumerate(lines):
            line_tokens = self.token_counter.count_tokens(line)

            # Try to break at logical boundaries (method/class endings)
            is_logical_boundary = (
                line.strip().endswith("}")
                or line.strip().startswith("public ")
                or line.strip().startswith("private ")
                or line.strip().startswith("protected ")
                or line.strip() == ""
                or line.strip().startswith("//")
            )

            if (
                current_tokens + line_tokens + header_tokens > max_tokens
                and current_chunk
                and is_logical_boundary
            ):
                # Save current chunk with header
                chunk_content = header + "\n" + "\n".join(current_chunk)
                chunks.append(
                    CodeChunk(
                        content=chunk_content,
                        start_line=i - len(current_chunk) + 1,
                        end_line=i,
                        chunk_type="text_chunk",
                        name=f"chunk_{len(chunks) + 1}",
                        token_count=current_tokens + header_tokens,
                        imports=imports,
                        package=package,
                    )
                )
                current_chunk = [line]
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens

        # Add final chunk
        if current_chunk:
            chunk_content = header + "\n" + "\n".join(current_chunk)
            chunks.append(
                CodeChunk(
                    content=chunk_content,
                    start_line=len(lines) - len(current_chunk) + 1,
                    end_line=len(lines),
                    chunk_type="text_chunk",
                    name=f"chunk_{len(chunks) + 1}",
                    token_count=current_tokens + header_tokens,
                    imports=imports,
                    package=package,
                )
            )

        return chunks

    def validate_java_syntax(self, code: str) -> Tuple[bool, str]:
        """Validate that Java code compiles.

        Args:
            code: Java source code

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to parse with javalang first (quick check)
            self.parse_java_code(code)
            return True, ""
        except Exception as e:
            return False, str(e)

    def extract_imports_from_code(self, code: str) -> List[str]:
        """Extract all import statements from Java code.

        Args:
            code: Java source code

        Returns:
            List of import statements
        """
        _, imports = self._extract_package_and_imports(code)
        return imports

    def deduplicate_methods(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """Remove duplicate method chunks.

        Args:
            chunks: List of code chunks

        Returns:
            Deduplicated list of chunks
        """
        seen_methods = set()
        deduplicated = []

        for chunk in chunks:
            if chunk.chunk_type in ["method", "large_method"]:
                if chunk.name not in seen_methods:
                    seen_methods.add(chunk.name)
                    deduplicated.append(chunk)
                else:
                    self.logger.warning(
                        f"Removing duplicate method chunk: {chunk.name}"
                    )
            else:
                deduplicated.append(chunk)

        return deduplicated
