---
description: SPDX License Compliance Rules
globs: "**/*"
---

# SPDX License Compliance

This file enforces SPDX license identifier standards for all EUCORA source files.

## License

**EUCORA** is licensed under **Apache License 2.0**.

All source files MUST include the appropriate SPDX license identifier.

## SPDX Header Requirements

### PowerShell Files (.ps1)

**REQUIRED**: SPDX header as the **first two lines** of every `.ps1` file.

```powershell
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#
<# 
.SYNOPSIS
    ...
#>
```

### Markdown Files (.md)

**REQUIRED**: SPDX identifier after the title.

```markdown
# Document Title

**SPDX-License-Identifier: Apache-2.0**

---

Content...
```

### Shell Scripts (.sh)

**REQUIRED**: SPDX header as the first two lines.

```bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
```

### JSON Files (.json)

JSON does not support comments. SPDX compliance is documented in:
1. The `LICENSE` file at repository root
2. Accompanying README or schema documentation

### Python Files (.py) - If Added

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
```

### TypeScript/JavaScript Files (.ts, .tsx, .js) - If Added

```typescript
// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2025 BuildWorks.AI
```

## Enforcement

1. **Pre-Commit Hooks**: Block commits of source files without SPDX headers
2. **CI/CD**: Automated SPDX compliance checks
3. **Code Review**: Reviewers must verify SPDX headers on new files

## Exceptions

The following file types do NOT require SPDX headers:
- `.gitignore`
- `.env` files
- `package.json`, `pyproject.toml` (license specified in metadata)
- Binary files (images, executables)
- Generated files (build artifacts)

## References

- [SPDX Specification](https://spdx.dev/specifications/)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
- [EUCORA LICENSE file](../../LICENSE)

---

**SPDX-License-Identifier: Apache-2.0**
