# Code Comprehender

A tool that adds documentation and creates architecture visualizations for Java code using LLMs.

## Setup

### Prerequisites
- Python 3.9+
- OpenAI API key
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Install dependencies:
```
   uv sync
```

2. Set up your API key:
``` 
   echo "OPENAI_API_KEY=your-api-key-here\nGITHUB_TOKEN=your-github-token-here" > .env
```

## Usage

### Single File Processing just for testing

# Add documentation to a Java file
```   
   uv run code-comprehender example/Calculator.java
```
# Create architecture visualization 
```   
   uv run code-comprehender --visualize example/Calculator.java
```

### GitHub Repository Analysis

# Analyze entire repository (creates both docs and visualizations)
```   
   uv run code-comprehender --github github_url
```

# Only documentation
```
   uv run code-comprehender --github github_url --docs-only
```
# Only visualizations
```   
   uv run code-comprehender --github github_url --visualize
```

### GitHub Token Setup

For private repositories, create a GitHub token:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate token with `repo` permissions
3. Either add to `.env` file: `GITHUB_TOKEN=your-token` or use `--github-token` flag

## Options

| Option | Description |
|--------|-------------|
| `--preset gpt-4` | Use GPT-4 instead of default gpt-4o-mini |
| `--visualize` | Create architecture diagrams |
| `--docs-only` | Skip visualizations |
| `--output-dir path` | Custom output directory |
| `--test-connection` | Test API connection |

## Output

- **Single files**: Creates documented version in `output/` directory
- **Repositories**: Creates `output/repo-name/` with:
  - `documentation/` - documented Java files
  - `visualizations/` - individual file architecture diagrams + **combined repository visualization**
  - `analysis/` - JSON analysis data + **repository-level analysis**



The combined visualization is saved as `repository_architecture.html` and provides a comprehensive view of your entire codebase architecture.

## Examples

# Test the tool
```   
   uv run code-comprehender example/Calculator.java
```

# Check available options
```
   uv run code-comprehender --help
```

# Test API connection
```
   uv run code-comprehender --test-connection
```

# Run Github Repository for documentation

```
   uv run code-code-comprehender --github github_url --docs-only
```

# Run Github Repository for visualization

```
   uv run code-code-comprehender --github github_url --visualize
```


# Run Github Repository for both

```
   uv run code-code-comprehender --github github_url
```