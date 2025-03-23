---
site_id: houston
region: amer
site_code: HOU01
address: "5555 San Felipe St, Houston, TX 77056"
coordinates: [29.7522, -95.4632]
connected_sites: [chicago, new_york]
primary_contact: "Carlos Mendez"
primary_contact_email: "carlos.mendez@company.com"
primary_contact_phone: "+1-713-555-4321"
last_audit: "2024-08-30"
---

# Houston Office (HOU01)

## Overview
Regional office serving the Southern US market with engineering, sales, and customer support teams. Secondary disaster recovery site for Chicago data center. Includes dedicated lab environment for product testing.

## Network Topology

### Internet Connectivity
- **Primary ISP**: AT&T Business Fiber (1 Gbps)
  - Circuit ID: ATT-HOU-29384
  - Handoff: 1000Base-LX
  - Router: hou-edge-01
- **Secondary ISP**: Comcast Business (500 Mbps)
  - Circuit ID: CMC-TX-38291
  - Handoff: 1000Base-T
  - Router: hou-edge-02

### Core Infrastructure
- **Core Switches**: 
  - hou-core-01 (Cisco Catalyst 9500)
  - hou-core-02 (Cisco Catalyst 9500)
  - Configured as stackwise virtual

### Access Layer
- **Office Floor 8**: 
  - hou-access-8a (Cisco Catalyst 9200)
  - hou-access-8b (Cisco Catalyst 9200)
- **Office Floor 9**: 
  - hou-access-9a (Cisco Catalyst 9200)
  - hou-access-9b (Cisco Catalyst 9200)
- **Lab Environment**:
  - hou-lab-sw01 (Cisco Catalyst 9300)
  - hou-lab-sw02 (Cisco Catalyst 9300)

### Wireless
- **Controller**: hou-wlc-01 (Cisco 9800-CL virtual)
- **Access Points**: 32x Cisco 9120AX

## IP Addressing

### Management Network
- **Subnet**: 10.300.0.0/24
- **VLAN**: 300
- **Gateway**: 10.300.0.1

### User Networks
- **Staff**: 10.301.0.0/23 (VLAN 301)
- **Guest**: 10.302.0.0/24 (VLAN 302)
- **Voice**: 10.303.0.0/24 (VLAN 303)

### Lab Networks
- **Lab General**: 10.310.0.0/23 (VLAN 310)
- **Lab Secure**: 10.311.0.0/24 (VLAN 311)
- **Lab DMZ**: 10.312.0.0/24 (VLAN 312)

### WAN Links
- **Houston → Chicago**: 172.16.3.0/30
- **Houston → New York**: 172.16.3.4/30

## Emergency Procedures

### Power Failure
1. Network equipment on UPS (15-minute runtime)
2. Contact building management at +1-713-555-8765
3. If DR failover needed, contact Chicago NOC to initiate

### Hurricane Preparedness
1. 72 hours prior: Begin monitoring weather service alerts
2. 48 hours prior: Ensure generator fuel and test DR systems
3. 24 hours prior: If evacuation ordered, initiate DR failover to Chicago

## Maintenance History

| Date       | Description                      | Performed By | Notes                               |
|------------|----------------------------------|--------------|-------------------------------------|
| 2024-08-25 | Access switch replacements       | M. Rodriguez | Floors 8-9 refresh completed        |
| 2024-07-10 | Lab network expansion            | Lab Team     | Added 10.311.0.0/24 secure segment  |
| 2024-05-05 | Wireless upgrade                 | Network Team | Migrated to 9800-CL virtual         |

## Common Issues

### Lab Environment Connectivity to Chicago
**Symptoms**: Occasional high latency to Chicago data center from lab network
**Resolution**: QoS policies implemented on 2024-08-01, monitoring for improvement

### Wireless Deadspots in Northeast Corner
**Symptoms**: Poor coverage in northeast corner offices
**Resolution**: Added AP (hou-ap-8-ne) on 2024-07-10, resolved issue