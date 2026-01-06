# Bandwidth Optimization

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

This document defines **bandwidth optimization strategies** for intermittent and constrained sites. Optimization reduces bandwidth consumption while maintaining deployment reliability.

**Design Principle**: Offline is First-Class — bandwidth optimization for constrained sites.

---

## Windows Optimization

### Delivery Optimization

**Default**: Enabled for all Intune deployments  
**Mechanism**: Peer-to-peer caching between devices

**Benefits**:
- Reduces WAN bandwidth usage
- Faster downloads for subsequent devices
- No additional infrastructure required

**Configuration**:
- Enabled by default in Intune
- Configurable via Group Policy
- Works automatically for Intune Win32 apps

### Microsoft Connected Cache

**Use Case**: Sites with >100 devices  
**Mechanism**: On-premises caching server

**Benefits**:
- Centralized caching at site
- Reduces WAN bandwidth significantly
- Faster downloads for all devices

**Requirements**:
- Windows Server with Delivery Optimization role
- Network connectivity to Intune
- Configuration via Intune admin center

### SCCM Distribution Points

**Use Case**: Intermittent or air-gapped sites  
**Mechanism**: Local content distribution

**Benefits**:
- No WAN bandwidth usage
- Fast local distribution
- Works offline

**Configuration**:
- SCCM DP at site
- Packages distributed to DP
- Devices download from local DP

---

## macOS Optimization

### Jamf Distribution Points

**Use Case**: Intermittent sites with Jamf  
**Mechanism**: Local content caching

**Benefits**:
- Reduces WAN bandwidth
- Faster downloads
- Works with intermittent connectivity

**Configuration**:
- Jamf DP at site
- Packages cached at DP
- Devices download from local DP

### Intune Caching

**Use Case**: Intermittent sites with Intune  
**Mechanism**: Device-side caching

**Benefits**:
- Automatic caching
- No additional infrastructure
- Works with periodic connectivity

**Limitations**:
- Less efficient than DP for large sites
- Requires periodic connectivity

---

## Linux Optimization

### APT Mirrors

**Use Case**: Intermittent or air-gapped sites  
**Mechanism**: Local APT repository mirror

**Benefits**:
- No WAN bandwidth for package downloads
- Fast local updates
- Works offline

**Configuration**:
- APT mirror at site
- Periodic sync with central repo
- Devices configured to use local mirror

### Landscape Scheduling

**Use Case**: Bandwidth-constrained sites  
**Mechanism**: Scheduled updates during off-peak hours

**Benefits**:
- Reduces peak bandwidth usage
- Scheduled during low-usage periods
- Configurable update windows

---

## Optimization Strategies by Site Class

### Online Sites

**Windows**: Delivery Optimization (default)  
**macOS**: Intune/Jamf standard caching  
**Linux**: Central APT repo (no optimization needed)

### Intermittent Sites

**Windows**: Delivery Optimization + Connected Cache (if >100 devices) or SCCM DP  
**macOS**: Jamf DP or Intune caching  
**Linux**: Site APT mirror + Landscape scheduling

### Air-Gapped Sites

**Windows**: SCCM DP (mandatory)  
**macOS**: Jamf DP via import  
**Linux**: APT mirror via import

---

## Bandwidth Monitoring

### Metrics

- **WAN Bandwidth Usage**: Total bandwidth consumed
- **Cache Hit Rate**: Percentage of requests served from cache
- **Download Times**: Average download time per device
- **Peak Usage**: Peak bandwidth usage periods

### Alerting

- **High Bandwidth Usage**: Alert if usage exceeds thresholds
- **Cache Miss Rate**: Alert if cache hit rate < 80%
- **Slow Downloads**: Alert if download times exceed thresholds

---

## Optimization Recommendations

### Small Sites (<50 devices)

- **Windows**: Delivery Optimization (default)
- **macOS**: Intune/Jamf standard caching
- **Linux**: Central APT repo

### Medium Sites (50-200 devices)

- **Windows**: Delivery Optimization + Connected Cache
- **macOS**: Jamf DP or Intune caching
- **Linux**: Site APT mirror

### Large Sites (>200 devices)

- **Windows**: Connected Cache or SCCM DP
- **macOS**: Jamf DP
- **Linux**: Site APT mirror + Landscape

---

## References

- [Site Classification](./site-classification.md)
- [Distribution Decision Matrix](./distribution-decision-matrix.md)
- [Co-Management](./co-management.md)

