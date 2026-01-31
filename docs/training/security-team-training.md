# Security Team Training

**SPDX-License-Identifier: Apache-2.0**

## Learning Objectives

By the end of this training, you will be able to:
1. Use SecOps Agent to manage vulnerabilities and remediation
2. Use IAM Security Agent to monitor identity access and detect anomalies
3. Integrate with SIEM platforms for security alert correlation
4. Monitor compliance against security frameworks
5. Understand risk classification and approval workflows for security operations

---

## Key Concepts

### SecOps Agent Overview

**Vulnerability Management**:
- Integrates with Qualys, Nessus, Rapid7, Microsoft Defender
- Tracks CVEs and maps to applications
- Creates remediation plans
- Tracks remediation status

**SIEM Integration**:
- Syncs alerts from Splunk, Sentinel, QRadar
- Correlates alerts with vulnerabilities
- Generates security incidents

**Compliance Monitoring**:
- Tracks compliance against CIS, NIST, SOC2, ISO27001
- Performs compliance checks
- Generates compliance reports

### IAM Security Agent Overview

**Identity Monitoring**:
- Monitors sign-in events across Entra ID, Okta, AD
- Tracks permission changes
- Detects security anomalies

**Anomaly Detection**:
- AI-powered anomaly detection
- Unusual sign-in patterns
- Privilege escalation detection
- Suspicious activity identification

---

## Hands-On Exercises

### Exercise 1: Managing Vulnerabilities

**Objective**: Sync vulnerabilities and create remediation plan

**Steps**:
1. Navigate to **SecOps** dashboard
2. Go to **Scanners** tab
3. Verify scanner is configured
4. Click **Sync** on scanner
5. Monitor sync progress
6. Go to **Vulnerabilities** tab
7. Review vulnerabilities:
   - Filter by severity (Critical, High, Medium, Low)
   - Review CVE details
   - Check affected instances
8. Select critical vulnerability
9. Create remediation plan:
   - Click **Create Plan**
   - Define remediation steps
   - Set risk level (R2 or R3)
   - Submit for approval

**Expected Outcome**: Vulnerabilities synced and remediation plan created

### Exercise 2: SIEM Alert Correlation

**Objective**: Sync SIEM alerts and correlate with vulnerabilities

**Steps**:
1. Navigate to **SecOps** → **SIEM**
2. Verify SIEM connection is configured
3. Click **Sync Alerts**
4. Go to **Alerts** tab
5. Review security alerts:
   - Filter by severity
   - Review alert details
   - Check affected assets
6. Correlate alert with vulnerability:
   - Select alert
   - Click **Correlate**
   - Link related vulnerabilities
7. Create incident if needed

**Expected Outcome**: SIEM alerts synced and correlated with vulnerabilities

### Exercise 3: Compliance Monitoring

**Objective**: Run compliance check and review results

**Steps**:
1. Navigate to **SecOps** → **Compliance**
2. Go to **Baselines** tab
3. Review active baselines (CIS, NIST, SOC2, ISO27001)
4. Go to **Checks** tab
5. Click **Run Check**
6. Select baseline and asset
7. Review compliance results:
   - Overall score
   - Passed controls
   - Failed controls
   - Control-level details
8. Address failed controls
9. Review compliance status report

**Expected Outcome**: Compliance check completed with results reviewed

### Exercise 4: Monitoring Identity Access

**Objective**: Monitor sign-in events and detect anomalies

**Steps**:
1. Navigate to **IAM Security** dashboard
2. Go to **Sign-Ins** tab
3. Review sign-in events:
   - Filter by provider
   - Filter by user
   - Filter by success/failure
4. Go to **Anomalies** tab
5. Review detected anomalies:
   - Anomaly type
   - User principal
   - Confidence score
   - Status
6. Investigate anomaly:
   - Review related events
   - Check user activity history
   - Verify with user if needed
7. Resolve anomaly:
   - Mark as resolved or false positive
   - Add resolution notes

**Expected Outcome**: Identity access monitored and anomalies resolved

---

## Assessment Checklist

- [ ] Can sync vulnerabilities from scanners
- [ ] Can create remediation plans
- [ ] Can sync SIEM alerts
- [ ] Can correlate alerts with vulnerabilities
- [ ] Can run compliance checks
- [ ] Can review compliance results
- [ ] Can monitor sign-in events
- [ ] Can detect and resolve anomalies
- [ ] Understands risk classification for security operations
- [ ] Knows when CAB approval is required

---

## Quick Reference Card

### SecOps Agent
- **Sync Vulnerabilities**: SecOps → Scanners → Sync
- **View Vulnerabilities**: SecOps → Vulnerabilities
- **Create Remediation Plan**: SecOps → Remediation Plans → Create
- **Sync SIEM Alerts**: SecOps → SIEM → Sync Alerts
- **Run Compliance Check**: SecOps → Compliance → Run Check

### IAM Security Agent
- **View Sign-Ins**: IAM Security → Sign-Ins
- **Review Anomalies**: IAM Security → Anomalies
- **Resolve Anomaly**: Anomaly → Resolve
- **View Permission Changes**: IAM Security → Permission Changes
- **Security Actions**: IAM Security → Actions

---

## Related Documentation

- [SecOps Agent User Guide](../user-guides/secops-agent.md)
- [IAM Security Agent User Guide](../user-guides/iam-security-agent.md)
- [Agent Configuration Guide](../admin-guides/agent-configuration.md)
- [Integration Setup Guide](../admin-guides/integration-setup.md)
