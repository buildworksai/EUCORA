# Quick Commands Reference

Common commands for sprint execution.

---

## Django Backend

### App Management

```bash
# Create new app
cd backend
python manage.py startapp {app_name}
mv {app_name} apps/

# Create migrations
python manage.py makemigrations {app_name}

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Testing

```bash
# Run all tests with coverage
cd backend
pytest --cov=apps --cov-report=term-missing

# Run with coverage threshold
pytest --cov=apps --cov-fail-under=90

# Run specific app tests
pytest apps/{app_name}/tests/

# Run with verbose output
pytest -v apps/{app_name}/tests/

# Run specific test file
pytest apps/{app_name}/tests/test_api.py

# Run specific test class
pytest apps/{app_name}/tests/test_api.py::TestYourModelAPI

# Run specific test
pytest apps/{app_name}/tests/test_api.py::TestYourModelAPI::test_list_models
```

### Type Checking

```bash
# Run mypy on all apps
cd backend
mypy apps/

# Run mypy on specific app
mypy apps/{app_name}/
```

### Linting

```bash
# Run flake8
cd backend
flake8 apps/

# Run black (check only)
black --check apps/

# Run black (format)
black apps/

# Run isort (check only)
isort --check-only apps/

# Run isort (format)
isort apps/
```

---

## React Frontend

### Development

```bash
# Start development server
cd frontend
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Type Checking

```bash
# Full TypeScript check
cd frontend
npx tsc --noEmit

# Check specific file
npx tsc --noEmit src/routes/{file}.tsx

# Watch mode
npx tsc --noEmit --watch
```

### Linting

```bash
# Run ESLint
cd frontend
npm run lint

# Run ESLint with auto-fix
npm run lint -- --fix

# Check specific file
npx eslint src/routes/{file}.tsx

# Check with zero warnings
npx eslint src/ --max-warnings 0
```

### Testing

```bash
# Run tests
cd frontend
npm run test

# Run tests with coverage
npm run test -- --coverage

# Run specific test file
npm run test -- src/components/{Component}.test.tsx

# Watch mode
npm run test -- --watch
```

---

## Git Commands

### Status and Diff

```bash
# Check status
git status

# Show diff
git diff

# Show staged diff
git diff --staged

# Show untracked files
git ls-files --others --exclude-standard
```

### Committing

```bash
# Add all changes
git add .

# Add specific file
git add path/to/file

# Commit with message (HEREDOC format per CLAUDE.md)
git commit -m "$(cat <<'EOF'
feat(rbac): implement comprehensive RBAC system

Add 9 personas with granular permissions and scope-based isolation.
EOF
)"

# Amend last commit (ONLY if not pushed, per CLAUDE.md)
git commit --amend -m "$(cat <<'EOF'
Updated commit message
EOF
)"
```

### Branching

```bash
# Create and switch to new branch
git checkout -b feature/{enhancement-name}

# Switch branches
git checkout {branch-name}

# Delete branch
git branch -d {branch-name}
```

---

## Pre-Commit

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run {hook-id} --all-files

# Skip hooks (FORBIDDEN per CLAUDE.md, for emergency only)
# git commit --no-verify
```

---

## Celery (Background Tasks)

```bash
# Start Celery worker
cd backend
celery -A config worker -l info

# Start Celery beat (scheduler)
celery -A config beat -l info

# Start both (development)
celery -A config worker -B -l info
```

---

## Docker

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Run command in container
docker-compose exec backend python manage.py migrate
```

---

## Database

### PostgreSQL

```bash
# Connect to database
psql -h localhost -U postgres -d eucora

# Enable pgvector extension
psql -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Backup database
pg_dump -h localhost -U postgres eucora > backup.sql

# Restore database
psql -h localhost -U postgres eucora < backup.sql
```

### Django Shell

```bash
# Open Django shell
cd backend
python manage.py shell

# Shell with IPython
python manage.py shell_plus
```

---

## Quality Gate Checks (Run Before Commit)

```bash
# Full quality check
cd backend && pytest --cov=apps --cov-fail-under=90 && \
cd ../frontend && npm run build && npm run lint && \
echo "✅ All quality gates passed"
```

---

## Tracker Update Commands

After completing work, update the tracker:

```bash
# Open tracker in editor
code docs/planning/PHASE-2-ENHANCEMENT-TRACKER.md

# Alternatively, use sed for status update (example)
# Update enhancement status from "Not Started" to "In Progress"
# Manually edit the file to update:
# - Task checkboxes: ⬜ → ✅
# - Status: 🔵 → 🟡 → 🟢
# - Progress percentage
# - Update history table
```
