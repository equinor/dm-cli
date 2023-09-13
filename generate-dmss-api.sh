#!/usr/bin/env bash

# DMSS must be running locally on port 5000.
# This can be achieved by running "docker-compose pull && docker-compose up -d" from the ./tests/integration folder
# Must be run from repository root, and will create folder 'dmss-api' under ./dm-cli

echo "Creating DMSS Python package version $PACKAGE_VERSION"
docker run --rm \
--network="host" \
-v ${PWD}/dm_cli/dmss_api:/local/dm_cli/dmss_api/ \
openapitools/openapi-generator-cli:v6.0.0 generate \
-i http://localhost:5000/openapi.json  \
-g python \
-o /local/dm_cli \
--additional-properties=packageName=dm_cli.dmss_api