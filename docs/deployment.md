# Deployment Guide

## Scheduler (Scheduled Jobs)

All pipeline jobs run via APScheduler in a single Python process. No cloud functions required.

### Running the Scheduler
```bash
# Start the scheduler (runs jobs on cron schedule)
python -m src.scheduler

# Run all jobs once immediately (for testing or manual trigger)
python -m src.scheduler --once
```

### Schedule Overview
| Job                | Schedule             | Description                        |
|--------------------|----------------------|------------------------------------|
| discover_daily     | Daily at 06:00 UTC   | Etsy + Google Trends demand scan   |
| competitor_monitor | Daily at 07:00 UTC   | Competitor shop tracking           |
| analytics_collect  | Daily at 08:00 UTC   | Sales data collection              |
| discover_weekly    | Sunday at 02:00 UTC  | Full keyword expansion + scoring   |
| weekly_digest      | Monday at 09:00 UTC  | Weekly performance report          |

### Running as a Service
For production, run the scheduler as a systemd service or Docker container:

```bash
# systemd example (create /etc/systemd/system/templatemill-scheduler.service)
[Unit]
Description=TemplateMill Pipeline Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=templatemill
WorkingDirectory=/opt/templatemill
ExecStart=/opt/templatemill/.venv/bin/python -m src.scheduler
Restart=always
EnvironmentFile=/opt/templatemill/.env

[Install]
WantedBy=multi-user.target
```

```bash
# Or with Docker
docker run -d --env-file .env --name templatemill-scheduler templatemill python -m src.scheduler
```

## Database Setup
```bash
# Run migrations
alembic upgrade head

# Seed initial keywords
python scripts/seed_keywords.py
```

## Dashboard Deployment
The Flask dashboard can be deployed to any WSGI-compatible host:
```bash
# Development
flask --app src.dashboard.app run --debug

# Production (gunicorn)
gunicorn 'src.dashboard.app:create_app()' --bind 0.0.0.0:8000
```
