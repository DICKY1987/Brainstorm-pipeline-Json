# Applies repository patches in canonical order and writes the final plan.
param(
  [string]$Base = "Jason updates/expanded_12_layer_plan.json",
  [string]$Out  = "Jason updates/final_263_layers_plan.json",
  [switch]$DryRun
)

$script = Join-Path $PSScriptRoot 'apply_patches_in_order.py'

if ($DryRun) {
  python $script --base $Base --out $Out --dry-run
} else {
  python $script --base $Base --out $Out
}

