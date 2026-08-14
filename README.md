# CodeVoyager 🚀

Learn open-source projects with AI-guided code exploration and hands-on learning.

CodeVoyager is an AI-powered learning tool designed to help developers understand and learn real-world open-source projects.

Instead of letting AI write the code for you, CodeVoyager focuses on helping you understand the project, explore the source code, and learn by doing.

💡 Why CodeVoyager?

Learning from real-world open-source projects can be difficult.

When opening a large GitHub repository, developers often face questions like:

Where should I start?
What does this project actually do?
How is the project structured?
Which modules are important?
How does the code flow through the system?
What should I learn first?
How can I verify that I really understand it?

CodeVoyager aims to turn a complex repository into a structured learning journey.

✨ Core Ideas

CodeVoyager is built around four principles:

🗺 Guided Learning

Analyze the project and generate a structured learning path instead of asking users to read the repository randomly.

🔍 Code Exploration

Help users understand:

Project structure
Core modules
Important files
Functions and classes
Code relationships
🤖 AI Tutor

The AI acts as a tutor rather than an autonomous coding agent.

Instead of immediately giving the answer, it can:

Explain unfamiliar code
Provide hints
Ask guiding questions
Help users reason about the project
🧑‍💻 Learn by Doing

Users remain actively involved in the learning process.

The goal is not:

AI builds the project for you.

The goal is:

AI helps you understand how the project was built.

🧩 Planned Workflow
Import GitHub Repository
        ↓
Analyze Project
        ↓
Understand Architecture
        ↓
Generate Learning Path
        ↓
Explore Source Code
        ↓
Complete Learning Tasks
        ↓
AI Guidance
        ↓
Track Learning Progress
🛠 Planned Tech Stack
Backend
Python
FastAPI
Pydantic
SQLAlchemy
AI
LLM API
Tool Calling
Agent Workflow
Code Analysis
Frontend
React
TypeScript
Electron
Monaco Editor
Infrastructure
Linux
Docker
PostgreSQL
Redis
📦 Project Structure
CodeVoyager/
├── backend/        # Backend services
├── frontend/       # Desktop application
├── agent/          # AI tutor and agent logic
├── docs/           # Design and development documents
└── deploy/         # Docker and deployment configuration

The project structure may change as CodeVoyager evolves.

🚧 Project Status

CodeVoyager is currently in the early development stage.

The first milestone focuses on:

Project initialization

GitHub repository import

Basic repository analysis

Project structure visualization

Learning path generation

AI-assisted source code explanation

Learning progress tracking

🎯 Vision

CodeVoyager aims to become a learning environment where developers can study real-world software engineering through open-source projects.

Rather than replacing developers with AI, CodeVoyager uses AI to help developers read more, think more, explore more, and build a deeper understanding of real software systems.

📄 License

License information will be added as the project develops.

## Local development

Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js and npm.

```bash
cp .env.example .env
cd backend && uv sync --dev
cd ../frontend && npm install
cd .. && ./scripts/dev.sh
```

The API runs at `http://127.0.0.1:8000`; its health endpoint is
`GET /health`, and interactive API documentation is available at `/docs`.
The desktop development server runs at `http://localhost:5173` and Electron
opens it automatically.

Run all checks with:

```bash
./scripts/test.sh
```

The repository keeps backend, desktop UI, agent logic, documentation, tests,
and operational scripts isolated so each module can evolve independently.
