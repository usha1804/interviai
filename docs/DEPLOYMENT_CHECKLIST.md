**Production Deployment Checklist**

- **Secrets & env**: Create `backend/.env` from `backend/.env.production.example` and set values: `SECRET_KEY`, `GROQ_API_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `REDIS_URL`.
- **Database**: Provision MySQL instance and run migrations (or ensure schema exists). Backup plan for migrations.
- **Chroma persistence**: Decide on Chroma persistence directory or use managed/remote vector DB. If using local Chroma, mount a persistent volume accessible to the `web` service.
- **SSL / Domains**: Configure TLS for API and frontend domains (Let's Encrypt or provider). Update `CORS_ORIGINS`.
- **Email & OAuth**: Configure SMTP and any OAuth providers (Google) in env.
- **Run smoke tests**: Steps to verify after deploy:
  - Login via `/auth/login` (create test user if needed)
  - POST `/rag/upload-jd` with a JD and verify indexing
  - POST `/rag/generate-questions` and ensure questions returned
  - POST `/resume/upload` with sample resume and confirm DB record
  - POST `/resume/generate-questions` and `/resume/evaluate` for flow
- **Monitoring & logs**: Ship logs to a central system and enable health checks. Configure automatic restarts.
- **Backups**: Schedule DB backups and secure storage for Chroma persistence (if applicable).
- **Rate limits & secrets**: Protect LLM/Groq API keys; consider request throttling and billing alerts.
- **CI/CD**: Wire the provided `CI` workflow to build and run tests; add a deployment workflow to push images or trigger platform deploys.
- **Post-deploy checklist**: Run smoke tests, validate CORS, verify tokens, and check analytics events.

Minimal deploy commands (Docker Compose):

1. Build and start:

```
docker compose -f docker-compose.prod.yml up -d --build
```

2. View logs:

```
docker compose -f docker-compose.prod.yml logs -f web
```
