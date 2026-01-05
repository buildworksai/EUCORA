# Mobile Packaging Standards

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Control Plane coordinates ABM/ADE + Android Enterprise packaging with deterministic rollback, caching, and evidence.
**Design Principle**: "Control Plane enforces policy/intent; MDM platforms execute apps with evidence and correlation IDs."

## Apple (iOS/iPadOS)
- Device enrollment via ABM + ADE; application licenses managed through VPP assignments (Intune primary).
- LOB apps distributed as signed IPAs; Control Plane stores `ipa_sha256`, `bundle_id`, `version`.
- Rollback: retain prior versions for **90 days** (or two latest releases); reassign previous version to smart group for rollback if still available.
- Offline behavior: caching only for corporate-owned devices; BYOD must check in at least every 7 days to maintain compliance.

## Android
- Enterprise apps published via Managed Google Play; Zero-touch for corporate-owned devices.
- Private APKs versioned; connectors track `track_id` and `version_code`. Rollback uses track management or targeted removal + reassign previous version.
- Offline constraint: devices may cache packages but require periodic connectivity (≤7 days) to refresh compliance.

## Evidence & Detection
- Evidence pack fields: `ipa_hash`, `apk_hash`, `vpp_assignment_id`, `track_id`, `rollback_plan`, `scan_report_id`.
- Detection logic: Intune checks `package_bundle_id`/`package_name` combos, verifying installed versions match desired ring.

## Rollback Strategies
- Public store apps: rollback via assignment/remove (downgrade not supported); evidence pack notes `public_store=true` and fallback plan.
- LOB apps: maintain release catalog; connectors fail if prior version unavailable (policy_violation) and require CAB-approved exception.
- Android private apps: use Managed Google Play versioning; rollover by updating track with `version_code` and verifying via `playdeveloperreport.googleapis.com`.

## Monitoring & Validation
- Telemetry tracks success rate per ring (target thresholds from ring model doc) and time-to-compliance per device class.
- Compliance check script `python scripts/mobile/check_compliance.py --platform ios` ensures devices report assigned version within 24h of deployment.

## Related Documentation
- [Architecture Overview v1.2](../../architecture/architecture-overview.md)
- [CAB Workflow](../cab-workflow.md)
- [Evidence Pack Rules](../../../.agents/rules/10-evidence-pack-rules.md)

---

**Mobile Packaging Standards v1.0 — Design**
