# Desktop Support Training

**SPDX-License-Identifier: Apache-2.0**

## Learning Objectives

By the end of this training, you will be able to:
1. Use KB & Triage Agent to triage tickets with AI assistance
2. Search knowledge base using semantic search
3. Use incident patterns to resolve recurring issues
4. Provide feedback to improve AI triage accuracy
5. Coordinate with Request Coordination Agent for SLA tracking

---

## Key Concepts

### KB & Triage Agent Overview

**Knowledge Base Integration**:
- Syncs articles from ServiceNow KB, Confluence, SharePoint
- Indexes articles for semantic search
- Tracks article usage and helpfulness

**AI-Powered Triage**:
- Automatically categorizes tickets
- Assigns priority based on content
- Suggests resolution steps
- Matches similar past incidents

**Incident Pattern Detection**:
- Identifies recurring issues
- Suggests resolutions for patterns
- Tracks pattern frequency

---

## Hands-On Exercises

### Exercise 1: Performing Ticket Triage

**Objective**: Triage a ticket using AI assistance

**Steps**:
1. Navigate to **KB & Triage** dashboard
2. Go to **Triage** tab
3. Click **New Request**
4. Enter ticket details:
   - Caller name and email
   - Affected service
   - Short description
   - Detailed description
5. Submit request
6. Review AI triage results:
   - Suggested category
   - Suggested priority
   - Suggested resolution
   - Matched knowledge articles
7. Accept or modify suggestions
8. Apply suggestions to ticket

**Expected Outcome**: Ticket triaged with AI suggestions applied

### Exercise 2: Semantic Knowledge Base Search

**Objective**: Search knowledge base using natural language

**Steps**:
1. Navigate to **KB & Triage** → **Articles**
2. Click **Search**
3. Enter natural language query:
   - Example: "How to reset user password in Active Directory"
4. Review search results:
   - Ranked by relevance
   - Article titles and snippets
   - Source and category
5. Click on article to view full content
6. Use article to resolve ticket

**Expected Outcome**: Relevant knowledge articles found using semantic search

### Exercise 3: Using Incident Patterns

**Objective**: Use incident patterns to resolve recurring issues

**Steps**:
1. Navigate to **KB & Triage** → **Patterns**
2. Review detected patterns:
   - Pattern name and description
   - Matching keywords
   - Frequency
   - Suggested resolution
3. Identify pattern matching current ticket
4. Apply suggested resolution
5. Document resolution outcome

**Expected Outcome**: Recurring issue resolved using pattern

### Exercise 4: Providing Feedback

**Objective**: Provide feedback to improve AI accuracy

**Steps**:
1. Resolve ticket using AI suggestions
2. Navigate to **KB & Triage** → **Triage**
3. Select resolved request
4. Click **Provide Feedback**
5. Rate triage suggestions:
   - Category accuracy (1-5 stars)
   - Priority accuracy (1-5 stars)
   - Resolution helpfulness (1-5 stars)
6. Add comments
7. Submit feedback

**Expected Outcome**: Feedback provided to improve AI triage

---

## Assessment Checklist

- [ ] Can create triage request
- [ ] Can review AI triage suggestions
- [ ] Can perform semantic knowledge base search
- [ ] Can use incident patterns for resolution
- [ ] Can provide feedback on triage accuracy
- [ ] Understands knowledge source integration
- [ ] Knows how to improve AI accuracy through feedback
- [ ] Can coordinate with Request Coordination Agent

---

## Quick Reference Card

### KB & Triage Agent
- **Create Triage Request**: KB & Triage → Triage → New Request
- **Search Knowledge Base**: KB & Triage → Articles → Search
- **View Patterns**: KB & Triage → Patterns
- **Provide Feedback**: KB & Triage → Triage → Provide Feedback

### Common Queries
- Password reset: "How to reset user password"
- Application access: "How to grant application access"
- Device issues: "How to troubleshoot device connectivity"
- Software installation: "How to install software on device"

---

## Related Documentation

- [KB & Triage Agent User Guide](../user-guides/kb-triage-agent.md)
- [Request Coordination Agent User Guide](../user-guides/request-coordination-agent.md)
- [RAG Pipeline Architecture](../architecture/rag-pipeline-architecture.md)
