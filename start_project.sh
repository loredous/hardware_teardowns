#!/bin/bash

if [[ -z "$1" ]]; then echo "Usage: $0 <project_name>"; exit 1; fi

mkdir "$1"
mkdir "$1/datasheets"
mkdir "$1/images"
mkdir "$1/outputs"

cp TEMPLATE.md "$1/NOTES.md"

echo "Project '$1' created with folder structure and NOTES.md template."