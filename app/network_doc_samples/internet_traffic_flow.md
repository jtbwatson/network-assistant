# Internet Traffic

## Overview
The company operates a hybrid internet access model with centralized breakout at datacenter locations for most sites, plus local internet breakout at select strategic sites. Traffic is secured through Palo Alto firewalls and SecureEdge Cloud proxy services.

## Internet Connectivity Architecture

### Datacenter Internet Connectivity

| **Field**                    | **Value**                                            |
|------------------------------|-----------------------------------------------------|
| **Connection Type:**         | Dedicated Internet Access (DIA)                      |
| **Primary Carrier:**         | GlobeConnect                                         |
| **Secondary Carrier:**       | NetwayLink                                           |
| **Bandwidth:**               | 10 Gbps per carrier (20 Gbps total per datacenter)   |
| **Router Models:**           | Cisco ASR 1000 Series                                |
| **Deployment:**              | Redundant pair per datacenter                        |
| **BGP Configuration:**       | eBGP with both carriers (full routes)                |
| **DDoS Protection:**         | SecureEdge Cloud + Carrier-provided                  |
| **Traffic Prioritization:**  | QoS for business-critical traffic                    |

#### Datacenter Internet Edge Diagram
```
                  +-------------------+     +-------------------+
                  |    GlobeConnect   |     |     NetwayLink    |
                  +-------------------+     +-------------------+
                            |                         |
                            v                         v
            +----------------+                  +----------------+
            | Internet Edge  |                  | Internet Edge  |
            | Router (ASR1)  |                  | Router (ASR2)  |
            +----------------+                  +----------------+
                     |                                 |
                     v                                 v
              +----------------------------------------+
              |          Palo Alto Firewall HA Pair    |
              +----------------------------------------+
                               |
                               v
                    +--------------------+
                    |   SecureEdge Cloud |
                    |   Proxy Service    |
                    +--------------------+
                               |
                               v
                    +--------------------+
                    |  Internal Network  |
                    +--------------------+
```

### Local Internet Breakout Connectivity

| **Field**                    | **Value**                                            |
|------------------------------|-----------------------------------------------------|
| **Site Selection Criteria:** | High user count, latency-sensitive applications      |
| **Connection Type:**         | Business broadband + 4G/LTE backup                   |
| **Primary Carrier:**         | Varies by region (typically GlobeConnect)            |
| **Secondary Carrier:**       | Varies by region (typically NetwayLink)              |
| **Bandwidth:**               | 1-2 Gbps primary, 100-200 Mbps backup               |
| **Router Models:**           | Cisco ISR 4000 Series                                |
| **Deployment:**              | Redundant pair per site                              |
| **Firewall:**                | Palo Alto PA-3200 Series                             |
| **SD-WAN:**                  | Enabled for intelligent path selection               |

#### Local Breakout Sites

| **Region**  | **Site Name**      | **Primary Bandwidth** | **Notes**                           |
|-------------|--------------------|-----------------------|-------------------------------------|
| Americas    | New York Office    | 2 Gbps                | Regional headquarters                |
| Americas    | San Francisco      | 1 Gbps                | R&D focused site                    |
| Europe      | London Office      | 2 Gbps                | Regional headquarters                |
| Europe      | Berlin Office      | 1 Gbps                | Large engineering center            |
| Asia        | Tokyo Office       | 1 Gbps                | Regional headquarters                |
| Asia        | Bangalore Office   | 1 Gbps                | Development center                  |
| ANZ         | Sydney Office      | 1 Gbps                | Regional headquarters                |

## Traffic Flow Patterns

### Centralized Internet Breakout Flow

1. **User initiates internet connection**
   - User device at branch location makes a request to an internet resource
   - Traffic is routed to the local branch router

2. **Traffic traverses WAN to datacenter**
   - Router forwards traffic over MPLS to the nearest regional datacenter
   - Traffic maintains QoS markings across the WAN

3. **Security inspection at datacenter**
   - Traffic arrives at datacenter edge router
   - Router forwards to Palo Alto firewall cluster

4. **Cloud proxy service inspection**
   - SecureEdge Cloud proxy service inspects HTTP/HTTPS traffic
   - URL filtering, malware scanning, and content inspection performed
   - Non-HTTP traffic is inspected directly by firewall

5. **Traffic forwarded to internet**
   - After security inspection, legitimate traffic is forwarded to the internet
   - Responses follow the reverse path

### Local Internet Breakout Flow

1. **User initiates internet connection**
   - User device makes a request to an internet resource
   - Traffic is routed to the local branch router

2. **Local security inspection**
   - Router forwards traffic to local Palo Alto firewall
   - Firewall performs initial security inspection

3. **Cloud proxy service inspection**
   - SecureEdge Cloud proxy service inspects HTTP/HTTPS traffic
   - Cloud-based security policies are enforced

4. **Traffic forwarded to internet**
   - After security inspection, legitimate traffic is forwarded to the internet
   - Direct local path reduces latency for cloud applications

5. **Failover mechanism**
   - If local internet connection fails, traffic automatically routes through MPLS to datacenter
   - SD-WAN controllers monitor path quality and adjust routing in real-time

## Security Controls

### URL Filtering

| **Category**              | **Policy**                 | **Examples**                       |
|---------------------------|----------------------------|-----------------------------------|
| **Malicious Sites**       | Block                      | Phishing, malware, command & control |
| **Adult Content**         | Block                      | Adult material, gambling           |
| **Suspicious Content**    | Allow with warning         | Newly registered domains, hacking  |
| **Social Media**          | Allow with quota           | Facebook, Twitter, LinkedIn        |
| **Streaming Media**       | Rate limited               | YouTube, Netflix, Spotify          |
| **Business Applications** | Allow                      | Office 365, Salesforce, Workday    |

### Application Control

| **Application Type**      | **Policy**                 | **Examples**                       |
|---------------------------|----------------------------|-----------------------------------|
| **Collaboration Tools**   | Allow                      | Zoom, Teams, Slack                 |
| **Cloud Storage**         | Allow corporate approved   | OneDrive, Google Drive (corporate) |
| **Personal Storage**      | Block upload               | Dropbox personal, WeTransfer       |
| **Remote Access**         | Allow corporate approved   | Corporate VPN, RDP to approved hosts |
| **File Sharing**          | Block                      | BitTorrent, P2P applications       |
| **Anonymizers**           | Block                      | TOR, VPN services, proxies         |

### Data Loss Prevention

| **Data Type**             | **Control**                | **Action**                         |
|---------------------------|----------------------------|-----------------------------------|
| **PII Data**              | Pattern matching           | Block transmission, alert security |
| **Credit Card Numbers**   | Pattern matching, validation | Block transmission, alert security |
| **Intellectual Property** | Fingerprinting            | Block transmission, alert security |
| **Source Code**           | File type detection        | Block to unapproved destinations   |
| **Financial Data**        | Keyword and pattern matching | Allow to approved destinations only |

## DNS Architecture

### Internal DNS

| **Field**                    | **Value**                                         |
|------------------------------|--------------------------------------------------|
| **DNS Server Platform:**     | Microsoft Active Directory DNS                    |
| **Deployment:**              | Redundant servers in each datacenter              |
| **Zone Structure:**          | corp.local (internal), subdomain per business unit |
| **Dynamic DNS:**             | Enabled for internal clients                      |
| **DNS Security:**            | DNSSEC for internal zones                         |

### External DNS

| **Field**                    | **Value**                                         |
|------------------------------|--------------------------------------------------|
| **DNS Provider:**            | Mixed (Cloudflare + regional providers)           |
| **Redundancy:**              | Minimum 2 providers per domain                    |
| **Security:**                | DNSSEC enabled, CAA records                       |
| **Monitoring:**              | 24/7 external monitoring service                  |

### Secure DNS Architecture

| **Component**                | **Implementation**                                |
|------------------------------|--------------------------------------------------|
| **DNS Filtering:**           | SecureEdge Cloud DNS security                     |
| **Query Encryption:**        | DNS over HTTPS (DoH) for compatible clients       |
| **Split DNS:**               | Separate internal/external resolution paths       |
| **DNS Analytics:**           | Logging and analysis for security monitoring      |

## Quality of Service (QoS)

### Internet Traffic Classification

| **Traffic Type**           | **Priority** | **DSCP Marking** | **Bandwidth Allocation** |
|----------------------------|--------------|------------------|--------------------------|
| **Business Critical Apps** | High         | AF31, AF32, AF33 | 30% guaranteed           |
| **Voice/Video**            | Highest      | EF, AF41         | 20% guaranteed           |
| **Standard Web Browsing**  | Medium       | AF21             | 40% shared               |
| **Software Updates**       | Low          | AF11, AF12       | 5% limited               |
| **General Internet**       | Best Effort  | Default          | Remaining bandwidth      |

### Per-Site Bandwidth Management

| **Site Type**              | **Business Critical** | **Voice/Video** | **Standard Web** | **Updates** | **General** |
|----------------------------|----------------------|-----------------|------------------|-------------|-------------|
| **Datacenter**             | 6 Gbps               | 4 Gbps          | 8 Gbps           | 1 Gbps      | Remaining   |
| **Regional HQ**            | 600 Mbps             | 400 Mbps        | 800 Mbps         | 100 Mbps    | Remaining   |
| **Large Office**           | 300 Mbps             | 200 Mbps        | 400 Mbps         | 50 Mbps     | Remaining   |
| **Small Office**           | 45 Mbps              | 30 Mbps         | 60 Mbps          | 7.5 Mbps    | Remaining   |

## Public IP Addressing

### Public IP Allocation

| **Region**                 | **IP Block Size** | **Subnet Example**  | **Usage**                     |
|----------------------------|-------------------|---------------------|-------------------------------|
| **Americas**               | /24 per datacenter | 203.0.113.0/24      | Internet-facing services      |
| **Europe**                 | /24 per datacenter | 198.51.100.0/24     | Internet-facing services      |
| **Asia**                   | /24 per datacenter | 192.0.2.0/24        | Internet-facing services      |
| **ANZ**                    | /24 per datacenter | 198.18.0.0/24       | Internet-facing services      |
| **All Regions**            | /25 per LBO site   | 203.0.114.0/25      | Local breakout addressing     |

### NAT Configuration

| **NAT Type**               | **Implementation**                               | **Notes**                     |
|----------------------------|--------------------------------------------------|-------------------------------|
| **Source NAT**             | PAT overload (many-to-one)                       | General internet access       |
| **Static NAT**             | One-to-one for public services                   | Externally accessible servers |
| **Policy NAT**             | Context-dependent translation                    | Special application needs     |

## Public Services

### DMZ Architecture

| **Field**                    | **Value**                                         |
|------------------------------|--------------------------------------------------|
| **Firewall Model:**          | Palo Alto PA-7000 Series                          |
| **DMZ Segmentation:**        | Multiple security zones                           |
| **Load Balancers:**          | F5 BIG-IP                                         |
| **WAF:**                     | F5 Advanced WAF                                   |

### Exposed Services

| **Service Type**           | **Protection Measures**                           | **Notes**                     |
|----------------------------|--------------------------------------------------|-------------------------------|
| **Web Applications**       | WAF, DDoS protection, TLS 1.3                    | Customer-facing applications  |
| **API Gateways**           | API Gateway with rate limiting, JWT validation    | Partner and customer APIs     |
| **Email**                  | Anti-spam, SPF, DKIM, DMARC                      | Office 365 with SecureEdge    |
| **VPN**                    | Palo Alto GlobalProtect                           | Remote access                 |

## Monitoring and Alerts

### Internet Health Monitoring

| **Metric**                 | **Monitoring Method**                             | **Alert Threshold**          |
|----------------------------|--------------------------------------------------|-------------------------------|
| **Connectivity**           | ICMP to multiple destinations                     | >5% packet loss              |
| **Latency**                | Synthetic transactions                            | >100ms increase from baseline |
| **Bandwidth Utilization**  | SNMP polling of edge devices                      | >80% for >15 minutes         |
| **BGP Stability**          | BGP session state and route changes               | Any flapping or major changes |

### Security Event Monitoring

| **Event Type**             | **Detection Method**                              | **Response**                  |
|----------------------------|--------------------------------------------------|-------------------------------|
| **Malware Detection**      | SecureEdge Cloud alerts + Palo Alto logs          | Auto-quarantine + ticket      |
| **Data Exfiltration**      | DLP alerts, unusual traffic patterns              | Block + security team alert   |
| **DNS Tunneling**          | DNS query analysis                                | Block + security team alert   |
| **Botnet Communication**   | Threat intelligence matching                      | Block + security team alert   |

## Troubleshooting Common Issues

### Internet Access Issues
1. **General Connectivity Problems**
   - Verify physical connectivity on internet edge routers
   - Check BGP session status with carriers
   - Verify firewall status and rule configuration
   - Check DNS resolution functionality

2. **Application-Specific Access Issues**
   - Verify application is not blocked by URL filtering or application control
   - Check for SSL inspection issues with specific applications
   - Validate QoS prioritization is working correctly
   - Test from different locations to isolate the issue

3. **Performance Issues**
   - Run bandwidth tests at different times of day
   - Check for packet loss on WAN and internet links
   - Verify QoS marking and policy enforcement
   - Monitor carrier performance against SLAs

### DNS Resolution Issues
1. **Internal Name Resolution**
   - Verify DNS server health and replication
   - Check client DNS configuration
   - Test resolution from different client locations
   - Verify DNS forwarding configuration

2. **External Name Resolution**
   - Check external DNS provider status
   - Verify domain registration and nameserver configuration
   - Test with alternative DNS resolvers
   - Check for DNS filtering or security blocks

## Support Information

### Internet Operations Team
- **Email**: internet-operations@corp.local
- **Phone**: ext. 5200
- **Ticket System**: IT Service Desk - Category: Network > Internet

### Carrier Support Contacts
- **GlobeConnect NOC**: 1-888-555-0100, noc@globeconnect.example.com
- **NetwayLink NOC**: 1-888-555-0200, support@netwaylink.example.com
- **SecureEdge Cloud Support**: 1-888-555-0300, support@secureedge.example.com