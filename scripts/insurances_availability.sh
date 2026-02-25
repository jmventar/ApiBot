#!/bin/bash
#
# Sample script: IT environment - fix mappings and sync schedules
# Usage: bash scripts/insurances_availability.sh
# WARNING: Never hardcode real tokens here. Export TOKEN before running or replace the placeholder.

set -euo pipefail

cd ~/workspace/ApiBot
source .venv/bin/activate

TOKEN="${TOKEN:-<your-bearer-token>}"

# IT - Fix mappings
python ./src/main.py \
  -m POST \
  -d 0.5 \
  -s "csv" \
  -f ~/Documents/IT_insurance_migration/mapping.csv \
  -u "https://<your-api-host>/api/admin/servicebase/{{sourceItemServiceId}}/{{targetItemServiceId}}" \
  -t "$TOKEN"

# IT - Sync affected schedules
python ./src/main.py \
  -m POST \
  -d 0.5 \
  --clean \
  -f ~/Documents/IT_insurance_migration/schedules.json \
  -u "https://<your-api-host>/api/admin/schedule/{{0}}/syncservices" \
  -t "$TOKEN"
