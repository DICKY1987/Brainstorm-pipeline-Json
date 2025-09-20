#!/usr/bin/env python3
"""
Workflow Bridge Module
Integrates CLI Multi-Rapid YAML workflows with Brainstorm Pipeline JSON layers
Enables configurable, non-hardcoded workflow orchestration
"""

import json
import yaml
import re
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from jinja2 import Template, Environment, FileSystemLoader
import jsonschema
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class WorkflowVariable:
    """Represents a configurable variable in a workflow template"""
    name: str
    type: str  # "string", "list", "dict", "boolean", "number"
    default: Any = None
    required: bool = True
    description: str = ""
    options: Optional[List[Any]] = None  # For enum-like variables

@dataclass
class ToolConfiguration:
    """Configuration for a specific tool"""
    name: str
    type: str  # "ai_agent", "static_analyzer", "validator", etc.
    endpoint: Optional[str] = None
    api_key_env: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    custom_params: Optional[Dict[str, Any]] = None

@dataclass
class RoleConfiguration:
    """Configuration for an agent role"""
    name: str
    description: str
    system_prompt: str
    tools: List[str]
    capabilities: List[str]

@dataclass
class WorkflowTemplate:
    """Represents a complete workflow template"""
    name: str
    version: str
    description: str
    variables: List[WorkflowVariable]
    tools: List[ToolConfiguration]
    roles: List[RoleConfiguration]
    layers: List[Dict[str, Any]]
    orchestrator_config: Dict[str, Any]

class WorkflowBridge:
    """Main class for bridging CLI Multi-Rapid and Brainstorm Pipeline workflows"""

    def __init__(self, template_dir: str = "templates", schema_dir: str = "schemas"):
        self.template_dir = Path(template_dir)
        self.schema_dir = Path(schema_dir)
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self._load_schemas()

    def _load_schemas(self):
        """Load JSON schemas for validation"""
        self.schemas = {}
        schema_files = [
            "workflow_template.json",
            "runtime_config.json",
            "tool_config.json",
            "layer_template.json"
        ]

        for schema_file in schema_files:
            schema_path = self.schema_dir / schema_file
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema_name = schema_file.replace('.json', '')
                    self.schemas[schema_name] = json.load(f)

    def load_workflow_template(self, template_path: str) -> WorkflowTemplate:
        """Load a workflow template from YAML file"""
        template_file = self.template_dir / template_path

        if not template_file.exists():
            raise FileNotFoundError(f"Workflow template not found: {template_file}")

        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)

        # Validate against schema if available
        if "workflow_template" in self.schemas:
            jsonschema.validate(template_data, self.schemas["workflow_template"])

        # Parse into WorkflowTemplate object
        variables = [
            WorkflowVariable(**var) for var in template_data.get("variables", [])
        ]

        tools = [
            ToolConfiguration(**tool) for tool in template_data.get("tools", [])
        ]

        roles = [
            RoleConfiguration(**role) for role in template_data.get("roles", [])
        ]

        return WorkflowTemplate(
            name=template_data["name"],
            version=template_data.get("version", "1.0"),
            description=template_data.get("description", ""),
            variables=variables,
            tools=tools,
            roles=roles,
            layers=template_data.get("layers", []),
            orchestrator_config=template_data.get("orchestrator", {})
        )

    def render_workflow(self, template: WorkflowTemplate, config: Dict[str, Any]) -> Dict[str, Any]:
        """Render a workflow template with provided configuration"""
        # Validate configuration against variables
        self._validate_config(template, config)

        # Create Jinja2 context
        context = self._build_context(template, config)

        # Render the workflow layers
        rendered_layers = []
        for layer_template in template.layers:
            rendered_layer = self._render_layer(layer_template, context)
            rendered_layers.append(rendered_layer)

        # Create the final Brainstorm Pipeline JSON structure
        pipeline = {
            "version": template.version,
            "name": template.name,
            "description": template.description,
            "orchestrator": self._render_dict(template.orchestrator_config, context),
            "shared": self._generate_shared_config(template, context),
            "layers": rendered_layers,
            "metadata": {
                "template": template.name,
                "generated_at": datetime.utcnow().isoformat(),
                "config_hash": self._hash_config(config)
            }
        }

        return pipeline

    def _validate_config(self, template: WorkflowTemplate, config: Dict[str, Any]):
        """Validate runtime configuration against template variables"""
        errors = []

        for variable in template.variables:
            if variable.required and variable.name not in config:
                errors.append(f"Required variable '{variable.name}' not provided")

            if variable.name in config:
                value = config[variable.name]

                # Type validation
                expected_type = variable.type
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Variable '{variable.name}' must be string, got {type(value).__name__}")
                elif expected_type == "list" and not isinstance(value, list):
                    errors.append(f"Variable '{variable.name}' must be list, got {type(value).__name__}")
                elif expected_type == "dict" and not isinstance(value, dict):
                    errors.append(f"Variable '{variable.name}' must be dict, got {type(value).__name__}")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"Variable '{variable.name}' must be boolean, got {type(value).__name__}")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Variable '{variable.name}' must be number, got {type(value).__name__}")

                # Options validation
                if variable.options and value not in variable.options:
                    errors.append(f"Variable '{variable.name}' must be one of {variable.options}, got {value}")

        if errors:
            raise ValueError("Configuration validation errors:\n" + "\n".join(errors))

    def _build_context(self, template: WorkflowTemplate, config: Dict[str, Any]) -> Dict[str, Any]:
        """Build Jinja2 template context"""
        context = config.copy()

        # Add defaults for missing variables
        for variable in template.variables:
            if variable.name not in context and variable.default is not None:
                context[variable.name] = variable.default

        # Add tools and roles as lookup maps
        context["_tools"] = {tool.name: asdict(tool) for tool in template.tools}
        context["_roles"] = {role.name: asdict(role) for role in template.roles}

        # Add helper functions
        context["_generate_id"] = lambda prefix: f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        return context

    def _render_layer(self, layer_template: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Render a single layer template"""
        layer = {}

        for key, value in layer_template.items():
            if isinstance(value, str):
                # Render string templates
                template = Template(value)
                layer[key] = template.render(**context)
            elif isinstance(value, (dict, list)):
                # Recursively render nested structures
                layer[key] = self._render_dict(value, context)
            else:
                # Copy as-is for primitive values
                layer[key] = value

        return layer

    def _render_dict(self, obj: Union[Dict, List, str], context: Dict[str, Any]) -> Any:
        """Recursively render dictionary/list structures"""
        if isinstance(obj, dict):
            return {k: self._render_dict(v, context) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._render_dict(item, context) for item in obj]
        elif isinstance(obj, str):
            template = Template(obj)
            return template.render(**context)
        else:
            return obj

    def _generate_shared_config(self, template: WorkflowTemplate, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate shared configuration section"""
        return {
            "knowledge_store": "vector://patterns,contracts,postmortems",
            "artifact_bus": f"s3://workflows/{template.name.lower().replace(' ', '_')}/{{run_id}}/",
            "scoring": {
                "pass_threshold": context.get("pass_threshold", 0.85),
                "gates": {
                    "req_coverage": context.get("req_coverage", 0.8),
                    "unit_coverage": context.get("unit_coverage", 0.8),
                    "sec_critical": context.get("sec_critical", 0)
                }
            },
            "provenance": {
                "manifest_fields": [
                    "inputs", "model_versions", "prompt_hashes",
                    "artifact_hashes", "scores", "costs"
                ]
            },
            "tools": {tool.name: asdict(tool) for tool in template.tools},
            "roles": {role.name: asdict(role) for role in template.roles}
        }

    def _hash_config(self, config: Dict[str, Any]) -> str:
        """Generate hash of configuration for tracking"""
        import hashlib
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:12]

    def generate_cli_multi_rapid_config(self, pipeline: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CLI Multi-Rapid compatible workflow configuration"""
        layers = pipeline.get("layers", [])

        # Convert layers to CLI Multi-Rapid jobs
        jobs = []
        for i, layer in enumerate(layers):
            job = {
                "name": layer.get("name", f"layer-{i}").lower().replace(" ", "-"),
                "tool": self._map_agents_to_tools(layer.get("agents", [])),
                "branch": f"workflow/{layer.get('id', f'layer-{i}')}",
                "worktree": f"../wt-{layer.get('id', f'layer-{i}')}",
                "watch": layer.get("watch_patterns", ["**/*"]),
                "tests": layer.get("test_command", "echo 'No tests defined'"),
                "commit_on": layer.get("commit_trigger", "tests_green")
            }
            jobs.append(job)

        return {
            "version": 2,
            "defaults": {
                "commit_on": "tests_green",
                "max_changes_per_commit": 50,
                "shell": "pwsh",
                "precommit": True
            },
            "jobs": jobs
        }

    def _map_agents_to_tools(self, agents: List[str]) -> str:
        """Map Brainstorm Pipeline agents to CLI Multi-Rapid tools"""
        agent_tool_mapping = {
            "Generator": "claude_code",
            "Critic": "aider_local",
            "Researcher": "gemini_cli",
            "Judge": "auto_fixer"
        }

        # Return the first mapped tool or default
        for agent in agents:
            if agent in agent_tool_mapping:
                return agent_tool_mapping[agent]

        return "claude_code"  # Default fallback

def main():
    """CLI interface for the workflow bridge"""
    import argparse

    parser = argparse.ArgumentParser(description="Workflow Bridge CLI")
    parser.add_argument("command", choices=["render", "validate", "list-templates"])
    parser.add_argument("--template", "-t", help="Template file path")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    bridge = WorkflowBridge()

    if args.command == "list-templates":
        templates = list(bridge.template_dir.glob("*.yaml"))
        print("Available templates:")
        for template in templates:
            print(f"  - {template.name}")

    elif args.command == "validate":
        if not args.template:
            print("Error: --template required for validate command")
            return 1

        try:
            template = bridge.load_workflow_template(args.template)
            print(f"Template '{template.name}' is valid")
            return 0
        except Exception as e:
            print(f"Validation error: {e}")
            return 1

    elif args.command == "render":
        if not args.template or not args.config:
            print("Error: --template and --config required for render command")
            return 1

        try:
            template = bridge.load_workflow_template(args.template)

            with open(args.config, 'r') as f:
                config = yaml.safe_load(f) if args.config.endswith('.yaml') else json.load(f)

            pipeline = bridge.render_workflow(template, config)

            output_path = args.output or f"rendered_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_path, 'w') as f:
                json.dump(pipeline, f, indent=2)

            print(f"Workflow rendered successfully: {output_path}")
            return 0

        except Exception as e:
            print(f"Render error: {e}")
            return 1

    return 0

if __name__ == "__main__":
    exit(main())