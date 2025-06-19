"""LLM prompts for different code analysis tasks."""

# Documentation prompt for adding comprehensive comments
DOCUMENTATION_PROMPT = """You are an expert developer and technical writer. Your task is to add extremely comprehensive documentation to the provided code, transforming it into a well-documented, professional codebase.

CRITICAL REQUIREMENT: You MUST add inline comments inside EVERY method body explaining each step of the code. This is not optional.

Please add the following comprehensive documentation:

1. **Class-Level Documentation:**
   - Detailed documentation with class purpose, functionality, and design patterns used
   - Author, version, since tags where appropriate
   - References to related classes
   - Usage examples and typical workflows
   - Thread safety notes if applicable

2. **Method-Level Documentation:**
   - Comprehensive documentation explaining method purpose, algorithm, and behavior
   - Detailed parameter descriptions with types, constraints, and expected values
   - Return descriptions explaining what is returned and under what conditions
   - Exception documentation for all possible exceptions with scenarios
   - Deprecated tags with alternatives if applicable
   - Performance considerations and Big O complexity where relevant
   - Usage examples for complex methods

3. **Field-Level Documentation:**
   - Purpose and usage of each field
   - Value ranges, constraints, and default values
   - Relationships to other fields
   - Thread safety considerations for shared fields

4. **Inline Comments (MANDATORY - MUST BE ADDED INSIDE ALL METHOD BODIES):**
   
   EVERY METHOD BODY MUST HAVE INLINE COMMENTS. For EVERY line or block of code inside methods, add explanatory comments:

   - Add a comment before EVERY while loop explaining what the loop does
   - Add a comment before EVERY for loop explaining its purpose
   - Add a comment before EVERY if statement explaining the condition
   - Add a comment before EVERY switch statement explaining what's being switched
   - Add a comment for EVERY case in switch statements
   - Add a comment before EVERY try-catch block explaining what might fail
   - Add a comment explaining EVERY variable declaration inside methods
   - Add a comment explaining EVERY method call inside methods
   - Add a comment explaining EVERY assignment operation that's not obvious

5. **Code Structure Comments:**
   - Section headers for logical code blocks
   - TODO/FIXME/NOTE comments for improvement areas
   - Comments explaining design decisions and trade-offs
   - References to external documentation or specifications

6. **Special Considerations:**
   - Document any assumptions made by the code
   - Explain error handling strategies
   - Note any platform-specific behavior
   - Document configuration requirements
   - Explain initialization and cleanup procedures

Requirements:
- Keep the original code structure and logic completely intact
- Add only comments and documentation - do not modify any executable code
- Use proper documentation format with all appropriate tags
- Make comments clear, professional, and informative
- Explain both "what" the code does and "why" it does it
- Use proper grammar and professional technical writing style
- Ensure comments are helpful for both novice and experienced developers
- Add blank lines and spacing to improve readability where appropriate
- Use consistent commenting style throughout

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY the pure code with added documentation
- Do NOT include any markdown code blocks
- Do NOT include any explanatory text before or after the code
- Do NOT include any markdown formatting whatsoever
- The output should start directly with the code (package declaration or comments)
- The output should end directly with the closing brace of the class
- Ensure the code can be directly saved as a source file and compiled

Return ONLY the fully documented source code."""

# Code visualization prompt for extracting relationships
VISUALIZATION_PROMPT = """You are an expert code analyzer. Your task is to analyze the provided code and extract the architectural relationships for creating a code visualization diagram.

Analyze the code and identify:

1. **Classes**: All class definitions with their names
2. **Methods/Functions**: All method definitions within each class
3. **Relationships**: Method calls and dependencies between classes and methods

For each code chunk, return a JSON object with the following structure:

{
  "classes": [
    {
      "name": "ClassName",
      "methods": ["method1", "method2", "method3"],
      "fields": ["field1", "field2"]
    }
  ],
  "relationships": [
    {
      "from": "ClassName.methodName",
      "to": "OtherClass.otherMethod",
      "type": "method_call"
    },
    {
      "from": "ClassName",
      "to": "OtherClass",
      "type": "dependency"
    }
  ],
  "external_calls": [
    {
      "from": "ClassName.methodName",
      "to": "System.out.println",
      "type": "external_method_call"
    }
  ]
}

Guidelines:
- Identify all classes, even inner classes
- List all public, private, and protected methods
- Identify method calls within the same class and to other classes
- Include constructor calls as relationships
- Identify field access between classes
- Include external library calls (like System.out.println, Scanner, etc.)
- Use full qualified names when possible (ClassName.methodName)
- If analyzing a code chunk, focus only on relationships visible in that chunk

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY valid JSON
- Do NOT include any explanatory text before or after the JSON
- Do NOT include any markdown formatting
- Ensure the JSON is properly formatted and parseable

Return ONLY the JSON object."""


# Repository-level architectural analysis prompt
REPOSITORY_ARCHITECTURE_PROMPT = """You are an expert software architect analyzing a Java codebase. Your task is to identify the high-level architectural relationships between Java files for creating a repository-level architecture diagram.

FOCUS: Analyze the provided Java code and extract ONLY file-to-file relationships, not method-level details.

For the given Java file, identify:

1. **File Identity**: The main class name and its role/purpose
2. **Dependencies**: Other Java files this file depends on (imports, instantiations, extends/implements)
3. **File Type**: Classify the file's architectural role
4. **Entry/Exit Points**: Whether this file serves as an entry point or exit point

Return a JSON object with this structure:

{
  "file_info": {
    "name": "FileName",
    "main_class": "MainClassName", 
    "file_type": "entry_point|service|utility|data|controller|model|config|exit_point",
    "purpose": "Brief description of file's role",
    "is_entry_point": true/false,
    "is_exit_point": true/false
  },
  "dependencies": [
    {
      "target_file": "OtherFileName",
      "target_class": "OtherClassName",
      "relationship_type": "import|extends|implements|instantiation|static_call",
      "description": "Brief description of dependency"
    }
  ],
  "provides_to": [
    {
      "interface_name": "InterfaceName",
      "service_type": "api|service|utility|data_access",
      "description": "What this file provides to others"
    }
  ]
}

Classification Guidelines:
- **entry_point**: Main classes, CLI entry points, web controllers, application launchers
- **service**: Business logic, service classes, processors
- **utility**: Helper classes, utilities, common functions
- **data**: Models, DTOs, data structures, entities
- **controller**: Request handlers, controllers, coordinators
- **model**: Data models, domain objects
- **config**: Configuration classes, settings, constants
- **exit_point**: Database connections, external API clients, file writers, loggers

Entry/Exit Point Rules:
- **Entry Point**: Has main() method, @Controller annotations, CLI interfaces, or serves as application start
- **Exit Point**: Connects to external systems (databases, APIs, files, networks), logging systems

Focus Areas:
- Import statements (file dependencies)
- Class inheritance (extends/implements)
- Object instantiation of other classes
- Static method calls to other classes
- Interface implementations
- Annotation usage that indicates architectural patterns

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY valid JSON
- Do NOT include explanatory text
- Do NOT include markdown formatting
- Focus on FILE-LEVEL relationships, not method details
- Identify clear entry and exit points

Return ONLY the JSON object."""