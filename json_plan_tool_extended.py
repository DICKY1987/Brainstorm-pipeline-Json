#!/usr/bin/env python3
"""
Extended JSON Plan Tool with Template Processing
Extends the original json_plan_tool.py with workflow template capabilities
"""

import json, argparse, sys, os, tempfile, hashlib, shutil, difflib, datetime
import yaml
from typing import Any, Tuple, List, Dict, Optional
from pathlib import Path

# Import original json_plan_tool functions
sys.path.append(str(Path(__file__).parent / "Jason updates"))
from json_plan_tool import (
    sha256_bytes, read_json, write_atomic, pointer_get, pointer_add,
    pointer_replace, pointer_remove, _split_pointer, _unescape_token
)

# Import workflow bridge
from workflow_bridge import WorkflowBridge, WorkflowTemplate

class ExtendedJSONPlanTool:
    """Extended JSON Plan Tool with template processing capabilities"""

    def __init__(self):
        self.bridge = WorkflowBridge()

    def render_template_to_plan(self, template_path: str, config_path: str, output_path: str, dry_run: bool = False) -> bool:
        """Render a workflow template into a JSON plan"""
        try:
            # Load template and config
            template = self.bridge.load_workflow_template(template_path)

            with open(config_path, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)

            # Extract variables from config
            variables = config.get('variables', {})

            # Render the workflow
            rendered_pipeline = self.bridge.render_workflow(template, variables)

            if dry_run:
                print("DRY RUN: Rendered pipeline preview:")
                print(json.dumps(rendered_pipeline, indent=2))
                return True

            # Write the rendered pipeline
            write_atomic(output_path, rendered_pipeline)
            print(f"Template rendered successfully: {output_path}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to render template: {e}", file=sys.stderr)
            return False

    def update_plan_from_template(self, plan_path: str, template_path: str, config_path: str,
                                dry_run: bool = False, merge_strategy: str = "replace") -> bool:
        """Update existing plan with rendered template"""
        try:
            # Load existing plan
            existing_plan, _ = read_json(plan_path)

            # Render new template
            template = self.bridge.load_workflow_template(template_path)

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) if config_path.endswith(('.yaml', '.yml')) else json.load(f)

            rendered_pipeline = self.bridge.render_workflow(template, config.get('variables', {}))

            # Merge strategies
            if merge_strategy == "replace":
                merged_plan = rendered_pipeline
            elif merge_strategy == "merge_layers":
                merged_plan = existing_plan.copy()
                merged_plan["layers"] = rendered_pipeline.get("layers", [])
                # Update orchestrator if provided
                if "orchestrator" in rendered_pipeline:
                    merged_plan["orchestrator"] = rendered_pipeline["orchestrator"]
            elif merge_strategy == "append_layers":
                merged_plan = existing_plan.copy()
                existing_layers = merged_plan.get("layers", [])
                new_layers = rendered_pipeline.get("layers", [])
                merged_plan["layers"] = existing_layers + new_layers
            else:
                raise ValueError(f"Unknown merge strategy: {merge_strategy}")

            if dry_run:
                print("DRY RUN: Merged plan preview:")
                print(json.dumps(merged_plan, indent=2))
                return True

            # Write merged plan
            write_atomic(plan_path, merged_plan)
            print(f"Plan updated successfully with template: {plan_path}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to update plan from template: {e}", file=sys.stderr)
            return False

    def validate_template(self, template_path: str) -> bool:
        """Validate a workflow template"""
        try:
            template = self.bridge.load_workflow_template(template_path)
            print(f"Template '{template.name}' v{template.version} is valid")
            print(f"Description: {template.description}")
            print(f"Variables: {len(template.variables)}")
            print(f"Tools: {len(template.tools)}")
            print(f"Roles: {len(template.roles)}")
            print(f"Layers: {len(template.layers)}")
            return True
        except Exception as e:
            print(f"ERROR: Template validation failed: {e}", file=sys.stderr)
            return False

    def list_template_variables(self, template_path: str) -> bool:
        """List all variables in a template"""
        try:
            template = self.bridge.load_workflow_template(template_path)

            print(f"Variables in template '{template.name}':")
            for var in template.variables:
                required = "(required)" if var.required else "(optional)"
                default = f" [default: {var.default}]" if var.default is not None else ""
                options = f" [options: {', '.join(map(str, var.options))}]" if var.options else ""

                print(f"  {var.name} ({var.type}) {required}{default}{options}")
                if var.description:
                    print(f"    {var.description}")

            return True
        except Exception as e:
            print(f"ERROR: Failed to list template variables: {e}", file=sys.stderr)
            return False

    def generate_config_template(self, template_path: str, output_path: str) -> bool:
        """Generate a configuration template from a workflow template"""
        try:
            template = self.bridge.load_workflow_template(template_path)

            config = {
                "# Configuration for": template.name,
                "# Generated": datetime.datetime.utcnow().isoformat(),
                "variables": {}
            }

            # Add variables with defaults/examples
            for var in template.variables:
                if var.default is not None:
                    config["variables"][var.name] = var.default
                elif var.options:
                    config["variables"][var.name] = var.options[0]  # First option as example
                else:
                    # Provide example based on type
                    examples = {
                        "string": "example_value",
                        "number": 42,
                        "boolean": True,
                        "list": ["example", "items"],
                        "dict": {"example": "value"}
                    }
                    config["variables"][var.name] = examples.get(var.type, "CHANGE_ME")

            # Add execution configuration template
            config["execution_config"] = {
                "dry_run": False,
                "parallel_execution": True,
                "max_retries": 3,
                "timeout_minutes": 60
            }

            config["cost_controls"] = {
                "max_total_cost": 50.0,
                "cost_per_layer_limit": 5.0,
                "preferred_models": ["gemini-pro", "claude-3-haiku", "claude-3-sonnet"]
            }

            # Write as YAML for better readability
            with open(output_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2, sort_keys=False)

            print(f"Configuration template generated: {output_path}")
            return True

        except Exception as e:
            print(f"ERROR: Failed to generate config template: {e}", file=sys.stderr)
            return False

    def diff_templates(self, template1_path: str, template2_path: str, config_path: str) -> bool:
        """Show differences between two rendered templates"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) if config_path.endswith(('.yaml', '.yml')) else json.load(f)

            # Render both templates
            template1 = self.bridge.load_workflow_template(template1_path)
            template2 = self.bridge.load_workflow_template(template2_path)

            pipeline1 = self.bridge.render_workflow(template1, config.get('variables', {}))
            pipeline2 = self.bridge.render_workflow(template2, config.get('variables', {}))

            # Generate diff
            json1 = json.dumps(pipeline1, indent=2, sort_keys=True).splitlines()
            json2 = json.dumps(pipeline2, indent=2, sort_keys=True).splitlines()

            diff = list(difflib.unified_diff(
                json1, json2,
                fromfile=f"Template: {template1.name}",
                tofile=f"Template: {template2.name}",
                lineterm=''
            ))

            if not diff:
                print("Templates produce identical output with given configuration")
            else:
                print("\n".join(diff))

            return True

        except Exception as e:
            print(f"ERROR: Failed to compare templates: {e}", file=sys.stderr)
            return False

def main():
    parser = argparse.ArgumentParser(description="Extended JSON Plan Tool with Template Processing")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Original commands (delegate to original tool)
    original_parser = subparsers.add_parser('original', help='Use original json_plan_tool commands')
    original_parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments for original tool')

    # Template rendering
    render_parser = subparsers.add_parser('render-template', help='Render workflow template to JSON plan')
    render_parser.add_argument('template', help='Path to workflow template (YAML)')
    render_parser.add_argument('config', help='Path to configuration file (YAML/JSON)')
    render_parser.add_argument('output', help='Output path for rendered JSON plan')
    render_parser.add_argument('--dry-run', action='store_true', help='Preview output without writing')

    # Update existing plan
    update_parser = subparsers.add_parser('update-from-template', help='Update existing plan with template')
    update_parser.add_argument('plan', help='Path to existing JSON plan')
    update_parser.add_argument('template', help='Path to workflow template')
    update_parser.add_argument('config', help='Path to configuration file')
    update_parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    update_parser.add_argument('--merge', choices=['replace', 'merge_layers', 'append_layers'],
                              default='replace', help='Merge strategy')

    # Template validation
    validate_parser = subparsers.add_parser('validate-template', help='Validate workflow template')
    validate_parser.add_argument('template', help='Path to workflow template')

    # List variables
    vars_parser = subparsers.add_parser('list-variables', help='List template variables')
    vars_parser.add_argument('template', help='Path to workflow template')

    # Generate config template
    genconfig_parser = subparsers.add_parser('generate-config', help='Generate configuration template')
    genconfig_parser.add_argument('template', help='Path to workflow template')
    genconfig_parser.add_argument('output', help='Output path for configuration template')

    # Compare templates
    diff_parser = subparsers.add_parser('diff-templates', help='Compare two rendered templates')
    diff_parser.add_argument('template1', help='First template')
    diff_parser.add_argument('template2', help='Second template')
    diff_parser.add_argument('config', help='Configuration to use for both')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    tool = ExtendedJSONPlanTool()

    # Delegate to original tool for backwards compatibility
    if args.command == 'original':
        import subprocess
        original_script = Path(__file__).parent / "Jason updates" / "json_plan_tool.py"
        return subprocess.call([sys.executable, str(original_script)] + args.args)

    # Handle template commands
    elif args.command == 'render-template':
        success = tool.render_template_to_plan(args.template, args.config, args.output, args.dry_run)
        return 0 if success else 1

    elif args.command == 'update-from-template':
        success = tool.update_plan_from_template(args.plan, args.template, args.config,
                                               args.dry_run, args.merge)
        return 0 if success else 1

    elif args.command == 'validate-template':
        success = tool.validate_template(args.template)
        return 0 if success else 1

    elif args.command == 'list-variables':
        success = tool.list_template_variables(args.template)
        return 0 if success else 1

    elif args.command == 'generate-config':
        success = tool.generate_config_template(args.template, args.output)
        return 0 if success else 1

    elif args.command == 'diff-templates':
        success = tool.diff_templates(args.template1, args.template2, args.config)
        return 0 if success else 1

    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    exit(main())