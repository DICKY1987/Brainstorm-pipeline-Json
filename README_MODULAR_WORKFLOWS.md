# Modular Workflow Integration System

This system integrates CLI Multi-Rapid's YAML-based workflow orchestration with Brainstorm Pipeline's JSON-based layer system to create configurable, non-hardcoded workflows.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install pydantic jinja2 jsonschema pyyaml
```

### 2. Basic Usage

```bash
# Validate a workflow template
python json_plan_tool_extended.py validate-template templates/sdlc_12_layer_template.yaml

# Generate a configuration template
python json_plan_tool_extended.py generate-config templates/sdlc_12_layer_template.yaml my_config.yaml

# Render workflow with configuration
python json_plan_tool_extended.py render-template templates/sdlc_12_layer_template.yaml configs/example_config.yaml output.json

# Execute workflow with CLI Multi-Rapid
python cli_multi_rapid_integration.py execute templates/sdlc_12_layer_template.yaml configs/example_config.yaml
```

## 📁 Directory Structure

```
brainstorm-pipeline-integration/
├── workflow_bridge.py              # Core integration module
├── json_plan_tool_extended.py      # Extended JSON plan tool
├── cli_multi_rapid_integration.py  # CLI Multi-Rapid integration
├── templates/                      # Workflow templates
│   ├── sdlc_12_layer_template.yaml # 12-layer SDLC template
│   ├── simple_pipeline.yaml       # Simple 3-layer template
│   └── security_focused.yaml      # Security-focused template
├── schemas/                        # Validation schemas
│   ├── workflow_template.json     # Template schema
│   ├── runtime_config.json       # Runtime config schema
│   └── tool_config.json          # Tool configuration schema
├── configs/                        # Runtime configurations
│   ├── example_config.yaml       # Example configuration
│   ├── python_project.yaml       # Python project config
│   └── security_audit.yaml       # Security audit config
└── artifacts/                     # Generated artifacts
    ├── rendered_workflows/        # Rendered JSON pipelines
    ├── execution_logs/           # Execution logs
    └── layer_outputs/           # Layer-specific outputs
```

## 🔧 Core Components

### 1. Workflow Bridge (`workflow_bridge.py`)

The main integration module that:
- Loads YAML workflow templates
- Validates configurations against schemas
- Renders templates with Jinja2
- Generates CLI Multi-Rapid compatible configurations

### 2. Extended JSON Plan Tool (`json_plan_tool_extended.py`)

Enhanced version of the original tool with:
- Template processing capabilities
- Configuration generation
- Template validation and comparison
- Backward compatibility with original tool

### 3. CLI Multi-Rapid Integration (`cli_multi_rapid_integration.py`)

Orchestrates execution with:
- CLI Multi-Rapid framework integration
- Local fallback execution
- Cost tracking and budget enforcement
- Artifact management

## 📝 Template Structure

### Basic Template Format

```yaml
name: "My Workflow Template"
version: "1.0"
description: "Description of what this workflow does"

variables:
  - name: "project_name"
    type: "string"
    required: true
    description: "Name of the project"

  - name: "ai_tool"
    type: "string"
    default: "claude_code"
    options: ["claude_code", "aider_local", "gemini_cli"]
    description: "AI tool to use"

tools:
  - name: "claude_code"
    type: "ai_agent"
    model: "claude-3-sonnet"
    max_tokens: 4000
    temperature: 0.1

roles:
  - name: "Generator"
    description: "Generates code and documentation"
    system_prompt: "You are a {{ primary_language }} expert..."
    tools: ["{{ ai_tool }}"]

layers:
  - name: "{{ project_name }} - Requirements"
    purpose: "Requirements gathering for {{ project_name }}"
    agents: ["Generator", "Critic"]
    # ... layer configuration
```

### Variable Types

- **string**: Text values
- **number**: Numeric values (int/float)
- **boolean**: True/false values
- **list**: Array of values
- **dict**: Key-value objects

### Template Features

- **Jinja2 templating**: Use `{{ variable }}` syntax
- **Conditional logic**: `{{ condition and 'value1' or 'value2' }}`
- **Tool/role references**: Dynamic tool assignment
- **Schema validation**: Automatic validation against JSON schemas

## ⚙️ Configuration

### Runtime Configuration Format

```yaml
variables:
  project_name: "E-Commerce Platform"
  primary_language: "python"
  ai_tool: "claude_code"
  cost_budget_usd: 25.0

tool_overrides:
  claude_code:
    model: "claude-3-sonnet"
    temperature: 0.05
    max_tokens: 8000

execution_config:
  dry_run: false
  parallel_execution: true
  max_retries: 3
  timeout_minutes: 60

cost_controls:
  max_total_cost: 25.0
  cost_per_layer_limit: 3.0
  preferred_models:
    - "gemini-pro"      # Cheapest
    - "claude-3-haiku"  # Medium
    - "claude-3-sonnet" # Premium

git_config:
  auto_commit: true
  branch_prefix: "workflow/"
  commit_message_template: "{{ layer.section }}: {{ layer.purpose }}"
```

## 🎯 Usage Examples

### Example 1: Python Web Application

```bash
# Create configuration for Python web app
cat > python_webapp.yaml << EOF
variables:
  project_name: "Django E-Commerce"
  primary_language: "python"
  ai_tool: "claude_code"
  test_framework: "pytest"
  enable_security_scanning: true
  cost_budget_usd: 30.0
EOF

# Render and execute
python json_plan_tool_extended.py render-template \
  templates/sdlc_12_layer_template.yaml \
  python_webapp.yaml \
  django_pipeline.json

python cli_multi_rapid_integration.py execute \
  templates/sdlc_12_layer_template.yaml \
  python_webapp.yaml
```

### Example 2: Security-Focused Audit

```bash
# Create security audit configuration
cat > security_audit.yaml << EOF
variables:
  project_name: "Security Audit"
  primary_language: "javascript"
  ai_tool: "gemini_cli"  # Cost-effective for analysis
  enable_security_scanning: true
  max_loops_per_layer: 5  # More thorough
  cost_budget_usd: 15.0

execution_config:
  parallel_execution: false  # Sequential for thoroughness
  timeout_minutes: 120
EOF

# Execute security-focused workflow
python cli_multi_rapid_integration.py execute \
  templates/security_focused.yaml \
  security_audit.yaml
```

### Example 3: Multi-Language Project

```bash
# Create multi-language configuration
cat > microservices.yaml << EOF
variables:
  project_name: "Microservices Platform"
  services:
    - name: "user-service"
      language: "java"
      framework: "spring-boot"
    - name: "payment-service"
      language: "python"
      framework: "fastapi"
    - name: "frontend"
      language: "javascript"
      framework: "react"
  ai_tool: "claude_code"
  cost_budget_usd: 50.0
EOF

# Use custom template for microservices
python cli_multi_rapid_integration.py execute \
  templates/microservices_template.yaml \
  microservices.yaml
```

## 🔍 Advanced Features

### Template Validation

```bash
# Validate template syntax and schema
python json_plan_tool_extended.py validate-template templates/my_template.yaml

# List all variables in a template
python json_plan_tool_extended.py list-variables templates/sdlc_12_layer_template.yaml

# Compare two templates with same config
python json_plan_tool_extended.py diff-templates \
  templates/template_v1.yaml \
  templates/template_v2.yaml \
  configs/test_config.yaml
```

### Configuration Management

```bash
# Generate configuration template from workflow template
python json_plan_tool_extended.py generate-config \
  templates/sdlc_12_layer_template.yaml \
  new_project_config.yaml

# Update existing pipeline with new template
python json_plan_tool_extended.py update-from-template \
  existing_pipeline.json \
  templates/updated_template.yaml \
  configs/my_config.yaml \
  --merge merge_layers
```

### Cost and Budget Management

The system includes sophisticated cost controls:

- **Budget limits**: Set maximum spend per workflow/layer
- **Model preferences**: Use cheaper models first
- **Cost tracking**: Real-time cost monitoring
- **Fallback strategies**: Switch models when budget constrained

### Git Integration

Automatic git integration features:
- **Branch management**: Create branches per workflow
- **Commit automation**: Auto-commit layer completions
- **Merge strategies**: Handle conflicts automatically
- **Provenance tracking**: Full audit trail

## 🛠️ Creating Custom Templates

### Step 1: Define Template Structure

```yaml
name: "Custom Pipeline"
version: "1.0"
description: "Custom workflow for specific needs"

variables:
  # Define your configurable variables
  - name: "custom_param"
    type: "string"
    required: true
    description: "Custom parameter description"

tools:
  # Define available tools
  - name: "custom_tool"
    type: "ai_agent"
    # ... tool configuration

roles:
  # Define agent roles
  - name: "CustomRole"
    description: "Custom role description"
    system_prompt: "Custom prompt with {{ variables }}"

layers:
  # Define workflow layers
  - name: "Custom Layer"
    # ... layer configuration
```

### Step 2: Create Schema (Optional)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Custom Template Schema",
  "type": "object",
  "properties": {
    // Define custom validation rules
  }
}
```

### Step 3: Test Template

```bash
# Validate your template
python json_plan_tool_extended.py validate-template templates/custom_template.yaml

# Generate configuration
python json_plan_tool_extended.py generate-config \
  templates/custom_template.yaml \
  custom_config.yaml

# Test rendering
python json_plan_tool_extended.py render-template \
  templates/custom_template.yaml \
  custom_config.yaml \
  output.json \
  --dry-run
```

## 🚨 Troubleshooting

### Common Issues

1. **Template validation fails**
   ```bash
   # Check template syntax
   python -c "import yaml; yaml.safe_load(open('template.yaml'))"

   # Validate against schema
   python json_plan_tool_extended.py validate-template template.yaml
   ```

2. **Configuration errors**
   ```bash
   # Check required variables
   python json_plan_tool_extended.py list-variables template.yaml

   # Validate configuration
   python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
   ```

3. **CLI Multi-Rapid integration issues**
   ```bash
   # Test integration
   python cli_multi_rapid_integration.py test template.yaml config.yaml

   # Generate manual commands
   python cli_multi_rapid_integration.py generate-commands template.yaml config.yaml
   ```

4. **Cost overruns**
   - Set lower `max_total_cost` in configuration
   - Use cheaper models in `preferred_models`
   - Enable `dry_run` for testing

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export DEBUG_WORKFLOW=true
python cli_multi_rapid_integration.py execute template.yaml config.yaml
```

## 📚 API Reference

### WorkflowBridge Class

```python
from workflow_bridge import WorkflowBridge

bridge = WorkflowBridge()

# Load template
template = bridge.load_workflow_template("template.yaml")

# Render with configuration
pipeline = bridge.render_workflow(template, {"var": "value"})

# Generate CLI Multi-Rapid config
cli_config = bridge.generate_cli_multi_rapid_config(pipeline)
```

### CLIMultiRapidIntegration Class

```python
from cli_multi_rapid_integration import CLIMultiRapidIntegration

integration = CLIMultiRapidIntegration()

# Execute workflow
result = integration.execute_workflow("template.yaml", "config.yaml")

# Generate CLI commands
commands = integration.generate_cli_commands("template.yaml", "config.yaml")
```

## 🤝 Contributing

1. Create new templates in `templates/`
2. Add schemas in `schemas/`
3. Test with example configurations
4. Update documentation
5. Submit pull request

## 📄 License

This integration system follows the same license as the parent repositories.

---

**Need help?** Check the troubleshooting section or create an issue with your template and configuration files.