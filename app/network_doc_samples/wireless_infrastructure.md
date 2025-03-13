# Wireless Infrastructure

## SSIDs

### 1. Corporate WiFi
| **Field**                  | **Value**                                 |
|----------------------------|-------------------------------------------|
| **SSID Name:**             | `CORP-SECURE`                             |
| **Purpose:**               | Corporate WiFi for internal use           |
| **Security Protocol:**     | WPA2-Enterprise                           |
| **Authentication Method:** | 802.1X with RADIUS server                 |
| **VLAN:**                  | `172`                                     |
| **VLAN Name:**             | `corp-wireless`                           |
| **Access Control:**        | Restricted to corporate devices           |
| **Access:**                | Access to internal resources and internet |
| **Bandwidth Allocation:**  | High priority                             |

#### Authentication Details
- **Device Type:** Windows laptops
- **Authentication Method:** Machine certificates
- **Connection Process:**
  - **Step 1:** Users connect to an access point.
  - **Step 2:** The access point tunnels the connection back to the local Wireless LAN Controller (WLC) cluster.
  - **Step 3:** One of the WLCs sends an authentication request to ClearPass NAC.
  - **Step 4:** ClearPass NAC verifies the request against predefined rules.
  - **Step 5:** If the request matches the rules, ClearPass NAC grants access to the network.
- **Monitoring:** Authentications can be monitored by going to ClearPass Policy Manager Dashboard.

#### Traffic Flow
- **AP to Controller:** The AP tunnels traffic to the controller.
- **Controller to Core Switches:**
  - Each controller is trunked on VLAN 172 and VLAN 10 (Network Management) to the local core switches.
  - **VLAN Layer 3 Interface:**
    - The Layer 3 interface for the VLAN is located on the core switches.
    - The gateway for the VLAN is shared between the core switches, with the exact configuration varying by site.
    - This setup ensures that the next hop for traffic on the VLAN is the core switches.

#### ClearPass NAC Authentication Example
| **Field**                  | **Value**                  |
|----------------------------|----------------------------|
| **Service:**               | `Corp-WiFi-802.1X`         |
| **Authentication Method:** | `EAP-TLS`                  |
| **Authentication Source:** | `AD-CORP-DOMAIN`           |
| **Authorization Source:**  | `CORP-LDAP-SERVER`         |
| **Roles:**                 | `corporate-wifi-role`      |
| **Enforcement Profiles:**  | `corp-access-profile`      |
| **Service Monitor Mode:**  | `Disabled`                 |
| **Online Status:**         | `Not Available`            |

#### Additional Information
- **Radius:WLC:WLC-User-Role:** `wlc-corporate-wifi-role`
  - This role is assigned directly on the WLC.
- **Status-Update:Endpoint:** `Known`

#### Role Assignment Explanation
- **ClearPass NAC Role Assignment:**
  - **Roles:** `corporate-wifi-role`
    - These roles are assigned by ClearPass NAC during the authentication process and used to determine access and enforcement profiles.
- **WLC Role Assignment:**
  - **Radius:WLC:WLC-User-Role:** `wlc-corporate-wifi-role`
    - This role is assigned by the WLC to enforce network policies and permissions for the device.

### 2. Staff BYOD WiFi
| **Field**                  | **Value**                                                         |
|----------------------------|-------------------------------------------------------------------|
| **SSID Name:**             | `STAFF-BYOD`                                                      |
| **Purpose:**               | WiFi for staff personal devices and corporate Macbooks (BYOD)     |
| **Security Protocol:**     | WPA2-PSK                                                          |
| **Authentication Method:** | Pre-shared key                                                    |
| **VLAN:**                  | `173`                                                             |
| **VLAN Name:**             | `staff-byod`                                                      |
| **Access Control:**        | Limited access to internal resources, Full access to the internet |
| **Bandwidth Allocation:**  | Medium priority                                                   |

#### Authentication Details
- **Device Types:** 
  - Staff member's personal devices
  - Staff member's BYOD devices
- **Connection Process:**
  - **Step 1:** Users join `STAFF-BYOD` with the pre-shared key (PSK).
  - **Step 2:** Users are directed to a captive portal presented by ClearPass NAC.
  - **Step 3:** Users enter their Active Directory (AD) credentials.
  - **Step 4:** ClearPass NAC verifies the user's credentials.
  - **Step 5:** If the credentials are valid, ClearPass NAC allows the user onto the `STAFF-BYOD` network.
- **Monitoring:** Authentications can be monitored by going to ClearPass Policy Manager Dashboard.

#### Traffic Flow
- **Sites with Local Internet Breakout:**
  - **AP to Controller:** AP tunnels traffic to the local controller pair.
  - **Controller to Firewall:** The local controller pair has Layer 2 (L2) connectivity to the firewall.
  - **VLAN Layer 3 Interface:**
    - The Layer 3 (L3) interface for the VLAN is located on the firewall.
    - DHCP is provided by the firewall.
- **Sites without Local Internet Breakout:**
  - **AP to Local Controller:** AP tunnels traffic to the local controller pair.
  - **Local Controller to Hub Controller:** The local controller pair tunnels traffic to the hub/datacenter wireless controller pair.
  - **Hub Controller to Firewall:** The hub controllers have Layer 2 (L2) connectivity to the firewall.
  - **VLAN Layer 3 Interface:**
    - The Layer 3 (L3) interface for the VLAN is located on the firewall.
    - DHCP is provided by the firewall.

#### ClearPass NAC Authentication Example
| **Field**                  | **Value**                  |
|----------------------------|----------------------------|
| **Service:**               | `BYOD-Device-Auth`         |
| **Authentication Method:** | `MAC-AUTH`                 |
| **Authentication Source:** | `AD-CORP-DOMAIN`           |
| **Authorization Source:**  | `BYOD-Device-Repository`   |
| **Roles:**                 | `staff-wifi-role`          |
| **Enforcement Profiles:**  | `byod-access-profile`      |
| **Service Monitor Mode:**  | `Disabled`                 |
| **Online Status:**         | `Offline`                  |
| **System Posture Status:** | `UNKNOWN (100)`            |
| **Audit Posture Status:**  | `UNKNOWN (100)`            |

#### Additional Information
- **Radius:WLC:WLC-User-Role:** `wlc-staff-wifi-role`
  - This role is assigned directly on the WLC.
- **Status-Update:Endpoint:** `Known`

#### Role Assignment Explanation
- **ClearPass NAC Role Assignment:**
  - **Roles:** `staff-wifi-role`
    - These roles are assigned by ClearPass NAC during the authentication process and used to determine access and enforcement profiles.
- **WLC Role Assignment:**
  - **Radius:WLC:WLC-User-Role:** `wlc-staff-wifi-role`
    - This role is assigned by the WLC to enforce network policies and permissions for the device.

### 3. Guest WiFi
| **Field**                  | **Value**                                                    |
|----------------------------|--------------------------------------------------------------|
| **SSID Name:**             | `GUEST-NET`                                                  |
| **Purpose:**               | WiFi for guest users                                         |
| **Security Protocol:**     | WPA2-PSK                                                     |
| **Authentication Method:** | Pre-shared key                                               |
| **VLAN:**                  | `174`                                                        |
| **VLAN Name:**             | `guest`                                                      |
| **Access Control:**        | No access to internal resources, Full access to the internet |
| **Bandwidth Allocation:**  | Low priority                                                 |

#### Authentication Details
- **Device Types:** 
  - Guest devices
- **Connection Process:**
  - **Step 1:** Users join `GUEST-NET` with the pre-shared key (PSK).
  - **Step 2:** Users are directed to a captive portal presented by ClearPass NAC.
  - **Step 3:** Users enter their guest credentials.
  - **Step 4:** ClearPass NAC verifies the user's credentials.
  - **Step 5:** If the credentials are valid, ClearPass NAC allows the user onto the `GUEST-NET` network.
- **Monitoring:** Authentications can be monitored by going to ClearPass Policy Manager Dashboard.

#### Traffic Flow
- **Sites with Local Internet Breakout:**
  - **AP to Controller:** AP tunnels traffic to the local controller pair.
  - **Controller to Firewall:** The local controller pair has Layer 2 (L2) connectivity to the firewall.
  - **VLAN Layer 3 Interface:**
    - The Layer 3 (L3) interface for the VLAN is located on the firewall.
    - DHCP is provided by the firewall.
- **Sites without Local Internet Breakout:**
  - **AP to Local Controller:** AP tunnels traffic to the local controller pair.
  - **Local Controller to Hub Controller:** The local controller pair tunnels traffic to the hub/datacenter wireless controller pair.
  - **Hub Controller to Firewall:** The hub controllers have Layer 2 (L2) connectivity to the firewall.
  - **VLAN Layer 3 Interface:**
    - The Layer 3 (L3) interface for the VLAN is located on the firewall.
    - DHCP is provided by the firewall.

#### ClearPass NAC Authentication Example
| **Field**                  | **Value**                |
|----------------------------|--------------------------|
| **Service:**               | `Guest-Portal-Auth`      |
| **Authentication Method:** | `MAC-AUTH`               |
| **Authentication Source:** | `Guest-Account-DB`       |
| **Authorization Source:**  | `Guest-Policy-Store`     |
| **Roles:**                 | `guest-wifi-role`        |
| **Enforcement Profiles:**  | `guest-access-profile`   |
| **Service Monitor Mode:**  | `Disabled`               |
| **Online Status:**         | `Offline`                |
| **System Posture Status:** | `UNKNOWN (100)`          |
| **Audit Posture Status:**  | `UNKNOWN (100)`          |

#### Additional Information
- **Radius:WLC:WLC-User-Role:** `wlc-guest-wifi-role`
  - This role is assigned directly on the WLC.
- **Status-Update:Endpoint:** `Known`

#### Role Assignment Explanation
- **ClearPass NAC Role Assignment:**
  - **Roles:** `guest-wifi-role`
    - These roles are assigned by ClearPass NAC during the authentication process and used to determine access and enforcement profiles.
- **WLC Role Assignment:**
  - **Radius:WLC:WLC-User-Role:** `wlc-guest-wifi-role`
    - This role is assigned by the WLC to enforce network policies and permissions for the device.

## Wireless Access Points

### Access Point Models
| **Model**             | **Count** | **Primary Locations**  | **Notes**                       |
|-----------------------|-----------|------------------------|---------------------------------|
| Cisco Catalyst 9130   | 158       | Main Campus, HQ        | Wi-Fi 6, 4x4 MIMO               |
| Cisco Catalyst 9120   | 267       | Branch Offices         | Wi-Fi 6, 2x2 MIMO               |
| Cisco Aironet 3800    | 112       | Warehouse, Industrial  | Legacy, planned for replacement |
| Meraki MR46           | 54        | Remote Sites           | Cloud-managed                   |

### Access Point Placement Guidelines
- **Office Environments**: 1 AP per 1000 sq ft
- **High-Density Areas**: 1 AP per 600 sq ft
- **Warehouse Environments**: 1 AP per 2500 sq ft with external antennas
- **Outdoor Coverage**: Strategic placement with 150-200 ft radius

## Radio Management Configuration

### RF Profiles
| **Profile Name**      | **Target Environment** | **Key Settings**                                   |
|-----------------------|------------------------|----------------------------------------------------|
| Corporate-Standard    | Office spaces          | Auto channel, 5 GHz preferred, -67 dBm min RSSI    |
| Corporate-HighDensity | Conference rooms       | Fixed channel plan, RRM disabled, -65 dBm min RSSI |
| Corporate-Warehouse   | Warehouse, industrial  | Max TX power, 2.4 GHz preferred, -72 dBm min RSSI  |

### Channel Planning
- **2.4 GHz Band**: Channels 1, 6, 11 (non-overlapping)
- **5 GHz Band**: Channels 36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 132, 136, 140, 149, 153, 157, 161
- **DFS Channels**: Enabled where regulatory domain allows

## RADIUS Configuration

### RADIUS Servers
| **Server Name**         | **IP Address**  | **Port** | **Purpose**              |
|-------------------------|-----------------|----------|--------------------------|
| radius1.corp.local      | 10.10.20.10     | 1812     | Primary Authentication   |
| radius2.corp.local      | 10.10.20.11     | 1812     | Secondary Authentication |
| accounting1.corp.local  | 10.10.20.10     | 1813     | Primary Accounting       |
| accounting2.corp.local  | 10.10.20.11     | 1813     | Secondary Accounting     |

### RADIUS Server Groups
| **Group Name**  | **Servers**                                    | **Purpose**              |
|-----------------|------------------------------------------------|--------------------------|
| Corp-Auth       | radius1.corp.local, radius2.corp.local         | Corporate authentication |
| Guest-Auth      | radius1.corp.local, radius2.corp.local         | Guest authentication     |
| Accounting      | accounting1.corp.local, accounting2.corp.local | All accounting           |

## Troubleshooting Common Issues

### Authentication Failures
1. Verify RADIUS server connectivity
2. Check certificate validity for EAP-TLS authentications
3. Validate user credentials in Active Directory
4. Check ClearPass NAC policies and enforcement profiles

### Connectivity Issues
1. Verify client can see SSID
2. Check signal strength at client location (should be above -67 dBm)
3. Verify client has obtained IP address from DHCP
4. Test connectivity to wireless gateway
5. Analyze packet capture for association issues

### Performance Issues
1. Check channel utilization on access point
2. Verify client signal strength
3. Test with alternative device to rule out client-specific issues
4. Check for RF interference sources
5. Verify QoS marking and prioritization is working

## Support Information

### Wireless Engineering Team
- **Email**: wireless-support@corp.local
- **Phone**: ext. 5500
- **Ticket System**: IT Service Desk - Category: Network > Wireless

### Vendor Support
- Cisco TAC: 1-800-553-2447, Case # prefix: WIFI-
- Aruba/ClearPass Support: 1-800-796-3365, Portal: support.arubanetworks.com