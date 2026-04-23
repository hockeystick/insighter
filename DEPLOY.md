# Deploying Insighter

Insighter is self-hostable. Two supported paths: **native** (recommended for
development and demos) and **Docker Compose** (recommended for judges or
reviewers who want one command).

## Native (Python 3.11+)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py loaddata taxonomy_seed
.venv/bin/python manage.py seed_demo_refs      # sponsors, specialists, tags
export ANTHROPIC_API_KEY=sk-ant-...             # for synthesis + mismatch
.venv/bin/python manage.py runserver
```

Then:
- `http://127.0.0.1:8000/taxonomy/` — public read-only taxonomy browser
- `http://127.0.0.1:8000/admin/` — add outlets, tag them, log in
- `http://127.0.0.1:8000/` — outlet tracker

## Docker Compose

Requires Docker Desktop (or equivalent).

```bash
export ANTHROPIC_API_KEY=sk-ant-...
docker compose up --build
```

On startup the container runs `migrate → loaddata taxonomy_seed →
seed_demo_refs → runserver 0.0.0.0:8000`. Database lives in the named
volume `insighter-db`; stopping and restarting the container preserves
state.

You still need a staff user to access the app. In another terminal:

```bash
docker compose exec web python manage.py createsuperuser
```

## Running tests

Native path only:

```bash
.venv/bin/python manage.py test
```

Tests never hit the Anthropic API — the synthesis flow is fully mocked.

## Security posture (v0.1)

- Staff-only, single-tenant. Django login is the full access story.
- No per-outlet permissions, no 2FA, no audit log beyond the append-only
  `CapabilityState` table.
- `DEBUG=1` is on in both local and Compose configurations — do not expose
  publicly. A v0.2 production deployment needs `DEBUG=0`, a real
  `SECRET_KEY` from env, `ALLOWED_HOSTS` tightening, and an HTTPS
  terminator.
- `ANTHROPIC_API_KEY` is read from the environment. Never commit it.

## Reloading the taxonomy from the xlsx

The taxonomy in git is a generated artefact. To regenerate from the desk
xlsx (which is gitignored):

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/build_taxonomy_fixture.py
.venv/bin/python manage.py shell -c "
from capabilities.models import Cluster, CapabilityItem, CapabilityState
CapabilityState.objects.all().delete()
CapabilityItem.objects.all().delete()
Cluster.objects.all().delete()
"
.venv/bin/python manage.py loaddata taxonomy_seed
```

The xlsx stays out of git (see `.gitignore`) because it's marked
INTERNAL / WIP at the desk.
