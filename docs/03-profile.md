# Profile Reference

The profile is the one file a person writes to describe a universe: the twin's base image, packages, files to provision, environment variables to pass through, dependencies, exposed ports, local repositories to publish, and URLs to rewrite.
`validate-profile` checks it and `launch` renders it into a `compose.yaml` and supporting files that plain `docker compose` runs.

The schema is not designed yet. Every field will be documented here, with its type, default, and what it renders to, before `validate-profile` lands.
