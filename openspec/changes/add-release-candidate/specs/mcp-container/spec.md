# Spec Delta

## Purpose

Ship a Dockerfile that runs the read-only Lodestone MCP stdio server so
operators can start the server from an image without a local Python
install, and prove the image builds in CI.

## ADDED Requirements

### Requirement: MCP server container image
The repository SHALL include a `Dockerfile` that installs `lodestone-kb`
and sets the container entrypoint to `lodestone mcp`. A `.dockerignore`
SHALL exclude tests, git metadata, and build artifacts from the build
context.

#### Scenario: Image entrypoint is the MCP server
- **WHEN** the Dockerfile is read
- **THEN** it installs the package and uses `lodestone mcp` as the
  entrypoint (offline is the documented default command)

### Requirement: CI builds the image without pushing
CI SHALL include an Ubuntu-only job that runs `docker build` for the MCP
image and does not push to a registry. The job MUST NOT use quoted
`run: "$VAR/..."` YAML scalars.

#### Scenario: Ubuntu docker-build job
- **WHEN** CI runs on a pull request or push to main
- **THEN** an Ubuntu job executes `docker build` and does not include a
  docker push or registry login step
