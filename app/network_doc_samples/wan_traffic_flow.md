# WAN Traffic

## Overview
The company's WAN infrastructure primarily uses MPLS with some point-to-point links for critical sites. All sites have redundant WAN connectivity through diverse carriers and paths to ensure business continuity.

## WAN Connectivity Types

### MPLS Network

| **Field**              | **Value**                                      |
| ---------------------- | ---------------------------------------------- |
| **Primary Carrier:**   | GlobeConnect                                   |
| **Secondary Carrier:** | NetwayLink                                     |
| **Service Type:**      | Layer 3 MPLS VPN                               |
| **Global Coverage:**   | All company locations                          |
| **QoS Support:**       | End-to-end QoS with 6 service classes          |
| **Redundancy:**        | Dual-homed at each location                    |
| **CoS Preservation:**  | DSCP-based markings preserved across MPLS core |
| **Monitoring:**        | Carrier and internal SolarWinds monitoring     |

#### MPLS Service Classes

| **Class Name**       | **Traffic Type**                    | **DSCP Values**  | **Priority**    |
| -------------------- | ----------------------------------- | ---------------- | --------------- |
| **Realtime**         | Voice, video conferencing           | EF               | Strict Priority |
| **Interactive**      | Interactive applications, signaling | CS3, AF31        | High            |
| **Mission Critical** | ERP, CRM, critical applications     | AF31, AF32, AF33 | Medium-High     |
| **Business Data**    | Standard business applications      | AF21, AF22, AF23 | Medium          |
| **General Data**     | Email, file transfers, web browsing | AF11, AF12, AF13 | Low             |
| **Best Effort**      | Internet traffic, backups           | Default          | Best Effort     |

### Point-to-Point Links

| **Field**              | **Value**                                              |
| ---------------------- | ------------------------------------------------------ |
| **Service Type:**      | Carrier Ethernet (Metro Ethernet, VPLS)                |
| **Used For:**          | Critical datacenter interconnections, Campus-to-Campus |
| **Bandwidth:**         | 1-10 Gbps depending on location                        |
| **Latency Guarantee:** | <5ms round-trip for metro, <30ms for regional          |
| **Redundancy:**        | Diverse carrier and physically diverse routes          |
| **Monitoring:**        | Proactive monitoring with SNMP and NetFlow             |

#### Key Point-to-Point Links

| **Connection**             | **Bandwidth** | **Primary Carrier** | **Secondary Carrier** | **Notes**               |
| -------------------------- | ------------- | ------------------- | --------------------- | ----------------------- |
| **AM-DC1 to AM-DC2**       | 10 Gbps       | GlobeConnect        | NetwayLink            | Datacenter interconnect |
| **EU-DC1 to EU-DC2**       | 10 Gbps       | GlobeConnect        | NetwayLink            | Datacenter interconnect |
| **AS-DC1 to AS-DC2**       | 10 Gbps       | GlobeConnect        | NetwayLink            | Datacenter interconnect |
| **ANZ-DC1 to ANZ-DC2**     | 5 Gbps        | GlobeConnect        | NetwayLink            | Datacenter interconnect |
| **NY to DC Campus**        | 5 Gbps        | GlobeConnect        | NetwayLink            | Campus interconnect     |
| **Frankfurt to Berlin**    | 2 Gbps        | GlobeConnect        | NetwayLink            | Campus interconnect     |
| **Singapore to Bangalore** | 1 Gbps        | GlobeConnect        | NetwayLink            | Office interconnect     |

## WAN Architecture

### Site Classifications

| **Site Type**     | **Criteria**                      | **WAN Connectivity**         | **Count** |
| ----------------- | --------------------------------- | ---------------------------- | --------- |
| **Datacenter**    | Core infrastructure site          | 2x10 Gbps MPLS + 10 Gbps P2P | 8         |
| **Regional HQ**   | >1000 users, regional main office | 2x1 Gbps MPLS                | 4         |
| **Large Office**  | 250-1000 users                    | 2x500 Mbps MPLS              | 15        |
| **Medium Office** | 50-250 users                      | 2x100 Mbps MPLS              | 30        |
| **Small Office**  | 10-50 users                       | 2x50 Mbps MPLS               | 45        |
| **Micro Office**  | <10 users                         | 2x20 Mbps MPLS               | 25        |

### WAN Edge Infrastructure

| **Site Type**     | **Router Models**     | **Deployment**                    | **Additional Features**      |
| ----------------- | --------------------- | --------------------------------- | ---------------------------- |
| **Datacenter**    | Cisco ASR 1000 Series | Dual routers with redundant links | Full BGP, HSRP, advanced QoS |
| **Regional HQ**   | Cisco ASR 1000 Series | Dual routers with redundant links | Full BGP, HSRP, advanced QoS |
| **Large Office**  | Cisco ISR 4451        | Dual routers with redundant links | BGP/OSPF, HSRP, QoS          |
| **Medium Office** | Cisco ISR 4431        | Dual routers with redundant links | OSPF, HSRP, QoS              |
| **Small Office**  | Cisco ISR 4331        | Dual routers with redundant links | OSPF, HSRP, QoS              |
| **Micro Office**  | Cisco ISR 4321        | Dual routers with redundant links | OSPF, HSRP, basic QoS        |

### WAN Routing Design

| **Field**                | **Value**                                   |
| ------------------------ | ------------------------------------------- |
| **Internal Routing:**    | OSPF within site hierarchies                |
| **External Routing:**    | BGP between regions and to MPLS carriers    |
| **Route Summarization:** | Implemented at regional and site boundaries |
| **Default Routes:**      | Conditional default routing with backups    |
| **Failure Detection:**   | BFD enabled for fast convergence            |

#### BGP Configuration Standards

| **Parameter**         | **Configuration**                                            |
| --------------------- | ------------------------------------------------------------ |
| **AS Numbering:**     | Private AS per region (Americas: 65001, Europe: 65002, etc.) |
| **iBGP Peering:**     | Full mesh within each region                                 |
| **Route Reflectors:** | Deployed in each regional datacenter                         |
| **Communities:**      | Used to control route distribution and preference            |
| **Filters:**          | Prefix lists and AS path filters at external boundaries      |
| **Attributes:**       | Local preference for path preference                         |

## Traffic Flow Patterns

### Regional Traffic Flows

| **Traffic Type**         | **Flow Pattern**                                      | **Routing Control**                    |
| ------------------------ | ----------------------------------------------------- | -------------------------------------- |
| **Intra-Site Traffic**   | Local switching and routing within site               | Local switching at access/distribution |
| **Intra-Region Traffic** | Direct path over regional MPLS backbone               | Regional OSPF/BGP                      |
| **Inter-Region Traffic** | Via regional datacenters                              | BGP with route reflectors              |
| **Datacenter Access**    | Direct path over MPLS to nearest regional DC          | MPLS with QoS                          |
| **Internet Access**      | Via nearest datacenter (or local breakout if enabled) | Default routing with backup paths      |

### Traffic Flow Diagram
```
                    +----------------+
                    | Internet Edge  |
                    +----------------+
                            ^
                            |
                    +----------------+     +----------------+
                    | Regional DC-A  |<--->| Regional DC-B  |
                    +----------------+     +----------------+
                     ^      ^     ^         ^      ^     ^
                     |      |     |         |      |     |
          +----------+      |     +------+  |      |     +----------+
          |                 |            |  |      |                |
+-----------------+ +----------------+ +-----------------+ +----------------+
| Regional HQ-A1  | | Regional HQ-A2 | | Regional HQ-B1  | | Regional HQ-B2 |
+-----------------+ +----------------+ +-----------------+ +----------------+
     ^      ^           ^      ^           ^      ^           ^      ^
     |      |           |      |           |      |           |      |
+--------+ +--------+ +--------+ +--------+ +--------+ +--------+ +--------+ +--------+
| Office | | Office | | Office | | Office | | Office | | Office | | Office | | Office |
+--------+ +--------+ +--------+ +--------+ +--------+ +--------+ +--------+ +--------+
```

### Regional Datacenter Connectivity

| **Connection**        | **Bandwidth** | **Primary Routing** | **Backup Route**  |
| --------------------- | ------------- | ------------------- | ----------------- |
| **AM-DC1 to EU-DC1**  | 1 Gbps        | Direct MPLS path    | Secondary carrier |
| **AM-DC1 to AS-DC1**  | 500 Mbps      | Direct MPLS path    | Secondary carrier |
| **AM-DC1 to ANZ-DC1** | 500 Mbps      | Direct MPLS path    | Secondary carrier |
| **EU-DC1 to AS-DC1**  | 500 Mbps      | Direct MPLS path    | Secondary carrier |
| **EU-DC1 to ANZ-DC1** | 500 Mbps      | Direct MPLS path    | Secondary carrier |
| **AS-DC1 to ANZ-DC1** | 500 Mbps      | Direct MPLS path    | Secondary carrier |

## Path Selection and Failover

### Path Selection Mechanisms

| **Scenario**               | **Primary Method**                           | **Backup Method**              |
| -------------------------- | -------------------------------------------- | ------------------------------ |
| **Multiple MPLS Carriers** | BGP path selection based on local preference | BFD-triggered failover         |
| **MPLS + Internet Backup** | Policy-based routing with SLA monitoring     | BFD-triggered failover         |
| **Point-to-Point Links**   | EIGRP with best path selection               | Dynamic rerouting via MPLS     |
| **Load Distribution**      | Per-flow load balancing where possible       | Per-destination load balancing |

### Failover Timing

| **Connection Type**         | **Detection Time** | **Convergence Time** | **Total Failover** |
| --------------------------- | ------------------ | -------------------- | ------------------ |
| **Intra-site Routing**      | <1 second          | <1 second            | <2 seconds         |
| **MPLS with BFD**           | 1-3 seconds        | 2-3 seconds          | 3-6 seconds        |
| **Point-to-Point with BFD** | <1 second          | 1-2 seconds          | 1-3 seconds        |
| **MPLS to Internet Backup** | 3-5 seconds        | 5-10 seconds         | 8-15 seconds       |

## QoS Implementation

### End-to-End QoS Strategy

| **Field**                 | **Value**                                                             |
| ------------------------- | --------------------------------------------------------------------- |
| **QoS Model:**            | Differentiated Services (DiffServ)                                    |
| **Marking Points:**       | Access edge (trusted endpoints), WAN edge routers                     |
| **Trust Boundaries:**     | Access switch ports, WAN router LAN interfaces                        |
| **Policing:**             | At WAN edge for rate enforcement                                      |
| **Shaping:**              | At WAN edge to carrier contracted rates                               |
| **Congestion Mgmt:**      | Low-Latency Queuing (LLQ) + Class-Based Weighted Fair Queuing (CBWFQ) |
| **Congestion Avoidance:** | Weighted Random Early Detection (WRED)                                |

### QoS Bandwidth Allocation (% of Link)

| **Traffic Class**           | **Datacenter** | **Regional HQ** | **Medium/Large Office** | **Small Office** |
| --------------------------- | -------------- | --------------- | ----------------------- | ---------------- |
| **Voice (EF)**              | 10%            | 10%             | 15%                     | 20%              |
| **Video (AF4x)**            | 15%            | 15%             | 15%                     | 15%              |
| **Interactive (CS3, AF3x)** | 25%            | 25%             | 25%                     | 20%              |
| **Business Data (AF2x)**    | 25%            | 25%             | 20%                     | 20%              |
| **General Data (AF1x)**     | 15%            | 15%             | 15%                     | 15%              |
| **Best Effort**             | 10%            | 10%             | 10%                     | 10%              |

### Example Router QoS Configuration

```
class-map match-all VOICE
 match dscp ef
class-map match-all VIDEO
 match dscp af41 af42 af43
class-map match-all INTERACTIVE
 match dscp cs3 af31 af32 af33
class-map match-all BUSINESS
 match dscp af21 af22 af23
class-map match-all GENERAL
 match dscp af11 af12 af13
!
policy-map WAN-EDGE
 class VOICE
  priority percent 10
 class VIDEO
  priority percent 15
 class INTERACTIVE
  bandwidth percent 25
  random-detect dscp-based
 class BUSINESS
  bandwidth percent 25
  random-detect dscp-based
 class GENERAL
  bandwidth percent 15
  random-detect dscp-based
 class class-default
  bandwidth percent 10
  random-detect
!
interface GigabitEthernet0/0/0
 description WAN CONNECTION TO CARRIER
 service-policy output WAN-EDGE
```

## WAN Security

### Security Controls

| **Control Type**             | **Implementation**                    | **Purpose**                          |
| ---------------------------- | ------------------------------------- | ------------------------------------ |
| **Traffic Encryption**       | DMVPN with IPsec over MPLS            | Added security for sensitive traffic |
| **Zone-Based Firewall**      | Configured on branch routers          | Traffic filtering between segments   |
| **Access Control Lists**     | Infrastructure ACLs on WAN interfaces | Block unauthorized access            |
| **Control Plane Protection** | CoPP on all routers                   | Protect router resources             |
| **Management Security**      | Out-of-band management where possible | Secure management access             |
| **AAA**                      | TACACS+ for all device authentication | Centralized authentication           |

### Segmentation Strategy

| **Segment Type**           | **Traffic Isolation Method**           | **Security Controls**            |
| -------------------------- | -------------------------------------- | -------------------------------- |
| **Corporate Data**         | Primary MPLS VPN                       | Standard WAN security            |
| **Guest/Internet Traffic** | Separate logical path                  | Strict filtering, no DC access   |
| **IoT/Building Systems**   | Separate MPLS VPN                      | Strict filtering, limited access |
| **Management Traffic**     | Out-of-band where possible or MPLS VPN | Strict filtering, limited access |

## Redundancy Design

### Device Redundancy

| **Site Type**     | **Router Redundancy** | **Power Redundancy**                | **Hardware Redundancy**              |
| ----------------- | --------------------- | ----------------------------------- | ------------------------------------ |
| **Datacenter**    | Active/Active pair    | Dual power supplies, UPS, Generator | Redundant line cards, supervisors    |
| **Regional HQ**   | Active/Active pair    | Dual power supplies, UPS            | Redundant components where available |
| **Large Office**  | Active/Active pair    | UPS backup                          | Selected redundant components        |
| **Medium Office** | Active/Active pair    | UPS backup                          | Basic redundancy                     |
| **Small Office**  | Active/Active pair    | UPS backup                          | No internal redundancy               |
| **Micro Office**  | Active/Active pair    | UPS backup                          | No internal redundancy               |

### Circuit Redundancy

| **Site Type**     | **Primary Circuit**          | **Secondary Circuit**      | **Additional Backup** |
| ----------------- | ---------------------------- | -------------------------- | --------------------- |
| **Datacenter**    | 10 Gbps MPLS (GlobeConnect)  | 10 Gbps MPLS (NetwayLink)  | 10 Gbps DIA internet  |
| **Regional HQ**   | 1 Gbps MPLS (GlobeConnect)   | 1 Gbps MPLS (NetwayLink)   | 1 Gbps DIA internet   |
| **Large Office**  | 500 Mbps MPLS (GlobeConnect) | 500 Mbps MPLS (NetwayLink) | 4G/LTE backup         |
| **Medium Office** | 100 Mbps MPLS (GlobeConnect) | 100 Mbps MPLS (NetwayLink) | 4G/LTE backup         |
| **Small Office**  | 50 Mbps MPLS (GlobeConnect)  | 50 Mbps MPLS (NetwayLink)  | 4G/LTE backup         |
| **Micro Office**  | 20 Mbps MPLS (GlobeConnect)  | 20 Mbps MPLS (NetwayLink)  | 4G/LTE backup         |

### First-Hop Redundancy

| **Protocol** | **Implementation**                       | **Sites Used**                      |
| ------------ | ---------------------------------------- | ----------------------------------- |
| **HSRP**     | Active/Standby with 1-second hello timer | All sites                           |
| **VRRP**     | Alternative where HSRP not supported     | Select sites with non-Cisco devices |
| **GLBP**     | For load balancing where appropriate     | Large datacenters only              |

## Monitoring and Management

### WAN Monitoring Tools

| **Tool**                | **Purpose**                        | **Key Metrics Monitored**         |
| ----------------------- | ---------------------------------- | --------------------------------- |
| **SolarWinds NPM**      | Network performance monitoring     | Availability, utilization, errors |
| **NetFlow Analyzer**    | Traffic analysis and visualization | Application usage, top talkers    |
| **Cisco IPPM**          | IP SLA monitoring                  | Latency, jitter, packet loss      |
| **Custom SNMP Scripts** | Specific metric collection         | Custom thresholds and metrics     |

### Key Performance Indicators

| **Metric**       | **Target**                                      | **Alert Threshold**          |
| ---------------- | ----------------------------------------------- | ---------------------------- |
| **Availability** | 99.99% for datacenter links, 99.9% for branches | Any outage                   |
| **Latency**      | <50ms intra-region, <150ms inter-region         | >20% deviation from baseline |
| **Jitter**       | <15ms for voice/video                           | >20ms sustained              |
| **Packet Loss**  | <0.1% for all WAN links                         | >0.5% over 5 minutes         |
| **Utilization**  | <70% normal operation                           | >85% for >15 minutes         |
| **Errors**       | <0.001% of packets                              | Any consistent errors        |

### Management Access

| **Access Method**          | **Implementation**                        | **Security Controls**                  |
| -------------------------- | ----------------------------------------- | -------------------------------------- |
| **In-band Management**     | Dedicated management VLAN/VRF             | ACLs, IPsec, SSH only                  |
| **Out-of-band Management** | Separate physical network where available | Strict ACLs, 2FA                       |
| **Emergency Access**       | Console servers with cellular backup      | Limited to network team, audit logging |
| **Change Management**      | In-house configuration management system  | Approval workflow, config validation   |

## Capacity Planning

### Capacity Management Process

| **Activity**           | **Frequency** | **Responsible Team** |
| ---------------------- | ------------- | -------------------- |
| **Utilization Review** | Weekly        | Network Operations   |
| **Trend Analysis**     | Monthly       | Network Engineering  |
| **Capacity Report**    | Quarterly     | Network Architecture |
| **Upgrade Planning**   | Semi-annually | Network Architecture |

### Growth Planning Factors

| **Site Type**           | **Annual Growth Rate** | **Upgrade Trigger Point** | **Lead Time Required** |
| ----------------------- | ---------------------- | ------------------------- | ---------------------- |
| **Datacenter**          | 25-30%                 | 70% sustained utilization | 3-6 months             |
| **Regional HQ**         | 20-25%                 | 75% sustained utilization | 2-3 months             |
| **Large Office**        | 15-20%                 | 80% sustained utilization | 1-2 months             |
| **Medium/Small Office** | 10-15%                 | 80% sustained utilization | 1 month                |

## Troubleshooting Common Issues

### Connectivity Issues
1. **Complete WAN Outage**
   - Check physical connectivity on WAN routers
   - Verify carrier circuit status
   - Check for hardware failures
   - Validate failover to backup circuits

2. **Intermittent Connectivity**
   - Check for interface errors (CRC, input/output drops)
   - Monitor for microbursts causing congestion
   - Verify BFD/routing protocol stability
   - Check for QoS misconfiguration

3. **Slow Performance**
   - Analyze bandwidth utilization trends
   - Check for QoS mismarking or congestion
   - Verify application path selection
   - Test end-to-end latency and packet loss

### Protocol Issues
1. **BGP Problems**
   - Verify BGP session state
   - Check for route advertisement/withdrawal flapping
   - Validate route policies and filters
   - Ensure consistent AS path and communities

2. **OSPF Problems**
   - Verify OSPF neighbor relationships
   - Check area configuration consistency
   - Validate LSA database synchronization
   - Monitor for MTU mismatches or duplicate router IDs

## Support Information

### WAN Operations Team
- **Email**: wan-operations@corp.local
- **Phone**: ext. 5100
- **Ticket System**: IT Service Desk - Category: Network > WAN
- **Emergency Bridge**: 1-800-555-1234, Access Code: 987654

### Carrier Support Contacts
- **GlobeConnect NOC**: 1-888-555-0100, noc@globeconnect.example.com
- **NetwayLink NOC**: 1-888-555-0200, support@netwaylink.example.com
- **Circuit Reference Numbers**:
  - Format: [Region]-[Carrier]-[Site Code]-[Circuit ID]
  - Example: AM-GC-DC1-GC12345678