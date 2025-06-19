"""Repository Architecture Analyzer - Creates high-level architectural visualizations."""

import json
import os
from typing import List, Dict, Any, Set, Tuple, Optional
from pathlib import Path
from pyvis.network import Network

from code_comprehender.java_parser import JavaParser
from code_comprehender.llm_client import LLMClient
from code_comprehender.token_counter import TokenCounter
from code_comprehender.prompts import REPOSITORY_ARCHITECTURE_PROMPT
from code_comprehender.logger import get_logger, log_progress, log_success, log_warning
from code_comprehender.llm_presets import get_preset, get_default_preset


class RepositoryArchitectureAnalyzer:
    """Analyzes and visualizes repository-level architecture showing file-to-file relationships."""
    
    def __init__(self, preset_name: str = None):
        """Initialize the repository architecture analyzer.
        
        Args:
            preset_name: Name of the LLM preset to use
        """
        self.logger = get_logger(self.__class__.__name__)
        
        # Get the preset configuration
        if preset_name:
            self.preset = get_preset(preset_name)
        else:
            self.preset = get_default_preset()
        
        # Initialize components
        self.java_parser = JavaParser()
        self.llm_client = LLMClient(self.preset.model_name)
        self.token_counter = TokenCounter(self.preset.model_name)
        
        # Architecture data
        self.file_analyses: Dict[str, Dict[str, Any]] = {}
        self.file_relationships: List[Dict[str, Any]] = []
        
        self.logger.info(f"Repository Architecture Analyzer initialized with preset: {self.preset.name}")
    
    def analyze_file_architecture(self, java_file_path: str) -> Dict[str, Any]:
        """Analyze a single Java file for repository-level architecture.
        
        Args:
            java_file_path: Path to the Java file
            
        Returns:
            Dictionary containing architectural analysis results
        """
        if not os.path.exists(java_file_path):
            raise FileNotFoundError(f"Java file not found: {java_file_path}")
        
        file_name = Path(java_file_path).stem
        
        try:
            # Read the Java file
            code = self.java_parser.parse_file(java_file_path)
            
            # Check token count
            total_tokens = self.token_counter.count_tokens(code)
            max_tokens = self.preset.max_chunk_size // 2  # Use half for architecture analysis
            
            if total_tokens > max_tokens:
                # For large files, extract key architectural elements first
                code = self._extract_architectural_elements(code)
                self.logger.info(f"Extracted architectural elements from large file ({total_tokens:,} tokens)")
            
            # Analyze with LLM
            analysis_result = self._analyze_with_llm(code, file_name)
            
            if analysis_result:
                # Store the analysis
                self.file_analyses[file_name] = analysis_result
                
                return analysis_result
            else:
                self.logger.warning(f"Failed to analyze {file_name}")
                return self._create_fallback_analysis(file_name, code)
                
        except Exception as e:
            self.logger.error(f"Error analyzing {file_name}: {e}")
            return self._create_fallback_analysis(file_name, "")
    
    def _extract_architectural_elements(self, code: str) -> str:
        """Extract key architectural elements from large code files.
        
        Args:
            code: Full Java code
            
        Returns:
            Simplified code focusing on architectural elements
        """
        lines = code.split('\n')
        architectural_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Include architectural elements
            if (stripped.startswith('package ') or
                stripped.startswith('import ') or
                stripped.startswith('public class ') or
                stripped.startswith('class ') or
                stripped.startswith('public interface ') or
                stripped.startswith('interface ') or
                stripped.startswith('public enum ') or
                stripped.startswith('enum ') or
                stripped.startswith('@') or
                'extends' in stripped or
                'implements' in stripped or
                'new ' in stripped and ('(' in stripped) or
                'main(' in stripped):
                architectural_lines.append(line)
        
        return '\n'.join(architectural_lines)
    
    def _analyze_with_llm(self, code: str, file_name: str) -> Optional[Dict[str, Any]]:
        """Analyze code with LLM for architectural relationships.
        
        Args:
            code: Java code to analyze
            file_name: Name of the file being analyzed
            
        Returns:
            Analysis results or None if failed
        """
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content=REPOSITORY_ARCHITECTURE_PROMPT),
                HumanMessage(content=f"Analyze this Java file for repository architecture:\n\nFile: {file_name}.java\n\n{code}")
            ]
            
            response = self.llm_client.llm.invoke(messages)
            response_content = response.content.strip()
            
            # Parse JSON response
            try:
                analysis_result = json.loads(response_content)
                return analysis_result
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse LLM response for {file_name}: {e}")
                self.logger.debug(f"LLM response: {response_content}")
                return None
                
        except Exception as e:
            self.logger.error(f"LLM analysis failed for {file_name}: {e}")
            return None
    
    def _create_fallback_analysis(self, file_name: str, code: str) -> Dict[str, Any]:
        """Create a fallback analysis when LLM analysis fails.
        
        Args:
            file_name: Name of the file
            code: Java code (may be empty)
            
        Returns:
            Basic analysis structure
        """
        # Try to extract basic information from code
        main_class = file_name
        file_type = "service"  # Default type
        is_entry_point = "main(" in code
        is_exit_point = any(keyword in code.lower() for keyword in 
                           ["connection", "database", "api", "client", "writer", "logger"])
        
        return {
            "file_info": {
                "name": file_name,
                "main_class": main_class,
                "file_type": "entry_point" if is_entry_point else ("exit_point" if is_exit_point else file_type),
                "purpose": f"Java class: {main_class}",
                "is_entry_point": is_entry_point,
                "is_exit_point": is_exit_point
            },
            "dependencies": [],
            "provides_to": []
        }
    
    def _extract_file_relationships(self, file_name: str, analysis: Dict[str, Any]):
        """Extract relationships from file analysis.
        
        Args:
            file_name: Name of the source file
            analysis: Analysis results
        """
        # Extract dependencies
        dependencies = analysis.get("dependencies", [])
        self.logger.debug(f"Processing {len(dependencies)} dependencies for {file_name}")
        
        for dep in dependencies:
            # Get target file/class name and normalize it
            target = dep.get("target_file", dep.get("target_class", "Unknown"))
            original_target = target
            
            # Remove .java extension if present to match node names
            if target.endswith(".java"):
                target = target[:-5]  # Remove ".java"
            
            self.logger.debug(f"  Checking dependency: {file_name} -> {original_target} (normalized: {target})")
            
            # Check if target exists in our analysis
            target_exists = target in self.file_analyses
            is_external_allowed = self._should_include_external_dependency(target)
            
            self.logger.debug(f"    Target exists in analysis: {target_exists}")
            self.logger.debug(f"    Is external allowed: {is_external_allowed}")
            
            # Skip external dependencies that aren't in our analysis
            if not target_exists and not is_external_allowed:
                self.logger.debug(f"    SKIPPED: External dependency not allowed")
                continue
            
            relationship = {
                "from": file_name,
                "to": target,
                "type": dep.get("relationship_type", "dependency"),
                "description": dep.get("description", "")
            }
            self.file_relationships.append(relationship)
            self.logger.debug(f"    ADDED: {file_name} -> {target} ({relationship['type']})")
    
    def _ensure_all_relationships_extracted(self):
        """Extract all relationships from file analyses after all files have been analyzed.
        
        This method processes all file analyses to extract relationships, ensuring that
        all target files exist in the analysis before creating relationships. This avoids
        processing order dependencies.
        """
        # Extract relationships from all file analyses
        
        # Clear existing relationships and rebuild from scratch
        # (since we disabled extraction during individual file analysis)
        initial_count = len(self.file_relationships)
        self.file_relationships.clear()
        
        # Track relationships to avoid duplicates
        existing_relationships = set()
        relationships_added = 0
        
        # Re-process all file analyses
        for file_name, analysis in self.file_analyses.items():
            dependencies = analysis.get("dependencies", [])
            
            for dep in dependencies:
                # Get target file/class name and normalize it
                target = dep.get("target_file", dep.get("target_class", "Unknown"))
                original_target = target
                
                # Remove .java extension if present to match node names
                if target.endswith(".java"):
                    target = target[:-5]  # Remove ".java"
                
                # Skip external dependencies that aren't in our analysis
                if target not in self.file_analyses and not self._should_include_external_dependency(target):
                    self.logger.debug(f"  SKIPPING external dependency: {file_name} -> {target}")
                    continue
                
                # Check if this relationship already exists
                relationship_key = f"{file_name}->{target}-{dep.get('relationship_type', 'dependency')}"
                if relationship_key in existing_relationships:
                    self.logger.debug(f"  SKIPPING duplicate: {relationship_key}")
                    continue
                
                # Add the relationship
                relationship = {
                    "from": file_name,
                    "to": target,
                    "type": dep.get("relationship_type", "dependency"),
                    "description": dep.get("description", "")
                }
                self.file_relationships.append(relationship)
                existing_relationships.add(relationship_key)
                relationships_added += 1
                
                self.logger.debug(f"Extracted: {file_name} -> {target} ({relationship['type']})")
        
        self.logger.info(f"Extracted {len(self.file_relationships)} relationships")
        
        # Add implicit architectural relationships (e.g., JDBC patterns)
        self._add_implicit_relationships()
    
    def _add_implicit_relationships(self):
        """Add implicit architectural relationships that aren't explicitly coded but are architecturally significant.
        
        For example, JDBC applications typically use DriverManager.getConnection() without directly importing
        the driver class, but there's an implicit architectural dependency.
        """
        implicit_added = 0
        
        # Find entry points that use JDBC patterns
        for file_name, analysis in self.file_analyses.items():
            file_info = analysis.get("file_info", {})
            is_entry_point = file_info.get("is_entry_point", False)
            dependencies = analysis.get("dependencies", [])
            
            # Check if this is a JDBC entry point
            uses_driver_manager = any(
                "DriverManager" in dep.get("target_file", "") or "DriverManager" in dep.get("target_class", "")
                for dep in dependencies
            )
            uses_connection = any(
                "Connection" in dep.get("target_file", "") or "Connection" in dep.get("target_class", "")
                for dep in dependencies
            )
            
            if is_entry_point and (uses_driver_manager or uses_connection):
                # Look for driver classes in the analysis
                driver_classes = []
                for driver_name, driver_analysis in self.file_analyses.items():
                    driver_info = driver_analysis.get("file_info", {})
                    driver_purpose = driver_info.get("purpose", "").lower()
                    
                    # Identify driver classes
                    if ("driver" in driver_name.lower() and 
                        ("implements" in driver_purpose or "driver interface" in driver_purpose)):
                        driver_classes.append(driver_name)
                
                # Add implicit relationships to driver classes
                for driver_class in driver_classes:
                    # Check if relationship already exists
                    existing = any(
                        rel["from"] == file_name and rel["to"] == driver_class
                        for rel in self.file_relationships
                    )
                    
                    if not existing:
                        implicit_relationship = {
                            "from": file_name,
                            "to": driver_class,
                            "type": "implicit_jdbc",
                            "description": f"Implicit JDBC relationship: {file_name} uses {driver_class} through DriverManager"
                        }
                        self.file_relationships.append(implicit_relationship)
                        implicit_added += 1
                        self.logger.debug(f"Added implicit JDBC relationship: {file_name} -> {driver_class}")
        
        if implicit_added > 0:
            self.logger.info(f"Added {implicit_added} implicit architectural relationships")
    
    def create_repository_visualization(self, output_path: str, repository_info: Dict[str, Any]) -> str:
        """Create a repository-level architectural visualization.
        
        Args:
            output_path: Path where to save the visualization
            repository_info: Information about the repository
            
        Returns:
            Path to the created visualization
        """
        # Remove verbose visualization creation logging
        
        # Ensure all relationships are extracted from file analyses
        self._ensure_all_relationships_extracted()
        
        # Create full-screen pyvis network with hierarchical tree structure
        net = Network(
            directed=True,
            height="100vh",
            width="100vw",
            bgcolor="#ffffff",
            font_color="#2c3e50",
            notebook=False,
        )
        
        # Calculate dynamic spacing based on repository size
        total_files = len(self.file_analyses)
        
        # Dynamic spacing that scales with repository size
        if total_files <= 15:
            level_separation = 200
            node_spacing = 250
            tree_spacing = 300
            font_size = 16
            node_size = 35
        elif total_files <= 50:
            level_separation = 300
            node_spacing = 180
            tree_spacing = 200
            font_size = 14
            node_size = 30
        else:  # Large repositories (50+ files)
            level_separation = 400
            node_spacing = 120
            tree_spacing = 150
            font_size = 12
            node_size = 25
        
        # Configure hierarchical tree layout with dynamic spacing
        net.set_options(f"""
        {{
          "layout": {{
            "hierarchical": {{
              "enabled": true,
              "direction": "UD",
              "sortMethod": "directed",
              "levelSeparation": {level_separation},
              "nodeSpacing": {node_spacing},
              "treeSpacing": {tree_spacing},
              "blockShifting": true,
              "edgeMinimization": true,
              "parentCentralization": true,
              "shakeTowards": "roots"
            }}
          }},
          "physics": {{
            "enabled": false
          }},
          "nodes": {{
            "font": {{
              "size": {font_size},
              "face": "Arial, sans-serif",
              "color": "white",
              "bold": true
            }},
            "margin": 10,
            "borderWidth": 2,
            "shadow": {{
              "enabled": true,
              "color": "rgba(0,0,0,0.3)",
              "size": 8,
              "x": 2,
              "y": 2
            }},
            "widthConstraint": {{
              "minimum": 100,
              "maximum": 180
            }},
            "heightConstraint": {{
              "minimum": 40,
              "maximum": 60
            }}
          }},
          "edges": {{
            "arrows": {{
              "to": {{
                "enabled": true,
                "scaleFactor": 1.0,
                "type": "arrow"
              }}
            }},
            "smooth": {{
              "enabled": false,
              "type": "straightCross"
            }},
            "width": 1.5,
            "shadow": false,
            "color": {{
              "inherit": false,
              "color": "#2c3e50"
            }}
          }},
                    "interaction": {{
             "dragNodes": true,
             "dragView": true,
             "zoomView": true,
             "hover": true,
             "selectConnectedEdges": true,
             "selectable": true,
             "navigationButtons": true,
             "keyboard": true,
             "tooltipDelay": 300,
             "hideEdgesOnDrag": false,
             "hideNodesOnDrag": false
           }}
        }}
        """)
        
        # Add nodes with hierarchical positioning
        self._add_architecture_nodes_hierarchical(net)
        
        # Add edges for relationships
        self._add_architecture_edges(net)
        
        # Save the visualization
        output_dir = os.path.dirname(output_path)
        if output_dir:  # Only create directory if there's a directory path
            os.makedirs(output_dir, exist_ok=True)
        
        # Save with full-screen CSS
        net.show(output_path, notebook=False)
        
        # Add custom CSS to remove boundaries and center content
        with open(output_path, 'r') as f:
            html_content = f.read()
        
        # Add full-screen CSS styling with improved responsiveness
        custom_css = """
        <style>
        * {
            box-sizing: border-box;
        }
        html, body {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: white;
            font-family: Arial, sans-serif;
        }
        #mynetworkid {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            z-index: 1;
        }
        .vis-network {
            width: 100% !important;
            height: 100% !important;
        }
        /* Navigation controls styling */
        .vis-navigation {
            position: fixed !important;
            top: 10px !important;
            right: 10px !important;
            z-index: 1000 !important;
            background: rgba(255, 255, 255, 0.9) !important;
            border-radius: 5px !important;
            padding: 5px !important;
        }
        /* Info panel for large repositories */
        .repo-info {
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            z-index: 1000;
            max-width: 300px;
        }
        </style>
        """
        
        # Add info panel for large repositories
        total_files = len(self.file_analyses)
        info_panel = ""
        if total_files > 50:
            info_panel = f"""
            <div class="repo-info">
                <strong>Large Repository View</strong><br>
                Files: {total_files}<br>
                Use mouse wheel to zoom<br>
                Drag to pan around<br>
                Click and drag nodes to rearrange
            </div>
            """
        
        # Insert CSS before closing head tag
        html_content = html_content.replace('</head>', custom_css + '</head>')
        
        # Insert info panel after opening body tag
        if info_panel:
            html_content = html_content.replace('<body>', '<body>' + info_panel)
        
        # Write back the modified HTML
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        # Save comprehensive JSON analysis in the same directory
        self._save_architecture_json(output_path, repository_info)
        
        self.logger.info(f"Repository architecture visualization saved: {output_path}")
        return output_path
    
    def _add_architecture_nodes_hierarchical(self, net: Network):
        """Add file nodes to the network with hierarchical tree positioning.
        
        Args:
            net: PyVis network object
        """
        # Define hierarchical levels based on architectural roles
        hierarchy_levels = {
            "entry_point": 0,    # Top level - application entry points
            "controller": 1,     # Level 1 - controllers and coordinators
            "service": 2,        # Level 2 - business logic services
            "model": 3,          # Level 3 - data models and domain objects
            "data": 3,           # Level 3 - data structures (same as models)
            "utility": 4,        # Level 4 - utility and helper classes
            "config": 4,         # Level 4 - configuration (same as utilities)
            "exit_point": 5      # Bottom level - external connections
        }
        
        # Define node styles with consistent coloring
        node_styles = {
            "entry_point": {
                "color": {"background": "#27ae60", "border": "#1e8449"},
                "emoji": "🚀"
            },
            "controller": {
                "color": {"background": "#f39c12", "border": "#e67e22"},
                "emoji": "🎛️"
            },
            "service": {
                "color": {"background": "#3498db", "border": "#2980b9"},
                "emoji": "⚙️"
            },
            "model": {
                "color": {"background": "#9b59b6", "border": "#8e44ad"},
                "emoji": "📦"
            },
            "data": {
                "color": {"background": "#e91e63", "border": "#c2185b"},
                "emoji": "💾"
            },
            "utility": {
                "color": {"background": "#95a5a6", "border": "#7f8c8d"},
                "emoji": "🔧"
            },
            "config": {
                "color": {"background": "#8d6e63", "border": "#6d4c41"},
                "emoji": "⚙️"
            },
            "exit_point": {
                "color": {"background": "#e74c3c", "border": "#c0392b"},
                "emoji": "🎯"
            }
        }
        
        # Group files by hierarchy level
        levels = {}
        for file_name, analysis in self.file_analyses.items():
            file_info = analysis.get("file_info", {})
            file_type = file_info.get("file_type", "service")
            level = hierarchy_levels.get(file_type, 2)  # Default to service level
            
            if level not in levels:
                levels[level] = []
            levels[level].append((file_name, analysis, file_type))
        
        # Position nodes hierarchically
        for level, files in levels.items():
            y_position = level * 200  # 200px between levels
            
            # Calculate x positions to center nodes horizontally
            num_files = len(files)
            if num_files == 1:
                x_positions = [0]
            else:
                spacing = 300  # 300px between nodes
                total_width = (num_files - 1) * spacing
                start_x = -total_width / 2
                x_positions = [start_x + i * spacing for i in range(num_files)]
            
            # Add nodes at calculated positions
            for i, (file_name, analysis, file_type) in enumerate(files):
                file_info = analysis.get("file_info", {})
                main_class = file_info.get("main_class", file_name)
                
                # Get style for this file type
                style = node_styles.get(file_type, node_styles["service"])
                
                # Create readable node label
                display_name = main_class.replace("_", " ").replace("-", " ")
                if len(display_name) > 18:
                    display_name = display_name[:15] + "..."
                
                # Add emoji prefix for visual hierarchy
                emoji_label = f"{style['emoji']} {display_name}"
                
                # Create rich interactive tooltip with file information
                analysis = self.file_analyses.get(file_name, {})
                file_info = analysis.get("file_info", {})
                dependencies = analysis.get("dependencies", [])
                
                # Build HTML tooltip with styling
                tooltip_parts = [
                    f"<div style='font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 8px;'>{style['emoji']} {file_name}.java</div>",
                    f"<div style='color: #7f8c8d; margin-bottom: 4px;'><b>Type:</b> {file_type.replace('_', ' ').title()}</div>",
                    f"<div style='color: #7f8c8d; margin-bottom: 4px;'><b>Hierarchy Level:</b> {level}</div>"
                ]
                
                if file_info.get("purpose"):
                    purpose = file_info['purpose'][:80] + "..." if len(file_info['purpose']) > 80 else file_info['purpose']
                    tooltip_parts.append(f"<div style='color: #34495e; margin: 8px 0; font-style: italic;'>{purpose}</div>")
                
                if dependencies:
                    tooltip_parts.append(f"<div style='color: #e74c3c; font-weight: bold; margin-top: 8px;'>{len(dependencies)} Dependencies:</div>")
                    for dep in dependencies[:3]:  # Show up to 3 dependencies
                        target = dep.get('target_class', dep.get('target_file', 'Unknown'))
                        if target.endswith('.java'):
                            target = target[:-5]
                        rel_type = dep.get('relationship_type', 'dependency')
                        tooltip_parts.append(f"<div style='margin-left: 10px; color: #2980b9;'>• {target} ({rel_type})</div>")
                    if len(dependencies) > 3:
                        tooltip_parts.append(f"<div style='margin-left: 10px; color: #95a5a6;'>... and {len(dependencies)-3} more</div>")
                
                # Add interaction hints
                tooltip_parts.append("<div style='margin-top: 12px; padding-top: 8px; border-top: 1px solid #bdc3c7; color: #95a5a6; font-size: 11px;'>💡 Click to select • Drag to move • Hover to see connections</div>")
                
                title = "".join(tooltip_parts)
                
                # Calculate dynamic node size based on repository size
                total_files = len(self.file_analyses)
                if total_files <= 15:
                    node_font_size = 16
                elif total_files <= 50:
                    node_font_size = 14
                else:
                    node_font_size = 12
                
                # Add node with dynamic sizing and interactivity
                net.add_node(
                    file_name,
                    label=emoji_label,
                    title=title,
                    color=style["color"],
                    shape="box",
                    font={"size": node_font_size, "color": "white", "bold": True},
                    level=level,
                    x=x_positions[i],
                    y=y_position,
                    fixed={"x": False, "y": False},  # Allow dragging
                    chosen={"node": True, "label": True},  # Enable selection highlighting
                    borderWidth=2,
                    borderWidthSelected=4,
                    shapeProperties={"borderRadius": 6}
                )
    
    def _add_architecture_edges(self, net: Network):
        """Add relationship edges to the network with hierarchical flow.
        
        Args:
            net: PyVis network object
        """
        # Define edge styles based on relationship types
        edge_styles = {
            "import": {"color": "#3498db", "width": 2, "label": "imports"},
            "extends": {"color": "#e74c3c", "width": 3, "label": "extends"},
            "implements": {"color": "#f39c12", "width": 3, "label": "implements"},
            "instantiation": {"color": "#27ae60", "width": 2, "label": "creates"},
            "static_call": {"color": "#9b59b6", "width": 2, "label": "calls"},
            "dependency": {"color": "#2c3e50", "width": 2, "label": "uses"},
            "implicit_jdbc": {"color": "#e67e22", "width": 3, "label": "uses via JDBC"}
        }
        
        # Track added edges to avoid duplicates
        added_edges = set()
        edges_added = 0
        
        self.logger.info(f"Processing {len(self.file_relationships)} relationships for edges...")
        
        for relationship in self.file_relationships:
            from_file = relationship["from"]
            to_file = relationship["to"]
            rel_type = relationship.get("type", "dependency")
            
            self.logger.debug(f"Checking relationship: {from_file} -> {to_file} ({rel_type})")
            
            # Skip if source node doesn't exist
            if from_file not in self.file_analyses:
                self.logger.debug(f"Skipping: source node {from_file} not found in analyses")
                continue
            
            # Create edge key to avoid duplicates
            edge_key = f"{from_file}->{to_file}"
            if edge_key in added_edges:
                self.logger.debug(f"Skipping: duplicate edge {edge_key}")
                continue
            added_edges.add(edge_key)
            
            # Only add edges between files in our analysis (internal relationships)
            if to_file in self.file_analyses:
                # Get edge style
                style = edge_styles.get(rel_type, edge_styles["dependency"])
                
                # Create rich edge tooltip
                from_type = self.file_analyses.get(from_file, {}).get("file_info", {}).get("file_type", "unknown")
                to_type = self.file_analyses.get(to_file, {}).get("file_info", {}).get("file_type", "unknown")
                
                edge_tooltip = f"""
                <div style='font-size: 13px; font-weight: bold; color: #2c3e50; margin-bottom: 6px;'>
                    {style['label'].title()} Relationship
                </div>
                <div style='color: #7f8c8d; margin-bottom: 4px;'>
                    <b>From:</b> {from_file} ({from_type.replace('_', ' ').title()})
                </div>
                <div style='color: #7f8c8d; margin-bottom: 8px;'>
                    <b>To:</b> {to_file} ({to_type.replace('_', ' ').title()})
                </div>
                <div style='color: #95a5a6; font-size: 11px; font-style: italic;'>
                    Click nodes to highlight all connections
                </div>
                """
                
                # Add straight edge with proper styling and rich tooltip
                net.add_edge(
                    from_file,
                    to_file,
                    title=edge_tooltip,
                    color=style["color"],
                    width=style["width"],
                    smooth=False,
                    arrows={"to": {"enabled": True, "scaleFactor": 1.2}},
                    hoverWidth=style["width"] + 1,
                    selectionWidth=style["width"] + 2
                )
                edges_added += 1
                self.logger.debug(f"Added edge: {from_file} -> {to_file}")
            else:
                self.logger.debug(f"Skipping: target node {to_file} not found in analyses")
        
        self.logger.info(f"Added {edges_added} edges to the visualization")
    
    def _save_architecture_json(self, html_output_path: str, repository_info: Dict[str, Any]):
        """Save comprehensive repository architecture analysis as JSON.
        
        Args:
            html_output_path: Path to the HTML visualization file
            repository_info: Information about the repository
        """
        # Create JSON file path in the same directory as HTML
        output_dir = os.path.dirname(html_output_path)
        json_filename = "repository_architecture_analysis.json"
        json_path = os.path.join(output_dir, json_filename)
        
        # Prepare comprehensive architecture data
        architecture_data = {
            "metadata": {
                "generated_at": self._get_current_timestamp(),
                "repository_name": repository_info.get("name", "Unknown"),
                "total_files_analyzed": len(self.file_analyses),
                "total_relationships": len(self.file_relationships),
                "analysis_type": "repository_architecture",
                "visualization_file": os.path.basename(html_output_path)
            },
            
            "hierarchy": self._get_hierarchy_structure(),
            
            "files": {
                file_name: {
                    "file_info": analysis.get("file_info", {}),
                    "dependencies": analysis.get("dependencies", []),
                    "provides_to": analysis.get("provides_to", []),
                    "hierarchy_level": self._get_file_hierarchy_level(analysis.get("file_info", {}).get("file_type", "service")),
                    "architectural_role": analysis.get("file_info", {}).get("file_type", "service"),
                    "is_entry_point": analysis.get("file_info", {}).get("is_entry_point", False),
                    "is_exit_point": analysis.get("file_info", {}).get("is_exit_point", False)
                }
                for file_name, analysis in self.file_analyses.items()
            },
            
            "relationships": [
                {
                    "from": rel["from"],
                    "to": rel["to"],
                    "type": rel["type"],
                    "description": rel.get("description", ""),
                    "from_level": self._get_file_hierarchy_level(
                        self.file_analyses.get(rel["from"], {}).get("file_info", {}).get("file_type", "service")
                    ),
                    "to_level": self._get_file_hierarchy_level(
                        self.file_analyses.get(rel["to"], {}).get("file_info", {}).get("file_type", "service")
                    )
                }
                for rel in self.file_relationships
            ],
            
            "architecture_summary": self.get_architecture_summary(),
            
            "file_types": {
                "entry_point": {
                    "description": "Application entry points, main classes, CLI launchers",
                    "level": 0,
                    "emoji": "🚀",
                    "files": [name for name, analysis in self.file_analyses.items() 
                             if analysis.get("file_info", {}).get("file_type") == "entry_point"]
                },
                "controller": {
                    "description": "Request handlers, coordinators, API controllers",
                    "level": 1,
                    "emoji": "🎛️",
                    "files": [name for name, analysis in self.file_analyses.items() 
                             if analysis.get("file_info", {}).get("file_type") == "controller"]
                },
                "service": {
                    "description": "Business logic, service classes, core functionality",
                    "level": 2,
                    "emoji": "⚙️",
                    "files": [name for name, analysis in self.file_analyses.items() 
                             if analysis.get("file_info", {}).get("file_type") == "service"]
                },
                "model": {
                    "description": "Data models, domain objects, entities",
                    "level": 3,
                    "emoji": "📦",
                    "files": [name for name, analysis in self.file_analyses.items() 
                             if analysis.get("file_info", {}).get("file_type") == "model"]
                },
                "data": {
                    "description": "Data access, repositories, DTOs, data structures",
                    "level": 3,
                    "emoji": "💾",
                    "files": [name for name, analysis in self.file_analyses.items() 
                             if analysis.get("file_info", {}).get("file_type") == "data"]
                },
                "utility": {
                    "description": "Helper classes, common functions, utilities",
                    "level": 4,
                    "emoji": "🔧",
                    "files": [name for name, analysis in self.file_analyses.items() 
                             if analysis.get("file_info", {}).get("file_type") == "utility"]
                },
                "config": {
                    "description": "Configuration, settings, application setup",
                    "level": 4,
                    "emoji": "⚙️",
                    "files": [name for name, analysis in self.file_analyses.items() 
                             if analysis.get("file_info", {}).get("file_type") == "config"]
                },
                "exit_point": {
                    "description": "External system connections, databases, APIs, loggers",
                    "level": 5,
                    "emoji": "🎯",
                    "files": [name for name, analysis in self.file_analyses.items() 
                             if analysis.get("file_info", {}).get("file_type") == "exit_point"]
                }
            },
            
            "statistics": {
                "relationships_by_type": self._get_relationship_statistics(),
                "files_by_level": self._get_files_by_level_statistics(),
                "connectivity_metrics": self._get_connectivity_metrics()
            }
        }
        
        # Save JSON file
        try:
            with open(json_path, 'w') as f:
                json.dump(architecture_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Repository architecture JSON analysis saved: {json_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save architecture JSON: {e}")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_hierarchy_structure(self) -> Dict[str, Any]:
        """Get the hierarchical structure of the repository."""
        hierarchy_levels = {
            "entry_point": 0, "controller": 1, "service": 2, 
            "model": 3, "data": 3, "utility": 4, "config": 4, "exit_point": 5
        }
        
        levels = {}
        for file_name, analysis in self.file_analyses.items():
            file_type = analysis.get("file_info", {}).get("file_type", "service")
            level = hierarchy_levels.get(file_type, 2)
            
            if level not in levels:
                levels[level] = []
            levels[level].append({
                "name": file_name,
                "type": file_type,
                "purpose": analysis.get("file_info", {}).get("purpose", "")
            })
        
        return {
            "description": "Hierarchical organization of files by architectural role",
            "levels": levels,
            "level_descriptions": {
                0: "Entry Points - Application launchers and main classes",
                1: "Controllers - Request handlers and coordinators", 
                2: "Services - Business logic and core functionality",
                3: "Models & Data - Domain objects and data access",
                4: "Utilities & Config - Support classes and configuration",
                5: "Exit Points - External system integrations"
            }
        }
    
    def _get_file_hierarchy_level(self, file_type: str) -> int:
        """Get hierarchy level for a file type."""
        hierarchy_levels = {
            "entry_point": 0, "controller": 1, "service": 2,
            "model": 3, "data": 3, "utility": 4, "config": 4, "exit_point": 5
        }
        return hierarchy_levels.get(file_type, 2)
    
    def _get_relationship_statistics(self) -> Dict[str, int]:
        """Get statistics about relationship types."""
        stats = {}
        for rel in self.file_relationships:
            rel_type = rel.get("type", "dependency")
            stats[rel_type] = stats.get(rel_type, 0) + 1
        return stats
    
    def _get_files_by_level_statistics(self) -> Dict[int, int]:
        """Get count of files by hierarchy level."""
        level_counts = {}
        for analysis in self.file_analyses.values():
            file_type = analysis.get("file_info", {}).get("file_type", "service")
            level = self._get_file_hierarchy_level(file_type)
            level_counts[level] = level_counts.get(level, 0) + 1
        return level_counts
    
    def _get_connectivity_metrics(self) -> Dict[str, Any]:
        """Get connectivity metrics for the architecture."""
        # Calculate in-degree and out-degree for each file
        in_degree = {}
        out_degree = {}
        
        for rel in self.file_relationships:
            from_file = rel["from"]
            to_file = rel["to"]
            
            out_degree[from_file] = out_degree.get(from_file, 0) + 1
            in_degree[to_file] = in_degree.get(to_file, 0) + 1
        
        # Find most connected files
        most_dependencies = max(out_degree.items(), key=lambda x: x[1]) if out_degree else ("None", 0)
        most_dependents = max(in_degree.items(), key=lambda x: x[1]) if in_degree else ("None", 0)
        
        return {
            "total_connections": len(self.file_relationships),
            "average_connections_per_file": len(self.file_relationships) / len(self.file_analyses) if self.file_analyses else 0,
            "most_dependencies": {
                "file": most_dependencies[0],
                "count": most_dependencies[1]
            },
            "most_dependents": {
                "file": most_dependents[0], 
                "count": most_dependents[1]
            },
            "isolated_files": [
                name for name in self.file_analyses.keys()
                if name not in in_degree and name not in out_degree
            ]
        }
    
    def _should_include_external_dependency(self, target: str) -> bool:
        """Determine if an external dependency should be included in the visualization.
        
        Args:
            target: Target dependency name
            
        Returns:
            True if should be included
        """
        # Include common external dependencies that are architecturally significant
        significant_externals = [
            "Scanner", "File", "Connection", "Database", "API", "Client", 
            "Logger", "Configuration", "Properties", "System"
        ]
        
        return any(ext.lower() in target.lower() for ext in significant_externals)
    
    def get_architecture_summary(self) -> Dict[str, Any]:
        """Get a summary of the repository architecture.
        
        Returns:
            Dictionary containing architecture summary
        """
        if not self.file_analyses:
            return {"error": "No files analyzed"}
        
        # Count file types
        file_types = {}
        entry_points = []
        exit_points = []
        
        for file_name, analysis in self.file_analyses.items():
            file_info = analysis.get("file_info", {})
            file_type = file_info.get("file_type", "unknown")
            
            file_types[file_type] = file_types.get(file_type, 0) + 1
            
            if file_info.get("is_entry_point", False):
                entry_points.append(file_name)
            if file_info.get("is_exit_point", False):
                exit_points.append(file_name)
        
        return {
            "total_files": len(self.file_analyses),
            "total_relationships": len(self.file_relationships),
            "file_types": file_types,
            "entry_points": entry_points,
            "exit_points": exit_points,
            "architecture_pattern": self._identify_architecture_pattern()
        }
    
    def _identify_architecture_pattern(self) -> str:
        """Identify the overall architecture pattern of the repository.
        
        Returns:
            String describing the architecture pattern
        """
        file_types = set()
        for analysis in self.file_analyses.values():
            file_type = analysis.get("file_info", {}).get("file_type", "")
            file_types.add(file_type)
        
        # Simple pattern detection
        if "controller" in file_types and "model" in file_types and "service" in file_types:
            return "MVC (Model-View-Controller)"
        elif "service" in file_types and "data" in file_types:
            return "Service-Oriented Architecture"
        elif len([f for f in file_types if f in ["utility", "service"]]) > len(file_types) // 2:
            return "Utility/Library Architecture"
        else:
            return "Custom Architecture" 