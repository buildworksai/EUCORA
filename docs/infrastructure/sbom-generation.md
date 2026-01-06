# SBOM Generation

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Software Bill of Materials (SBOM) generation is **mandatory** for all artifacts. SBOMs provide transparency into package dependencies and enable vulnerability tracking.

**Design Principle**: Supply Chain Transparency — all artifacts must have SBOMs.

---

## SBOM Formats

### Supported Formats

1. **SPDX** (Software Package Data Exchange)
   - Format: JSON, YAML, Tag-Value
   - Standard: ISO/IEC 5962:2021
   - Preferred format

2. **CycloneDX**
   - Format: JSON, XML
   - Standard: OWASP CycloneDX
   - Alternative format

### Format Selection

- **Default**: SPDX JSON
- **Alternative**: CycloneDX JSON (if tooling requires)

---

## SBOM Generation Tools

### Recommended Tools

1. **syft** (Anchore)
   - Supports: Windows, macOS, Linux
   - Output: SPDX, CycloneDX
   - Integration: CLI, API

2. **cyclonedx-cli**
   - Supports: Multiple languages
   - Output: CycloneDX
   - Integration: CLI

3. **Enterprise Tools**
   - Snyk, FOSSA, or approved enterprise scanner

### Tool Selection

- **Windows**: syft (preferred) or enterprise tool
- **macOS**: syft (preferred) or enterprise tool
- **Linux**: syft (preferred) or cyclonedx-cli

---

## SBOM Content Requirements

### Minimum Required Fields

1. **Document Information**
   - Document name
   - SPDX version
   - Creation timestamp
   - Creator (tool + organization)

2. **Package Information**
   - Package name
   - Package version
   - Package download location
   - Package checksum (SHA-256)

3. **Dependency Information**
   - Component name
   - Component version
   - Component license
   - Component checksum

4. **Relationship Information**
   - Dependency relationships
   - Contains relationships

### Example SPDX Structure

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "eucora-app-v1.2.3",
  "documentNamespace": "https://eucora.example.com/spdx/eucora-app-v1.2.3",
  "creationInfo": {
    "created": "2026-01-06T10:00:00Z",
    "creators": [
      "Tool: syft-1.0.0",
      "Organization: BuildWorks.AI"
    ]
  },
  "packages": [
    {
      "SPDXID": "SPDXRef-Package",
      "name": "eucora-app",
      "versionInfo": "1.2.3",
      "downloadLocation": "https://artifacts.example.com/eucora-app-1.2.3.msi",
      "checksums": [
        {
          "algorithm": "SHA256",
          "checksumValue": "abc123..."
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-Package",
      "relationshipType": "CONTAINS",
      "relatedSpdxElement": "SPDXRef-Component-library"
    }
  ]
}
```

---

## Generation Process

### Pipeline Integration

1. **After Build Stage**
   - Generate SBOM from built package
   - Store SBOM alongside artifact

2. **SBOM Validation**
   - Validate SBOM format
   - Verify required fields present
   - Check for known issues

3. **SBOM Storage**
   - Store in artifact store
   - Link to artifact metadata
   - Include in evidence pack

### Command Examples

**syft (SPDX)**:
```bash
syft packages package.msi -o spdx-json > package.spdx.json
```

**cyclonedx-cli**:
```bash
cyclonedx-bom -o package.cdx.json package.deb
```

---

## SBOM Validation

### Format Validation

- Validate against SPDX/CycloneDX schema
- Verify required fields present
- Check for format errors

### Content Validation

- Verify package information accuracy
- Validate dependency relationships
- Check for missing dependencies

---

## SBOM Storage

### Storage Location

- **Artifact Store**: MinIO/S3 bucket `eucora-sboms/`
- **Path Pattern**: `{platform}/{app_name}/{version}/sbom.{format}`
- **Metadata**: Linked to artifact record

### Access Control

- **Read**: All authenticated users
- **Write**: Packaging engineers only
- **Audit**: All access logged

---

## SBOM Usage

### Vulnerability Tracking

- Link SBOM components to CVE databases
- Track vulnerability impact across dependencies
- Enable dependency vulnerability scanning

### License Compliance

- Identify license obligations
- Track license compatibility
- Generate license reports

### Supply Chain Security

- Verify component authenticity
- Track component provenance
- Enable supply chain risk assessment

---

## References

- [Packaging Pipelines](./packaging-pipelines.md)
- [Vulnerability Scan Policy](./vuln-scan-policy.md)
- [Evidence Pack Schema](../architecture/evidence-pack-schema.md)

