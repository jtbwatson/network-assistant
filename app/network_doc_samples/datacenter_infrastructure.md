# Datacenter Infrastructure

## Overview
The company operates two datacenters in each global region (Americas, Europe, Asia, ANZ) for a total of eight datacenters worldwide. Each datacenter uses a hybrid architecture with Cisco ACI for server farms and traditional core switches for datacenter interconnection.

## Datacenter Locations

| **Region** | **DC Name** | **Location**  | **Tier** | **Primary/Secondary** |
| ---------- | ----------- | ------------- | -------- | --------------------- |
| Americas   | AM-DC1      | Virginia, USA | Tier IV  | Primary               |
| Americas   | AM-DC2      | Texas, USA    | Tier III | Secondary             |
| Europe     | EU-DC1      | Frankfurt, DE | Tier IV  | Primary               |
| Europe     | EU-DC2      | Dublin, IE    | Tier III | Secondary             |
| Asia       | AS-DC1      | Singapore     | Tier IV  | Primary               |
| Asia       | AS-DC2      | Tokyo, JP     | Tier III | Secondary             |
| ANZ        | ANZ-DC1     | Sydney, AU    | Tier III | Primary               |
| ANZ        | ANZ-DC2     | Auckland, NZ  | Tier III | Secondary             |

## Network Architecture

### Core Network Layer

| **Field**             | **Value**                                      |
| --------------------- | ---------------------------------------------- |
| **Switch Models:**    | Cisco Nexus 9336C-FX2                          |
| **Deployment:**       | Redundant pair per datacenter                  |
| **Uplinks:**          | Multiple 100G connections to WAN edge routers  |
| **Downlinks:**        | 100G connections to ACI fabric and aggregation |
| **Routing Protocol:** | OSPF within DC; BGP between DCs and to WAN     |
| **VLAN Trunking:**    | Limited to infrastructure VLANs only           |

#### Core Layer Configuration Details
- **Routing Instances:** Separate VRF for each tenant/environment
- **Quality of Service:** Strict priority for critical services
- **High Availability:** HSRP/VRRP with sub-second failover
- **Monitoring:** SNMP, NetFlow, and SolarWinds monitoring

### ACI Fabric (Server Farm)

| **Field**                | **Value**                                 |
| ------------------------ | ----------------------------------------- |
| **APIC Controllers:**    | 3 controllers per datacenter              |
| **Spine Models:**        | Cisco Nexus 9336C-FX2                     |
| **Leaf Models:**         | Cisco Nexus 93180YC-FX                    |
| **Uplinks:**             | 100G spine-to-leaf connectivity           |
| **Server Connectivity:** | 10G/25G to servers, 100G to blade chassis |
| **Fabric Protocol:**     | IS-IS (automatically configured by ACI)   |

#### ACI Physical Topology
- **Spine Switches:** 4 per datacenter
- **Leaf Switches:** 12-20 per datacenter (varies by location)
- **CLOS Architecture:** Non-blocking fabric with 4:1 oversubscription
- **Expansion Capability:** Designed for 50% growth without architecture changes

#### ACI Logical Configuration
- **Tenants:** Production, Development, QA, Management
- **Application Profiles:** Organized by business unit and application
- **Endpoint Groups (EPGs):** Logical grouping of endpoints by application tier
- **Contracts:** Define allowed traffic flows between EPGs

### Storage Network

| **Field**            | **Value**                                  |
| -------------------- | ------------------------------------------ |
| **Switch Models:**   | Cisco MDS 9710 Series                      |
| **Protocol:**        | Fibre Channel (32G)                        |
| **Deployment:**      | Dual-fabric (A/B) design for redundancy    |
| **Storage Arrays:**  | Dell EMC PowerMax, Pure Storage FlashArray |
| **Zoning Strategy:** | Single-initiator, single-target            |

#### Storage Configuration Details
- **VSAN Design:** Separate VSAN per tenant/environment
- **Zoning Format:** WWN-based (not port-based)
- **Multipathing:** PowerPath for EMC, MPIO for generic systems
- **Redundancy:** Dual-fabric connectivity for all hosts

## IP Addressing and VLAN Design

### Infrastructure IP Addressing

| **Network Purpose**   | **Subnet**  | **VLAN ID Range** | **Notes**                |
| --------------------- | ----------- | ----------------- | ------------------------ |
| Management Network    | 10.0.0.0/16 | 10-19             | OOB management only      |
| Server Infrastructure | 10.1.0.0/16 | 20-49             | Infrastructure servers   |
| Inter-DC Transit      | 10.2.0.0/16 | 50-69             | L3 transit between DCs   |
| Storage Management    | 10.3.0.0/16 | 70-79             | Storage array management |
| Backup Network        | 10.4.0.0/16 | 80-89             | Dedicated backup traffic |

### Application Environments
Each application environment (Prod, Dev, QA) has dedicated address space:

| **Environment** | **Address Space** | **VLAN ID Range** | **Notes**                |
| --------------- | ----------------- | ----------------- | ------------------------ |
| Production      | 10.10.0.0/16      | 100-499           | Production applications  |
| Development     | 10.20.0.0/16      | 500-699           | Development environments |
| QA/Testing      | 10.30.0.0/16      | 700-899           | Testing environments     |
| DMZ             | 10.40.0.0/16      | 900-999           | Internet-facing services |

## Cisco ACI Configuration

### Tenant Structure

| **Tenant Name** | **Description**                        |
| --------------- | -------------------------------------- |
| **common**      | Shared services (DNS, NTP, DHCP, etc.) |
| **prod**        | Production application workloads       |
| **dev**         | Development application workloads      |
| **qa**          | QA/Testing application workloads       |
| **infra**       | ACI infrastructure (auto-created)      |
| **mgmt**        | Management functions (auto-created)    |

### Application Profiles
Each tenant contains multiple Application Profiles:

| **Application Profile** | **Purpose**                                 |
| ----------------------- | ------------------------------------------- |
| **Core-Services**       | Infrastructure services for the environment |
| **ERP-System**          | ERP application components                  |
| **CRM-System**          | CRM application components                  |
| **Data-Analytics**      | Analytics platform components               |
| **Web-Apps**            | Web applications                            |

### Example EPG Configuration
For a typical 3-tier application:

| **EPG Name** | **Function**        | **Contract Consumption** |
| ------------ | ------------------- | ------------------------ |
| **WebTier**  | Web servers         | Provides: web-service    |
|              |                     | Consumes: app-api        |
| **AppTier**  | Application servers | Provides: app-api        |
|              |                     | Consumes: database       |
| **DBTier**   | Database servers    | Provides: database       |
|              |                     | Consumes: -              |

### Micro-Segmentation Strategy
- **Production:** Full micro-segmentation with specific contracts
- **Development:** More permissive with broader contracts
- **QA/Testing:** Limited segmentation, focused on environment isolation

## Server Connectivity

### Standard Server Connectivity

| **Server Type**              | **Connectivity**                             | **Teaming Mode**        |
| ---------------------------- | -------------------------------------------- | ----------------------- |
| **Standard Rack Servers**    | 2x 10G (separate leaf switches)              | Active/Active with LACP |
| **High-Performance Servers** | 4x 25G (separate leaf switches)              | Active/Active with LACP |
| **Blade Servers**            | 2x 100G per chassis (separate leaf switches) | vPC to chassis          |

### Network Interface Configurations

| **Operating System** | **Teaming Configuration**              | **Notes**               |
| -------------------- | -------------------------------------- | ----------------------- |
| **Windows Server**   | LBFO teams with Dynamic load balancing | Hyper-V hosts use SET   |
| **Linux**            | Bonding with mode 4 (802.3ad)          | Requires LACP on switch |
| **VMware ESXi**      | vDS with Route based on IP hash        | dvUplink active/active  |

## Virtualization Networking

### VMware Infrastructure

| **Component**            | **Configuration**                             |
| ------------------------ | --------------------------------------------- |
| **Virtual Switch:**      | VMware Distributed Switch (VDS)               |
| **Network I/O Control:** | Enabled with resource allocation              |
| **Load Balancing:**      | Route based on physical NIC load              |
| **Security Policy:**     | Strict - reject MAC changes, forged transmits |
| **Traffic Shaping:**     | Applied to vMotion and backup traffic         |

### Standard Virtual Networks

| **Network Name**  | **Purpose**            | **VLAN/PVLAN**         |
| ----------------- | ---------------------- | ---------------------- |
| **VM-Production** | Production VM traffic  | Multiple (see IP plan) |
| **vMotion**       | VMware vMotion traffic | 3001                   |
| **iSCSI-Storage** | iSCSI storage traffic  | 3002, 3003             |
| **Backup**        | VM backup traffic      | 3004                   |
| **Management**    | ESXi management        | 10                     |

## Load Balancing

### F5 Load Balancers

| **Field**               | **Value**                          |
| ----------------------- | ---------------------------------- |
| **Models:**             | F5 BIG-IP i7800                    |
| **Deployment:**         | Active/Standby pair per datacenter |
| **Interface Speed:**    | 40G interfaces to leaf switches    |
| **Virtual Server IPs:** | From dedicated load balancer pools |

### Standard Load Balancer Configuration

| **Application Type** | **LB Method**     | **Health Monitor**             | **Persistence** |
| -------------------- | ----------------- | ------------------------------ | --------------- |
| **Web Applications** | Least Connections | HTTP GET with content match    | Cookie Insert   |
| **API Services**     | Round Robin       | HTTPS GET with JSON validation | None            |
| **Database**         | Least Connections | TCP half-open                  | Source Address  |

## Datacenter Interconnect

### DCI Configuration

| **Field**                 | **Value**                            |
| ------------------------- | ------------------------------------ |
| **Technology:**           | VXLAN with MP-BGP EVPN               |
| **Transport:**            | Private MPLS with redundant circuits |
| **Capacity:**             | 2x 100G per datacenter pair          |
| **Latency Requirements:** | <5ms for regional DC pairs           |

### Extended VLANs/Networks
Only specific VLANs are extended between paired datacenters:

| **VLAN Purpose**          | **Extended** | **Notes**                    |
| ------------------------- | ------------ | ---------------------------- |
| **Database Clusters**     | Yes          | For database synchronization |
| **Application Clusters**  | Yes          | For application HA           |
| **Standard Applications** | No           | Separate instances per DC    |
| **Management Network**    | Yes          | For centralized management   |

## Disaster Recovery

### DR Capabilities

| **Service Tier**       | **RTO**    | **RPO**    | **DR Strategy**                 |
| ---------------------- | ---------- | ---------- | ------------------------------- |
| **Tier 1 (Critical)**  | 15 minutes | Near zero  | Active/Active multi-DC          |
| **Tier 2 (Important)** | 4 hours    | 15 minutes | Active/Standby with replication |
| **Tier 3 (Standard)**  | 24 hours   | 24 hours   | Backup-based recovery           |

### Data Replication Methods

| **Technology**                | **Used For**            | **Configuration**              |
| ----------------------------- | ----------------------- | ------------------------------ |
| **Storage Array Replication** | Tier 1 & 2 applications | Synchronous for Tier 1         |
|                               |                         | Asynchronous for Tier 2        |
| **Database Replication**      | Critical databases      | Always-On Availability Groups  |
| **Backup Software**           | Tier 3 applications     | Daily full, hourly incremental |

## Network Security

### Datacenter Firewalls

| **Field**            | **Value**                      |
| -------------------- | ------------------------------ |
| **Firewall Models:** | Palo Alto PA-7000 Series       |
| **Deployment:**      | Active/Active pairs with HA    |
| **Interface Speed:** | 100G to core layer             |
| **Inspection:**      | Layer 7 with threat prevention |

### Segmentation Strategy

| **Zone**            | **Description**                       | **Default Policy**              |
| ------------------- | ------------------------------------- | ------------------------------- |
| **Internet-Facing** | DMZ services accessible from internet | Explicit permit with inspection |
| **Production**      | Production application environments   | Implicit deny between segments  |
| **Development**     | Development environments              | More permissive within zone     |
| **Management**      | Infrastructure management             | Strictly controlled access      |

### Security Services

| **Service**         | **Implementation**                | **Notes**                        |
| ------------------- | --------------------------------- | -------------------------------- |
| **IPS/IDS**         | Integrated in Palo Alto firewalls | All inter-zone traffic inspected |
| **WAF**             | F5 Advanced WAF                   | For internet-facing applications |
| **Anti-Malware**    | Integrated in Palo Alto firewalls | All internet traffic scanned     |
| **DDoS Protection** | "SecureEdge Cloud" DDoS service   | For internet-facing services     |

## Troubleshooting Common Issues

### ACI Fabric Issues
1. **Endpoint Reachability**
   - Check endpoint registration in APIC
   - Verify EPG assignment and contract configuration
   - Check leaf switch port status
   - Verify encapsulation (VLAN) configuration

2. **Contract/Policy Issues**
   - Review contract configuration between source and destination EPGs
   - Check filter entries for correct protocol/ports
   - Verify contract application direction (provider/consumer)
   - Use Atomic Counter and Latency statistics for verification

### Storage Connectivity Issues
1. **Fibre Channel Connectivity**
   - Check physical connectivity and SFP status
   - Verify zoning configuration
   - Check for fabric isolation or segmentation
   - Review storage array LUN masking

2. **iSCSI Connectivity**
   - Verify network connectivity between initiator and target
   - Check VLAN configuration and routing
   - Verify iSCSI initiator and target configuration
   - Review multipathing configuration

### Virtualization Networking Issues
1. **VM Connectivity**
   - Check virtual switch configuration
   - Verify port group VLAN settings
   - Check physical uplink status
   - Review teaming and failover configuration

## Support Information

### Datacenter Network Team
- **Email**: datacenter-network@corp.local
- **Phone**: ext. 5300
- **Ticket System**: IT Service Desk - Category: Network > Datacenter

### Vendor Support Contacts
- **Cisco TAC**: 1-800-553-2447
- **Cisco ACI Specialized Support**: 1-800-553-2447, Option 4
- **F5 Support**: 1-888-882-7535
- **Palo Alto Networks**: 1-866-898-9087