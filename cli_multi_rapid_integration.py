#!/usr/bin/env python3
"""
CLI Multi-Rapid Integration Script
Integrates Brainstorm Pipeline JSON system with CLI Multi-Rapid orchestrator
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import tempfile
import os
from dataclasses import dataclass, asdict

# Add CLI Multi-Rapid to path if available
CLI_MULTI_RAPID_PATH = Path(__file__).parent.parent / "cli_multi_rapid_DEV"
if CLI_MULTI_RAPID_PATH.exists():
    sys.path.insert(0, str(CLI_MULTI_RAPID_PATH))

try:
    from workflow_bridge import WorkflowBridge
except ImportError:
    print("ERROR: workflow_bridge module not found. Ensure it's in the same directory.")
    sys.exit(1)

@dataclass
class ExecutionResult:
    """Result of workflow execution"""
    success: bool
    layers_completed: int
    total_layers: int
    cost_used: float
    execution_time: float
    artifacts: List[str]
    errors: List[str]

class CLIMultiRapidIntegration:
    """Integration between Brainstorm Pipeline and CLI Multi-Rapid"""

    def __init__(self, cli_multi_rapid_path: Optional[str] = None):
        self.bridge = WorkflowBridge()
        self.cli_path = Path(cli_multi_rapid_path) if cli_multi_rapid_path else CLI_MULTI_RAPID_PATH
        self.temp_dir = Path(tempfile.mkdtemp(prefix="brainstorm_integration_"))

    def execute_workflow(self, template_path: str, config_path: str,
                        output_dir: str = "artifacts") -> ExecutionResult:
        """Execute a workflow using CLI Multi-Rapid orchestrator"""

        try:
            # Step 1: Render the workflow template
            print("🔧 Rendering workflow template...")
            template = self.bridge.load_workflow_template(template_path)

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) if config_path.endswith(('.yaml', '.yml')) else json.load(f)

            # Extract variables
            variables = config.get('variables', {})
            rendered_pipeline = self.bridge.render_workflow(template, variables)

            # Step 2: Create CLI Multi-Rapid compatible configuration
            print("🔀 Converting to CLI Multi-Rapid format...")
            cli_config = self.bridge.generate_cli_multi_rapid_config(rendered_pipeline)

            # Step 3: Setup execution environment
            execution_dir = self._setup_execution_environment(rendered_pipeline, cli_config, output_dir)

            # Step 4: Execute workflow layers
            print(f"🚀 Executing workflow with {len(rendered_pipeline['layers'])} layers...")
            result = self._execute_layers(rendered_pipeline, cli_config, execution_dir, config)

            print(f"✅ Workflow execution completed: {result.layers_completed}/{result.total_layers} layers")
            return result

        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            return ExecutionResult(
                success=False,
                layers_completed=0,
                total_layers=0,
                cost_used=0.0,
                execution_time=0.0,
                artifacts=[],
                errors=[str(e)]
            )

    def _setup_execution_environment(self, pipeline: Dict[str, Any],
                                   cli_config: Dict[str, Any], output_dir: str) -> Path:
        """Setup execution environment with necessary files"""

        execution_dir = self.temp_dir / "execution"
        execution_dir.mkdir(parents=True, exist_ok=True)

        # Create output directory
        artifacts_dir = Path(output_dir)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Write pipeline definition
        pipeline_file = execution_dir / "pipeline.json"
        with open(pipeline_file, 'w') as f:
            json.dump(pipeline, f, indent=2)

        # Write CLI Multi-Rapid job configuration
        jobs_file = execution_dir / "agent_jobs.yaml"
        with open(jobs_file, 'w') as f:
            yaml.dump(cli_config, f, default_flow_style=False, indent=2)

        # Create workspace directories for each job
        for job in cli_config.get('jobs', []):
            worktree_path = execution_dir / job['worktree'].lstrip('../')
            worktree_path.mkdir(parents=True, exist_ok=True)

        return execution_dir

    def _execute_layers(self, pipeline: Dict[str, Any], cli_config: Dict[str, Any],
                       execution_dir: Path, config: Dict[str, Any]) -> ExecutionResult:
        """Execute workflow layers using CLI Multi-Rapid orchestrator"""

        layers = pipeline.get('layers', [])
        total_layers = len(layers)
        completed_layers = 0
        total_cost = 0.0
        artifacts = []
        errors = []

        import time
        start_time = time.time()

        try:
            # Check if CLI Multi-Rapid is available
            if not self._check_cli_multi_rapid_availability():
                # Fallback to local execution
                result = self._execute_layers_locally(layers, execution_dir, config)
            else:
                # Use CLI Multi-Rapid orchestrator
                result = self._execute_with_cli_multi_rapid(cli_config, execution_dir, config)

            execution_time = time.time() - start_time

            return ExecutionResult(
                success=result.get('success', True),
                layers_completed=result.get('completed_layers', total_layers),
                total_layers=total_layers,
                cost_used=result.get('cost_used', 0.0),
                execution_time=execution_time,
                artifacts=result.get('artifacts', []),
                errors=result.get('errors', [])
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                layers_completed=completed_layers,
                total_layers=total_layers,
                cost_used=total_cost,
                execution_time=execution_time,
                artifacts=artifacts,
                errors=[str(e)]
            )

    def _check_cli_multi_rapid_availability(self) -> bool:
        """Check if CLI Multi-Rapid is available"""
        agentic_framework = self.cli_path / "agentic_framework_v3.py"
        return agentic_framework.exists()

    def _execute_with_cli_multi_rapid(self, cli_config: Dict[str, Any],
                                    execution_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute using CLI Multi-Rapid orchestrator"""

        agentic_framework = self.cli_path / "agentic_framework_v3.py"

        # Prepare execution command
        cmd = [
            sys.executable,
            str(agentic_framework),
            "execute-workflow",
            "--config", str(execution_dir / "agent_jobs.yaml"),
            "--output-dir", str(execution_dir / "artifacts")
        ]

        # Add cost controls if specified
        cost_controls = config.get('cost_controls', {})
        if 'max_total_cost' in cost_controls:
            cmd.extend(['--max-cost', str(cost_controls['max_total_cost'])])

        # Add execution config
        exec_config = config.get('execution_config', {})
        if exec_config.get('dry_run'):
            cmd.append('--dry-run')
        if exec_config.get('parallel_execution', True):
            cmd.append('--parallel')

        try:
            print(f"🔧 Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(execution_dir))

            if result.returncode == 0:
                # Parse results from CLI Multi-Rapid output
                return self._parse_cli_output(result.stdout, execution_dir)
            else:
                return {
                    'success': False,
                    'errors': [result.stderr],
                    'completed_layers': 0,
                    'cost_used': 0.0,
                    'artifacts': []
                }

        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'errors': [f"CLI Multi-Rapid execution failed: {e}"],
                'completed_layers': 0,
                'cost_used': 0.0,
                'artifacts': []
            }

    def _execute_layers_locally(self, layers: List[Dict[str, Any]],
                               execution_dir: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback local execution when CLI Multi-Rapid is not available"""

        print("ℹ️  CLI Multi-Rapid not available, executing layers locally...")

        completed = 0
        artifacts = []
        errors = []

        for i, layer in enumerate(layers):
            try:
                print(f"🔄 Processing layer {i+1}/{len(layers)}: {layer.get('name', f'Layer {i+1}')}")

                # Simulate layer execution
                layer_result = self._simulate_layer_execution(layer, execution_dir)

                if layer_result['success']:
                    completed += 1
                    artifacts.extend(layer_result.get('artifacts', []))
                    print(f"✅ Layer {i+1} completed")
                else:
                    errors.extend(layer_result.get('errors', []))
                    print(f"❌ Layer {i+1} failed: {layer_result.get('error', 'Unknown error')}")

                    # Check if we should continue or halt
                    if not config.get('execution_config', {}).get('continue_on_failure', False):
                        break

            except Exception as e:
                errors.append(f"Layer {i+1} execution error: {str(e)}")
                break

        return {
            'success': len(errors) == 0,
            'completed_layers': completed,
            'cost_used': 0.0,  # No actual cost for simulation
            'artifacts': artifacts,
            'errors': errors
        }

    def _simulate_layer_execution(self, layer: Dict[str, Any], execution_dir: Path) -> Dict[str, Any]:
        """Simulate layer execution for local testing"""

        layer_name = layer.get('name', 'Unknown Layer')
        layer_id = layer.get('id', 'unknown')

        # Create layer output directory
        layer_dir = execution_dir / "artifacts" / layer_id
        layer_dir.mkdir(parents=True, exist_ok=True)

        # Simulate artifacts creation
        artifacts = layer.get('artifacts', {})
        created_artifacts = []

        for artifact_name, artifact_path in artifacts.items():
            full_path = layer_dir / artifact_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Create placeholder artifact
            content = f"# {artifact_name}\n\nGenerated for layer: {layer_name}\nLayer ID: {layer_id}\nGenerated at: {time.ctime()}\n\nThis is a simulated artifact."

            with open(full_path, 'w') as f:
                f.write(content)

            created_artifacts.append(str(full_path))

        # Simulate some processing time
        import time
        time.sleep(0.5)

        return {
            'success': True,
            'artifacts': created_artifacts,
            'layer_id': layer_id,
            'layer_name': layer_name
        }

    def _parse_cli_output(self, output: str, execution_dir: Path) -> Dict[str, Any]:
        """Parse CLI Multi-Rapid output for results"""

        # This is a simplified parser - in reality, you'd parse actual CLI output
        lines = output.split('\n')

        completed_layers = 0
        cost_used = 0.0
        artifacts = []

        for line in lines:
            if "Layer completed" in line:
                completed_layers += 1
            elif "Total cost:" in line:
                try:
                    cost_used = float(line.split("$")[1])
                except (IndexError, ValueError):
                    pass
            elif "Artifact created:" in line:
                artifacts.append(line.split(":", 1)[1].strip())

        return {
            'success': True,
            'completed_layers': completed_layers,
            'cost_used': cost_used,
            'artifacts': artifacts,
            'errors': []
        }

    def generate_cli_commands(self, template_path: str, config_path: str) -> List[str]:
        """Generate CLI commands for manual execution"""

        commands = [
            "# Brainstorm Pipeline - CLI Multi-Rapid Integration",
            "# Generated commands for manual execution",
            "",
            f"# 1. Validate template",
            f"python json_plan_tool_extended.py validate-template {template_path}",
            "",
            f"# 2. Generate configuration if needed",
            f"python json_plan_tool_extended.py generate-config {template_path} example_config.yaml",
            "",
            f"# 3. Render workflow",
            f"python json_plan_tool_extended.py render-template {template_path} {config_path} rendered_workflow.json",
            "",
            f"# 4. Execute with CLI Multi-Rapid (if available)",
            f"python cli_multi_rapid_integration.py execute {template_path} {config_path}",
            "",
            f"# 5. View results",
            f"ls -la artifacts/",
            "",
        ]

        return commands

def main():
    import argparse

    parser = argparse.ArgumentParser(description="CLI Multi-Rapid Integration for Brainstorm Pipeline")
    parser.add_argument('command', choices=['execute', 'generate-commands', 'test'])
    parser.add_argument('template', help='Path to workflow template')
    parser.add_argument('config', help='Path to configuration file')
    parser.add_argument('--output-dir', '-o', default='artifacts', help='Output directory for artifacts')
    parser.add_argument('--cli-path', help='Path to CLI Multi-Rapid installation')

    args = parser.parse_args()

    integration = CLIMultiRapidIntegration(args.cli_path)

    if args.command == 'execute':
        result = integration.execute_workflow(args.template, args.config, args.output_dir)

        print("\n" + "="*50)
        print("EXECUTION SUMMARY")
        print("="*50)
        print(f"Success: {result.success}")
        print(f"Layers: {result.layers_completed}/{result.total_layers}")
        print(f"Cost: ${result.cost_used:.2f}")
        print(f"Time: {result.execution_time:.1f}s")
        print(f"Artifacts: {len(result.artifacts)}")

        if result.errors:
            print(f"Errors: {len(result.errors)}")
            for error in result.errors:
                print(f"  - {error}")

        return 0 if result.success else 1

    elif args.command == 'generate-commands':
        commands = integration.generate_cli_commands(args.template, args.config)

        output_file = "execution_commands.sh"
        with open(output_file, 'w') as f:
            f.write('\n'.join(commands))

        print(f"Generated execution commands: {output_file}")
        print("\nCommands:")
        for cmd in commands:
            print(cmd)

        return 0

    elif args.command == 'test':
        # Test mode - validate template and config without execution
        try:
            integration.bridge.load_workflow_template(args.template)
            print(f"✅ Template valid: {args.template}")

            with open(args.config, 'r') as f:
                config = yaml.safe_load(f) if args.config.endswith(('.yaml', '.yml')) else json.load(f)
            print(f"✅ Configuration valid: {args.config}")

            print("✅ Integration test passed")
            return 0

        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            return 1

if __name__ == "__main__":
    exit(main())