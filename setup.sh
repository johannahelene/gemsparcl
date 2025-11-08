#!/bin/bash
#
# Setup script for gemsparcl
# This script configures the environment to use gemsparcl with sketchlib

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "     gemsparcl Setup Script"
echo "======================================"
echo ""

# Default sketchlib path for development
DEFAULT_SKETCHLIB="/hps/nobackup/rdf/metagenomics/research-team/johanna/projects/PhD_main/bin/sketchlib.rust/target/release/sketchlib"

# Check if sketchlib exists at the default location
if [ -f "$DEFAULT_SKETCHLIB" ] && [ -x "$DEFAULT_SKETCHLIB" ]; then
    echo -e "${GREEN}✓${NC} Found sketchlib at default location"
    export SKETCHLIB_PATH="$DEFAULT_SKETCHLIB"
else
    echo -e "${YELLOW}!${NC} Sketchlib not found at default location"
    echo ""
    echo "Please provide the path to your sketchlib binary:"
    read -p "SKETCHLIB_PATH: " SKETCHLIB_PATH

    if [ ! -f "$SKETCHLIB_PATH" ] || [ ! -x "$SKETCHLIB_PATH" ]; then
        echo -e "${RED}✗${NC} Invalid path or file is not executable"
        exit 1
    fi

    export SKETCHLIB_PATH
fi

# Verify sketchlib works
echo -n "Verifying sketchlib... "
if $SKETCHLIB_PATH --version > /dev/null 2>&1; then
    VERSION=$($SKETCHLIB_PATH --version)
    echo -e "${GREEN}✓${NC} $VERSION"
else
    echo -e "${RED}✗${NC} Failed to run sketchlib"
    exit 1
fi

echo ""
echo "======================================"
echo "Setup complete!"
echo ""
echo "To use gemsparcl, run this in your shell:"
echo -e "${GREEN}export SKETCHLIB_PATH=\"$SKETCHLIB_PATH\"${NC}"
echo ""
echo "Or add it to your ~/.bashrc for permanent setup:"
echo -e "${GREEN}echo 'export SKETCHLIB_PATH=\"$SKETCHLIB_PATH\"' >> ~/.bashrc${NC}"
echo ""
echo "Then run:"
echo -e "${GREEN}gemsparcl --help${NC}"
echo "======================================"