#!/bin/bash
# Helper script to run the pytest coverage suite with dynamic context tracking,
# and print the comprehensive test redundancy/overlap audit report.

set -e

# Change directory to project root
cd "$(dirname "$0")/.."

# 1. Run the standard test suite with coverage
echo "==== Running pytest with dynamic context coverage collection... ===="
venv/bin/pytest --cov=src -k "not functional"

# 2. Run the global redundancy measurement audit
echo ""
echo "================================================================================"
echo "==== [GLOBAL] TEST SUITE OVERLAP & REDUNDANCY AUDIT                         ===="
echo "================================================================================"
venv/bin/python3 bin/measure-overlap.py

# 3. Run the isolated unit tier redundancy audit
echo ""
echo "================================================================================"
echo "==== [TIER: UNIT] ISOLATED REDUNDANCY AUDIT                                ===="
echo "================================================================================"
venv/bin/python3 bin/measure-overlap.py --filter "test_attributes,test_resolver,test_preprocessor,test_transformers_unit"

# 4. Run the isolated integration tier redundancy audit
echo ""
echo "================================================================================"
echo "==== [TIER: INTEGRATION] ISOLATED REDUNDANCY AUDIT                          ===="
echo "================================================================================"
venv/bin/python3 bin/measure-overlap.py --filter "test_blocks,test_inlines,test_serializer,test_callouts,test_document_header,test_docutils_backend,test_location_coordinates,test_integration,test_examples,test_tck,test_combined"
