"""Repository processor for batch processing of Java files from GitHub repositories."""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Tuple


from code_comprehender.git_handler import GitHandler
from code_comprehender.code_documenter import CodeDocumenter
from code_comprehender.code_visualizer import CodeVisualizer
from code_comprehender.async_code_documenter import AsyncCodeDocumenter
from code_comprehender.async_code_visualizer import AsyncCodeVisualizer
from code_comprehender.repository_architecture_analyzer import RepositoryArchitectureAnalyzer
from code_comprehender.config import OUTPUT_DIR, GITHUB_TOKEN, get_performance_profile, recommend_performance_profile, get_profile_description
from code_comprehender.logger import get_logger, log_progress, log_success, log_error, log_warning


class RepositoryProcessor:
    """Processes entire GitHub repositories for documentation and visualization."""
    
    def __init__(self, preset_name: str = None, github_token: str = None, 
                 performance_profile: str = "balanced"):
        """Initialize the repository processor.
        
        Args:
            preset_name: Name of the LLM preset to use
            github_token: GitHub personal access token
            performance_profile: Performance profile (conservative, balanced, aggressive) with auto-scaling
        """
        self.logger = get_logger(self.__class__.__name__)
        self.preset_name = preset_name
        
        # Use provided token or fallback to environment variable
        self.github_token = github_token or GITHUB_TOKEN
        
        # Get performance profile settings
        self.profile_settings = get_performance_profile(performance_profile)
        
        # Use performance profile settings
        self.max_concurrent_files = self.profile_settings["max_concurrent_files"]
        self.max_concurrent_llm_requests = self.profile_settings["max_concurrent_llm_requests"]
        self.max_concurrent_viz_requests = self.profile_settings["max_concurrent_viz_requests"]
        self.rate_limit_delay = self.profile_settings["rate_limit_delay"]
        self.performance_profile = performance_profile
        
        # Initialize processors
        self.documenter = CodeDocumenter(preset_name)
        self.visualizer = CodeVisualizer(preset_name)
        self.async_documenter = AsyncCodeDocumenter(preset_name, performance_profile)
        self.async_visualizer = AsyncCodeVisualizer(preset_name, performance_profile)
        self.architecture_analyzer = RepositoryArchitectureAnalyzer(preset_name)
        
        # Track processed files and graphs
        self.processed_files = []
        self.file_graphs = []  # Keep for individual file analysis (backward compatibility)
        self.repository_info = {}
        
        self.logger.info(f"Initialized with '{performance_profile}' profile ({self.max_concurrent_files} concurrent files)")
    
    def process_github_repository(self, github_url: str, output_dir: str = OUTPUT_DIR, 
                                documentation: bool = True, visualization: bool = True, 
                                use_parallel: bool = True) -> Dict[str, Any]:
        """Process a complete GitHub repository.
        
        Args:
            github_url: GitHub repository URL
            output_dir: Output directory for results
            documentation: Whether to create documentation
            visualization: Whether to create visualizations
            use_parallel: Whether to use parallel processing (default: True)
            
        Returns:
            Dictionary containing processing results
        """
        import time
        
        # Start timing the entire process
        total_start_time = time.time()
        
        results = {
            "repository_url": github_url,
            "output_directory": output_dir,
            "documentation_enabled": documentation,
            "visualization_enabled": visualization,
            "processed_files": [],
            "errors": [],
            "summary": {},
            "performance_metrics": {}
        }
        
        # Initialize git handler
        with GitHandler(self.github_token) as git_handler: 
            try:
                # Clone repository
                repo_path = git_handler.clone_repository(github_url)
                log_success(f"Repository cloned: {repo_path}")
                
                # Get repository information
                self.repository_info = git_handler.get_repository_info(repo_path, github_url)
                results["repository_info"] = self.repository_info
                
                file_count = self.repository_info['java_file_count']
                self.logger.info(f"Repository: {self.repository_info['name']} ({file_count} Java files)")
                
                if file_count == 0:
                    log_warning("No Java files found in repository")
                    return results
                
                # Create output directory structure
                repo_output_dir = self._create_output_structure(output_dir, self.repository_info['name'])
                results["output_directory"] = repo_output_dir
                
                # Process Java files
                java_files = self.repository_info['java_files']
                successful_files = 0
                
                # Auto-scale concurrency based on repository size
                self._auto_scale_concurrency(len(java_files))
                
                # Start timing file processing
                processing_start_time = time.time()
                
                if use_parallel and len(java_files) > 1:
                    mode_desc = "documentation" if documentation and not visualization else "visualization" if visualization and not documentation else "analysis"
                    self.logger.info(f"Processing {len(java_files)} files for {mode_desc} in parallel ({self.max_concurrent_files} concurrent)")
                    # Use parallel processing
                    try:
                        file_results = self._process_files_parallel(
                            java_files, repo_path, repo_output_dir, 
                            documentation, visualization
                        )
                        results["processed_files"] = file_results
                        successful_files = len([r for r in file_results if not r.get("errors")])
                    except Exception as e:
                        log_error(f"Parallel processing failed, falling back to sequential: {e}")
                        use_parallel = False
                
                if not use_parallel or len(java_files) == 1:
                    mode_desc = "documentation" if documentation and not visualization else "visualization" if visualization and not documentation else "analysis"
                    self.logger.info(f"Processing {len(java_files)} files for {mode_desc} sequentially")
                    # Use sequential processing (original method)
                    for i, java_file in enumerate(java_files):
                        log_progress(f"Processing: {Path(java_file).name}", i + 1, len(java_files))
                        
                        try:
                            file_result = self._process_single_file(
                                java_file, repo_path, repo_output_dir, 
                                documentation, visualization
                            )
                            results["processed_files"].append(file_result)
                            successful_files += 1
                            log_progress(f"Completed: {Path(java_file).name}", i + 1, len(java_files))
                            
                        except Exception as e:
                            error_info = {
                                "file": java_file,
                                "error": str(e)
                            }
                            results["errors"].append(error_info)
                            log_error(f"Failed to process {Path(java_file).name}: {e}")
                
                # End timing file processing
                processing_time = time.time() - processing_start_time
                
                # Create combined visualization if enabled
                viz_start_time = time.time()
                if visualization and self.architecture_analyzer.file_analyses:
                    try:
                        combined_viz_path = self._create_combined_visualization(repo_output_dir)
                        results["combined_visualization"] = combined_viz_path
                    except Exception as e:
                        log_error(f"Failed to create combined visualization: {e}")
                        results["errors"].append({"combined_visualization": str(e)})
                viz_time = time.time() - viz_start_time
                
                # Generate summary
                results["summary"] = {
                    "total_files": len(java_files),
                    "successful_files": successful_files,
                    "failed_files": len(results["errors"]),
                    "documentation_files": successful_files if documentation else 0,
                    "architecture_analyzed_files": len(self.architecture_analyzer.file_analyses) if visualization else 0
                }
                
                # Calculate total time and create performance summary
                total_time = time.time() - total_start_time
                
                # Create comprehensive performance metrics
                performance_metrics = {
                    "total_processing_time": round(total_time, 2),
                    "file_processing_time": round(processing_time, 2),
                    "visualization_time": round(viz_time, 2),
                    "files_per_minute": round((len(java_files) / total_time) * 60, 1) if total_time > 0 else 0,
                    "avg_time_per_file": round(processing_time / len(java_files), 2) if len(java_files) > 0 else 0,
                    "performance_profile": self.performance_profile,
                    "concurrency_settings": {
                        "max_concurrent_files": self.max_concurrent_files,
                        "max_concurrent_llm_requests": self.max_concurrent_llm_requests,
                        "max_concurrent_viz_requests": self.max_concurrent_viz_requests,
                        "rate_limit_delay": self.rate_limit_delay
                    },
                    "parallel_processing_used": use_parallel,
                    "total_relationships": len(self.architecture_analyzer.file_relationships) if visualization else 0,
                    "implicit_relationships_added": sum(1 for rel in self.architecture_analyzer.file_relationships if rel.get("type") == "implicit_jdbc") if visualization else 0
                }
                
                results["performance_metrics"] = performance_metrics
                
                # Save processing report
                self._save_processing_report(results, repo_output_dir)
                
                # Log comprehensive performance summary
                self._log_performance_summary(performance_metrics, successful_files, len(java_files))
                
                log_success(f"Repository processing completed!")
                log_success(f"Processed {successful_files}/{len(java_files)} files successfully")
                
                return results
                
            except Exception as e:
                log_error(f"Repository processing failed: {e}")
                results["errors"].append({"repository": str(e)})
                return results
    
    def _create_output_structure(self, base_output_dir: str, repo_name: str) -> str:
        """Create output directory structure for the repository.
        
        Args:
            base_output_dir: Base output directory
            repo_name: Repository name
            
        Returns:
            Path to the repository output directory
        """
        repo_output_dir = os.path.join(base_output_dir, f"{repo_name}")
        
        # Create directories
        os.makedirs(repo_output_dir, exist_ok=True)
        os.makedirs(os.path.join(repo_output_dir, "documentation"), exist_ok=True)
        os.makedirs(os.path.join(repo_output_dir, "visualizations"), exist_ok=True)
        os.makedirs(os.path.join(repo_output_dir, "analysis"), exist_ok=True)
        
        # Remove verbose output structure logging
        return repo_output_dir
    
    def _auto_scale_concurrency(self, file_count: int):
        """Auto-scale concurrency settings based on repository size.
        
        Args:
            file_count: Number of Java files in the repository
        """
        original_files = self.max_concurrent_files
        original_llm = self.max_concurrent_llm_requests
        
        if file_count <= 10:
            # Small repository - use conservative settings
            scale_factor = 1.0
        elif file_count <= 30:
            # Medium repository - moderate scaling
            scale_factor = 1.5
        elif file_count <= 80:
            # Large repository - significant scaling
            scale_factor = 2.0
        else:
            # Very large repository - maximum scaling
            scale_factor = 2.5
        
        # Scale file concurrency (but cap at reasonable limits)
        self.max_concurrent_files = min(int(self.max_concurrent_files * scale_factor), 20)
        
        # Scale LLM requests per file (but cap to avoid rate limits)
        self.max_concurrent_llm_requests = min(int(self.max_concurrent_llm_requests * scale_factor), 25)
        
        # Adjust rate limiting based on total load
        total_concurrent_requests = self.max_concurrent_files * self.max_concurrent_llm_requests
        if total_concurrent_requests > 100:
            self.rate_limit_delay = max(0.3, self.rate_limit_delay)
        elif total_concurrent_requests > 50:
            self.rate_limit_delay = max(0.2, self.rate_limit_delay)
        
        # Note: Async processors get their settings from performance profile automatically
        
        if (self.max_concurrent_files != original_files or 
            self.max_concurrent_llm_requests != original_llm):
            self.logger.info(f"Auto-scaled to {self.max_concurrent_files} concurrent files for {file_count} files")
    
    def _process_single_file(self, java_file: str, repo_path: str, output_dir: str, 
                           documentation: bool, visualization: bool) -> Dict[str, Any]:
        """Process a single Java file.
        
        Args:
            java_file: Path to the Java file
            repo_path: Repository root path
            output_dir: Output directory
            documentation: Whether to create documentation
            visualization: Whether to create visualization
            
        Returns:
            Dictionary containing file processing results
        """
        file_result = {
            "file_path": java_file,
            "relative_path": str(Path(java_file).relative_to(repo_path)),
            "documentation_path": None,
            "visualization_path": None,
            "analysis_path": None,
            "errors": []
        }
        
        try:
            # Documentation
            if documentation:
                doc_output_dir = os.path.join(output_dir, "documentation")
                
                # Preserve directory structure in output
                rel_path = Path(java_file).relative_to(repo_path)
                doc_file_dir = os.path.join(doc_output_dir, str(rel_path.parent))
                os.makedirs(doc_file_dir, exist_ok=True)
                
                documented_path = self.documenter.process_file(java_file, doc_file_dir)
                file_result["documentation_path"] = documented_path
                
        except Exception as e:
            file_result["errors"].append(f"Documentation failed: {e}")
        
        try:
            # Analysis only (no individual visualization files)
            if visualization:
                analysis_output_dir = os.path.join(output_dir, "analysis")
                os.makedirs(analysis_output_dir, exist_ok=True)
                
                # Use repository architecture analyzer for high-level analysis
                architecture_analysis = self.architecture_analyzer.analyze_file_architecture(java_file)
                
                # Save analysis data for the combined visualization
                file_name = Path(java_file).stem
                analysis_path = os.path.join(analysis_output_dir, f"{file_name}_analysis.json")
                with open(analysis_path, 'w') as f:
                    json.dump(architecture_analysis, f, indent=2)
                
                file_result["analysis_path"] = analysis_path
                file_result["visualization_path"] = None  # No individual HTML file
                
                # Store architecture data for later combination (repository-level visualization)
                # Note: file_graphs kept for backward compatibility, but architecture analysis is primary
                
        except Exception as e:
            file_result["errors"].append(f"Analysis failed: {e}")
        
        return file_result
    
    def _create_combined_visualization(self, output_dir: str) -> str:
        """Create a repository-level architectural visualization.
        
        This method:
        1. Uses the repository architecture analyzer to create a high-level view
        2. Shows only file-to-file relationships (not method-level details)
        3. Identifies entry and exit points
        4. Creates an architectural overview inspired by the provided design
        
        Args:
            output_dir: Output directory
            
        Returns:
            Path to the combined visualization
        """
        self.logger.info("Creating repository architecture visualization...")
        
        # Create the repository-level visualization using the architecture analyzer
        viz_path = os.path.join(output_dir, "visualizations", "repository_architecture.html")
        
        # Use the repository architecture analyzer to create the visualization
        result_path = self.architecture_analyzer.create_repository_visualization(viz_path, self.repository_info)
        
        # Get architecture summary
        architecture_summary = self.architecture_analyzer.get_architecture_summary()
        
        # Save architecture summary
        analysis_dir = os.path.join(output_dir, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)
        summary_path = os.path.join(analysis_dir, "repository_architecture_summary.json")
        
        combined_summary = {
            "repository_info": self.repository_info,
            "architecture_summary": architecture_summary,
            "visualization_type": "repository_architecture",
            "description": "High-level architectural view showing file-to-file relationships"
        }
        
        with open(summary_path, 'w') as f:
            json.dump(combined_summary, f, indent=2)
        
        # Log results
        log_success(f"Architecture visualization saved: {result_path}")
        
        # Log key architecture insights only
        if architecture_summary.get("entry_points") and architecture_summary.get("exit_points"):
            entry_count = len(architecture_summary['entry_points'])
            exit_count = len(architecture_summary['exit_points'])
            self.logger.info(f"Architecture: {entry_count} entry points, {exit_count} exit points")
        
        return result_path
    
    def _extract_package_from_file(self, file_path: str) -> str:
        """Extract package name from a Java file.
        
        Args:
            file_path: Path to the Java file
            
        Returns:
            Package name or None if not found
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('package ') and line.endswith(';'):
                        return line[8:-1].strip()  # Remove 'package ' and ';'
                    # Stop at first non-comment, non-package line
                    if line and not line.startswith('//') and not line.startswith('/*'):
                        break
        except Exception as e:
            self.logger.warning(f"Failed to extract package from {file_path}: {e}")
        return None
    
    def _analyze_cross_file_dependencies(self, all_nodes: Dict, file_packages: Dict) -> List[Dict]:
        """Analyze cross-file dependencies through imports and class references.
        
        Args:
            all_nodes: Dictionary of all nodes from all files
            file_packages: Dictionary mapping files to their packages
            
        Returns:
            List of cross-file dependency edges
        """
        cross_file_edges = []
        
        # Create package -> classes mapping and class -> package mapping
        package_classes = {}
        class_to_package = {}
        
        for node_name, node_info in all_nodes.items():
            if node_info["type"] == "class" and node_info["package"]:
                package = node_info["package"]
                class_name = node_name.split('.')[-1]
                
                if package not in package_classes:
                    package_classes[package] = []
                package_classes[package].append(class_name)
                class_to_package[class_name] = package
        
        # Analyze imports and dependencies from each file
        for file_path, package in file_packages.items():
            if not package:
                continue
                
            try:
                # Read the file and extract imports
                imports = self._extract_imports_from_file(file_path)
                
                for import_stmt in imports:
                    # Check if this import references classes from other packages in our analysis
                    imported_package = '.'.join(import_stmt.split('.')[:-1])  # Remove class name
                    imported_class = import_stmt.split('.')[-1]
                    
                    # If the imported package is different from current package and exists in our analysis
                    if (imported_package != package and 
                        imported_package in package_classes and
                        imported_class in package_classes[imported_package]):
                        
                        cross_file_edges.append({
                            "from": package,
                            "to": imported_package,
                            "type": "import_dependency",
                            "source_file": "cross_file_analysis",
                            "details": f"imports {imported_class}"
                        })
                        
            except Exception as e:
                self.logger.warning(f"Failed to analyze imports from {file_path}: {e}")
        
        # Also look for method calls and class instantiations across packages
        for edge in self._extract_cross_package_calls(all_nodes):
            cross_file_edges.append(edge)
        
        # Remove duplicates
        seen = set()
        unique_edges = []
        for edge in cross_file_edges:
            edge_key = (edge["from"], edge["to"], edge["type"])
            if edge_key not in seen:
                seen.add(edge_key)
                unique_edges.append(edge)
        
        return unique_edges
    
    def _extract_imports_from_file(self, file_path: str) -> List[str]:
        """Extract import statements from a Java file.
        
        Args:
            file_path: Path to the Java file
            
        Returns:
            List of imported class names with full package paths
        """
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('import ') and not line.startswith('import static'):
                        # Extract the import path, remove 'import ' and ';'
                        import_path = line[7:].rstrip(';').strip()
                        if not import_path.startswith('java.'):  # Skip standard Java imports
                            imports.append(import_path)
                    # Stop at class declaration
                    elif line.startswith('public class') or line.startswith('class'):
                        break
        except Exception as e:
            self.logger.warning(f"Failed to read imports from {file_path}: {e}")
        
        return imports
    
    def _extract_cross_package_calls(self, all_nodes: Dict) -> List[Dict]:
        """Extract cross-package method calls and dependencies.
        
        Args:
            all_nodes: Dictionary of all nodes
            
        Returns:
            List of cross-package dependency edges
        """
        cross_calls = []
        
        # Group nodes by package
        package_nodes = {}
        for node_name, node_info in all_nodes.items():
            package = node_info.get("package")
            if package:
                if package not in package_nodes:
                    package_nodes[package] = []
                package_nodes[package].append((node_name, node_info))
        
        # Look for references between different packages
        for package1, nodes1 in package_nodes.items():
            for package2, nodes2 in package_nodes.items():
                if package1 != package2:
                    # Check if any node in package1 references nodes in package2
                    for node1_name, node1_info in nodes1:
                        for node2_name, node2_info in nodes2:
                            # Simple heuristic: if class name from package2 appears in package1 context
                            class2_name = node2_name.split('.')[-1]
                            if (node2_info["type"] == "class" and 
                                class2_name in node1_name and 
                                node1_info["type"] in ["method", "class"]):
                                
                                cross_calls.append({
                                    "from": package1,
                                    "to": package2,
                                    "type": "usage_dependency",
                                    "source_file": "cross_package_analysis",
                                    "details": f"{node1_name} uses {class2_name}"
                                })
        
        return cross_calls
    
    def _add_repository_nodes(self, net, all_nodes: Dict, file_packages: Dict):
        """Add nodes to the repository visualization with proper hierarchy.
        
        Args:
            net: Pyvis network object
            all_nodes: Dictionary of all nodes
            file_packages: Dictionary mapping files to packages
        """
        # Group nodes by package for better organization
        packages = set(file_packages.values())
        
        # Add package nodes (Level 0)
        for package in packages:
            if package:
                net.add_node(
                    package,
                    label=package.split('.')[-1],  # Show only last part
                    title=f"Package: {package}",
                    color='#9C27B0',  # Purple for packages
                    shape='box',
                    size=35,
                    level=0
                )
        
        # Add class nodes (Level 1)
        for node_name, node_info in all_nodes.items():
            if node_info["type"] == "class":
                color = '#1976D2'  # Blue for classes
                shape = 'box'
                size = 25
                level = 1
                
                # Create label and title
                label = node_name.split('.')[-1] if '.' in node_name else node_name
                title = f"Class: {node_name}\\nFile: {node_info['file']}"
                if node_info["package"]:
                    title += f"\\nPackage: {node_info['package']}"
                
                net.add_node(
                    node_name,
                    label=label,
                    title=title,
                    color=color,
                    shape=shape,
                    size=size,
                    level=level
                )
        
        # Add ALL method nodes (Level 2) - but limit total count to avoid cluttering
        method_count = 0
        max_methods = 100  # Increased limit for better repository overview
        
        # Sort methods by importance (constructors, main, public methods first)
        method_nodes = [(name, info) for name, info in all_nodes.items() if info["type"] == "method"]
        
        def method_priority(item):
            name, info = item
            method_name = name.split('.')[-1]
            # Higher priority (lower number) = more important
            if method_name == 'main': return 0
            if method_name == info.get('parent', '').split('.')[-1]: return 1  # Constructor
            if method_name.startswith('get') or method_name.startswith('set'): return 2
            if method_name in ['toString', 'equals', 'hashCode']: return 3
            return 4  # Other methods
        
        method_nodes.sort(key=method_priority)
        
        for node_name, node_info in method_nodes:
            if method_count < max_methods:
                method_simple_name = node_name.split('.')[-1]
                color = '#4CAF50'  # Green for methods
                shape = 'ellipse'
                size = 15
                level = 2
                
                label = method_simple_name
                title = f"Method: {node_name}\\nFile: {node_info['file']}"
                if node_info.get('parent'):
                    title += f"\\nParent: {node_info['parent']}"
                
                net.add_node(
                    node_name,
                    label=label,
                    title=title,
                    color=color,
                    shape=shape,
                    size=size,
                    level=level
                )
                method_count += 1
    
    def _add_repository_edges(self, net, all_edges: List[Dict], all_nodes: Dict):
        """Add edges to the repository visualization.
        
        Args:
            net: Pyvis network object
            all_edges: List of all edges
            all_nodes: Dictionary of all nodes
        """
        valid_nodes = set(net.get_nodes())
        
        # Add package-to-class containment edges
        for node_name, node_info in all_nodes.items():
            if (node_info["type"] == "class" and 
                node_info["package"] and 
                node_info["package"] in valid_nodes and 
                node_name in valid_nodes):
                
                net.add_edge(
                    node_info["package"],
                    node_name,
                    title=f"contains: {node_info['package']} → {node_name}",
                    color='#666666',
                    width=1,
                    dashes=False
                )
        
        # Add class-to-method containment edges
        for node_name, node_info in all_nodes.items():
            if (node_info["type"] == "method" and 
                node_info["parent"] and 
                node_info["parent"] in valid_nodes and 
                node_name in valid_nodes):
                
                net.add_edge(
                    node_info["parent"],
                    node_name,
                    title=f"contains: {node_info['parent']} → {node_name}",
                    color='#666666',
                    width=1,
                    dashes=False
                )
        
        # Add cross-package dependencies
        for edge in all_edges:
            if (edge["type"] in ["package_dependency", "import_dependency", "usage_dependency"] and 
                edge["from"] in valid_nodes and 
                edge["to"] in valid_nodes and
                edge["from"] != edge["to"]):  # Avoid self-loops
                
                # Choose color and style based on dependency type
                if edge["type"] == "import_dependency":
                    color = '#FF5722'  # Red for imports
                    width = 2
                    dashes = True
                    title = f"imports: {edge['from']} → {edge['to']}"
                elif edge["type"] == "usage_dependency":
                    color = '#FF9800'  # Orange for usage
                    width = 2
                    dashes = True
                    title = f"uses: {edge['from']} → {edge['to']}"
                else:
                    color = '#F44336'  # Dark red for other dependencies
                    width = 2
                    dashes = True
                    title = f"depends on: {edge['from']} → {edge['to']}"
                
                if edge.get("details"):
                    title += f"\\n{edge['details']}"
                
                net.add_edge(
                    edge["from"],
                    edge["to"],
                    title=title,
                    color=color,
                    width=width,
                    dashes=dashes
                )
        
        # Add method-level relationships (but only for important ones to avoid clutter)
        important_relationship_types = ["method_call", "dependency", "external_call"]
        relationship_count = 0
        max_relationships = 50  # Limit to avoid overwhelming the visualization
        
        for edge in all_edges:
            if (relationship_count < max_relationships and
                edge["type"] in important_relationship_types and
                edge["from"] in valid_nodes and 
                edge["to"] in valid_nodes and
                edge["from"] != edge["to"]):
                
                # Style based on relationship type
                if edge["type"] == "method_call":
                    color = '#2196F3'  # Blue for method calls
                    width = 1
                    dashes = False
                elif edge["type"] == "dependency":
                    color = '#4CAF50'  # Green for dependencies
                    width = 1
                    dashes = False
                else:  # external_call
                    color = '#9E9E9E'  # Gray for external calls
                    width = 1
                    dashes = True
                
                net.add_edge(
                    edge["from"],
                    edge["to"],
                    title=f"{edge['type']}: {edge['from']} → {edge['to']}",
                    color=color,
                    width=width,
                    dashes=dashes
                )
                relationship_count += 1

    def _process_files_parallel(self, java_files: List[str], repo_path: str, output_dir: str,
                               documentation: bool, visualization: bool) -> List[Dict[str, Any]]:
        """Process multiple Java files in parallel.
        
        Args:
            java_files: List of Java file paths
            repo_path: Repository root path
            output_dir: Output directory
            documentation: Whether to create documentation
            visualization: Whether to create visualizations
            
        Returns:
            List of file processing results
        """
        # Shared progress tracking
        progress_lock = asyncio.Lock()
        progress_state = {
            'completed': 0,
            'total': len(java_files)
        }
        
        async def _process_all_files():
            # Create semaphore to limit concurrent file processing
            semaphore = asyncio.Semaphore(self.max_concurrent_files)
            
            # Track active processing for better logging
            active_files = set()
            active_lock = asyncio.Lock()
            
            async def _process_file_with_semaphore(java_file: str) -> Dict[str, Any]:
                file_name = Path(java_file).name
                
                # Wait for semaphore slot
                async with semaphore:
                    # Track active files for parallel processing visibility
                    async with active_lock:
                        active_files.add(file_name)
                    
                    # Process the file
                    result = await self._process_single_file_async(
                        java_file, repo_path, output_dir, documentation, visualization, 
                        progress_lock, progress_state
                    )
                    
                    # Remove from active files
                    async with active_lock:
                        active_files.discard(file_name)
                    
                    return result
            
            # Create tasks for all files
            tasks = []
            for java_file in java_files:
                task = _process_file_with_semaphore(java_file)
                tasks.append(task)
            
            
            # Execute all tasks concurrently and collect results
            import time
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Process results and convert exceptions to error dictionaries
            file_results = []
            successful_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    file_result = {
                        "file_path": java_files[i],
                        "relative_path": str(Path(java_files[i]).relative_to(repo_path)),
                        "documentation_path": None,
                        "visualization_path": None,
                        "analysis_path": None,
                        "errors": [f"Processing failed: {result}"]
                    }
                    log_error(f"Failed to process {Path(java_files[i]).name}: {result}")
                else:
                    file_result = result
                    successful_count += 1
                
                file_results.append(file_result)
            
            # Log concise parallel processing summary
            processing_time = end_time - start_time
            self.logger.info(f"Completed {successful_count}/{len(java_files)} files in {processing_time:.1f}s")
            
            return file_results
        
        # Run the async function
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_process_all_files())
    
    async def _process_single_file_async(self, java_file: str, repo_path: str, output_dir: str,
                                       documentation: bool, visualization: bool,
                                       progress_lock: asyncio.Lock = None, 
                                       progress_state: dict = None) -> Dict[str, Any]:
        """Process a single Java file asynchronously.
        
        Args:
            java_file: Path to the Java file
            repo_path: Repository root path
            output_dir: Output directory
            documentation: Whether to create documentation
            visualization: Whether to create visualization
            progress_lock: Lock for progress tracking
            progress_state: State for progress tracking
            
        Returns:
            Dictionary containing file processing results
        """
        file_result = {
            "file_path": java_file,
            "relative_path": str(Path(java_file).relative_to(repo_path)),
            "documentation_path": None,
            "visualization_path": None,
            "analysis_path": None,
            "errors": []
        }
        
        try:
            # Documentation (async)
            if documentation:
                doc_output_dir = os.path.join(output_dir, "documentation")
                
                # Preserve directory structure in output
                rel_path = Path(java_file).relative_to(repo_path)
                doc_file_dir = os.path.join(doc_output_dir, str(rel_path.parent))
                os.makedirs(doc_file_dir, exist_ok=True)
                
                documented_path = await self.async_documenter.process_file_async(java_file, doc_file_dir)
                file_result["documentation_path"] = documented_path
                
        except Exception as e:
            file_result["errors"].append(f"Documentation failed: {e}")
        
        try:
            # Analysis only (no individual visualization files)
            if visualization:
                analysis_output_dir = os.path.join(output_dir, "analysis")
                os.makedirs(analysis_output_dir, exist_ok=True)
                
                # Use repository architecture analyzer for high-level analysis (run in thread pool to avoid blocking)
                loop = asyncio.get_event_loop()
                architecture_analysis = await loop.run_in_executor(
                    None, 
                    self.architecture_analyzer.analyze_file_architecture, 
                    java_file
                )
                
                # Save analysis data for the combined visualization
                file_name = Path(java_file).stem
                analysis_path = os.path.join(analysis_output_dir, f"{file_name}_analysis.json")
                with open(analysis_path, 'w') as f:
                    json.dump(architecture_analysis, f, indent=2)
                
                file_result["analysis_path"] = analysis_path
                file_result["visualization_path"] = None  # No individual HTML file
                
                # Store architecture data for later combination (repository-level visualization)
                # Note: file_graphs kept for backward compatibility, but architecture analysis is primary
                
        except Exception as e:
            file_result["errors"].append(f"Analysis failed: {e}")
        
        # Log progress with timing
        if progress_lock and progress_state:
            async with progress_lock:
                progress_state['completed'] += 1
                completed = progress_state['completed']
                total = progress_state['total']
                percentage = (completed / total) * 100
                # Only log major milestones for large repositories
                if total >= 20 and completed in [total // 4, total // 2, (3 * total) // 4]:
                    self.logger.info(f"🎯 {completed}/{total} files completed ({percentage:.1f}%)")
        else:
            log_progress(f"Completed: {Path(java_file).name}", 1, 1)
        
        return file_result
    
    def _log_performance_summary(self, metrics: Dict[str, Any], successful_files: int, total_files: int):
        """Log concise performance summary.
        
        Args:
            metrics: Performance metrics dictionary
            successful_files: Number of successfully processed files
            total_files: Total number of files
        """
        
        # Concise summary
        self.logger.info("=" * 60)
        if metrics['total_relationships'] > 0:
            self.logger.info(f"Architecture: {metrics['total_relationships']} relationships found")
        self.logger.info("=" * 60)

    def _save_processing_report(self, results: Dict[str, Any], output_dir: str):
        """Save processing report to JSON file.
        
        Args:
            results: Processing results
            output_dir: Output directory
        """
        report_path = os.path.join(output_dir, "processing_report.json")
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Processing report saved: {report_path}") 