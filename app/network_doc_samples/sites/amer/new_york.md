---
site_id: new_york
region: amer
site_code: NYC01
address: "111 8th Ave, New York, NY 10011"
coordinates: [40.7412, -74.0018]
connected_sites: [chicago, houston, london]
primary_contact: "Sarah Martinez"
primary_contact_email: "sarah.martinez@company.com"
primary_contact_phone: "+1-212-555-6789"
last_audit: "2024-09-22"
---

# New York Campus (NYC01)

## Overview
Corporate headquarters with three connected buildings forming our East Coast campus. Houses executive offices, sales, marketing, and regional engineering teams. Connected directly to Chicago datacenter for primary services.

## Network Topology

### Internet Connectivity
- **Primary ISP**: Verizon FiOS Business (2 Gbps)
  - Circuit ID: VZW-NYC-45698
  - Handoff: 1000Base-LX
  - Router: nyc-edge-01
- **Secondary ISP**: Spectrum Business (1 Gbps)
  - Circuit ID: SPE-NY-78204
  - Handoff: 1000Base-LX
  - Router: nyc-edge-02

### Campus Infrastructure
- **Building A Core**:
  - nyc-core-a01 (Cisco Catalyst 9500)
  - nyc-core-a02 (Cisco Catalyst 9500)
- **Building B Core**:
  - nyc-core-b01 (Cisco Catalyst 9500)
  - nyc-core-b02 (Cisco Catalyst 9500)
- **Building C Core**:
  - nyc-core-c01 (Cisco Catalyst 9500)

### Access Layer
- **Building A**: 12x Cisco Catalyst 9200 switches
- **Building B**: 8x Cisco Catalyst 9200 switches
- **Building C**: 5x Cisco Catalyst 9200 switches

### Wireless
- **Controllers**: 
  - nyc-wlc-01 (Cisco 9800)
  - nyc-wlc-02 (Cisco 9800)
- **Access Points**: 85x Cisco 9130AX (distributed across campus)

## IP Addressing

### Management Network
- **Subnet**: 10.200.0.0/24
- **VLAN**: 200
- **Gateway**: 10.200.0.1

### User Networks
- **Staff**: 10.201.0.0/22 (VLAN 201)
- **Guest**: 10.202.0.0/24 (VLAN 202)
- **Voice**: 10.203.0.0/24 (VLAN 203)
- **IoT/Building Systems**: 10.204.0.0/24 (VLAN 204)

### WAN Links
- **New York → Chicago**: 172.16.2.0/30
- **New York → London**: 172.16.2.4/30
- **New York → Houston**: 172.16.2.8/30

## Emergency Procedures

### Building Power Failure
1. Verify UPS operation (30-minute runtime for network equipment)
2. Contact building management at +1-212-555-9876
3. Notify Chicago NOC for service failover

### Network Outage
1. Check edge router connectivity
2. Verify uplink status to Chicago
3. Contact NOC at +1-888-555-1234

## Maintenance History

| Date       | Description                       | Performed By | Notes                               |
|------------|-----------------------------------|--------------|-------------------------------------|
| 2024-09-20 | Wireless controller upgrade      | N. Chen      | Updated to IOS-XE 17.9.3            |
| 2024-08-05 | Added 10 new APs to Building B   | K. Johnson   | Floor 9-12 expansion                |
| 2024-06-12 | Increased Verizon circuit to 2G  | ISP          | Previously 1G                       |

## Common Issues

### Wireless Connectivity in Building C Conference Rooms
**Symptoms**: Users report intermittent connectivity in large conference spaces
**Resolution**: Adding additional APs in Q4 2024, currently recommend hardwired connections for presentations

### VoIP Quality Issues During Peak Hours
**Symptoms**: Call quality degradation between 1-3PM
**Resolution**: QoS reconfigured on core switches (2024-07-15), monitoring for improvement