# Air-Gapped Procedures

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

This document defines **controlled transfer procedures** for air-gapped sites. All air-gapped transfers require **hash verification**, **signature verification**, and **import audit events**.

**Design Principle**: Offline is First-Class — explicit procedures for air-gapped deployments.

---

## Transfer Requirements

### Mandatory Checks

1. **Hash Verification**: SHA-256 hash verification
2. **Signature Verification**: Package signature verification
3. **Import Audit Events**: Immutable audit trail for all imports

### Transfer Media

- **Encrypted USB drives** (AES-256)
- **Encrypted optical media** (for high-security sites)
- **Approved network transfer** (for sites with controlled network access)

---

## Windows Air-Gapped Transfer

### Preparation

1. **Package Preparation**
   - Build package in Packaging Factory
   - Sign with enterprise certificate
   - Generate SBOM
   - Run vulnerability scan
   - Store in artifact store

2. **Transfer Package Creation**
   - Create SCCM package
   - Distribute to staging DP
   - Generate transfer manifest

### Transfer Manifest

```json
{
  "transfer_id": "uuid",
  "package_name": "Application Name",
  "version": "1.2.3",
  "package_hash": "sha256:abc123...",
  "signature_hash": "sha256:def456...",
  "sbom_hash": "sha256:ghi789...",
  "transfer_date": "2026-01-06",
  "prepared_by": "packaging-engineer@example.com",
  "artifacts": [
    {
      "name": "package.intunewin",
      "hash": "sha256:abc123...",
      "size_bytes": 10485760
    }
  ]
}
```

### Transfer Process

1. **Export from Staging**
   - Export SCCM package to encrypted media
   - Include transfer manifest
   - Include hash verification script

2. **Physical Transfer**
   - Encrypted media transported via approved courier
   - Chain of custody documentation
   - Secure storage during transit

3. **Import to Air-Gapped Site**
   - Verify media integrity
   - Verify hash (SHA-256)
   - Verify signature
   - Import to SCCM DP
   - Generate import audit event

### Import Verification

```powershell
# Verify hash
$expectedHash = "abc123..."
$actualHash = (Get-FileHash package.intunewin -Algorithm SHA256).Hash
if ($actualHash -ne $expectedHash) {
    throw "Hash verification failed"
}

# Verify signature
$signature = Get-AuthenticodeSignature package.intunewin
if ($signature.Status -ne "Valid") {
    throw "Signature verification failed"
}
```

### Import Audit Event

```json
{
  "correlation_id": "transfer-uuid",
  "event_type": "AIR_GAPPED_IMPORT",
  "event_data": {
    "transfer_id": "uuid",
    "site_id": "air-gapped-site-1",
    "package_name": "Application Name",
    "version": "1.2.3",
    "hash_verified": true,
    "signature_verified": true,
    "imported_by": "site-admin@example.com",
    "import_timestamp": "2026-01-06T10:00:00Z"
  },
  "actor": "site-admin@example.com",
  "created_at": "2026-01-06T10:00:00Z"
}
```

---

## macOS Air-Gapped Transfer

### Preparation

1. **Package Preparation**
   - Build signed PKG
   - Notarize (if applicable)
   - Generate SBOM
   - Store in artifact store

2. **Transfer Package**
   - Create Jamf package
   - Generate transfer manifest

### Transfer Process

1. **Export**
   - Export Jamf package to encrypted media
   - Include transfer manifest
   - Include verification scripts

2. **Import**
   - Verify hash
   - Verify signature
   - Import to Jamf DP
   - Generate import audit event

---

## Linux Air-Gapped Transfer

### Preparation

1. **Mirror Preparation**
   - Prepare APT mirror with required packages
   - Sign repository
   - Generate transfer manifest

2. **Transfer Package**
   - Export mirror to encrypted media
   - Include GPG key (separate transfer)
   - Include verification scripts

### Transfer Process

1. **Export**
   - Export APT mirror to encrypted media
   - Export GPG key separately (secure transfer)
   - Include transfer manifest

2. **Import**
   - Import GPG key to trusted keyring
   - Verify repository signature
   - Import mirror to site
   - Configure APT to use local mirror
   - Generate import audit event

---

## Security Controls

### Media Encryption

- **Algorithm**: AES-256
- **Key Management**: Separate key transfer (secure channel)
- **Verification**: Decryption test before import

### Chain of Custody

- **Documentation**: Transfer log with signatures
- **Verification**: Hash verification at each transfer point
- **Storage**: Secure storage during transit

### Access Controls

- **Import Permissions**: Site admins only
- **Audit**: All import actions logged
- **Verification**: Two-person verification for critical packages

---

## Time-to-Compliance

**Air-Gapped Sites**: ≤ **7 days** (or next approved transfer window)

**Factors**:
- Transfer window frequency (monthly, quarterly)
- Import processing time
- Distribution time within site

---

## Exception Process

**Exceptions Require**:
- CAB approval
- Justification
- Compensating controls
- Expiry date

**Example Exception**:
- Expedited transfer outside normal window (requires CAB approval)

---

## References

- [Site Classification](./site-classification.md)
- [Distribution Decision Matrix](./distribution-decision-matrix.md)
- [Signing Procedures](./signing-procedures.md)
- [Audit Trail Schema](./audit-trail-schema.md)

