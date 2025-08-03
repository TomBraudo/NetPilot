# NetPilot Commands-Server Group Architecture

## 🎯 **Core Philosophy**

The commands-server acts as the **execution layer** for group-based network policies in NetPilot. It receives API requests from the upper application layer and translates them into router operations. The server maintains minimal state information about groups in its state file for efficient management while the upper layer remains the source of truth for group membership and detailed policies.

### **Key Principles**

1. **Execution-Only Layer**: Commands-server executes policies, doesn't manage group CRUD operations
2. **Minimal State Storage**: Only essential group information stored locally for efficiency
3. **API-Driven Operations**: Upper layer controls groups through simple API calls
4. **Policy Compilation**: High-level policies compiled into router command bundles
5. **Batch Application**: Multiple policy changes applied in single operations
6. **Lazy Infrastructure**: Router infrastructure created only when needed
7. **State Synchronization**: Maintains minimal difference between desired and actual router state

## 🏗️ **Commands-Server Architecture**

The commands-server transforms API requests into efficient router operations:

```
Upper Layer API Requests
         ↓
API Service Layer (Group Management Endpoints)
         ↓
Policy Compilation Layer (GroupPolicy → RouterCommandBundle)
         ↓
Batch Application Layer (Efficient Router Updates)
         ↓
Router Infrastructure (TC Classes + iptables Chains)
         ↓
State File Management (Minimal Group State Storage)
```

### **Commands-Server Responsibilities**

The commands-server is responsible for:

- **API Service**: Provides REST endpoints for group management operations
- **State Management**: Maintains minimal group state in local state file
- **Policy Execution**: Compiles and applies policies to router infrastructure  
- **Router Operations**: Manages TC classes, iptables chains, and DNS configurations
- **Synchronization**: Ensures router state matches requested group policies
- **Performance**: Optimizes router operations through batching and caching

### **State File Structure**

The commands-server maintains a minimal state file containing only essential group information:

```json
{
  "groups": {
    "0": {
      "name": "Guest Group",
      "active": true,
      "device_count": 5,
      "devices": [
        {
          "ip": "192.168.1.50",
          "mac": "aa:bb:cc:dd:ee:11"
        },
        {
          "ip": "192.168.1.51", 
          "mac": "aa:bb:cc:dd:ee:22"
        },
        {
          "ip": "192.168.1.52",
          "mac": "aa:bb:cc:dd:ee:33"
        },
        {
          "ip": "192.168.1.53",
          "mac": "aa:bb:cc:dd:ee:44"
        },
        {
          "ip": "192.168.1.54",
          "mac": "aa:bb:cc:dd:ee:55"
        }
      ],
      "tc_class": "1:100",
      "mark_value": 100,
      "policies": {
        "bandwidth_limit_mbps": null,
        "blocked_categories": [],
        "blocked_sites": [],
        "allowed_sites_only": [],
        "block_all_internet": false
      },
      "infrastructure_created": true,
      "last_sync": "2025-08-03T10:30:00Z"
    },
    "1": {
      "name": "Children Devices",
      "active": true, 
      "device_count": 3,
      "devices": [
        {
          "ip": "192.168.1.100",
          "mac": "d8:bb:c1:47:3a:43"
        },
        {
          "ip": "192.168.1.101",
          "mac": "aa:bb:cc:11:22:33"
        },
        {
          "ip": "192.168.1.102", 
          "mac": "bb:cc:dd:22:33:44"
        }
      ],
      "tc_class": "1:101",
      "mark_value": 101,
      "policies": {
        "bandwidth_limit_mbps": 50,
        "blocked_categories": ["adult", "gaming"],
        "blocked_sites": ["social-media.com"],
        "allowed_sites_only": [],
        "block_all_internet": false
      },
      "infrastructure_created": true,
      "last_sync": "2025-08-03T10:25:00Z"
    }
  },
  "infrastructure": {
    "base_setup_complete": true,
    "available_classes": ["1:102", "1:103", "1:104"],
    "next_mark_value": 102
  }
}
```

### **API Service Layer**

The commands-server exposes simple REST endpoints for the upper layer:

```
POST /api/groups/{group_id}/sync
- Synchronizes group policy with router
- Payload: GroupPolicy object from upper layer
- Returns: Success status and any error messages

PUT /api/groups/{group_id}/policy  
- Updates specific policy for a group
- Payload: Policy updates (bandwidth, access_control, etc.)
- Returns: Updated group state

DELETE /api/groups/{group_id}
- Removes group infrastructure and cleans up router
- Returns: Cleanup status

GET /api/groups/{group_id}/status
- Returns current group status and router state
- Includes infrastructure status and last sync time

POST /api/groups/sync-all
- Batch synchronization of multiple groups
- Payload: Array of GroupPolicy objects
- Returns: Batch operation results

GET /api/infrastructure/status
- Returns overall router infrastructure status
- Includes available classes, active groups, performance metrics
```

## 📋 **Core Data Structures**

### **Minimal Group State (Commands-Server)**
```python
@dataclass
class DeviceInfo:
    """Device information stored in state file"""
    ip: str
    mac: str

@dataclass
class GroupState:
    """Minimal group state stored in commands-server state file"""
    group_id: int
    name: str
    active: bool
    device_count: int  # Number of devices (for optimization)
    devices: List[DeviceInfo]  # Current devices with IP/MAC for verification
    tc_class: str  # e.g., "1:101"
    mark_value: int  # e.g., 101
    policies: GroupPolicySummary
    infrastructure_created: bool
    last_sync: datetime

@dataclass
class GroupPolicySummary:
    """Essential policy information for router operations"""
    bandwidth_limit_mbps: Optional[int] = None
    blocked_categories: List[str] = field(default_factory=list)
    blocked_sites: List[str] = field(default_factory=list)
    allowed_sites_only: List[str] = field(default_factory=list)
    block_all_internet: bool = False

@dataclass
class GroupSyncRequest:
    """API request format from upper layer to commands-server"""
    group_id: int
    name: str
    device_ips: List[str]  # Current device IPs for this group
    device_macs: List[str]  # Current device MACs for this group
    
    # Policy Components (sent from upper layer)
    bandwidth_policy: Optional[BandwidthPolicy]
    access_control_policy: Optional[AccessControlPolicy]
    time_based_policies: List[TimeBasedPolicy] = field(default_factory=list)
    
    active: bool = True
    force_sync: bool = False  # Force full sync even if no changes detected

@dataclass  
class BandwidthPolicy:
    """Traffic shaping policies"""
    limit_mbps: int
    burst_mbps: Optional[int] = None
    active: bool = True

@dataclass
class AccessControlPolicy:
    """Website and content filtering"""
    blocked_sites: List[str] = field(default_factory=list)
    blocked_categories: List[str] = field(default_factory=list)  
    allowed_sites_only: List[str] = field(default_factory=list)
    block_all_internet: bool = False
    active: bool = True

@dataclass
class TimeBasedPolicy:
    """Time-sensitive policy overrides (handled by commands-server cron)"""
    name: str
    start_time: str  # "22:00"
    end_time: str    # "08:00" 
    days: List[str]  # ["monday", "tuesday", ...]
    action: PolicyAction
    parameters: Dict[str, Any]
    active: bool = True

class PolicyAction(Enum):
    """Available actions for time-based policies"""
    BANDWIDTH_LIMIT = "bandwidth_limit"
    BLOCK_INTERNET = "block_internet"
    ACTIVATE_BLACKLIST = "activate_blacklist"
    BLOCK_SITES = "block_sites"
    ALLOW_SITES_ONLY = "allow_sites_only"
```

### **Router Command Bundle**
```python
@dataclass
class RouterCommandBundle:
    """Complete set of router commands for a group policy"""
    group_id: int
    
    # Command categories
    tc_commands: List[str] = field(default_factory=list)
    iptables_commands: List[str] = field(default_factory=list)
    dns_commands: List[str] = field(default_factory=list)
    cron_commands: List[str] = field(default_factory=list)
    cleanup_commands: List[str] = field(default_factory=list)
    
    # Metadata
    requires_reboot: bool = False
    estimated_duration_ms: int = 0
    dependencies: List[int] = field(default_factory=list)
```

## 🔧 **Commands-Server Components**

### **1. API Service Layer**
Handles incoming requests from the upper application layer.

```python
class GroupAPIService:
    """REST API endpoints for group management"""
    
    def sync_group(self, group_id: int, sync_request: GroupSyncRequest) -> SyncResponse:
        """Main endpoint: sync group policy with router"""
        
    def update_group_policy(self, group_id: int, policy_updates: Dict) -> UpdateResponse:
        """Update specific policy components"""
        
    def delete_group(self, group_id: int) -> DeleteResponse:
        """Remove group infrastructure and cleanup"""
        
    def get_group_status(self, group_id: int) -> GroupStatus:
        """Get current group status and router state"""
        
    def sync_all_groups(self, sync_requests: List[GroupSyncRequest]) -> BatchSyncResponse:
        """Batch synchronization endpoint"""
        
    def get_infrastructure_status(self) -> InfrastructureStatus:
        """Get overall router infrastructure status"""
```

### **2. Policy Compilation Layer**
Converts API requests into executable router commands.

```python
class GroupPolicyCompiler:
    """Converts sync requests into router command bundles"""
    
    def compile_sync_request(self, sync_request: GroupSyncRequest, current_state: GroupState) -> RouterCommandBundle:
        """Main compilation entry point"""
        
    def _compile_bandwidth_policy(self, group_id: int, policy: BandwidthPolicy, device_ips: List[str]) -> List[str]:
        """Generate TC commands for bandwidth limiting"""
        
    def _compile_access_control_policy(self, group_id: int, policy: AccessControlPolicy, device_macs: List[str]) -> List[str]:
        """Generate iptables and DNS commands for access control"""
        
    def _compile_time_based_policy(self, group_id: int, policy: TimeBasedPolicy) -> List[str]:
        """Generate cron jobs for time-based policy activation"""
        
    def _calculate_state_diff(self, current: GroupState, desired: GroupSyncRequest) -> CommandDiff:
        """Calculate minimal changes needed"""
```

### **3. Router Operations Engine**
Efficiently applies policy changes to the router.

```python
class RouterOperationsEngine:
    """Executes router commands and manages infrastructure"""
    
    def apply_command_bundle(self, bundle: RouterCommandBundle) -> OperationResult:
        """Execute router commands with error handling"""
        
    def create_group_infrastructure(self, group_id: int) -> InfrastructureResult:
        """Create TC classes and iptables chains for new group"""
        
    def cleanup_group_infrastructure(self, group_id: int) -> CleanupResult:
        """Remove unused infrastructure when group is deleted"""
        
    def verify_router_state(self, group_id: int, expected_state: GroupState) -> VerificationResult:
        """Verify router state matches expected configuration"""
```

### **4. State File Manager**
Manages the local state file for efficient operations.

```python
class StateFileManager:
    """Manages commands-server state file"""
    
    def load_state(self) -> Dict[str, Any]:
        """Load current state from file"""
        
    def save_group_state(self, group_id: int, state: GroupState) -> bool:
        """Update group state in file"""
        
    def delete_group_state(self, group_id: int) -> bool:
        """Remove group from state file"""
        
    def get_group_state(self, group_id: int) -> Optional[GroupState]:
        """Get specific group state"""
        
    def verify_devices(self, group_id: int, device_ips: List[str], device_macs: List[str]) -> DeviceVerificationResult:
        """Verify incoming device list against stored state"""
        
    def update_group_devices(self, group_id: int, devices: List[DeviceInfo]) -> bool:
        """Update device list for a group"""
        
    def get_device_changes(self, group_id: int, new_devices: List[DeviceInfo]) -> DeviceChanges:
        """Calculate which devices were added/removed/changed"""
        
    def allocate_tc_class(self) -> Tuple[str, int]:
        """Allocate next available TC class and mark value"""
        
    def release_tc_class(self, tc_class: str, mark_value: int) -> bool:
        """Release TC class back to available pool"""

@dataclass
class DeviceVerificationResult:
    """Result of device verification"""
    is_valid: bool
    added_devices: List[DeviceInfo]
    removed_devices: List[DeviceInfo]
    changed_devices: List[DeviceInfo]  # Devices with IP/MAC changes
    error_message: Optional[str] = None

@dataclass
class DeviceChanges:
    """Device changes between current and new state"""
    added: List[DeviceInfo]
    removed: List[DeviceInfo] 
    ip_changed: List[Tuple[DeviceInfo, DeviceInfo]]  # (old, new)
    mac_changed: List[Tuple[DeviceInfo, DeviceInfo]]  # (old, new)
    unchanged: List[DeviceInfo]
```

## 🚀 **Router Infrastructure Organization**

### **Multi-Policy Chain Structure**
The router infrastructure is organized into specialized chains for different policy types:

```bash
# Basic infrastructure (created at start_session)
iptables -t mangle -N NETPILOT_MAIN
iptables -t filter -N NETPILOT_ACCESS_CONTROL
iptables -t nat -N NETPILOT_DNS_REDIRECT

# Group-specific chains (created lazily)
iptables -t mangle -N NETPILOT_GROUP_{group_id}
iptables -t filter -N NETPILOT_GROUP_{group_id}_ACCESS

# Time-based chains (created/destroyed dynamically)
iptables -t filter -N NETPILOT_NIGHT_MODE
iptables -t mangle -N NETPILOT_SCHOOL_HOURS
```

### **TC Class Mapping Strategy**
Traffic Control classes are dynamically allocated based on group IDs:

- **Unlimited Class**: `1:1` (always exists, for unrestricted traffic)
- **Group 0 (Guest)**: `1:100` (always exists, default group)
- **Group Classes**: `1:(100 + group_id)` (created lazily for groups 1, 2, 3...)
- **Mark Values**: `100 + group_id` (consistent mapping)

**Example Mapping:**
- Group 0 → Class `1:100` → Mark `100` (Guest/Default)
- Group 1 → Class `1:101` → Mark `101` (Children)
- Group 2 → Class `1:102` → Mark `102` (Work Devices)
- Group N → Class `1:(100+N)` → Mark `(100+N)`

### **Lazy Infrastructure Creation**
Router infrastructure is created **just-in-time** when groups are first used:

1. **Basic Setup** (start_session): Creates root qdiscs and main chains
2. **Guest Group Setup** (always): Creates Group 0 infrastructure (TC class `1:100`)
3. **Additional Group Setup** (first device): Creates group-specific classes and chains for groups 1+
4. **Policy Setup** (policy activation): Adds specific rules and filters
5. **Cleanup** (group empty): Removes unused infrastructure (except Group 0)

## 🔄 **API Operation Flows**

### **Group Sync Operation (Primary Flow)**
```
1. Upper Layer Request
   - POST /api/groups/{group_id}/sync
   - Payload: GroupSyncRequest with current devices and policies
   
2. Device Verification
   - Load current group state from state file
   - Compare incoming device list (IPs/MACs) with stored state
   - Identify added, removed, or changed devices
   - Validate device changes are reasonable (security check)
   
3. State Comparison & Policy Compilation
   - Calculate difference between current and desired policies
   - Generate RouterCommandBundle for policy changes
   - Include device-specific commands for added/removed devices
   - Optimize for minimal router operations
   
4. Router Execution
   - Apply command bundle to router infrastructure
   - Update TC classes and iptables chains for device changes
   - Update DNS configurations for new/removed devices
   - Apply policy changes to affected devices
   
5. State Update
   - Update group state with new device list and policies
   - Record sync timestamp and updated device count
   - Return success/failure status with device change summary
```

### **Device Change Handling Flow**
```
1. Device Addition
   - Add new device IP/MAC to state file
   - Create iptables rules for new device
   - Apply group policies to new device
   - Update device count in state
   
2. Device Removal
   - Remove device-specific iptables rules
   - Clean up DNS configurations for device
   - Remove device from state file
   - Update device count in state
   
3. Device IP/MAC Changes
   - Remove old iptables rules
   - Add new iptables rules with updated IP/MAC
   - Update DNS configurations
   - Update device info in state file
   
4. Validation & Security
   - Detect suspicious mass device changes
   - Validate IP/MAC format and ranges
   - Check for duplicate devices across groups
   - Log significant device changes for audit
```

### **Time-Based Policy Activation (Cron-Triggered)**
```
1. Cron Job Execution
   - Time-based policy triggers (e.g., 22:00 bedtime restrictions)
   - Commands-server receives internal time event
   
2. Policy Override Application
   - Apply temporary policy changes (e.g., reduce bandwidth)
   - Maintain original policy in state for restoration
   
3. Automatic Restoration
   - End-time cron job restores original policies
   - Update router infrastructure back to base state
```

### **Infrastructure Management Flow**
```
1. Lazy Creation
   - New group triggers infrastructure creation
   - Allocate TC class (1:100+group_id) and mark value
   - Create group-specific iptables chains
   
2. Cleanup on Deletion
   - Remove all group-specific router rules
   - Release TC class back to available pool
   - Clean up DNS configurations and cron jobs
   
3. Optimization
   - Batch multiple group changes into single router interaction
   - Cache router state to minimize queries
   - Use state diffing to apply only necessary changes
```

## 📊 **Performance Characteristics**

### **Optimization Strategies**

1. **Batch Operations**: Multiple changes applied in single router interaction
2. **State Caching**: Minimal router queries through intelligent caching
3. **Lazy Creation**: Infrastructure created only when actually needed
4. **Incremental Updates**: Only changed components are updated
5. **Command Optimization**: Related commands grouped for efficiency

### **Scalability Considerations**

- **Group Limit**: Theoretical limit of ~900 groups (TC class limit: 1000, minus reserved classes)
- **Group 0 Requirement**: Group 0 ("Guest") always exists and cannot be deleted
- **Device Limit**: No practical limit (handled through iptables rules)
- **Policy Complexity**: Linear scaling with number of active policies
- **Time-Based Policies**: Minimal overhead through cron automation

### **Performance Metrics**

- **Policy Sync**: ~100-500ms per group (depending on complexity)
- **Infrastructure Creation**: ~200-800ms per new group
- **State Query**: ~50-200ms (cached results faster)
- **Time-Based Activation**: ~10-100ms (cron-triggered)

## 🎯 **Example API Usage**

### **Sync Children's Group with Restrictions**
```python
# Upper layer sends sync request to commands-server
sync_request = GroupSyncRequest(
    group_id=1,
    name="Children's Devices",
    device_ips=["192.168.1.100", "192.168.1.101", "192.168.1.102"],
    device_macs=["d8:bb:c1:47:3a:43", "aa:bb:cc:11:22:33", "bb:cc:dd:22:33:44"],
    
    bandwidth_policy=BandwidthPolicy(limit_mbps=50),
    
    access_control_policy=AccessControlPolicy(
        blocked_categories=["adult", "gaming"],
        blocked_sites=["social-media.com"]
    ),
    
    time_based_policies=[
        TimeBasedPolicy(
            name="school_night_restrictions",
            start_time="22:00", end_time="08:00",
            days=["sunday", "monday", "tuesday", "wednesday", "thursday"],
            action=PolicyAction.BANDWIDTH_LIMIT,
            parameters={"limit_mbps": 10}
        )
    ]
)

# API call to commands-server
response = requests.post(
    "http://commands-server:8080/api/groups/1/sync",
    json=sync_request.to_dict()
)

# Response includes device change summary
# {
#   "success": true,
#   "device_changes": {
#     "added": [{"ip": "192.168.1.102", "mac": "bb:cc:dd:22:33:44"}],
#     "removed": [],
#     "ip_changed": [],
#     "mac_changed": []
#   },
#   "policies_updated": ["bandwidth", "access_control"],
#   "sync_duration_ms": 245
# }
```

### **Update Group Policy (Bandwidth Only)**
```python
# Quick policy update without full sync
policy_update = {
    "bandwidth_policy": {
        "limit_mbps": 75,  # Increase bandwidth limit
        "active": True
    }
}

response = requests.put(
    "http://commands-server:8080/api/groups/1/policy",
    json=policy_update
)
```

### **Remove Group Infrastructure**
```python
# Clean up group when no longer needed
response = requests.delete(
    "http://commands-server:8080/api/groups/1"
)

# Commands-server will:
# 1. Remove all TC classes and iptables rules for group devices
# 2. Clean up DNS configurations for all group devices
# 3. Remove cron jobs for time-based policies
# 4. Delete group from state file (including all device records)
# 5. Release TC class back to pool
# 6. Return summary of cleanup operations performed

# Response includes cleanup summary
# {
#   "success": true,
#   "cleanup_summary": {
#     "devices_cleaned": 3,
#     "tc_rules_removed": 5,
#     "iptables_rules_removed": 12,
#     "dns_configs_removed": 3,
#     "cron_jobs_removed": 2
#   },
#   "tc_class_released": "1:101"
# }
```

## 🔮 **Commands-Server Extensions**

The commands-server architecture is designed to easily accommodate additional policy types through API extensions:

- **Application-Level Control**: Block/allow specific applications via DPI
- **Quality of Service**: Priority-based traffic handling
- **Usage Quotas**: Daily/weekly data limits with automatic enforcement
- **Advanced Time Patterns**: Complex scheduling with exceptions
- **Dynamic Policy Adjustment**: Performance-based automatic policy tuning

New policy types only require:
1. Extension of `GroupSyncRequest` data structure
2. New compilation methods in `GroupPolicyCompiler` 
3. Additional router command generation
4. State file schema updates for new policy storage

## 💡 **Commands-Server Benefits**

1. **Clear Separation of Concerns**: Execution layer separate from business logic
2. **Minimal State Storage**: Only essential information stored locally
3. **Simple API Interface**: Easy integration with upper application layers
4. **Efficient Router Operations**: Batching and optimization built-in
5. **Stateless Operation**: Can be restarted without losing group functionality
6. **Performance Optimized**: State diffing and caching minimize router load
7. **Extensible Design**: Easy addition of new policy types
8. **Error Resilience**: Comprehensive error handling and recovery

This architecture positions the commands-server as a dedicated, efficient execution engine for network policy management, providing a clean API interface to upper layers while maintaining optimal router performance.

## ⚗️ **Implementation Status & Experimental Areas**

### **Confirmed Working Implementations**
- **Bandwidth Limiting**: Fully confirmed using TC (Traffic Control) + iptables marking
- **Basic Infrastructure**: TC classes, iptables chains, and packet marking proven functional
- **Group Management**: Core group architecture and lazy infrastructure creation
- **Website Blocking**: DNS-based blocking using dnsmasq configuration with device-specific enforcement

### **Website Blocking Implementation Guide**

**Step 1: Create Categorized Blocked Sites Lists**
```bash
# Create modular DNS blocking configuration with categories
mkdir -p /etc/dnsmasq.d

# Social Media Category
echo "address=/facebook.com/127.0.0.1" > /etc/dnsmasq.d/blocked_social_media.conf
echo "address=/facebook.com/::1" >> /etc/dnsmasq.d/blocked_social_media.conf
echo "address=/instagram.com/127.0.0.1" >> /etc/dnsmasq.d/blocked_social_media.conf
echo "address=/instagram.com/::1" >> /etc/dnsmasq.d/blocked_social_media.conf
echo "address=/tiktok.com/127.0.0.1" >> /etc/dnsmasq.d/blocked_social_media.conf
echo "address=/tiktok.com/::1" >> /etc/dnsmasq.d/blocked_social_media.conf

# Streaming Category
echo "address=/netflix.com/127.0.0.1" > /etc/dnsmasq.d/blocked_streaming.conf
echo "address=/netflix.com/::1" >> /etc/dnsmasq.d/blocked_streaming.conf
echo "address=/youtube.com/127.0.0.1" >> /etc/dnsmasq.d/blocked_streaming.conf
echo "address=/youtube.com/::1" >> /etc/dnsmasq.d/blocked_streaming.conf
echo "address=/twitch.tv/127.0.0.1" >> /etc/dnsmasq.d/blocked_streaming.conf
echo "address=/twitch.tv/::1" >> /etc/dnsmasq.d/blocked_streaming.conf

# Adult Content Category
echo "address=/pornhub.com/127.0.0.1" > /etc/dnsmasq.d/blocked_adult.conf
echo "address=/pornhub.com/::1" >> /etc/dnsmasq.d/blocked_adult.conf
echo "address=/xvideos.com/127.0.0.1" >> /etc/dnsmasq.d/blocked_adult.conf
echo "address=/xvideos.com/::1" >> /etc/dnsmasq.d/blocked_adult.conf

# Gaming Category
echo "address=/twitch.tv/127.0.0.1" > /etc/dnsmasq.d/blocked_gaming.conf
echo "address=/twitch.tv/::1" >> /etc/dnsmasq.d/blocked_gaming.conf
echo "address=/steam.com/127.0.0.1" >> /etc/dnsmasq.d/blocked_gaming.conf
echo "address=/steam.com/::1" >> /etc/dnsmasq.d/blocked_gaming.conf

# News/Distracting Sites Category
echo "address=/reddit.com/127.0.0.1" > /etc/dnsmasq.d/blocked_news.conf
echo "address=/reddit.com/::1" >> /etc/dnsmasq.d/blocked_news.conf
echo "address=/cnn.com/127.0.0.1" >> /etc/dnsmasq.d/blocked_news.conf
echo "address=/cnn.com/::1" >> /etc/dnsmasq.d/blocked_news.conf

# Enable the configuration directory
grep -q "conf-dir=/etc/dnsmasq.d" /etc/dnsmasq.conf || echo "conf-dir=/etc/dnsmasq.d" >> /etc/dnsmasq.conf
```

**Step 2: Group-Specific Category Management**
```bash
# Function to activate specific categories for a device group
activate_blocking_categories() {
    local DEVICE_MAC="$1"
    local ROUTER_IP="192.168.1.1"
    shift  # Remove first argument (MAC), rest are categories
    local CATEGORIES=("$@")
    
    # Force device to use router DNS (prevents bypass)
    iptables -t nat -I PREROUTING -m mac --mac-source ${DEVICE_MAC} -p udp --dport 53 -j DNAT --to-destination ${ROUTER_IP}:53
    iptables -t nat -I PREROUTING -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 53 -j DNAT --to-destination ${ROUTER_IP}:53
    
    # Block encrypted DNS (DoT/DoH bypass prevention)
    iptables -I FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 853 -j DROP
    iptables -I FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 443 -d 1.1.1.1 -j DROP
    iptables -I FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 443 -d 8.8.8.8 -j DROP
    
    # Create group-specific DNS blocking configuration
    echo "# Group blocking configuration for MAC: ${DEVICE_MAC}" > /etc/dnsmasq.d/group_${DEVICE_MAC//:/}_blocking.conf
    
    # Combine selected categories into group config
    for category in "${CATEGORIES[@]}"; do
        if [ -f "/etc/dnsmasq.d/blocked_${category}.conf" ]; then
            echo "# --- ${category} category ---" >> /etc/dnsmasq.d/group_${DEVICE_MAC//:/}_blocking.conf
            cat /etc/dnsmasq.d/blocked_${category}.conf >> /etc/dnsmasq.d/group_${DEVICE_MAC//:/}_blocking.conf
        fi
    done
    
    # Restart dnsmasq to apply changes
    killall dnsmasq
    sleep 2
    /usr/sbin/dnsmasq -C /var/etc/dnsmasq.conf.cfg* -k -x /var/run/dnsmasq/*.pid &
}

# Example usage: Block social media and streaming for children's devices
activate_blocking_categories "d8:bb:c1:47:3a:43" "social_media" "streaming"

# Example usage: Block adult content only for guest devices  
activate_blocking_categories "aa:bb:cc:dd:ee:ff" "adult"
```

**Step 3: Category Management Functions**
```bash
# List available blocking categories
list_blocking_categories() {
    echo "Available blocking categories:"
    ls /etc/dnsmasq.d/blocked_*.conf | sed 's|/etc/dnsmasq.d/blocked_||g' | sed 's|\.conf||g'
}

# Add site to specific category
add_site_to_category() {
    local SITE="$1"
    local CATEGORY="$2"
    local CONFIG_FILE="/etc/dnsmasq.d/blocked_${CATEGORY}.conf"
    
    echo "address=/${SITE}/127.0.0.1" >> ${CONFIG_FILE}
    echo "address=/${SITE}/::1" >> ${CONFIG_FILE}
    
    # Restart dnsmasq to apply changes
    killall dnsmasq
    sleep 2
    /usr/sbin/dnsmasq -C /var/etc/dnsmasq.conf.cfg* -k -x /var/run/dnsmasq/*.pid &
}

# Remove site from specific category
remove_site_from_category() {
    local SITE="$1"
    local CATEGORY="$2"
    local CONFIG_FILE="/etc/dnsmasq.d/blocked_${CATEGORY}.conf"
    
    sed -i "/${SITE}/d" ${CONFIG_FILE}
    
    # Restart dnsmasq to apply changes
    killall dnsmasq
    sleep 2
    /usr/sbin/dnsmasq -C /var/etc/dnsmasq.conf.cfg* -k -x /var/run/dnsmasq/*.pid &
}

# Create new blocking category
create_blocking_category() {
    local CATEGORY="$1"
    local CONFIG_FILE="/etc/dnsmasq.d/blocked_${CATEGORY}.conf"
    
    touch ${CONFIG_FILE}
    echo "# ${CATEGORY} category blocking list" > ${CONFIG_FILE}
}
```
```bash
# Example: Block netflix.com for children's devices
DEVICE_MAC="d8:bb:c1:47:3a:43"
ROUTER_IP="192.168.1.1"

# Force device to use router DNS (prevents bypass)
iptables -t nat -I PREROUTING -m mac --mac-source ${DEVICE_MAC} -p udp --dport 53 -j DNAT --to-destination ${ROUTER_IP}:53
iptables -t nat -I PREROUTING -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 53 -j DNAT --to-destination ${ROUTER_IP}:53

# Block encrypted DNS (DoT/DoH bypass prevention)
iptables -I FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 853 -j DROP  # DNS over TLS
iptables -I FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 443 -d 1.1.1.1 -j DROP  # Cloudflare DoH
iptables -I FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 443 -d 8.8.8.8 -j DROP  # Google DoH
```

**Step 3: Activate DNS Configuration**
```bash
# Restart dnsmasq to apply DNS blocking
killall dnsmasq
sleep 2
/usr/sbin/dnsmasq -C /var/etc/dnsmasq.conf.cfg* -k -x /var/run/dnsmasq/*.pid &

# Verify blocking is active
nslookup netflix.com 127.0.0.1  # Should return 127.0.0.1
```

**Step 4: Complete Removal Commands**
```bash
# Remove all DNS blocking rules for a specific device
remove_device_blocking() {
    local DEVICE_MAC="$1"
    
    # Remove group-specific DNS configuration
    rm -f /etc/dnsmasq.d/group_${DEVICE_MAC//:/}_blocking.conf
    
    # Remove iptables rules for specific device
    iptables -t nat -D PREROUTING -m mac --mac-source ${DEVICE_MAC} -p udp --dport 53 -j DNAT --to-destination 192.168.1.1:53 2>/dev/null
    iptables -t nat -D PREROUTING -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 53 -j DNAT --to-destination 192.168.1.1:53 2>/dev/null
    iptables -D FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 853 -j DROP 2>/dev/null
    iptables -D FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 443 -d 1.1.1.1 -j DROP 2>/dev/null
    iptables -D FORWARD -m mac --mac-source ${DEVICE_MAC} -p tcp --dport 443 -d 8.8.8.8 -j DROP 2>/dev/null
    
    # Restart dnsmasq to apply changes
    killall dnsmasq
    sleep 2
    /usr/sbin/dnsmasq -C /var/etc/dnsmasq.conf.cfg* -k -x /var/run/dnsmasq/*.pid &
}

# Remove all blocking categories (complete cleanup)
remove_all_blocking() {
    rm -f /etc/dnsmasq.d/blocked_*.conf
    rm -f /etc/dnsmasq.d/group_*_blocking.conf
    
    # Remove all DNS redirect rules (adjust MAC addresses as needed)
    iptables -t nat -F PREROUTING 2>/dev/null
    iptables -F FORWARD 2>/dev/null
    
    # Restart dnsmasq
    killall dnsmasq
    sleep 2
    /usr/sbin/dnsmasq -C /var/etc/dnsmasq.conf.cfg* -k -x /var/run/dnsmasq/*.pid &
}

# Example: Remove blocking for specific device
remove_device_blocking "d8:bb:c1:47:3a:43"
```

**Frontend Integration Example:**
```javascript
// Frontend checkbox interface for category selection
const blockingCategories = [
    { id: 'social_media', name: 'Social Media', description: 'Facebook, Instagram, TikTok, etc.' },
    { id: 'streaming', name: 'Streaming Services', description: 'Netflix, YouTube, Twitch, etc.' },
    { id: 'adult', name: 'Adult Content', description: 'Adult and inappropriate content' },
    { id: 'gaming', name: 'Gaming', description: 'Steam, Epic Games, Battle.net, etc.' },
    { id: 'news_distracting', name: 'News & Distracting', description: 'Reddit, CNN, BuzzFeed, etc.' }
];

// API call to update group blocking categories
const updateGroupBlocking = async (groupId, selectedCategories) => {
    const response = await fetch(`/api/groups/${groupId}/blocking`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            blocked_categories: selectedCategories 
        })
    });
    return response.json();
};
```

### **Experimental/Research Required**
The following policy types require router experimentation to determine optimal implementation:

#### **Website/Content Blocking**
**Potential Methods:**
- **iptables string matching**: `iptables -m string --string "domain.com"` ❌ (string module not available on OpenWrt)
- **DNS-based blocking**: dnsmasq configuration or DNS redirection ✅ (confirmed working)
- **IP-based blocking**: Using ipset lists for blocked domains ❌ (not practical - too many changing IPs)
- **Proxy-based filtering**: Transparent proxy with content filtering

**Confirmed Working Implementation:**
```bash
# Global DNS blocking (affects all devices)
echo "address=/netflix.com/127.0.0.1" > /etc/dnsmasq.d/blocked_sites.conf
echo "address=/netflix.com/::1" >> /etc/dnsmasq.d/blocked_sites.conf
grep -q "conf-dir=/etc/dnsmasq.d" /etc/dnsmasq.conf || echo "conf-dir=/etc/dnsmasq.d" >> /etc/dnsmasq.conf
killall dnsmasq && /usr/sbin/dnsmasq -C /var/etc/dnsmasq.conf.cfg* -k -x /var/run/dnsmasq/*.pid &
```

**Device-Specific DNS Blocking (Group-Based):**
For blocking specific devices only, combine DNS blocking with iptables DNS redirection:
```bash
# Force specific devices to use router DNS (prevents DNS bypass)
iptables -t nat -I PREROUTING -m mac --mac-source {device_mac} -p udp --dport 53 -j DNAT --to-destination 192.168.1.1:53
iptables -t nat -I PREROUTING -m mac --mac-source {device_mac} -p tcp --dport 53 -j DNAT --to-destination 192.168.1.1:53

# Block encrypted DNS to prevent bypass
iptables -I FORWARD -m mac --mac-source {device_mac} -p tcp --dport 853 -j DROP
iptables -I FORWARD -m mac --mac-source {device_mac} -p tcp --dport 443 -d 1.1.1.1 -j DROP
iptables -I FORWARD -m mac --mac-source {device_mac} -p tcp --dport 443 -d 8.8.8.8 -j DROP
```

#### **Time-Based Policy Activation**
**Potential Methods (requires testing):**
- **UCI firewall rules**: OpenWrt's native firewall configuration with time-based rules (start_time, stop_time, weekdays)
- **Cron-based activation**: Scripts triggered by cron jobs
- **iptables time module**: `iptables -m time --timestart --timestop`
- **Persistent daemon**: Background service managing time-based changes
- **Router-native scheduling**: Using router's built-in scheduling if available

#### **Website/Content Blocking & Access Control**
**Potential Methods (requires testing):**
- **UCI firewall rules**: OpenWrt's native firewall with domain/URL filtering capabilities
- **DNS-based blocking**: dnsmasq configuration or DNS redirection
- **iptables string matching**: `iptables -m string --string "domain.com"`
- **IP-based blocking**: Using ipset lists for blocked domains
- **Proxy-based filtering**: Transparent proxy with content filtering
- **Whitelist-only access**: UCI firewall rules configured for default-deny with explicit allow lists for specific websites

#### **Advanced Access Control**
**Potential Methods (requires testing):**
- **UCI firewall comprehensive control**: Complete internet blocking with whitelist exceptions using OpenWrt's native configuration
- **Application identification**: DPI (Deep Packet Inspection) or port-based filtering
- **Category-based blocking**: Integration with web categorization services
- **Whitelist-only mode**: Default-deny with explicit allow rules for specific websites/services
- **MAC-based filtering**: Device-level access control using wireless interface MAC filtering

### **Implementation Priority**
1. **Core Infrastructure**: Group management and basic bandwidth limiting ✅
2. **Enhanced Bandwidth**: Multi-group support and time-based changes
3. **UCI Firewall Integration**: Experiment with OpenWrt's native firewall for time-based and access control policies
4. **Website Blocking**: Test various blocking methods including UCI firewall, DNS, and iptables approaches
5. **Time Automation**: Implement UCI firewall time-based rules and/or cron-based scheduling
6. **Advanced Features**: Application control, categories, quotas, and whitelist-only modes

**Note**: The architecture is designed to be implementation-agnostic for experimental features. The UCI firewall method appears promising for both time-based controls and comprehensive access management (including complete blocking with whitelist exceptions). The final choice of methods will depend on router capabilities, performance testing, and reliability requirements discovered during manual experimentation.

## 💡 **Commands-Server Benefits**

1. **Clear Separation of Concerns**: Execution layer separate from business logic
2. **Minimal State Storage**: Only essential information stored locally
3. **Simple API Interface**: Easy integration with upper application layers
4. **Efficient Router Operations**: Batching and optimization built-in
5. **Stateless Operation**: Can be restarted without losing group functionality
6. **Performance Optimized**: State diffing and caching minimize router load
7. **Extensible Design**: Easy addition of new policy types
8. **Error Resilience**: Comprehensive error handling and recovery

This architecture positions the commands-server as a dedicated, efficient execution engine for network policy management, providing a clean API interface to upper layers while maintaining optimal router performance.
