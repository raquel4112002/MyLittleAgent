# MyLittleAgent

MyLittleAgent is a research-oriented multi-agent orchestration platform being developed as part of an autonomous red-team project. It began from an evolved ChatDev-based codebase and is being extended into a more persistent, observable, and human-steerable system for complex agent workflows.

Rather than treating agent execution as a one-shot process, MyLittleAgent is being shaped as a live operational environment where workflows, agent conversations, supervision, and session continuity all matter.

## What MyLittleAgent is trying to become

The long-term goal of this project is to provide a platform where:

- multi-agent workflows can be defined and executed through structured YAML configurations
- agent activity can be observed in real time
- sessions remain persistent instead of disappearing after a single run
- the human operator can intervene during execution
- agents can explicitly ask for clarification and resume after receiving input
- conversations can continue after the main workflow has finished, without forcing a full relaunch
- the interface can evolve from a basic control panel into a richer operational workspace, including simulation-style visual views of agent collaboration

In other words, MyLittleAgent is not intended to be just another workflow launcher. It is being developed as a controllable, inspectable, and extensible multi-agent environment.

## Why this project was built from a ChatDev-based foundation

This project did not start from a blank slate. An existing ChatDev-based codebase provided a practical initial foundation for:

- multi-agent orchestration
- YAML-based workflow definition
- runtime execution scaffolding
- a frontend/backend structure suitable for experimentation
- rapid prototyping of collaborative agent pipelines

Using that base made it possible to move faster in the exploratory phase of development and focus earlier on the research and engineering questions that mattered most.

However, the original foundation was not enough for the intended use case. MyLittleAgent is being extended beyond that base to support features that are especially important for an autonomous red-team platform, such as:

- structured session persistence
- event-based observability
- human-in-the-loop pause/resume behaviour
- free-form human messaging during and after execution
- richer agent monitoring interfaces
- experimental operational views such as office-style and 2D simulation interfaces

## What currently comes from the inherited base

The inherited ChatDev-based foundation contributed important building blocks, including:

- the initial multi-agent workflow execution model
- YAML-driven workflow organization
- parts of the backend runtime structure
- the original frontend shell and workflow interaction patterns
- reusable orchestration concepts and project scaffolding

## What is new in MyLittleAgent

The project is being progressively extended with its own capabilities, including:

- session and event layers for observability
- persistent session tracking
- human request / reply flows
- support for free-form human messages into live sessions
- monitoring views such as session monitor, office view, and office 2D simulation view
- a redesigned visual identity distinct from the original ChatDev presentation

## Credits and acknowledgement

This project is built on top of an existing ChatDev-based foundation, and that original work deserves clear acknowledgement.

Credit goes to the ChatDev project for the foundational multi-agent ideas and implementation substrate that made early experimentation significantly faster and more practical.

- ChatDev GitHub: https://github.com/OpenBMB/ChatDev

MyLittleAgent should therefore be understood as an evolved and specialized derivative platform: it reuses useful architectural ideas from ChatDev while extending them in directions required by this project.

## Current status

At the current stage, this repository already includes:

- backend runtime and workflow engine
- frontend web UI
- YAML workflows created so far
- utility, tooling, and server modules
- observability-oriented session/event structures
- early human-in-the-loop and persistent-session features
- experimental office-style monitoring views

The system is still under active refactoring and expansion.

## Local setup

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
- `sessions/` - session persistence artifacts
- `events/` - structured event support

## Repository note

This project is intentionally being refactored incrementally. Visible names already reflect MyLittleAgent in many areas, but some internal references, legacy files, or inherited implementation details may still reflect the earlier ChatDev/DevAll lineage while the migration continues.
