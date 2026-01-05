# Remote-Exec & Templates Folder Analysis

**Date**: 2026-01-04  
**Analyst**: Amani (BuildWorks.AI)  
**Status**: ⚠️ **ARCHITECTURAL MISALIGNMENT DETECTED**

---

## Executive Summary

The `Remote-Exec/` and `Templates/` folders contain **legacy PSADT (PowerShell App Deployment Toolkit) scripts** that are **NOT aligned with EUCORA's Control Plane architecture**. These represent an **old approach** to application deployment that **contradicts** the thin control plane model.

**Recommendation**: **DEPRECATE** these folders and replace with proper Control Plane → Execution Plane workflow.

---

## Folder Analysis

### 1. Remote-Exec/ Folder

**Contents**: 1 file - `Invoke-RemoteInstall.ps1`

**Purpose**: Direct remote execution wrapper for PSADT packages

**What it does**:
- Copies PSADT package to remote computer via UNC path
- Executes `Deploy-Application.ps1` remotely via `Invoke-Command`
- Bypasses Control Plane entirely

**Architectural Violations**:
- ❌ **Direct endpoint connectivity** (forbidden by CLAUDE.md line 215)
- ❌ **Bypasses Control Plane** (no policy, no evidence, no CAB)
- ❌ **No correlation IDs** (no audit trail)
- ❌ **No execution plane integration** (should use Intune/SCCM/Jamf)
- ❌ **No idempotency checks**
- ❌ **No risk scoring**
- ❌ **No ring-based rollout**

**Quote from CLAUDE.md**:
> "The Control Plane has **no direct connectivity to endpoints**; it only interfaces with authorized management planes (Intune/Jamf/SCCM/AWX/Landscape). There is **no Control Plane → endpoint agent channel**..."

**Verdict**: ⛔ **VIOLATES CORE ARCHITECTURE** - Must be deprecated

---

### 2. Templates/ Folder

**Contents**: 3 subdirectories
- `EXE-Installation/Deploy-Application.ps1`
- `MSI-Installation/Deploy-Application.ps1`
- `Unpackaged-Installation/Deploy-Application.ps1`

**Purpose**: PSADT deployment script templates

**What they do**:
- Provide boilerplate for EXE/MSI/Unpackaged installations
- Include PSADT framework integration (commented out)
- Registry hacks to disable uninstall/repair buttons
- Manual installation logic

**Architectural Issues**:
- ⚠️ **Bypasses Packaging Factory** (no SBOM, no signing, no scanning)
- ⚠️ **No Control Plane integration** (no evidence packs, no CAB)
- ⚠️ **Manual deployment** (not orchestrated)
- ⚠️ **No execution plane connectors** (should use Intune Win32 app model)

**Potential Value**:
- ✅ Could be **reference examples** for packaging standards
- ✅ Registry disable logic is useful
- ✅ Shows install/uninstall patterns

**Verdict**: ⚠️ **LEGACY APPROACH** - Needs transformation into proper templates

---

## Relevance to EUCORA Architecture

### Current State: ❌ **NOT RELEVANT**

These folders represent a **pre-EUCORA** approach where:
1. Packages are deployed **directly to endpoints**
2. No **Control Plane** orchestration
3. No **Execution Plane** integration (Intune/Jamf/SCCM)
4. No **evidence packs** or **CAB approval**
5. No **ring-based rollout**

### EUCORA Architecture (Correct Approach):

```
┌─────────────────────────────────────────────┐
│           Control Plane                     │
│  (Policy + Orchestration + Evidence)        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│      Packaging & Publishing Factory         │
│  (Build → Sign → SBOM → Scan → Test)        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Execution Planes                    │
│  Intune | Jamf | SCCM | Landscape | Ansible │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            Endpoint Devices                 │
└─────────────────────────────────────────────┘
```

**Key Difference**: 
- ❌ Old: Script → Endpoint (direct)
- ✅ New: Control Plane → Execution Plane → Endpoint (orchestrated)

---

## Proposed Restructuring

### Option 1: DEPRECATE (Recommended)

**Action**: Move to `deprecated/` folder with clear warning

```
deprecated/
├── Remote-Exec/
│   └── Invoke-RemoteInstall.ps1  # ⛔ DO NOT USE
└── Templates/
    ├── EXE-Installation/
    ├── MSI-Installation/
    └── Unpackaged-Installation/
```

**Rationale**: These scripts fundamentally contradict EUCORA architecture

---

### Option 2: TRANSFORM INTO PROPER TEMPLATES

**Action**: Extract useful patterns, integrate with Control Plane

**New Structure**:
```
scripts/
├── packaging-factory/
│   ├── templates/
│   │   ├── windows-exe-template.ps1      # ✅ Packaging logic only
│   │   ├── windows-msi-template.ps1      # ✅ Packaging logic only
│   │   └── windows-unpackaged-template.ps1
│   └── build/
│       ├── Build-Win32Package.ps1        # ✅ Creates .intunewin
│       ├── Sign-Package.ps1              # ✅ Code signing
│       └── Generate-SBOM.ps1             # ✅ SBOM generation
└── connectors/
    └── intune/
        └── Publish-Win32App.ps1          # ✅ Publishes via Graph API
```

**What to Extract**:
1. ✅ Registry disable logic (useful for post-install)
2. ✅ Install/uninstall patterns (reference only)
3. ✅ Detection logic examples

**What to Discard**:
1. ❌ Direct remote execution (`Invoke-RemoteInstall.ps1`)
2. ❌ Manual deployment workflows
3. ❌ PSADT framework references (use Intune Win32 model instead)

---

## Recommended Actions

### Immediate (Critical)

1. **Create deprecation notice**:
   ```
   deprecated/
   └── README.md  # ⛔ WARNING: These scripts violate EUCORA architecture
   ```

2. **Move folders**:
   ```bash
   mkdir deprecated
   mv Remote-Exec deprecated/
   mv Templates deprecated/
   ```

3. **Update documentation** to remove any references

### Short-Term (High Priority)

4. **Create proper packaging templates** in `scripts/packaging-factory/templates/`

5. **Document correct workflow** in `docs/architecture/packaging-workflow.md`

6. **Add to AGENTS.md** as anti-pattern example

### Long-Term (Medium Priority)

7. **Build Packaging Factory scripts** (Phase 4 per planning docs)

8. **Implement Intune connector** for Win32 app publishing

9. **Create evidence pack generation** for CAB submissions

---

## Impact Analysis

### If We Keep These Folders

**Risks**:
- ❌ Developers use wrong approach (direct deployment)
- ❌ Bypasses all governance (no CAB, no evidence)
- ❌ No audit trail (no correlation IDs)
- ❌ Contradicts architecture documentation
- ❌ Fails compliance requirements

### If We Deprecate

**Benefits**:
- ✅ Forces correct Control Plane approach
- ✅ Aligns with AGENTS.md and CLAUDE.md
- ✅ Ensures CAB governance
- ✅ Maintains audit trail
- ✅ Enables ring-based rollout

**Effort**: Low (move folders, update docs)

---

## Conclusion

**Remote-Exec/** and **Templates/** folders are **legacy artifacts** from a pre-EUCORA approach that **directly contradict** the thin control plane architecture.

**Recommendation**: **DEPRECATE IMMEDIATELY**

These folders:
1. ⛔ Violate core architectural principle (no direct endpoint connectivity)
2. ⛔ Bypass Control Plane (no policy, evidence, or CAB)
3. ⛔ Prevent proper governance and audit trail
4. ⛔ Contradict AGENTS.md and CLAUDE.md

**Correct Approach**:
- Use **Packaging Factory** to build/sign/scan packages
- Use **Control Plane** to orchestrate deployments
- Use **Execution Plane Connectors** (Intune/Jamf/SCCM) to publish
- Use **Ring-based rollout** with promotion gates
- Generate **evidence packs** for CAB approval

---

## Next Steps

1. ✅ Move `Remote-Exec/` and `Templates/` to `deprecated/`
2. ✅ Create deprecation notice
3. ✅ Update all documentation
4. ✅ Add anti-pattern warning to AGENTS.md
5. 🔲 Build proper Packaging Factory templates (Phase 4)

---

*Build by BuildWorks.AI*

**SPDX-License-Identifier: Apache-2.0**
