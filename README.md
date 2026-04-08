# MyLittleAgent

MyLittleAgent is Raquel's forked multi-agent orchestration project, bootstrapped from an evolved ChatDev/DevAll codebase and now being adapted into a persistent, observable agent control center.

## Current goal

Turn this codebase into a system where:

- agent workflows run from YAML and orchestration logic
- the human can observe agents working in real time
- logs and intermediate events are visible live
- agents can ask questions to the human mid-run
- the human can answer without relaunching the workflow
- sessions preserve context across pauses and resumes

## Current status

This repository has already been seeded from the existing ChatDev-based project and includes:

- backend runtime and workflow engine
- frontend web UI
- YAML workflows created so far
- utility, tooling, and server modules

The next development steps are:

1. validate backend/frontend startup in this fork
2. introduce explicit session persistence primitives
3. add event streaming and live observability
4. add human-in-the-loop pause/resume messaging
5. evolve the UI into a real agent operations console

## Run notes

Preferred local setup is documented in [SETUP_LOCAL.md](./SETUP_LOCAL.md).

Backend:

```bash
python server_main.py --port 6400 --reload
```

Frontend:

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:6400 npm run dev
```

## Important folders

- `server/` - FastAPI backend
- `runtime/` - runtime abstractions
- `workflow/` - orchestration engine
- `frontend/` - Vue/Vite UI
- `yaml_instance/` - workflow YAMLs
- `functions/` - callable tool functions
- `utils/` - logging, helpers, env loading

## Migration note

This project is intentionally being refactored incrementally. Visible names may already say MyLittleAgent while deeper docs and some internal references may still mention ChatDev or DevAll until the runtime migration is fully complete.
