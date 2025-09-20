#!/bin/bash
# Demo Usage Script for Modular Workflow Integration System
# This script demonstrates the key features of the integration system

echo "🚀 Brainstorm Pipeline - Modular Workflow Integration Demo"
echo "========================================================"

# Step 1: Validate the template
echo ""
echo "📋 Step 1: Validating workflow template..."
python json_plan_tool_extended.py validate-template templates/sdlc_12_layer_template.yaml

if [ $? -ne 0 ]; then
    echo "❌ Template validation failed. Please check the template file."
    exit 1
fi

echo "✅ Template validation passed!"

# Step 2: List template variables
echo ""
echo "📝 Step 2: Listing template variables..."
python json_plan_tool_extended.py list-variables templates/sdlc_12_layer_template.yaml

# Step 3: Generate configuration template (if not exists)
echo ""
echo "⚙️  Step 3: Checking configuration..."
if [ ! -f "demo_config.yaml" ]; then
    echo "Generating configuration template..."
    python json_plan_tool_extended.py generate-config templates/sdlc_12_layer_template.yaml demo_config.yaml
    echo "✅ Configuration template generated: demo_config.yaml"
    echo "📝 Please review and customize demo_config.yaml before continuing."
    exit 0
else
    echo "✅ Configuration file exists: demo_config.yaml"
fi

# Step 4: Render the workflow (dry run first)
echo ""
echo "🔧 Step 4: Rendering workflow (dry run)..."
python json_plan_tool_extended.py render-template templates/sdlc_12_layer_template.yaml demo_config.yaml demo_output.json --dry-run

# Step 5: Render the actual workflow
echo ""
echo "🔧 Step 5: Rendering actual workflow..."
python json_plan_tool_extended.py render-template templates/sdlc_12_layer_template.yaml demo_config.yaml demo_output.json

if [ $? -eq 0 ]; then
    echo "✅ Workflow rendered successfully: demo_output.json"
    echo "📄 Pipeline has $(jq '.layers | length' demo_output.json) layers"
else
    echo "❌ Workflow rendering failed"
    exit 1
fi

# Step 6: Test integration (without actual execution)
echo ""
echo "🧪 Step 6: Testing integration..."
python cli_multi_rapid_integration.py test templates/sdlc_12_layer_template.yaml demo_config.yaml

if [ $? -eq 0 ]; then
    echo "✅ Integration test passed!"
else
    echo "❌ Integration test failed"
    exit 1
fi

# Step 7: Generate CLI commands for manual execution
echo ""
echo "📋 Step 7: Generating CLI commands..."
python cli_multi_rapid_integration.py generate-commands templates/sdlc_12_layer_template.yaml demo_config.yaml

# Step 8: Execute workflow (if CLI Multi-Rapid is available)
echo ""
echo "🚀 Step 8: Checking if we can execute the workflow..."

if [ -d "../cli_multi_rapid_DEV" ]; then
    echo "CLI Multi-Rapid detected. Would you like to execute the workflow? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "🚀 Executing workflow..."
        python cli_multi_rapid_integration.py execute templates/sdlc_12_layer_template.yaml demo_config.yaml --output-dir demo_artifacts

        if [ $? -eq 0 ]; then
            echo ""
            echo "🎉 Workflow execution completed!"
            echo "📁 Check demo_artifacts/ for generated artifacts"
            ls -la demo_artifacts/ 2>/dev/null || echo "No artifacts directory created"
        else
            echo "❌ Workflow execution failed"
        fi
    else
        echo "⏭️  Skipping workflow execution"
    fi
else
    echo "ℹ️  CLI Multi-Rapid not detected. Using local simulation mode..."
    python cli_multi_rapid_integration.py execute templates/sdlc_12_layer_template.yaml demo_config.yaml --output-dir demo_artifacts

    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Local simulation completed!"
        echo "📁 Check demo_artifacts/ for simulated artifacts"
        ls -la demo_artifacts/ 2>/dev/null || echo "No artifacts directory created"
    fi
fi

# Step 9: Show summary
echo ""
echo "📊 Demo Summary"
echo "==============="
echo "✅ Template validation"
echo "✅ Configuration generation"
echo "✅ Workflow rendering"
echo "✅ Integration testing"
echo "✅ Command generation"
echo "📁 Generated files:"
ls -la demo_config.yaml demo_output.json execution_commands.sh 2>/dev/null

echo ""
echo "🎯 Next Steps:"
echo "1. Customize demo_config.yaml for your project"
echo "2. Create your own templates in templates/"
echo "3. Run: python cli_multi_rapid_integration.py execute [template] [config]"
echo "4. Check artifacts/ directory for results"

echo ""
echo "📚 For more information, see README_MODULAR_WORKFLOWS.md"