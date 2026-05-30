# TalentHive

TalentHive is an AI-enhanced Telegram job board designed for recruiters, employers, and job seekers. It provides a conversational experience for posting jobs, managing applications, and discovering candidate profiles from within Telegram.

## Key Features

- Recruiter and employer workflows for posting and managing job listings
- Applicant workflows for browsing jobs, applying, and maintaining profiles
- Admin support for oversight and moderation
- Async database support with SQLAlchemy and Alembic migrations
- Redis cache integration for scalable performance
- Optional FastAPI dashboard support for web-based monitoring and management
- AI and NLP-ready dependencies for resume, job matching, and conversational extensions

## Architecture

The repository is organized into modular components:

- `applicants/` - applicant-facing handlers, states, and API logic
- `employers/` - employer-facing handlers, onboarding, and job management
- `modules/` - domain-specific services for admin, applicant, and employer flows
- `core/` - shared configuration, database session management, dependency injection, and event publishing
- `alembic/` - migrations for PostgreSQL schema management
- `tests/` - test coverage for core bot functionality

## Requirements

- Python 3.10+ (recommended)
- PostgreSQL for production data storage
- Redis for optional caching and queueing
- Telegram Bot API tokens for each bot role

Dependencies are listed in `requirements.txt` and include:

- `python-telegram-bot`
- `sqlalchemy[asyncio]`, `asyncpg`, `alembic`
- `redis`, `pydantic`, `dependency-injector`
- `openai`, `transformers`, `torch`, `sentencepiece`
- `fastapi`, `uvicorn`, `jinja2` for optional web dashboard

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/miketorreno/TalentHive.git
   cd TalentHive
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   ```env
   cp .env.example .env
   ```

4. Apply database migrations:
   ```bash
   alembic upgrade head
   ```

## Running the Bot

There are multiple entry points depending on the role you want to run.

- Applicant bot:
  ```bash
  python applicant.py
  ```
- Employer bot:
  ```bash
  python employer.py
  ```
- Core bot / shared Telegram flow:
  ```bash
  python bot.py
  ```

If you are using the modular package layout, run the relevant entrypoint in `applicants/`, `employers/`, or `modules/` as needed.

## Optional Web Dashboard

If you want to enable the optional dashboard, install the optional dependencies and start a FastAPI server:

```bash
uvicorn root.bot.main:app --reload
```

## Testing

Run the test suite with:

```bash
pytest
```

## Contributing

Contributions are welcome. Please follow standard Git workflows:

1. Create a feature branch.
2. Add tests for new functionality.
3. Open a pull request with a clear summary and description.

## Notes

- Use `core/config/settings.py` to centralize environment configuration.
- The repository supports both legacy scripts and a newer modular service architecture.
- `alembic/` keeps database schema changes versioned and repeatable.

---

## License

This project does not currently specify a license. Add a `LICENSE` file if you want to publish or share the code publicly.
