---
site_id: chicago
region: amer
site_code: CHI01
address: "350 E Cermak Rd, Chicago, IL 60616"
coordinates: [41.8534, -87.6183]
connected_sites: [new_york, houston, denver]
primary_contact: "Alex Johnson"
primary_contact_email: "alex.johnson@company.com"
primary_contact_phone: "+1-312-555-0123"
last_audit: "2024-09-15"
---

# Chicago Data Center (CHI01)

## Overview
Primary data center facility for the Midwest region. Tier 3 facility with redundant power and cooling. Houses core routing infrastructure and regional services.

## Network Topology

### Internet Connectivity
- **Primary ISP**: AT&T Business Fiber (10 Gbps)
  - Circuit ID: ATT-CHI-83927
  - Handoff: 10GBase-LR
  - Router: chi-edge-01
- **Secondary ISP**: Comcast Business (5 Gbps)
  - Circuit ID: CMC-IL-14572
  - Handoff: 10GBase-LR
  - Router: chi-edge-02

### Core Infrastructure
- **Core Switches**: 
  - chi-core-01 (Cisco Nexus 9336C-FX2)
  - chi-core-02 (Cisco Nexus 9336C-FX2)
  - Configured as VPC pair

### Distribution Layer
- **Pod A**:
  - chi-dist-a01 (Arista 7050X3)
  - chi-dist-a02 (Arista 7050X3)
- **Pod B**:
  - chi-dist-b01 (Arista 7050X3)
  - chi-dist-b02 (Arista 7050X3)

## IP Addressing

### Management Network
- **Subnet**: 10.100.0.0/24
- **VLAN**: 100
- **Gateway**: 10.100.0.1
- **DHCP Range**: 10.100.0.50-10.100.0.200

### Server Networks
- **Production**: 10.101.0.0/20 (VLAN 101)
- **Development**: 10.102.0.0/20 (VLAN 102)
- **Backup**: 10.103.0.0/24 (VLAN 103)

### WAN Links
- **Chicago → New York**: 172.16.1.0/30
- **Chicago → Houston**: 172.16.1.4/30
- **Chicago → Denver**: 172.16.1.8/30

## Emergency Procedures

### Power Failure
1. Verify generator operation (should auto-start within 15 seconds)
2. Contact facility management at +1-312-555-9876
3. If extended outage, initiate DR plan in Houston

### Network Outage
1. Check edge router connectivity
2. Verify ISP status via provider portals
3. Contact NOC at +1-888-555-1234

## Maintenance History

| Date       | Description                       | Performed By | Notes                               |
|------------|-----------------------------------|--------------|-------------------------------------|
| 2024-09-01 | Core switch firmware upgrade      | T. Williams  | Completed during maintenance window |
| 2024-08-15 | Added 2x new racks                | Datacenter   | Added to Pod B                      |
| 2024-07-22 | Increased AT&T circuit to 10 Gbps | ISP          | Upgraded from 5 Gbps                |

## Common Issues

### Intermittent Connectivity to Houston
**Symptoms**: Packet loss between Chicago and Houston sites, typically during high traffic periods
**Resolution**: Increased QoS allocation for critical traffic, monitoring for recurrence

### Access Switch chi-acc-b03 Reboots
**Symptoms**: Switch in rack B03-B05 occasionally reboots
**Resolution**: Replaced power supply on 2024-08-10, monitoring for recurrence