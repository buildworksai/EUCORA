# Signing Procedures

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

This document defines **mandatory signing procedures** for all packages across Windows, macOS, and Linux platforms. Unsigned packages are **blocked** from publication unless an approved exception exists.

**Design Principle**: Supply Chain Trust — all packages must be signed with enterprise certificates.

---

## Windows Code-Signing

### Certificate Requirements

- **Type**: Code Signing Certificate (EV or Standard)
- **Issuer**: Enterprise CA (DigiCert, Sectigo, etc.)
- **Storage**: Hardware Security Module (HSM) or secure key vault
- **Rotation**: Annual renewal with 90-day advance notice

### Signing Process

1. **Prepare Package**
   - Ensure package is final (no further modifications)
   - Generate SHA-256 hash

2. **Sign with signtool**
   ```powershell
   signtool sign /f certificate.pfx /p password /tr http://timestamp.digicert.com /td sha256 /fd sha256 package.exe
   ```

3. **Verify Signature**
   ```powershell
   signtool verify /pa /v package.exe
   ```

4. **Store Metadata**
   - Certificate thumbprint
   - Timestamp server URL
   - Signing timestamp

### Intune Win32 Packages

- Sign the **source** MSI/EXE before creating .intunewin
- .intunewin wrapper does not require signing
- Detection rules verify signature on deployed package

---

## macOS Signing & Notarization

### Signing Requirements

- **Identity**: Developer ID Application certificate
- **Team ID**: Enterprise Apple Developer account
- **Notarization**: Required for distribution outside App Store

### Signing Process

1. **Sign Package**
   ```bash
   codesign --sign "Developer ID Application: Company Name" --timestamp --options runtime package.pkg
   ```

2. **Verify Signature**
   ```bash
   codesign --verify --verbose package.pkg
   ```

3. **Notarize** (if required)
   ```bash
   xcrun notarytool submit package.pkg --apple-id {id} --team-id {team_id} --password {app_password} --wait
   ```

4. **Staple Ticket**
   ```bash
   xcrun stapler staple package.pkg
   ```

### Evidence Requirements

- Signing identity certificate
- Notarization ticket (if applicable)
- pkgutil receipt validation

---

## Linux APT Repository Signing

### GPG Key Requirements

- **Key Type**: RSA 4096-bit or Ed25519
- **Storage**: Secure key vault with access controls
- **Rotation**: Annual rotation with 90-day advance notice

### Signing Process

1. **Sign Package**
   ```bash
   debsign -k {key_id} package.deb
   ```

2. **Sign Repository**
   ```bash
   apt-ftparchive release . > Release
   gpg --clearsign -o InRelease Release
   gpg -abs -o Release.gpg Release
   ```

3. **Verify Signature**
   ```bash
   gpg --verify Release.gpg Release
   ```

### Key Management

- **Master Key**: Stored in HSM/vault (offline)
- **Subkey**: Used for daily signing (online)
- **Backup**: Encrypted backup in secure location

---

## Key Ownership & Rotation

### Key Ownership

- **Windows Code-Signing**: Security team (PKI team)
- **macOS Developer ID**: Apple platform owner
- **Linux APT Signing**: Linux platform owner

### Rotation Procedures

1. **90 Days Before Expiry**
   - Generate new certificate/key
   - Test signing process
   - Update pipeline configuration

2. **30 Days Before Expiry**
   - Begin dual-signing (old + new certificate)
   - Update documentation

3. **At Expiry**
   - Switch to new certificate only
   - Archive old certificate
   - Update all references

---

## Exception Process

Unsigned packages require:
- **Security Reviewer Approval**
- **Justification**: Why signing is not possible
- **Compensating Controls**: Hash verification, source verification
- **Expiry Date**: Maximum 90 days

---

## Audit Trail

All signing operations generate events:

```json
{
  "correlation_id": "uuid",
  "event_type": "PACKAGE_SIGNED",
  "event_data": {
    "artifact_id": "uuid",
    "platform": "windows|macos|linux",
    "certificate_thumbprint": "abc123...",
    "signing_timestamp": "2026-01-06T10:00:00Z",
    "signed_by": "packaging-engineer@example.com"
  },
  "actor": "packaging-engineer@example.com",
  "created_at": "2026-01-06T10:00:00Z"
}
```

---

## References

- [Key Management](./key-management.md)
- [Packaging Pipelines](./packaging-pipelines.md)
- [Exception Management](../architecture/exception-management.md)

