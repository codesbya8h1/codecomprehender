"""Code visualization module for creating architecture diagrams."""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from pyvis.network import Network

from code_comprehender.java_parser import CodeChunk, JavaParser
from code_comprehender.llm_client import LLMClient
from code_comprehender.llm_presets import get_default_preset, get_preset
from code_comprehender.logger import get_logger, log_progress, log_success, log_warning
from code_comprehender.prompts import VISUALIZATION_PROMPT
from code_comprehender.token_counter import TokenCounter


@dataclass(frozen=True)
class CodeNode:
    """Represents a node in the code architecture."""

    name: str
    node_type: str  # 'class', 'method', 'external'
    parent: str = None  # Parent class for methods


@dataclass(frozen=True)
class CodeRelationship:
    """Represents a relationship between code nodes."""

    from_node: str
    to_node: str
    relationship_type: str  # 'method_call', 'dependency', 'external_call'


class CodeVisualizer:
    """Creates visual representations of code architecture."""

    def __init__(self, preset_name: str = None):
        """Initialize the code visualizer.

        Args:
            preset_name: Name of the LLM preset to use
        """
        self.logger = get_logger(self.__class__.__name__)

        # Get the preset configuration
        if preset_name:
            self.preset = get_preset(preset_name)
        else:
            self.preset = get_default_preset()

        # Reuse existing components with preset settings
        self.java_parser = JavaParser()
        self.llm_client = LLMClient(self.preset.model_name)
        self.token_counter = TokenCounter(self.preset.model_name)

        # Visualization data
        self.nodes: Set[CodeNode] = set()
        self.relationships: List[CodeRelationship] = []

    def analyze_code_architecture(self, java_file_path: str) -> Dict[str, Any]:
        """Analyze Java code to extract architectural relationships.

        Args:
            java_file_path: Path to the Java file

        Returns:
            Dictionary containing architectural analysis results
        """
        if not os.path.exists(java_file_path):
            raise FileNotFoundError(f"Java file not found: {java_file_path}")

        self.logger.info(f"Analyzing architecture of: {java_file_path}")

        # Read and parse the Java file
        try:
            code = self.java_parser.parse_file(java_file_path)
        except Exception as e:
            raise Exception(f"Failed to read Java file: {e}")

        # Check if we need to chunk the code
        total_tokens = self.token_counter.count_tokens(code)
        max_tokens = 15000  # Conservative limit for analysis

        if total_tokens <= max_tokens:
            self.logger.info("File is within token limit, analyzing as single chunk")
            chunks = [
                CodeChunk(
                    content=code,
                    start_line=1,
                    end_line=len(code.split("\n")),
                    chunk_type="full_file",
                    name="complete_file",
                    token_count=total_tokens,
                )
            ]
        else:
            self.logger.info(
                f"File exceeds token limit ({max_tokens:,}), chunking for analysis"
            )
            chunks = self.java_parser.extract_chunks(code, max_tokens)
            self.logger.info(f"Created {len(chunks)} chunks for analysis")

        # Analyze each chunk with LLM
        analysis_results = []
        for i, chunk in enumerate(chunks):
            log_progress(
                f"Analyzing chunk: {chunk.name} ({chunk.token_count:,} tokens)",
                i + 1,
                len(chunks),
            )

            try:
                # Get architectural analysis from LLM
                result = self._analyze_chunk_with_llm(chunk.content)
                if result:
                    analysis_results.append(result)
            except Exception as e:
                self.logger.warning(f"Failed to analyze chunk {chunk.name}: {e}")

        # Combine all analysis results
        combined_analysis = self._combine_analysis_results(analysis_results)

        # Extract nodes and relationships
        self._extract_nodes_and_relationships(combined_analysis)

        return combined_analysis

    def _analyze_chunk_with_llm(self, code: str) -> Dict[str, Any]:
        """Analyze a code chunk using LLM to extract relationships.

        Args:
            code: Code chunk content

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Use LLM to analyze the code
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=VISUALIZATION_PROMPT),
                HumanMessage(
                    content=f"Analyze this code for architectural relationships:\n\n{code}"
                ),
            ]

            response = self.llm_client.llm.invoke(messages)
            response_content = response.content.strip()

            # Parse JSON response
            try:
                analysis_result = json.loads(response_content)
                return analysis_result
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse LLM response as JSON: {e}")
                self.logger.debug(f"LLM response: {response_content}")
                return None

        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return None

    def _combine_analysis_results(
        self, analysis_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Combine multiple analysis results into a single structure.

        Args:
            analysis_results: List of analysis dictionaries

        Returns:
            Combined analysis dictionary
        """
        combined = {"classes": [], "relationships": [], "external_calls": []}

        # Track seen classes to avoid duplicates
        seen_classes = set()

        for result in analysis_results:
            # Combine classes
            for class_info in result.get("classes", []):
                class_name = class_info.get("name")
                if class_name and class_name not in seen_classes:
                    combined["classes"].append(class_info)
                    seen_classes.add(class_name)

            # Add all relationships
            combined["relationships"].extend(result.get("relationships", []))
            combined["external_calls"].extend(result.get("external_calls", []))

        return combined

    def _extract_nodes_and_relationships(self, analysis: Dict[str, Any]):
        """Extract nodes and relationships from analysis results.

        Args:
            analysis: Combined analysis dictionary
        """
        # Clear existing data
        self.nodes.clear()
        self.relationships.clear()

        # Extract class nodes
        for class_info in analysis.get("classes", []):
            class_name = class_info.get("name")
            if class_name:
                # Add class node
                self.nodes.add(CodeNode(name=class_name, node_type="class"))

                # Add method nodes
                for method in class_info.get("methods", []):
                    self.nodes.add(
                        CodeNode(
                            name=f"{class_name}.{method}",
                            node_type="method",
                            parent=class_name,
                        )
                    )

        # Extract relationships
        for relationship in analysis.get("relationships", []):
            from_node = relationship.get("from")
            to_node = relationship.get("to")
            rel_type = relationship.get("type", "method_call")

            if from_node and to_node:
                self.relationships.append(
                    CodeRelationship(
                        from_node=from_node, to_node=to_node, relationship_type=rel_type
                    )
                )

        # Extract external calls
        for external_call in analysis.get("external_calls", []):
            from_node = external_call.get("from")
            to_node = external_call.get("to")

            if from_node and to_node:
                # Add external node if not exists
                self.nodes.add(CodeNode(name=to_node, node_type="external"))

                self.relationships.append(
                    CodeRelationship(
                        from_node=from_node,
                        to_node=to_node,
                        relationship_type="external_call",
                    )
                )

    def _get_node_color(self, node_type: str) -> str:
        """Get color for node based on type."""
        if node_type == "class":
            return "#1976D2"  # Blue for classes
        elif node_type == "method":
            return "#4CAF50"  # Green for methods
        elif node_type == "external":
            return "#F44336"  # Red for external dependencies
        else:
            return "#9E9E9E"  # Gray for unknown

    def _get_node_shape(self, node_type: str) -> str:
        """Get shape for node based on type."""
        if node_type == "class":
            return "box"  # Rectangle for classes
        elif node_type == "method":
            return "ellipse"  # Oval for methods
        elif node_type == "external":
            return "diamond"  # Diamond for external dependencies
        else:
            return "dot"  # Circle for unknown

    def _get_edge_color(self, relationship_type: str) -> str:
        """Get color for edge based on relationship type."""
        if relationship_type == "method_call":
            return "#2196F3"  # Blue for method calls
        elif relationship_type == "external_call":
            return "#FF5722"  # Deep orange for external calls
        elif relationship_type == "dependency":
            return "#4CAF50"  # Green for dependencies
        else:
            return "#9E9E9E"  # Gray for unknown

    def create_visualization(self, output_path: str, file_name: str) -> str:
        """Create an interactive network diagram of the code architecture.

        Args:
            output_path: Directory to save the visualization
            file_name: Base name for the output file

        Returns:
            Path to the saved visualization file
        """
        if not self.nodes:
            raise ValueError("No nodes found. Run analyze_code_architecture() first.")

        os.makedirs(output_path, exist_ok=True)

        # Create pyvis network
        net = Network(
            directed=True,
            height="800px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#333333",
            notebook=False,
        )

        # Configure clean hierarchical layout inspired by user's example
        net.set_options("""
        var options = {
          "layout": {
            "hierarchical": {
              "enabled": true,
              "direction": "UD",
              "sortMethod": "directed",
              "levelSeparation": 120,
              "nodeSpacing": 150,
              "treeSpacing": 200,
              "blockShifting": false,
              "edgeMinimization": true,
              "parentCentralization": true,
              "shakeTowards": "roots"
            }
          },
          "physics": {
            "enabled": false
          },
          "nodes": {
            "font": {"size": 12, "face": "Arial", "color": "#333"},
            "margin": 8,
            "borderWidth": 2,
            "shadow": false,
            "widthConstraint": {"maximum": 180}
          },
          "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 1}},
            "smooth": {"enabled": false},
            "width": 1,
            "shadow": false
          }
        }
        """)

        # Add nodes with hierarchical levels
        for node in self.nodes:
            color = self._get_node_color(node.node_type)
            shape = self._get_node_shape(node.node_type)

            # Create node label and title
            if node.node_type == "method" and "." in node.name:
                label = node.name.split(".")[-1]  # Show only method name
                title = f"Method: {node.name}\\nParent: {node.parent}"
            elif node.node_type == "external":
                label = node.name.split(".")[-1] if "." in node.name else node.name
                title = f"External: {node.name}"
            else:
                label = node.name
                title = f"Class: {node.name}"

            # Truncate long labels
            if len(label) > 20:
                label = label[:17] + "..."

            # Set hierarchical level for proper tree layout
            if node.node_type == "class":
                level = 0  # Root level
                size = 30
            elif node.node_type == "method":
                level = 1  # Second level
                size = 20
            else:  # external
                level = 2  # Third level
                size = 15

            net.add_node(
                node.name,
                label=label,
                title=title,
                color=color,
                shape=shape,
                size=size,
                level=level,
            )

        # Create a set of valid node names for validation
        valid_nodes = {node.name for node in self.nodes}

        # First, add parent-child relationships (class to methods)
        for node in self.nodes:
            if (
                node.node_type == "method"
                and node.parent
                and node.parent in valid_nodes
            ):
                # Add edge from parent class to method
                net.add_edge(
                    node.parent,
                    node.name,
                    title=f"contains: {node.parent} → {node.name}",
                    color="#666666",  # Gray for containment relationships
                    width=1,
                    dashes=False,
                )

        # Then add only meaningful hierarchical relationships
        # Only show external dependencies from methods to external services
        for relationship in self.relationships:
            # Only add edges where both nodes exist
            if (
                relationship.from_node not in valid_nodes
                or relationship.to_node not in valid_nodes
            ):
                log_warning(
                    f"Skipping edge {relationship.from_node} → {relationship.to_node}: missing node(s)"
                )
                continue

            # Only show external calls (method → external dependency)
            # Skip confusing method-to-method calls that clutter the tree
            if relationship.relationship_type == "external_call":
                edge_color = self._get_edge_color(relationship.relationship_type)
                title = f"uses: {relationship.from_node} → {relationship.to_node}"

                net.add_edge(
                    relationship.from_node,
                    relationship.to_node,
                    title=title,
                    color=edge_color,
                    width=2,
                    dashes=False,
                )

        # Save the interactive HTML file
        output_file = os.path.join(output_path, f"{file_name}_architecture.html")
        net.show(output_file, notebook=False)

        log_success(f"Interactive architecture diagram saved to: {output_file}")

        # Also save the analysis data as JSON
        json_file = os.path.join(output_path, f"{file_name}_analysis.json")
        analysis_data = {
            "nodes": [
                {"name": node.name, "type": node.node_type, "parent": node.parent}
                for node in self.nodes
            ],
            "relationships": [
                {
                    "from": rel.from_node,
                    "to": rel.to_node,
                    "type": rel.relationship_type,
                }
                for rel in self.relationships
            ],
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)

        log_success(f"Analysis data saved to: {json_file}")

        return output_file

    def analyze_file_structure(self, java_file_path: str) -> Dict[str, Any]:
        """Analyze Java code structure without creating visualization files.

        This method only performs the architectural analysis and returns the data
        for use in combined repository visualizations.

        Args:
            java_file_path: Path to the Java file

        Returns:
            Dictionary containing analysis data with nodes and relationships
        """
        # Analyze the code architecture
        self.analyze_code_architecture(java_file_path)

        # Convert to the format expected by repository processor
        analysis_data = {
            "nodes": [
                {"name": node.name, "type": node.node_type, "parent": node.parent}
                for node in self.nodes
            ],
            "relationships": [
                {
                    "from": rel.from_node,
                    "to": rel.to_node,
                    "type": rel.relationship_type,
                }
                for rel in self.relationships
            ],
        }

        return analysis_data

    def process_file(
        self, java_file_path: str, output_dir: str = "output"
    ) -> Tuple[str, str]:
        """Complete pipeline to analyze and visualize Java code architecture.

        Args:
            java_file_path: Path to the Java file
            output_dir: Directory to save outputs

        Returns:
            Tuple of (visualization_file_path, analysis_file_path)
        """
        # Extract file name for output
        file_name = Path(java_file_path).stem

        # Analyze the code
        self.analyze_code_architecture(java_file_path)

        # Create visualization
        viz_path = self.create_visualization(output_dir, file_name)
        json_path = os.path.join(output_dir, f"{file_name}_analysis.json")

        return viz_path, json_path
