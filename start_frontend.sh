#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/frontend"
VITE_API_BASE_URL=http://localhost:6400 npm run dev
