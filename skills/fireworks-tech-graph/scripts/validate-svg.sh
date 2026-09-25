#!/bin/bash
# SVG Validation Script
# Checks SVG syntax and reports detailed errors

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo "Usage: $0 <svg-file>"
    exit 1
fi

SVG_FILE="$1"

if [ ! -f "$SVG_FILE" ]; then
    echo -e "${RED}Error: File not found: $SVG_FILE${NC}"
    exit 1
fi

echo "Validating SVG: $SVG_FILE"
echo "----------------------------------------"

# Check 1: Tag balance
echo -n "Checking tag balance... "
OPEN_TAGS=$(grep -o '<[a-z][a-z0-9]*' "$SVG_FILE" 2>/dev/null | grep -v '</' | wc -l | tr -d ' ' || true)
SELF_CLOSING=$(grep -o '/>' "$SVG_FILE" 2>/dev/null | wc -l | tr -d ' ' || true)
CLOSE_TAGS=$(grep -o '</[a-z][a-z0-9]*>' "$SVG_FILE" 2>/dev/null | wc -l | tr -d ' ' || true)
TOTAL_CLOSE=$((SELF_CLOSING + CLOSE_TAGS))

if [ "$OPEN_TAGS" -eq "$TOTAL_CLOSE" ]; then
    echo -e "${GREEN}✓ Pass${NC} (${OPEN_TAGS} tags)"
else
    echo -e "${RED}✗ Fail${NC} (${OPEN_TAGS} open, ${TOTAL_CLOSE} close)"
fi

# Check 2: Quote check
echo -n "Checking attribute quotes... "
UNQUOTED=$(grep -oE '[a-z-]+=[^"'\''> ]' "$SVG_FILE" 2>/dev/null | wc -l | tr -d ' ' || true)
if [ "$UNQUOTED" -eq 0 ]; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${RED}✗ Fail${NC} (${UNQUOTED} unquoted attributes)"
    grep -n -oE '[a-z-]+=[^"'\''> ]' "$SVG_FILE" | head -5
fi

# Check 3: Special characters in text
echo -n "Checking special characters... "
SPECIAL=$(grep -oE '>[^<]*[<>&][^<]*<' "$SVG_FILE" 2>/dev/null | wc -l | tr -d ' ' || true)
if [ "$SPECIAL" -eq 0 ]; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${YELLOW}⚠ Warning${NC} (${SPECIAL} potential unescaped chars)"
fi

# Check 4: Marker references
echo -n "Checking marker references... "
MARKER_REFS=$(grep -oE 'marker-end="url\(#[^)]+\)"' "$SVG_FILE" 2>/dev/null | grep -oE '#[^)]+' | tr -d '#' | sort -u || true)
MARKER_DEFS=$(grep -oE '<marker id="[^"]+"' "$SVG_FILE" 2>/dev/null | grep -oE 'id="[^"]+"' | tr -d 'id="' | sort -u || true)

MISSING=0
for ref in $MARKER_REFS; do
    if ! echo "$MARKER_DEFS" | grep -q "^${ref}$"; then
        echo -e "${RED}✗ Missing marker: $ref${NC}"
        MISSING=$((MISSING + 1))
    fi
done

if [ "$MISSING" -eq 0 ]; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${RED}✗ Fail${NC} (${MISSING} missing markers)"
fi

# Check 5: Closing </svg> tag
echo -n "Checking closing tag... "
if grep -q '</svg>' "$SVG_FILE"; then
    echo -e "${GREEN}✓ Pass${NC}"
else
    echo -e "${RED}✗ Fail${NC} (missing </svg>)"
fi

# Check 6: rsvg-convert validation
echo -n "Running rsvg-convert validation... "
if command -v rsvg-convert &> /dev/null; then
    if rsvg-convert "$SVG_FILE" -o /tmp/test-output.png 2>/dev/null; then
        echo -e "${GREEN}✓ Pass${NC}"
        rm -f /tmp/test-output.png
    else
        echo -e "${RED}✗ Fail${NC}"
        echo "rsvg-convert error:"
        rsvg-convert "$SVG_FILE" -o /tmp/test-output.png 2>&1 || true
    fi
else
    echo -e "${YELLOW}⚠ Skipped${NC} (rsvg-convert not found)"
fi

echo "----------------------------------------"
echo "Validation complete"
