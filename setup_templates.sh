#!/bin/bash
# Create templates directory if it doesn't exist
mkdir -p templates

# Check if templates exist and copy them to the right location
if [ -f "templates/index.html" ]; then
    echo "Templates already exist"
else
    echo "Creating template files..."
    # Copy template files from the existing location if they exist
    if [ -d "challenge/templates" ]; then
        cp -r challenge/templates/* templates/
    fi
fi

echo "Template setup complete"

