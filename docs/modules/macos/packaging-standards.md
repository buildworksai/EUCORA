# macOS Packaging Standards

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Mac packaging adheres to notarization, signature, and evidence controls so the Control Plane can orchestrate Intune/Jamf deployments.
**Design Principle**: "Control Plane dictates policy; packaging produces signed PKGs with notarization artifacts ready for Intune+Jamf execution."

## Artifact Requirements
- Packages must be `.pkg` (flat) signed with Developer ID Installer certificate and notarized. Evidence pack includes notarization ticket ID + log.
- Manifest includes detection rules (pkgutil receipt, key files) and uninstall script (if any).
- Intune primary; Jamf secondary. Secondary artifacts require Jamf-specific distribution point metadata with DP IDs.

## Notarization & Signing
- `xcrun altool --notarize-app -f App.pkg --primary-bundle-id com.corp.app -u <appl-email> -p <app-specific-password>` used for notarization.
- Notarization status polled via `xcrun altool --notarization-info <requestUUID>` until success or failure (error_code identifies issues, e.g., 165, 142).
- Evidence pack includes `notarization_request_id`, `status`, `log_url`, and timestamp.

## Deployment Controls
- Intune deployment uses `.intunewin` wrapper or `PKG` rights; detection via `pkgutil --pkgs=com.corp.app`.
- Jamf connectors reference `policy_id` and `smart_group_id`; Intune uses `intune.package.id` assignment.
- Offline-constrained macOS sites rely on Jamf DPs; Control Plane ensures DP `site_scope` matches device tags.

## Validation & Audit
- Validation script: `shasum -a 256 App.pkg` verifying SHA-256 matches manifest hash.
- Evidence pack includes test install/uninstall logs (Ring 0 success rate target ≥98%).
- Log entry example: `{"correlation_id":"dp-20260104-00M1","status":"notarized","error_code":0}`.

## Retention
- Retain notarized builds for **90 days** or last **2 releases**; evidence pack references old versions for rollback.
- Unused notarization tickets pruned weekly by `scripts/notarization/prune.py`.

## Related Documentation
- [Architecture Overview v1.2](../../architecture/architecture-overview.md)
- [CAB Workflow](../cab-workflow.md)
- [Execution Plane Connectors](../../architecture/execution-plane-connectors.md)

---

**macOS Packaging Standards v1.0 — Design**
