#!/bin/bash
while true; do
  file=$(find . -type f ! -name '._*' | fzf --exit-0)
  [ -z "$file" ] && break
  open "$file"
done
