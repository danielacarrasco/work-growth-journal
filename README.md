# Work Mirror

A private leadership intelligence tool. Helps you profile stakeholders, log work interactions, detect political and workplace patterns, and reflect on your own leadership behaviour.

**The core question Work Mirror helps you answer:**
> What is happening in the system, what is happening in me, and what is the cleanest leadership move from here?

---

## What it is

- A private strategy notebook for leaders navigating complex work environments
- A structured log of interactions, stakeholders, and project dynamics
- A pattern detection tool grounded in your own data
- An AI-assisted meeting prep and reflection tool (optional)

## What it is not

- A therapy app — it does not provide clinical advice
- A productivity dashboard — no vanity metrics
- A team tool — single-user, local, private
- A calendar, Slack integration, or analytics platform

---

## Quick start

### 1. Clone and set up

```bash
cd work-growth-journal
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your values:

```env
OPENAI_API_KEY=sk-...       # Optional. Leave blank to run without AI.
AI_ENABLED=true             # Set to false to disable all AI features.
SECRET_KEY=your-secret-key  # Change this to something random.
```

### 3. Run

```bash
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

### 4. Load example data (optional)

On the home page, click **Load example data** to see the app with sample stakeholders, a project, and an interaction. Delete the examples when you're ready to start your own log.

---

## Setting the OpenAI API key

1. Get an API key at [platform.openai.com](https://platform.openai.com)
2. Add it to your `.env` file: `OPENAI_API_KEY=sk-...`
3. In Settings, confirm AI is enabled and select your preferred model (default: gpt-4o)

AI features include:
- Generate stakeholder profile updates from interaction logs
- Generate political weather reports for projects
- Generate self-pattern insights from recent interactions
- Generate full meeting prep briefs with advisor voices
- Ask the Advisor direct questions

---

## Disabling AI

Set `AI_ENABLED=false` in your `.env` file, or toggle it off in the Settings page.

When AI is disabled:
- All core features still work: logging, stakeholder profiles, projects, meeting prep
- AI buttons are hidden or show manual reflection prompts instead
- No data is sent to OpenAI
- Manual reflection prompts guide you through the same analysis process

---

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard (OPENAI_API_KEY, SECRET_KEY, AI_ENABLED)
6. The SQLite database will be stored on the Render disk — use a persistent disk for production

---

## Project structure

```
main.py           — FastAPI app, all routes
database.py       — SQLAlchemy engine and session
models.py         — Database models
crud.py           — Database operations
ai_service.py     — OpenAI integration (all AI calls go through here)
templates/        — Jinja2 HTML templates
static/styles.css — All styles
requirements.txt  — Python dependencies
.env.example      — Environment variable template
```

---

## Core concepts

**Stakeholder profiles** are behaviour-based, not judgmental. Describe what you observe: "requests detailed written updates before any verbal discussion" rather than "is controlling."

**Interaction logs** capture both what happened externally and how you showed up internally. The shrink/expand rating asks: did you take up more or less space than the situation required?

**Patterns** are always labelled as possible patterns with evidence from your logs. The app does not present AI interpretation as fact.

**Meeting prep** produces a full brief: system read, stakeholder read, your pattern risk, talking points, where to hold firm, where to stay flexible, and the recommended next action.

**Advisor voices** bring different perspectives to the same situation. Use the Strategist for political reads, the Reflector for self-awareness, the Operator for execution clarity, and the No-Bullshit Friend when you need the direct version.

---

## Privacy

All data is stored locally in `work_mirror.db` (SQLite). Nothing leaves your machine unless AI is enabled, in which case interaction content is sent to OpenAI for analysis. Export your data at any time from Settings → Export data.
