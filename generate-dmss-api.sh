#!/usr/bin/env bash
set -euo pipefail

# Regenerates dm_cli/dmss_api from a running DMSS.
#
# Run from the repository root, with DMSS available on $DMSS_URL. That can be had with
# "docker compose pull && docker compose up -d" from ./tests/integration.
#
# Nothing in dm_cli/dmss_api should be edited by hand - it is deleted and rewritten here.

DMSS_URL="${DMSS_URL:-http://localhost:5000}"
GENERATOR_VERSION="v7.24.0"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "Fetching the OpenAPI specification from $DMSS_URL"
curl --fail --silent --show-error "$DMSS_URL/openapi.json" -o "$WORK_DIR/openapi.json"

echo "Generating the client with openapi-generator $GENERATOR_VERSION"
# The specification is mounted rather than fetched by the container, so this does not need
# --network=host, which does not work on Docker Desktop.
docker run --rm \
    --user "$(id -u):$(id -g)" \
    -v "$WORK_DIR:/local" \
    "openapitools/openapi-generator-cli:$GENERATOR_VERSION" generate \
    -i /local/openapi.json \
    -g python \
    -o /local/out \
    --additional-properties=packageName=dm_cli.dmss_api \
    > /dev/null

# Removed rather than copied over, so that models dropped from the specification do not linger.
rm -rf dm_cli/dmss_api
cp -R "$WORK_DIR/out/dm_cli/dmss_api" dm_cli/dmss_api

# Regenerating rewrites files without necessarily changing their size, and Python only compares
# mtime to the second, so leftover bytecode can shadow the new source.
find dm_cli/dmss_api -name __pycache__ -type d -exec rm -rf {} +

echo
echo "Regenerated dm_cli/dmss_api. Now run 'pytest tests/unit'."
