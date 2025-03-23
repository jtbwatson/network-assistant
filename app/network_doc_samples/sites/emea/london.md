---
site_id: london
region: emea
site_code: LON01
address: "1 Braham Street, London E1 8EP"
coordinates: [51.5142, -0.0730]
connected_sites: [paris, madrid, new_york, chicago]
primary_contact: "James Wilson"
primary_contact_email: "james.wilson@company.com"
primary_contact_phone: "+44-20-7946-0123"
last_audit: "2024-10-05"
---

# London Data Center (LON01)

## Overview
Primary EMEA region data center facility. Tier 3 design with 2N power redundancy and N+1 cooling. Main hub for European operations with direct connectivity to Paris and Madrid offices as well as transatlantic links to US data centers.

## Network Topology

### Internet Connectivity
- **Primary ISP**: BT Business (10 Gbps)
  - Circuit ID: BT-LON-78543
  - Handoff: 10GBase-LR
  - Router: lon-edge-01
- **Secondary ISP**: Vodafone (5 Gbps)
  - Circuit ID: VF-UK-92367
  - Handoff: 10GBase-LR
  - Router: lon-edge-02

### Core Infrastructure
- **Core Switches**: 
  - lon-core-01 (Cisco Nexus 9336C-FX2)
  - lon-core-02 (Cisco Nexus 9336C-FX2)
  - Configured as VPC pair

### Distribution Layer
- **Pod A**:
  - lon-dist-a01 (Cisco Nexus 93180YC-FX)
  - lon-dist-a02 (Cisco Nexus 93180YC-FX)
- **Pod B**:
  - lon-dist-b01 (Cisco Nexus 93180YC-FX)
  - lon-dist-b02 (Cisco Nexus 93180YC-FX)

### Server Access Layer
- 8x Cisco Nexus 93108TC-FX (2 per rack)

## IP Addressing

### Management Network
- **Subnet**: 10.400.0.0/24
- **VLAN**: 400
- **Gateway**: 10.400.0.1

### Server Networks
- **Production**: 10.401.0.0/20 (VLAN 401)
- **Development**: 10.402.0.0/20 (VLAN 402)
- **Backup**: 10.403.0.0/24 (VLAN 403)
- **DMZ**: 10.404.0.0/24 (VLAN 404)

### WAN Links
- **London → Paris**: 172.16.10.0/30
- **London → Madrid**: 172.16.10.4/30
- **London → New York**: 172.16.11.0/30
- **London → Chicago**: 172.16.11.4/30

## Emergency Procedures

### Power Failure
1. Verify generator operation (should auto-start within 10 seconds)
2. Contact facility management at +44-20-7946-8888
3. If extended outage, monitor transition to generator power

### Network Outage
1. Check edge router connectivity
2. Verify ISP status via provider portals
3. Contact EMEA NOC at +44-20-7946-1234

## Maintenance History

| Date       | Description                       | Performed By | Notes                               |
|------------|-----------------------------------|--------------|-------------------------------------|
| 2024-10-01 | Core switch firmware upgrade      | A. Thompson  | Updated to NX-OS 10.2(3)            |
| 2024-09-15 | Added new storage network         | Storage Team | New VLAN 409 for SAN expansion      |
| 2024-08-20 | Increased BT circuit to 10 Gbps   | BT           | Upgraded from 5 Gbps                |

## Common Issues

### Transatlantic Link Latency Spikes
**Symptoms**: Periodic latency increases to US data centers during peak hours
**Resolution**: Working with providers to optimize routing, considering tertiary link

### Pod B Power Monitoring
**Symptoms**: UPS for Pod B occasionally reports calibration warnings
**Resolution**: UPS scheduled for replacement in Q4 2024, monitoring weekly