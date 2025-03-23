---
site_id: madrid
region: emea
site_code: MAD01
address: "Calle de Albasanz, 16, 28037 Madrid"
coordinates: [40.4320, -3.6260]
connected_sites: [london, paris]
primary_contact: "Elena Rodriguez"
primary_contact_email: "elena.rodriguez@company.com"
primary_contact_phone: "+34-91-123-4567"
last_audit: "2024-08-18"
---

# Madrid Office (MAD01)

## Overview
Regional office serving the Spanish and Portuguese markets. Houses sales, technical support, and a small development team focused on localization. Connected to London data center for primary services with secondary connection to Paris office.

## Network Topology

### Internet Connectivity
- **Primary ISP**: Telefonica (500 Mbps)
  - Circuit ID: TEF-MAD-54376
  - Handoff: 1000Base-T
  - Router: mad-edge-01
- **Secondary ISP**: Orange España (250 Mbps)
  - Circuit ID: OBS-ES-87612
  - Handoff: 1000Base-T
  - Router: mad-edge-02

### Core Infrastructure
- **Core Switch**: 
  - mad-core-01 (Cisco Catalyst 9500)
  - mad-core-02 (Cisco Catalyst 9500)

### Access Layer
- **Floor 2**:
  - mad-access-2a (Cisco Catalyst 9200)
  - mad-access-2b (Cisco Catalyst 9200)
- **Floor 3**:
  - mad-access-3a (Cisco Catalyst 9200)

### Wireless
- **Controller**: mad-wlc-01 (Cisco 9800-CL virtual)
- **Access Points**: 22x Cisco 9120AX

## IP Addressing

### Management Network
- **Subnet**: 10.600.0.0/24
- **VLAN**: 600
- **Gateway**: 10.600.0.1

### User Networks
- **Staff**: 10.601.0.0/24 (VLAN 601)
- **Guest**: 10.602.0.0/24 (VLAN 602)
- **Voice**: 10.603.0.0/24 (VLAN 603)
- **Development**: 10.604.0.0/24 (VLAN 604)

### WAN Links
- **Madrid → London**: 172.16.13.0/30
- **Madrid → Paris**: 172.16.13.4/30

## Emergency Procedures

### Power Failure
1. Verify UPS operation (15-minute runtime for network equipment)
2. Contact building management at +34-91-123-9876
3. Notify London NOC for service failover

### Network Outage
1. Check edge router connectivity
2. Verify uplink status to London and Paris
3. Contact EMEA NOC at +44-20-7946-1234

## Maintenance History

| Date       | Description                       | Performed By | Notes                               |
|------------|-----------------------------------|--------------|-------------------------------------|
| 2024-08-15 | Core switch firmware upgrade      | J. Sanchez   | Updated to IOS-XE 17.9.3            |
| 2024-07-20 | Added development network segment | Dev Team     | New VLAN 604 with secure access     |
| 2024-06-10 | Migrated to virtual WLC          | Network Team | Moved from physical to 9800-CL      |

## Common Issues

### Building HVAC Interference
**Symptoms**: Wi-Fi interference on 2.4GHz near central air handlers
**Resolution**: Reconfigured APs to use 5GHz only in affected areas, installed extra AP

### VPN Connectivity for Remote Developers
**Symptoms**: Remote developers report unstable VPN connections to development servers
**Resolution**: Split-tunnel VPN configuration deployed on 2024-07-25, monitoring