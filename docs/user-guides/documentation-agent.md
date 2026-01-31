# Documentation Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The Documentation Agent helps developers and technical writers automatically generate documentation from codebases. It analyzes repositories, generates API documentation, README files, architecture diagrams, and runbooks.

## Key Features

- **Repository Analysis**: Analyzes code repositories (GitHub, GitLab, local)
- **Automated Documentation Generation**: Generates API docs, READMEs, architecture docs, runbooks
- **Module Documentation Tracking**: Tracks documentation status for code modules
- **Template-Based Generation**: Uses templates for consistent documentation
- **Version Control Integration**: Tracks documentation changes over time

## Getting Started

### Accessing the Agent

1. Navigate to **Documentation** from the main dashboard
2. You'll see the Documentation Dashboard with repositories, analyses, and generated documents

### Prerequisites

- Repository access (GitHub, GitLab, or local file system)
- Documentation Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Adding Code Repository

**Step 1**: Navigate to **Repositories** tab
**Step 2**: Click **Add Repository**
**Step 3**: Select repository type:
- GitHub
- GitLab
- Local

**Step 4**: Enter repository details:
- Name
- Repository URL (for GitHub/GitLab) or path (for local)
- Branch (default: main/master)
- Authentication (if private repository)

**Step 5**: Test connection
**Step 6**: Save and activate repository

### 2. Running Code Analysis

**Step 1**: Go to **Analyses** tab
**Step 2**: Click **Start Analysis**
**Step 3**: Select repository
**Step 4**: Choose analysis scope:
- **Full Analysis**: Analyze entire repository
- **Incremental**: Analyze only changes since last analysis
- **Module-Specific**: Analyze specific modules

**Step 5**: Start analysis
**Step 6**: Monitor analysis progress
**Step 7**: Review analysis results:
- Modules analyzed
- Documentation status
- Issues found

### 3. Viewing Module Documentation Status

**Step 1**: Navigate to **Modules** tab
**Step 2**: View module list:
- Module path and name
- Documentation status:
  - **Missing**: No documentation
  - **Outdated**: Documentation needs update
  - **Current**: Documentation is up to date
- Last analyzed date

**Step 3**: Filter by:
- Repository
- Documentation status
- Module path

**Step 4**: Click on module to view details

### 4. Generating Documentation

**Step 1**: Go to **Documents** tab
**Step 2**: Click **Generate Documentation**
**Step 3**: Select:
- Repository
- Document type:
  - **API Docs**: API reference documentation
  - **README**: Project README file
  - **Architecture**: Architecture documentation
  - **Runbook**: Operational runbook

**Step 4**: Configure generation options:
- Output format (Markdown, HTML, PDF)
- Include diagrams
- Template selection

**Step 5**: Generate documentation
**Step 6**: Review generated document
**Step 7**: Download or commit to repository

### 5. Using Documentation Templates

**Step 1**: Navigate to **Templates** tab
**Step 2**: View available templates:
- API documentation template
- README template
- Architecture template
- Runbook template

**Step 3**: Preview template
**Step 4**: Use template when generating documentation
**Step 5**: Customize template if needed (admin access required)

### 6. Viewing Generated Documents

**Step 1**: Go to **Documents** tab
**Step 2**: View document list:
- Document name
- Document type
- Repository
- Generated date
- File path

**Step 3**: Filter by:
- Repository
- Document type
- Date range

**Step 4**: Click on document to:
- View content
- Download
- View generation history

### 7. Tracking Documentation Status

**Step 1**: Navigate to **Modules** tab
**Step 2**: Review documentation coverage:
- Total modules
- Modules with documentation
- Modules missing documentation
- Modules with outdated documentation

**Step 3**: Prioritize documentation:
- Focus on critical modules first
- Update outdated documentation
- Generate missing documentation

## Configuration Options

### Analysis Configuration

- **Analysis Frequency**: Configure automatic analysis schedule
- **Language Support**: Configure supported programming languages
- **Documentation Standards**: Configure documentation requirements

### Generation Configuration

- **Output Formats**: Configure supported output formats
- **Diagram Generation**: Enable/disable diagram generation
- **Template Customization**: Customize documentation templates

## Best Practices

1. **Regular Analysis**: Run code analysis regularly to track documentation status
2. **Keep Documentation Updated**: Update documentation when code changes
3. **Use Templates**: Standardize documentation with templates
4. **Review Generated Docs**: Always review and edit generated documentation
5. **Version Control**: Commit documentation to version control
6. **Document Critical Modules First**: Prioritize documentation for critical modules

## Troubleshooting

### Repository Issues

**Problem**: Repository connection fails
**Solution**: Verify repository URL, credentials, and network access

**Problem**: Analysis fails
**Solution**: Check repository access and code structure

### Generation Issues

**Problem**: Documentation generation fails
**Solution**: Verify repository structure and template configuration

**Problem**: Generated documentation incomplete
**Solution**: Check code comments and documentation standards

### Module Tracking Issues

**Problem**: Modules not detected
**Solution**: Verify code structure and analysis configuration

**Problem**: Documentation status incorrect
**Solution**: Re-run analysis or manually update status

## Related Documentation

- [Documentation Agent API Reference](../api/documentation-agent-api.yaml)
- [Admin Configuration Guide](../admin-guides/workflow-management.md)
- [Planning Document](../planning/21-documentation-agent.md)
