---
site_id: paris
region: emea
site_code: PAR01
address: "114 Rue Ambroise Croizat, 93200 Saint-Denis"
coordinates: [48.9360, 2.3574]
connected_sites: [london, madrid]
primary_contact: "Sophie Laurent"
primary_contact_email: "sophie.laurent@company.com"
primary_contact_phone: "+33-1-84-95-6789"
last_audit: "2024-09-10"
---

# Paris Office (PAR01)

## Overview
EMEA regional headquarters serving the French and Central European markets. Houses sales, marketing, customer support, and regional administration teams. Connected to London data center for primary services.

## Network Topology

### Internet Connectivity
- **Primary ISP**: Orange Business (1 Gbps)
  - Circuit ID: OBS-PAR-34721
  - Handoff: 1000Base-LX
  - Router: par-edge-01
- **Secondary ISP**: SFR Business (500 Mbps)
  - Circuit ID: SFR-FR-56123
  - Handoff: 1000Base-T
  - Router: par-edge-02

### Core Infrastructure
- **Core Switches**: 
  - par-core-01 (Cisco Catalyst 9500)
  - par-core-02 (Cisco Catalyst 9500)

### Access Layer
- **Floor 3**:
  - par-access-3a (Cisco Catalyst 9200)
  - par-access-3b (Cisco Catalyst 9200)
- **Floor 4**:
  - par-access-4a (Cisco Catalyst 9200)
  - par-access-4b (Cisco Catalyst 9200)
- **Floor 5**:
  - par-access-5a (Cisco Catalyst 9200)
  - par-access-5b (Cisco Catalyst 9200)

### Wireless
- **Controller**: par-wlc-01 (Cisco 9800)
- **Access Points**: 45x Cisco 9120AX

## IP Addressing

### Management Network
- **Subnet**: 10.500.0.0/24
- **VLAN**: 500
- **Gateway**: 10.500.0.1

### User Networks
- **Staff**: 10.501.0.0/23 (VLAN 501)
- **Guest**: 10.502.0.0/24 (VLAN 502)
- **Voice**: 10.503.0.0/24 (VLAN 503)
- **IoT/Building Systems**: 10.504.0.0/24 (VLAN 504)

### WAN Links
- **Paris → London**: 172.16.12.0/30
- **Paris → Madrid**: 172.16.12.4/30

## Emergency Procedures

### Power Failure
1. Verify UPS operation (20-minute runtime for network equipment)
2. Contact building management at +33-1-84-95-8765
3. Notify London NOC for service failover

### Network Outage
1. Check edge router connectivity
2. Verify uplink status to London
3. Contact EMEA NOC at +44-20-7946-1234

## Maintenance History

| Date       | Description                       | Performed By | Notes                               |
|------------|-----------------------------------|--------------|-------------------------------------|
| 2024-09-05 | Switch stack firmware upgrade     | E. Dubois    | Updated to IOS-XE 17.9.3            |
| 2024-08-10 | Wireless network expansion        | Network Team | Added 15 new APs for floor 5        |
| 2024-07-22 | Voice system upgrade              | Voice Team   | Migrated to new call manager        |

## Common Issues

### Meeting Room 4B Wi-Fi Coverage
**Symptoms**: Users report poor Wi-Fi in large conference room on floor 4
**Resolution**: Additional AP installed (par-ap-4-conf) on 2024-08-15, monitoring

### VoIP Quality to Madrid Office
**Symptoms**: Occasional voice quality issues on calls to Madrid office
**Resolution**: QoS policies updated on 2024-09-01, direct SIP trunk under consideration