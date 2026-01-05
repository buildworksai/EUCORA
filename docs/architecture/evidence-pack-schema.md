# Evidence Pack Schema

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-04

---

## Overview

Evidence packs are **immutable, versioned documents** that contain all required evidence for CAB approval decisions. Every high-risk (`Risk > 50`) or privileged deployment MUST have a complete evidence pack before CAB submission.

**Design Principle**: Evidence-first governance — CAB decisions include standardized evidence packs with no missing fields.

---

## Evidence Pack Requirements (Mandatory Fields)

At minimum, every CAB submission includes:

1. **Artifact hashes + signatures** (SHA-256, signing metadata, certificate details)
2. **SBOM + scan report + policy decision** (SPDX/CycloneDX, vulnerability scan results, pass/fail/exception)
3. **Install/uninstall/detection documentation** (silent install commands, detection rules, exit codes)
4. **Rollout plan** (rings, schedule, targeting, exclusions, promotion gates)
5. **Rollback plan** (plane-specific strategy, validation evidence)
6. **Test evidence** (lab + Ring 0 results, success rates, failure analysis)
7. **Exception record(s)** (if any, with expiry dates and compensating controls)

**Enforcement**: CAB submission is **blocked** if any required field is missing or incomplete.

---

## Evidence Pack Schema (JSON)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": [
    "evidence_pack_id",
    "version",
    "created_at",
    "created_by",
    "deployment_intent_id",
    "application",
    "artifact",
    "sbom",
    "vulnerability_scan",
    "installation",
    "rollout_plan",
    "rollback_plan",
    "test_evidence",
    "risk_assessment",
    "exceptions"
  ],
  "properties": {
    "evidence_pack_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this evidence pack"
    },
    "version": {
      "type": "string",
      "pattern": "^v\\d+\\.\\d+$",
      "description": "Evidence pack schema version (e.g., v1.0)"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Evidence pack creation timestamp (ISO 8601)"
    },
    "created_by": {
      "type": "string",
      "format": "email",
      "description": "Packaging Engineer who created this evidence pack"
    },
    "deployment_intent_id": {
      "type": "string",
      "format": "uuid",
      "description": "Associated deployment intent ID"
    },
    "application": {
      "type": "object",
      "required": ["id", "name", "version", "vendor", "category", "support_tier"],
      "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+"},
        "vendor": {"type": "string"},
        "category": {"type": "string", "enum": ["productivity", "security", "lob", "development", "infrastructure"]},
        "support_tier": {"type": "string", "enum": ["tier_1_critical", "tier_2_standard", "tier_3_community"]},
        "licensing_model": {"type": "string", "enum": ["per_device", "per_user", "site_license", "free"]},
        "documentation_url": {"type": "string", "format": "uri"}
      }
    },
    "artifact": {
      "type": "object",
      "required": ["artifact_id", "hash", "size_bytes", "signing", "provenance"],
      "properties": {
        "artifact_id": {"type": "string", "format": "uuid"},
        "hash": {
          "type": "object",
          "required": ["algorithm", "value"],
          "properties": {
            "algorithm": {"type": "string", "enum": ["sha256", "sha512"]},
            "value": {"type": "string", "pattern": "^[a-f0-9]{64,128}$"}
          }
        },
        "size_bytes": {"type": "integer", "minimum": 0},
        "signing": {
          "type": "object",
          "required": ["signed", "certificate_thumbprint", "signing_time"],
          "properties": {
            "signed": {"type": "boolean"},
            "certificate_thumbprint": {"type": "string"},
            "signing_time": {"type": "string", "format": "date-time"},
            "certificate_subject": {"type": "string"},
            "certificate_issuer": {"type": "string"},
            "certificate_expiry": {"type": "string", "format": "date-time"},
            "notarization": {
              "type": "object",
              "description": "macOS notarization details (if applicable)",
              "properties": {
                "notarized": {"type": "boolean"},
                "ticket_id": {"type": "string"},
                "notarization_date": {"type": "string", "format": "date-time"}
              }
            }
          }
        },
        "provenance": {
          "type": "object",
          "required": ["builder_identity", "pipeline_run_id", "build_time", "source_repo"],
          "properties": {
            "builder_identity": {"type": "string"},
            "pipeline_run_id": {"type": "string"},
            "build_time": {"type": "string", "format": "date-time"},
            "source_repo": {"type": "string", "format": "uri"},
            "source_commit": {"type": "string"},
            "build_inputs": {"type": "array", "items": {"type": "string"}}
          }
        }
      }
    },
    "sbom": {
      "type": "object",
      "required": ["format", "sbom_url", "component_count"],
      "properties": {
        "format": {"type": "string", "enum": ["SPDX", "CycloneDX"]},
        "sbom_url": {"type": "string", "format": "uri", "description": "URL to SBOM file in artifact store"},
        "component_count": {"type": "integer", "minimum": 0},
        "license_summary": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "license": {"type": "string"},
              "component_count": {"type": "integer"}
            }
          }
        }
      }
    },
    "vulnerability_scan": {
      "type": "object",
      "required": ["scanner", "scan_time", "policy_decision", "findings"],
      "properties": {
        "scanner": {"type": "string", "enum": ["Trivy", "Grype", "Snyk", "enterprise_scanner"]},
        "scan_time": {"type": "string", "format": "date-time"},
        "policy_decision": {"type": "string", "enum": ["pass", "fail", "exception_granted"]},
        "findings": {
          "type": "object",
          "properties": {
            "critical": {"type": "integer", "minimum": 0},
            "high": {"type": "integer", "minimum": 0},
            "medium": {"type": "integer", "minimum": 0},
            "low": {"type": "integer", "minimum": 0}
          }
        },
        "scan_report_url": {"type": "string", "format": "uri", "description": "URL to full scan report"},
        "malware_scan": {
          "type": "object",
          "properties": {
            "scanner": {"type": "string"},
            "scan_time": {"type": "string", "format": "date-time"},
            "result": {"type": "string", "enum": ["clean", "detected", "error"]},
            "details": {"type": "string"}
          }
        }
      }
    },
    "installation": {
      "type": "object",
      "required": ["install_command", "uninstall_command", "detection_rules", "reboot_required"],
      "properties": {
        "install_command": {"type": "string", "description": "Silent install command (no UI)"},
        "uninstall_command": {"type": "string", "description": "Silent uninstall command"},
        "detection_rules": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type", "value"],
            "properties": {
              "type": {"type": "string", "enum": ["file", "registry", "productcode", "script"]},
              "value": {"type": "string"},
              "expected_result": {"type": "string"}
            }
          }
        },
        "reboot_required": {"type": "boolean"},
        "install_time_minutes": {"type": "integer", "minimum": 0},
        "exit_code_mapping": {
          "type": "object",
          "description": "Exit code to result mapping",
          "patternProperties": {
            "^\\d+$": {"type": "string", "enum": ["success", "success_reboot", "failure", "retry"]}
          }
        },
        "dependencies": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "version": {"type": "string"},
              "required": {"type": "boolean"}
            }
          }
        }
      }
    },
    "rollout_plan": {
      "type": "object",
      "required": ["rings", "schedule", "targeting", "promotion_gates"],
      "properties": {
        "rings": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["ring_id", "ring_name", "target_device_count"],
            "properties": {
              "ring_id": {"type": "string"},
              "ring_name": {"type": "string", "enum": ["ring-0-lab", "ring-1-canary", "ring-2-pilot", "ring-3-department", "ring-4-global"]},
              "target_device_count": {"type": "integer", "minimum": 0},
              "target_groups": {"type": "array", "items": {"type": "string"}},
              "exclusions": {"type": "array", "items": {"type": "string"}}
            }
          }
        },
        "schedule": {
          "type": "object",
          "description": "Start time and duration per ring",
          "patternProperties": {
            "^ring-\\d+-.*$": {
              "type": "object",
              "properties": {
                "start": {"type": "string", "format": "date-time"},
                "duration_hours": {"type": "integer", "minimum": 0}
              }
            }
          }
        },
        "targeting": {
          "type": "object",
          "properties": {
            "acquisition_boundary": {"type": "string"},
            "business_unit": {"type": "string"},
            "site_class": {"type": "string", "enum": ["online", "intermittent", "air_gapped"]}
          }
        },
        "promotion_gates": {
          "type": "object",
          "properties": {
            "success_rate_threshold": {"type": "number", "minimum": 0, "maximum": 1},
            "time_to_compliance_hours": {"type": "integer", "minimum": 0},
            "max_incidents": {"type": "integer", "minimum": 0}
          }
        }
      }
    },
    "rollback_plan": {
      "type": "object",
      "required": ["strategy", "rollback_version", "validated", "validation_date"],
      "properties": {
        "strategy": {"type": "string", "enum": ["intune_supersedence", "jamf_version_pinning", "sccm_rollback_package", "apt_pinning", "assignment_remove"]},
        "rollback_version": {"type": "string", "description": "Version to rollback to"},
        "validated": {"type": "boolean", "description": "Rollback strategy tested and validated"},
        "validation_date": {"type": "string", "format": "date-time"},
        "validation_evidence": {"type": "string", "description": "URL to validation test results"},
        "rollback_time_minutes": {"type": "integer", "minimum": 0, "description": "Expected time to complete rollback"},
        "rollback_steps": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "test_evidence": {
      "type": "object",
      "required": ["lab_tests", "ring_0_results"],
      "properties": {
        "lab_tests": {
          "type": "object",
          "required": ["test_date", "test_scenarios", "success_rate"],
          "properties": {
            "test_date": {"type": "string", "format": "date-time"},
            "test_scenarios": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "scenario": {"type": "string"},
                  "result": {"type": "string", "enum": ["pass", "fail"]},
                  "notes": {"type": "string"}
                }
              }
            },
            "success_rate": {"type": "number", "minimum": 0, "maximum": 1},
            "test_report_url": {"type": "string", "format": "uri"}
          }
        },
        "ring_0_results": {
          "type": "object",
          "required": ["deployment_date", "target_devices", "successful_installs", "failed_installs"],
          "properties": {
            "deployment_date": {"type": "string", "format": "date-time"},
            "target_devices": {"type": "integer", "minimum": 0},
            "successful_installs": {"type": "integer", "minimum": 0},
            "failed_installs": {"type": "integer", "minimum": 0},
            "failure_analysis": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "failure_reason": {"type": "string"},
                  "count": {"type": "integer"},
                  "remediation": {"type": "string"}
                }
              }
            }
          }
        }
      }
    },
    "risk_assessment": {
      "type": "object",
      "required": ["risk_score", "risk_model_version", "threshold", "cab_required", "factors"],
      "properties": {
        "risk_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "risk_model_version": {"type": "string", "pattern": "^v\\d+\\.\\d+$"},
        "threshold": {"type": "string", "enum": ["AUTOMATED_ALLOWED", "CAB_REQUIRED", "PRIVILEGED_TOOLING"]},
        "cab_required": {"type": "boolean"},
        "factors": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "normalized_value": {"type": "number", "minimum": 0, "maximum": 1},
              "weight": {"type": "integer"},
              "contribution": {"type": "number"},
              "rationale": {"type": "string"}
            }
          }
        }
      }
    },
    "exceptions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["exception_id", "exception_type", "severity", "details", "compensating_controls", "approved_by", "expiry"],
        "properties": {
          "exception_id": {"type": "string", "format": "uuid"},
          "exception_type": {"type": "string", "enum": ["vulnerability", "unsigned_package", "scope_violation"]},
          "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
          "details": {"type": "string"},
          "compensating_controls": {"type": "array", "items": {"type": "string"}},
          "approved_by": {"type": "string", "format": "email"},
          "approved_at": {"type": "string", "format": "date-time"},
          "expiry": {"type": "string", "format": "date-time"},
          "owner": {"type": "string", "format": "email"}
        }
      }
    },
    "cab_submission": {
      "type": "object",
      "properties": {
        "submitted_at": {"type": "string", "format": "date-time"},
        "submitted_by": {"type": "string", "format": "email"},
        "justification": {"type": "string"},
        "scope_diff": {
          "type": "object",
          "description": "Scope changes from previous version (if any)",
          "properties": {
            "previous_scope": {"type": "object"},
            "requested_scope": {"type": "object"},
            "blast_radius_summary": {"type": "string"}
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "immutable": {"type": "boolean", "const": true, "description": "Evidence pack is immutable once created"},
        "storage_url": {"type": "string", "format": "uri", "description": "URL to evidence pack in object store"},
        "checksum": {"type": "string", "description": "SHA-256 checksum of evidence pack JSON"},
        "retention_policy_days": {"type": "integer", "minimum": 0, "description": "Retention period per compliance requirements"}
      }
    }
  }
}
```

---

## Example Evidence Pack (Windows Desktop App)

```json
{
  "evidence_pack_id": "ep-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "version": "v1.0",
  "created_at": "2026-01-04T10:00:00Z",
  "created_by": "packaging-eng@example.com",
  "deployment_intent_id": "di-12345678-90ab-cdef-1234-567890abcdef",
  "application": {
    "id": "app-notepadplusplus",
    "name": "Notepad++",
    "version": "8.6.2",
    "vendor": "Notepad++ Team (Don Ho)",
    "category": "productivity",
    "support_tier": "tier_3_community",
    "licensing_model": "free",
    "documentation_url": "https://notepad-plus-plus.org/docs/"
  },
  "artifact": {
    "artifact_id": "artifact-abc123",
    "hash": {
      "algorithm": "sha256",
      "value": "a1b2c3d4e5f67890abcdef1234567890a1b2c3d4e5f67890abcdef1234567890"
    },
    "size_bytes": 4567890,
    "signing": {
      "signed": true,
      "certificate_thumbprint": "1A2B3C4D5E6F7890ABCDEF1234567890ABCDEF12",
      "signing_time": "2026-01-03T15:30:00Z",
      "certificate_subject": "CN=Notepad++, O=Notepad++ Team, C=US",
      "certificate_issuer": "CN=DigiCert SHA2 Assured ID Code Signing CA, OU=www.digicert.com, O=DigiCert Inc, C=US",
      "certificate_expiry": "2027-01-03T15:30:00Z"
    },
    "provenance": {
      "builder_identity": "packaging-pipeline@example.com",
      "pipeline_run_id": "build-20260104-001",
      "build_time": "2026-01-04T09:00:00Z",
      "source_repo": "https://github.com/notepad-plus-plus/notepad-plus-plus",
      "source_commit": "v8.6.2",
      "build_inputs": [
        "npp.8.6.2.Installer.x64.exe (from official release)",
        "enterprise-config.xml (custom settings)"
      ]
    }
  },
  "sbom": {
    "format": "SPDX",
    "sbom_url": "https://artifacts.example.com/sbom/notepadplusplus-8.6.2-sbom.json",
    "component_count": 12,
    "license_summary": [
      {"license": "GPL-3.0", "component_count": 10},
      {"license": "MIT", "component_count": 2}
    ]
  },
  "vulnerability_scan": {
    "scanner": "Trivy",
    "scan_time": "2026-01-04T09:30:00Z",
    "policy_decision": "pass",
    "findings": {
      "critical": 0,
      "high": 0,
      "medium": 1,
      "low": 3
    },
    "scan_report_url": "https://artifacts.example.com/scan-reports/notepadplusplus-8.6.2-trivy.json",
    "malware_scan": {
      "scanner": "Windows Defender",
      "scan_time": "2026-01-04T09:35:00Z",
      "result": "clean",
      "details": "No threats detected"
    }
  },
  "installation": {
    "install_command": "msiexec /i notepadplusplus-8.6.2.msi /qn /norestart",
    "uninstall_command": "msiexec /x {A1B2C3D4-E5F6-7890-ABCD-EF1234567890} /qn /norestart",
    "detection_rules": [
      {
        "type": "file",
        "value": "C:\\Program Files\\Notepad++\\notepad++.exe",
        "expected_result": "exists"
      },
      {
        "type": "registry",
        "value": "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}\\DisplayVersion",
        "expected_result": "8.6.2"
      },
      {
        "type": "productcode",
        "value": "{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}",
        "expected_result": "installed"
      }
    ],
    "reboot_required": false,
    "install_time_minutes": 2,
    "exit_code_mapping": {
      "0": "success",
      "1641": "success_reboot",
      "3010": "success_reboot",
      "1603": "failure",
      "1618": "retry"
    },
    "dependencies": []
  },
  "rollout_plan": {
    "rings": [
      {
        "ring_id": "ring-0-lab",
        "ring_name": "ring-0-lab",
        "target_device_count": 5,
        "target_groups": ["AAD-TestLab-Devices"],
        "exclusions": []
      },
      {
        "ring_id": "ring-1-canary",
        "ring_name": "ring-1-canary",
        "target_device_count": 50,
        "target_groups": ["AAD-Canary-IT-Dept"],
        "exclusions": ["AAD-Executives"]
      },
      {
        "ring_id": "ring-2-pilot",
        "ring_name": "ring-2-pilot",
        "target_device_count": 500,
        "target_groups": ["AAD-Pilot-Finance-BU"],
        "exclusions": ["AAD-Executives", "AAD-Critical-Infra"]
      },
      {
        "ring_id": "ring-3-department",
        "ring_name": "ring-3-department",
        "target_device_count": 5000,
        "target_groups": ["AAD-Finance-BU-All"],
        "exclusions": ["AAD-Executives"]
      },
      {
        "ring_id": "ring-4-global",
        "ring_name": "ring-4-global",
        "target_device_count": 50000,
        "target_groups": ["AAD-All-Devices"],
        "exclusions": []
      }
    ],
    "schedule": {
      "ring-0-lab": {"start": "2026-01-05T00:00:00Z", "duration_hours": 24},
      "ring-1-canary": {"start": "2026-01-06T00:00:00Z", "duration_hours": 24},
      "ring-2-pilot": {"start": "2026-01-07T00:00:00Z", "duration_hours": 48},
      "ring-3-department": {"start": "2026-01-09T00:00:00Z", "duration_hours": 72},
      "ring-4-global": {"start": "2026-01-12T00:00:00Z", "duration_hours": 168}
    },
    "targeting": {
      "acquisition_boundary": "acq-001",
      "business_unit": "bu-finance",
      "site_class": "online"
    },
    "promotion_gates": {
      "success_rate_threshold": 0.98,
      "time_to_compliance_hours": 24,
      "max_incidents": 0
    }
  },
  "rollback_plan": {
    "strategy": "intune_supersedence",
    "rollback_version": "8.6.1",
    "validated": true,
    "validation_date": "2026-01-04T08:00:00Z",
    "validation_evidence": "https://artifacts.example.com/test-reports/notepadplusplus-rollback-test.html",
    "rollback_time_minutes": 5,
    "rollback_steps": [
      "1. Update Intune app supersedence to version 8.6.1",
      "2. Remove assignments for version 8.6.2",
      "3. Add assignments for version 8.6.1 to affected rings",
      "4. Monitor install success rate (target: >98% within 24h)",
      "5. Validate detection rules for version 8.6.1"
    ]
  },
  "test_evidence": {
    "lab_tests": {
      "test_date": "2026-01-04T07:00:00Z",
      "test_scenarios": [
        {"scenario": "Fresh install on Windows 10 22H2", "result": "pass", "notes": "Installed successfully in 2 minutes"},
        {"scenario": "Fresh install on Windows 11 23H2", "result": "pass", "notes": "Installed successfully in 2 minutes"},
        {"scenario": "Upgrade from 8.6.1 to 8.6.2", "result": "pass", "notes": "In-place upgrade successful"},
        {"scenario": "Uninstall clean removal", "result": "pass", "notes": "No residual files or registry keys"},
        {"scenario": "Detection rule validation", "result": "pass", "notes": "All detection rules validated"}
      ],
      "success_rate": 1.0,
      "test_report_url": "https://artifacts.example.com/test-reports/notepadplusplus-lab-tests.html"
    },
    "ring_0_results": {
      "deployment_date": "2026-01-05T00:00:00Z",
      "target_devices": 5,
      "successful_installs": 5,
      "failed_installs": 0,
      "failure_analysis": []
    }
  },
  "risk_assessment": {
    "risk_score": 14,
    "risk_model_version": "v1.0",
    "threshold": "AUTOMATED_ALLOWED",
    "cab_required": false,
    "factors": [
      {"name": "privilege_impact", "normalized_value": 0.2, "weight": 20, "contribution": 4, "rationale": "User-context install, no elevation"},
      {"name": "supply_chain_trust", "normalized_value": 0.1, "weight": 15, "contribution": 1.5, "rationale": "Signed + known vendor (open-source)"},
      {"name": "exploitability", "normalized_value": 0.2, "weight": 10, "contribution": 2, "rationale": "No listeners, no macro/scripting"},
      {"name": "data_access", "normalized_value": 0.1, "weight": 10, "contribution": 1, "rationale": "Scoped to opened files"},
      {"name": "sbom_vulnerability", "normalized_value": 0.0, "weight": 15, "contribution": 0, "rationale": "No High/Critical findings"},
      {"name": "blast_radius", "normalized_value": 0.3, "weight": 10, "contribution": 3, "rationale": "Ring 1 (Canary), 50 devices"},
      {"name": "operational_complexity", "normalized_value": 0.1, "weight": 10, "contribution": 1, "rationale": "Online install, no reboot, < 5 min"},
      {"name": "history", "normalized_value": 0.1, "weight": 10, "contribution": 1, "rationale": "No prior incidents, success rate > 99%"}
    ]
  },
  "exceptions": [],
  "cab_submission": {
    "submitted_at": "2026-01-04T10:00:00Z",
    "submitted_by": "packaging-eng@example.com",
    "justification": "Routine version update with no breaking changes. Security patch for minor CVE-2025-XXXX (Medium severity).",
    "scope_diff": null
  },
  "metadata": {
    "immutable": true,
    "storage_url": "https://artifacts.example.com/evidence-packs/ep-a1b2c3d4-e5f6-7890-abcd-ef1234567890.json",
    "checksum": "b1c2d3e4f5a67890bcdef1234567890b1c2d3e4f5a67890bcdef1234567890",
    "retention_policy_days": 2555
  }
}
```

---

## Evidence Pack Validation Rules

### Completeness Check

All required fields must be present and non-empty:

```python
def validate_evidence_pack(evidence_pack: dict) -> ValidationResult:
    """Validate evidence pack completeness before CAB submission."""
    errors = []

    # Required top-level fields
    required_fields = [
        "evidence_pack_id", "version", "created_at", "created_by",
        "deployment_intent_id", "application", "artifact", "sbom",
        "vulnerability_scan", "installation", "rollout_plan",
        "rollback_plan", "test_evidence", "risk_assessment", "exceptions"
    ]

    for field in required_fields:
        if field not in evidence_pack or not evidence_pack[field]:
            errors.append(f"Missing required field: {field}")

    # Artifact signing validation
    if not evidence_pack["artifact"]["signing"]["signed"]:
        errors.append("Artifact must be signed")

    # Vulnerability scan policy validation
    scan = evidence_pack["vulnerability_scan"]
    if scan["findings"]["critical"] > 0 and scan["policy_decision"] != "exception_granted":
        errors.append("Critical vulnerabilities present without approved exception")

    # Rollback validation check
    if not evidence_pack["rollback_plan"]["validated"]:
        errors.append("Rollback plan must be validated before CAB submission")

    # Ring 0 test evidence validation
    ring_0 = evidence_pack["test_evidence"]["ring_0_results"]
    if ring_0["successful_installs"] == 0:
        errors.append("Ring 0 must have at least one successful install")

    # CAB requirement validation
    risk = evidence_pack["risk_assessment"]
    if risk["cab_required"] and not evidence_pack.get("cab_submission"):
        errors.append("CAB submission required for high-risk deployment")

    return ValidationResult(valid=len(errors) == 0, errors=errors)
```

---

## Evidence Pack Storage

**Storage Requirements**:
- Immutable object store (WORM - Write Once Read Many)
- Versioning support (evidence pack schema versions)
- Retention policy: 7 years (or per enterprise compliance requirements)
- Hash verification on read (integrity check)
- Access control: read (CAB Approvers + Auditors), write (Control Plane only)

**Storage Format**:
- JSON files stored in object store (Azure Blob, AWS S3, MinIO)
- File naming: `{evidence_pack_id}.json`
- Directory structure: `evidence-packs/{YYYY}/{MM}/{evidence_pack_id}.json`
- Metadata file: `{evidence_pack_id}.metadata.json` (checksum, creation time, creator)

**Storage URL Pattern**:
```
https://artifacts.example.com/evidence-packs/2026/01/ep-a1b2c3d4-e5f6-7890-abcd-ef1234567890.json
```

---

## Evidence Pack Versioning

**Schema Versioning**: `v1.0`, `v1.1`, `v2.0`

**Backward Compatibility**:
- Control Plane supports multiple schema versions concurrently
- Evidence packs include `version` field to track schema version
- Schema changes require versioning and migration plan

**Version History**:
| Version | Effective Date | Changes | Breaking? |
|---|---|---|---|
| v1.0 | 2026-01-04 | Initial schema | N/A |
| v1.1 | TBD | Add `scope_diff` to `cab_submission` (optional) | No |
| v2.0 | TBD | Require `malware_scan` in `vulnerability_scan` | Yes |

---

## CAB Submission Workflow

1. **Packaging Engineer** builds artifact → generates SBOM → runs vuln scan
2. **Packaging Factory** validates completeness → creates evidence pack → stores in immutable object store
3. **Control Plane** computes risk score → determines CAB requirement
4. **If CAB required**: Evidence pack submitted for review → CAB Approvers notified
5. **CAB Approvers** review evidence pack → approve/deny → record decision
6. **If approved**: Publisher can publish to Ring 1+ → evidence pack linked to deployment intent
7. **Audit Trail**: All evidence pack accesses logged to immutable event store

---

## Related Documentation

- [Architecture Overview](architecture-overview.md)
- [Control Plane Design](control-plane-design.md)
- [Risk Model](risk-model.md)
- [CAB Workflow](cab-workflow.md)
- [Exception Management](exception-management.md)

---

**Evidence Pack Schema v1.0 — Subject to refinement based on Phase 1 deployment feedback.**
