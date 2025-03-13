# Wired Campus Infrastructure

## Overview
Global enterprise with collapsed core architecture using Arista switches across all campus locations.

## Campus Network Design

### Core Switches
| **Field**                 | **Value**                                         |
|---------------------------|---------------------------------------------------|
| **Model:**                | Arista 7280R2 Series                              |
| **Deployment:**           | Redundant pair per campus location                |
| **Uplinks:**              | 2x 100G connections to each distribution switch   |
| **Routing Protocol:**     | OSPF within campus; BGP for WAN connectivity      |
| **Management:**           | Out-of-band management via dedicated network      |
| **Configuration Backup:** | Daily via in-house configuration management       |

#### Core Switch Configuration Standards
- **MLAG Configuration:** Peer-link over dedicated 100G ports
- **Control Plane Policing:** Enabled to protect against DoS attacks
- **Spanning Tree:** MSTP with core switches as root bridges
- **QoS Configuration:** 8-queue model prioritizing voice and critical applications
- **VLAN Distribution:** Core switches handle all inter-VLAN routing

### Distribution Switches
| **Field**                    | **Value**                                      |
|------------------------------|------------------------------------------------|
| **Model:**                   | Arista 7050X3 Series                           |
| **Deployment:**              | Redundant pair per building or floor           |
| **Uplinks to Core:**         | 2x 100G per switch (MLAG to core pair)         |
| **Downlinks to Access:**     | 25G to access switches, redundant connections  |
| **Layer 3 Features:**        | No routing; pure Layer 2 to access layer       |
| **Spanning Tree Role:**      | Secondary root bridges                         |

#### Distribution Switch Configuration Standards
- **MLAG Configuration:** Peer-link over dedicated 25G ports
- **Port Channels:** LACP for all uplinks and downlinks
- **Storm Control:** Enabled (broadcast, multicast, unknown unicast)
- **LLDP/CDP:** Both enabled for device discovery

### Access Switches
| **Field**                    | **Value**                                      |
|------------------------------|------------------------------------------------|
| **Model:**                   | Arista 7020R Series                            |
| **Deployment:**              | Distributed throughout office spaces           |
| **Uplinks:**                 | 2x 25G to distribution layer (MLAG)            |
| **User Ports:**              | 1G/10G/25G depending on device requirements    |
| **PoE Capability:**          | PoE+ (30W) on all user ports                   |

#### Access Switch Configuration Standards
- **Port Security:** Enabled on all user ports (MAC-based)
- **DHCP Snooping:** Enabled on all user VLANs
- **Dynamic ARP Inspection:** Enabled on all user VLANs
- **802.1X Authentication:** Enabled on all user ports
- **Voice VLAN:** Automatically assigned to Cisco IP phones
- **QoS Trust Boundary:** At access switch user ports

## VLANs and IP Addressing

### Standard VLAN Configuration
| **VLAN ID** | **VLAN Name**          | **Purpose**                          | **DHCP Server**      |
|-------------|------------------------|--------------------------------------|----------------------|
| 10          | `management`           | Network device management             | 10.10.10.5          |
| 20          | `servers-local`        | Local servers at campus               | 10.20.x.5           |
| 100         | `user-data`            | Primary user workstation network      | 10.100.x.5          |
| 110         | `printers`             | Printers and multifunction devices    | 10.110.x.5          |
| 120         | `voice`                | Voice traffic (IP telephony)          | 10.120.x.5          |
| 172         | `corp-wireless`        | Corporate wireless devices            | See Wireless Doc    |
| 173         | `staff-byod`           | Staff BYOD wireless devices           | See Wireless Doc    |
| 174         | `guest`                | Guest wireless devices                | See Wireless Doc    |
| 200         | `security-systems`     | Physical security systems             | 10.200.x.5          |
| 900         | `transit`              | Transit networks between devices      | N/A (not assigned)  |

### VLAN Distribution Guidelines
- Each campus location uses a dedicated VLAN block starting at x00/x10/x20
- Local services VLAN block starts at x00
- User VLANs are in blocks of 10 (x10, x20, etc.)
- Special purpose VLANs start at x50

## QoS Configuration

### Priority Queue Assignments
| **Queue** | **Priority**  | **Traffic Type**                           | **DSCP Marking** |
|-----------|---------------|-------------------------------------------|------------------|
| 7         | Highest       | Network control (routing protocols)        | CS6, CS7         |
| 6         | Very High     | Voice RTP                                  | EF               |
| 5         | High          | Video conferencing                         | AF41, AF42, AF43 |
| 4         | Medium-High   | Call signaling                             | CS3              |
| 3         | Medium        | Critical business applications             | AF31, AF32, AF33 |
| 2         | Medium-Low    | Standard business applications             | AF21, AF22, AF23 |
| 1         | Low           | Batch applications, email                  | AF11, AF12, AF13 |
| 0         | Best Effort   | Default traffic                            | BE               |

### Traffic Marking Policies
- **Voice Traffic:** Marked as EF (DSCP 46) at IP phone
- **Video Conferencing:** Marked as AF41 (DSCP 34) at endpoint
- **Signaling Traffic:** Marked as CS3 (DSCP 24) at endpoint
- **Default User Traffic:** Untrusted, remarked based on policy

## Standard Port Configurations

### User Access Ports
```
interface Ethernet1/1
  description User Access Port
  switchport access vlan 100
  switchport mode access
  switchport voice vlan 120
  spanning-tree portfast
  spanning-tree bpduguard enable
  storm-control broadcast level 0.2
  storm-control multicast level 0.4
  storm-control unknown-unicast level 0.4
  dot1x pae authenticator
  dot1x authentication multiple-hosts
  dot1x host-mode multi-auth
  dot1x timeout server-timeout 10
  dot1x max-reauth-req 2
  service-policy input TRUST-MARKINGS
  service-policy output QOS-POLICY
```

### Printer Ports
```
interface Ethernet2/1
  description Printer Port
  switchport access vlan 110
  switchport mode access
  spanning-tree portfast
  spanning-tree bpduguard enable
  storm-control broadcast level 0.2
  storm-control multicast level 0.4
  service-policy output QOS-POLICY
```

### Server Ports
```
interface Ethernet3/1
  description Server Port
  switchport access vlan 20
  switchport mode access
  spanning-tree portfast
  no spanning-tree bpduguard enable
  service-policy output QOS-POLICY
```

### Uplink Ports
```
interface Port-Channel10
  description Uplink to Distribution Switch
  switchport mode trunk
  switchport trunk allowed vlan 10,20,100,110,120,172-174,200,900
  mlag 10
  service-policy output QOS-POLICY
```

## 802.1X Authentication

### Authentication Configuration
| **Field**                  | **Value**                                              |
|----------------------------|--------------------------------------------------------|
| **Authentication Server:** | ClearPass NAC                                          |
| **Authentication Method:** | 802.1X with EAP-TLS and MAB fallback                   |
| **Auth Failure VLAN:**     | 999 (restricted network)                               |
| **Guest VLAN:**            | Not used (guest access via wireless only)              |
| **Client Timeout:**        | 30 seconds                                             |

### Authentication Flow
1. **Device connects to wired port**
2. **Switch initiates 802.1X authentication:**
   - Switch (authenticator) sends EAP Request Identity to client
   - Client (supplicant) sends EAP Response Identity
   - Switch forwards via RADIUS to ClearPass NAC
3. **ClearPass NAC processes authentication:**
   - Checks certificate validity for EAP-TLS
   - Verifies client against AD/LDAP directory
   - Assigns appropriate authorization attributes
4. **Switch receives RADIUS Accept/Reject:**
   - On Accept: Places port in authorized VLAN
   - On Reject: Places port in Auth Failure VLAN
   - On Timeout: Falls back to MAB if configured

### Authorization Profiles
| **Profile Name**        | **Target Devices**    | **Access Level**                                 |
|-------------------------|------------------------|--------------------------------------------------|
| `corporate-workstation` | Domain-joined laptops  | Full access to corporate resources               |
| `contractor-device`     | Approved contractor PCs | Limited access (contractor-specific resources)   |
| `ip-phone`              | Cisco IP phones        | Voice VLAN access                                |
| `iot-device`            | IoT devices            | Isolated network with specific allowed services  |
| `unknown-device`        | Unknown MAC addresses  | Internet-only restricted access                  |

## Troubleshooting Common Issues

### Authentication Issues
1. Verify ClearPass NAC is reachable from network switches
2. Check certificate status for client and server certificates
3. Verify RADIUS shared secret configuration
4. Check for correct VLAN assignment in authorization profiles
5. Inspect client supplicant configuration

### Connectivity Issues
1. Verify physical connectivity (check for link status, errors, CRC errors)
2. Validate VLAN configuration on port
3. Check port security status (not in err-disabled state)
4. Verify MAC address learning and forwarding
5. Test connectivity to default gateway
6. Check for ACL or policy restrictions

### Performance Issues
1. Check port statistics for errors, discards, or collisions
2. Verify port speed and duplex settings
3. Monitor utilization on uplinks
4. Validate QoS markings and queue assignments
5. Check for broadcast storms or high multicast traffic

## Support Information

### Campus Network Engineering Team
- **Email**: campus-network@corp.local
- **Phone**: ext. 5400
- **Ticket System**: IT Service Desk - Category: Network > Campus

### Vendor Support
- Arista Support: 1-866-476-0000, support@arista.com
- Support Portal: https://www.arista.com/en/support
- TAC Case Manager: https://tac.arista.com