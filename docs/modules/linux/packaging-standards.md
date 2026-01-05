# Linux Packaging Standards

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Linux packaging relies on signed APT repos, drift policy, and Ansible/Landscape enforcement.
**Design Principle**: "Control Plane orchestrates; Landscape/Ansible enforce packages via deterministic repo and drift policies."

## Repository & Signing
- APT repo signed with GPG keys stored in Azure Key Vault + offline copy for air-gapped sites.
- Repository layout: `dists/<suite>/<component>/binary-amd64/` with `Release` file containing `SHA256` hashes.
- Signature command: `gpg --default-key repo-key --output Release.gpg --detach-sign Release`.

## Mirror Management
- Site-local mirrors sync via `rsync --checksum` with `hash-verification` step; script records `correlation_id` & `mirror_uri`.
- Offline mirrors imported via secure media, hash verified with `sha256sum -c manifest.sha256` before ingestion.
- Mirror sync schedule tagged to site class: Online (every 1h), Intermittent (every 6h), Air-gapped (per transfer window).

## Drift Policy
- Phase 2 (detect-only): Landscape inventory scans compare installed versions vs desired; drift events logged (`error_class=policy_violation` if unauthorized change).
- Phase 3 (enforce): Ansible/Landscape run remediation playbooks; connectors reapply desired packages and log remediation events.

## Validation & Evidence
- Validation script: `apt-ftparchive release . | tee Release` ensures metadata complete; `python scripts/validate_repo.py --repo ./repo --hashes Release.sha256` verifies all packages.
- Evidence pack includes `repo_version`, `manifest_hash`, `drift_event_count`, `remediation_status` (if Phase 3 enforcement).

## Retention & Rollback
- Retain releases for 90 days or last 3 versions; rollback uses `apt pin` to revert to previous version recorded in evidence pack.
- Rollback plan documents `pin_priority`, `release_file`, and `Ansible playbook` for reversion.

## Related Documentation
- [Architecture Overview v1.2](../../architecture/architecture-overview.md)
- [Execution Plane Connectors](../../architecture/execution-plane-connectors.md)
- [Hybrid Distribution](../infrastructure/site-classification.md)

---

**Linux Packaging Standards v1.0 — Design**
