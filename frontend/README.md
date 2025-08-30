CrewAI AutoDev Frontend
=======================

This folder contains a minimal set of React/Next.js components that
mirror the specification.  To use them you should integrate them
into an existing Next.js project.  The easiest way to get started is
to create a fresh Next.js application, then copy the `components`
and `pages` directories into your project.

```bash
  # create a new Next.js app
  npx create-next-app@latest autodev-ui

  # move into the project
  cd autodev-ui

  # copy the provided components
  cp -r ../autodev/frontend/components ./src/components
  cp -r ../autodev/frontend/pages ./src/pages

  # install any required dependencies (e.g. ws for websockets)
  npm install
  npm run dev
```

These components are purely presentational; they do not connect to
the backend or handle authentication.  You will need to wire them
up to your API endpoints and WebSocket streams to make them fully
functional.
