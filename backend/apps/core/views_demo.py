# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin demo data endpoints.
"""
from django.conf import settings
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from apps.core.demo_data import clear_demo_data, demo_data_stats, seed_demo_data
from apps.core.utils import get_demo_mode_enabled, set_demo_mode_enabled

# In development, allow any user (including unauthenticated) to access demo data endpoints
# In production, require IsAdminUser
DEMO_DATA_PERMISSION = AllowAny if settings.DEBUG else IsAdminUser

# In development, exempt CSRF for these API views to allow mock auth
# DRF's @api_view handles CSRF, but SessionAuthentication still enforces it
# This exemption allows unauthenticated requests in development
if settings.DEBUG:
    # Apply csrf_exempt to all views in development
    def exempt_csrf(view_func):
        return csrf_exempt(view_func)

else:

    def exempt_csrf(view_func):
        return view_func


@exempt_csrf
@api_view(["GET"])
@permission_classes([DEMO_DATA_PERMISSION])
def demo_data_stats_view(request):
    """
    Get demo data stats.

    GET /api/v1/admin/demo-data-stats
    """
    try:
        return Response(
            {
                "counts": demo_data_stats(),
                "demo_mode_enabled": get_demo_mode_enabled(),
            }
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exempt_csrf
@api_view(["POST"])
@permission_classes([DEMO_DATA_PERMISSION])
def seed_demo_data_view(request):
    """
    Seed demo data - attempts to restore from backup first, falls back to seeding.

    POST /api/v1/admin/seed-demo-data

    Strategy:
    1. If backup file exists, restore from backup (fast, ~2-5 seconds)
    2. Otherwise, seed data using the seeding function (slower, ~30-60 seconds)

    Query params:
    - use_backup: If True, only restore from backup (fails if backup doesn't exist)
    - force_seed: If True, skip backup and force seeding
    """
    import logging
    import os
    import subprocess
    from pathlib import Path

    logger = logging.getLogger(__name__)

    try:
        payload = request.data or {}
        use_backup_only = payload.get("use_backup", False)  # Default to FALSE - use form parameters
        force_seed = payload.get("force_seed", False)

        if isinstance(use_backup_only, str):
            use_backup_only = use_backup_only.lower() in ["true", "1", "yes"]
        if isinstance(force_seed, str):
            force_seed = force_seed.lower() in ["true", "1", "yes"]

        # Extract form parameters
        assets = int(payload.get("assets", 0))
        applications = int(payload.get("applications", 0))
        deployments = int(payload.get("deployments", 0))
        users = int(payload.get("users", 0))
        events = int(payload.get("events", 0))

        # CRITICAL: If user provided form parameters, ALWAYS use seeding (not restore)
        # This ensures user's requested counts (e.g., 50,000 assets) are respected
        has_form_parameters = assets > 0 or applications > 0 or deployments > 0 or users > 0 or events > 0

        # Check for backup file
        # Try multiple paths: container path, relative path, and host path
        backup_file = None
        possible_paths = [
            Path("/app/data/demo_db_backup.sql.gz"),  # Container path
            Path(__file__).parent.parent.parent / "data" / "demo_db_backup.sql.gz",  # Relative to backend/
            Path("/app/backend/data/demo_db_backup.sql.gz"),  # Alternative container path
        ]

        for path in possible_paths:
            if path.exists():
                backup_file = path
                logger.info(f"Found backup file at: {backup_file}")
                break

        if not backup_file:
            logger.warning("Backup file not found in any expected location")

        # Try to restore from backup ONLY if:
        # 1. User explicitly requested backup (use_backup_only=True)
        # 2. AND no form parameters provided (has_form_parameters=False)
        # 3. AND not forced to seed
        # Otherwise, use seeding with form parameters
        if not force_seed and not has_form_parameters and backup_file and backup_file.exists() and use_backup_only:
            logger.info(f"Restoring demo data from backup: {backup_file}")

            try:
                # CRITICAL: Clear existing demo data FIRST before restoring
                # This prevents foreign key constraint violations and duplicate key errors
                logger.info("Clearing existing demo data before restore...")
                from django.contrib.auth.models import User
                from django.db import transaction

                from apps.core.demo_data import clear_demo_data

                # Clear demo data
                clear_demo_data()

                # Also clear demo users (but keep system users like devadmin)
                with transaction.atomic():
                    User.objects.filter(username__startswith="demo").delete()
                    # Also delete the 'demo' user if it exists
                    User.objects.filter(username="demo").delete()

                logger.info("Demo data and demo users cleared successfully")

                # Use psql directly via subprocess to restore
                # We can't use docker exec from inside container, so use psql via connection string
                import os
                import subprocess

                from django.conf import settings

                logger.info(f"Restoring backup using psql: {backup_file}")

                # Get database connection details from Django settings
                db_settings = settings.DATABASES["default"]
                db_user = db_settings["USER"]
                db_name = db_settings["NAME"]
                db_host = db_settings["HOST"]
                db_port = db_settings.get("PORT", "5432")
                db_password = db_settings.get("PASSWORD", "")

                # Set PGPASSWORD environment variable for psql
                env = os.environ.copy()
                if db_password:
                    env["PGPASSWORD"] = db_password

                # Create a temporary SQL script that handles conflicts properly
                # We need to filter out non-demo users and handle foreign key constraints
                import gzip
                import re
                import tempfile

                # Read the backup file
                if backup_file.suffix == ".gz":
                    with gzip.open(backup_file, "rt", encoding="utf-8") as f:
                        sql_content = f.read()
                else:
                    sql_content = backup_file.read_text(encoding="utf-8")

                # Process the SQL to handle conflicts
                # 1. Filter out user ID 1 (devadmin) from auth_user COPY
                # 2. Wrap in transaction with proper error handling
                processed_lines = []
                skip_user_line = False
                in_auth_user_copy = False

                for line in sql_content.split("\n"):
                    # Detect auth_user COPY block
                    if "COPY public.auth_user" in line:
                        in_auth_user_copy = True
                        processed_lines.append(line)
                        continue

                    # End of COPY block
                    if line.strip() == "\\." and in_auth_user_copy:
                        in_auth_user_copy = False
                        processed_lines.append(line)
                        continue

                    # Skip user ID 1 (devadmin) in auth_user COPY
                    if in_auth_user_copy and line.strip() and not line.strip().startswith("--"):
                        # Check if this is user ID 1 (starts with "1\t")
                        if re.match(r"^1\t", line):
                            logger.info("Skipping non-demo user (devadmin, ID=1) from restore")
                            continue

                    processed_lines.append(line)

                processed_sql = "\n".join(processed_lines)

                # Don't wrap in transaction - let each COPY succeed/fail independently
                # This way errors in one table don't abort the entire restore
                # Use ON_ERROR_STOP=0 in psql to continue on errors
                wrapped_sql = f"""
-- Temporarily disable triggers (helps with some constraints)
SET session_replication_role = 'replica';

{processed_sql}

-- Re-enable triggers
SET session_replication_role = 'origin';
"""

                # Write to temporary file
                with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8") as tmp_file:
                    tmp_file.write(wrapped_sql)
                    tmp_sql_file = tmp_file.name

                try:
                    # Restore using psql with error handling
                    # Use ON_ERROR_STOP=0 to continue on errors (for duplicate keys, etc.)
                    result = subprocess.run(
                        [
                            "psql",
                            "-h",
                            db_host,
                            "-p",
                            str(db_port),
                            "-U",
                            db_user,
                            "-d",
                            db_name,
                            "-v",
                            "ON_ERROR_STOP=0",
                            "-f",
                            tmp_sql_file,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        env=env,
                    )
                    returncode = result.returncode
                    stdout = result.stdout
                    stderr = result.stderr
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_sql_file)
                    except OSError as cleanup_error:
                        logger.warning(f"Failed to delete temporary SQL file {tmp_sql_file}: {cleanup_error}")

                # Log the output for debugging
                stdout_str = stdout.decode("utf-8") if isinstance(stdout, bytes) else stdout
                stderr_str = stderr.decode("utf-8") if isinstance(stderr, bytes) else stderr

                if returncode != 0:
                    # Log full error for debugging
                    logger.error(f"Restore psql return code: {returncode}")
                    logger.error(f"Restore stderr: {stderr_str[:1000]}")
                    logger.error(f"Restore stdout: {stdout_str[:500]}")

                    # Check if it's just warnings (like "relation already exists" or "duplicate key")
                    if "ERROR" in stderr_str.upper():
                        # Check for specific errors we can ignore
                        ignorable_errors = ["relation", "duplicate", "already exists", "does not exist"]
                        if any(err in stderr_str.lower() for err in ignorable_errors):
                            logger.warning(f"Restore completed with ignorable errors: {stderr_str[:500]}")
                        else:
                            logger.error(f"Restore failed with critical errors: {stderr_str[:1000]}")
                            raise Exception(f"Database restore failed: {stderr_str[:1000]}")
                    else:
                        logger.info(f"Restore completed with warnings: {stderr_str[:500]}")
                else:
                    logger.info(f"Restore completed successfully")
                    if stderr_str:
                        logger.info(f"Restore warnings: {stderr_str[:500]}")

                # Enable demo mode
                set_demo_mode_enabled(True)

                # Get stats
                stats = demo_data_stats()

                logger.info(f"Demo data restored successfully from backup: {stats}")
                return Response(
                    {
                        "status": "success",
                        "counts": stats,
                        "message": "Demo data restored from backup successfully",
                        "method": "backup_restore",
                    },
                    status=status.HTTP_200_OK,
                )

            except subprocess.TimeoutExpired:
                logger.error("Backup restore timed out")
                raise Exception("Backup restore timed out after 60 seconds")
            except subprocess.CalledProcessError as e:
                logger.error(f'Backup restore process failed: {e.stderr if hasattr(e, "stderr") else str(e)}')
                raise Exception(f'Backup restore failed: {e.stderr if hasattr(e, "stderr") else str(e)}')
            except Exception as e:
                logger.warning(f"Failed to restore from backup: {e}, falling back to seeding", exc_info=True)
                # Fall through to seeding

        # Fallback to seeding if backup restore failed or not available
        # OR if user provided form parameters (which takes priority)
        if force_seed or has_form_parameters or not (use_backup_only and backup_file and backup_file.exists()):
            logger.info(
                f"Seeding demo data using seeding function with parameters: assets={assets}, applications={applications}, deployments={deployments}, users={users}, events={events}..."
            )

            from apps.core.tasks import seed_demo_data_task

            clear_existing = payload.get("clear_existing", True)  # Default to clearing when using seed
            if isinstance(clear_existing, str):
                clear_existing = clear_existing.lower() in ["true", "1", "yes"]

            # Use form parameters if provided, otherwise use defaults
            assets = int(payload.get("assets", 100)) if assets == 0 else assets
            applications = int(payload.get("applications", 20)) if applications == 0 else applications
            deployments = int(payload.get("deployments", 50)) if deployments == 0 else deployments
            users = int(payload.get("users", 10)) if users == 0 else users
            events = int(payload.get("events", 200)) if events == 0 else events
            batch_size = int(payload.get("batch_size", 50))

            # For small datasets, run synchronously for immediate feedback
            # For large datasets, run asynchronously to avoid timeouts
            total_items = assets + applications + deployments + events
            use_async = total_items > 5000

            if use_async:
                logger.info(
                    f"Queueing async demo data seed task: assets={assets}, applications={applications}, "
                    f"deployments={deployments}, users={users}, events={events}, clear_existing={clear_existing}"
                )

                # Queue the task
                task = seed_demo_data_task.delay(
                    assets=assets,
                    applications=applications,
                    deployments=deployments,
                    users=users,
                    events=events,
                    clear_existing=bool(clear_existing),
                    batch_size=batch_size,
                )

                return Response(
                    {
                        "status": "queued",
                        "message": "Demo data seeding started in background. Check demo-data-stats endpoint for progress.",
                        "task_id": str(task.id),
                        "method": "async_seed",
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
            else:
                # Run synchronously for small datasets
                logger.info(
                    f"Starting synchronous demo data seed: assets={assets}, applications={applications}, "
                    f"deployments={deployments}, users={users}, events={events}, clear_existing={clear_existing}"
                )

                results = seed_demo_data(
                    assets=assets,
                    applications=applications,
                    deployments=deployments,
                    users=users,
                    events=events,
                    clear_existing=bool(clear_existing),
                    batch_size=batch_size,
                )

                logger.info(f"Demo data seed completed successfully: {results}")
                return Response(
                    {
                        "status": "success",
                        "counts": results,
                        "message": "Demo data seeded successfully",
                        "method": "sync_seed",
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            # Backup doesn't exist and use_backup_only is True
            return Response(
                {
                    "status": "error",
                    "error": "Backup file not found and use_backup_only is True. Set force_seed=true to seed instead.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

    except Exception as e:
        logger.error(f"Error seeding demo data: {e}", exc_info=True)
        return Response({"status": "error", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exempt_csrf
@api_view(["DELETE"])
@permission_classes([DEMO_DATA_PERMISSION])
def clear_demo_data_view(request):
    """
    Clear demo data only.

    DELETE /api/v1/admin/clear-demo-data
    """
    results = clear_demo_data()
    return Response({"status": "success", "counts": results}, status=status.HTTP_200_OK)


@exempt_csrf
@api_view(["GET", "POST"])
@permission_classes([DEMO_DATA_PERMISSION])
def demo_mode_view(request):
    """
    Get or set demo mode.

    GET /api/v1/admin/demo-mode
    POST /api/v1/admin/demo-mode { "enabled": true }
    """
    try:
        if request.method == "POST":
            enabled = request.data.get("enabled", False)
            if isinstance(enabled, str):
                enabled = enabled.lower() in ["true", "1", "yes"]
            current = set_demo_mode_enabled(enabled)
            return Response({"demo_mode_enabled": current})

        return Response({"demo_mode_enabled": get_demo_mode_enabled()})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exempt_csrf
@api_view(["GET"])
@permission_classes([DEMO_DATA_PERMISSION])
def csrf_token_view(request):
    """
    Get CSRF token for frontend requests.

    GET /api/v1/admin/csrf-token
    """
    token = get_token(request)
    return Response({"csrf_token": token})
