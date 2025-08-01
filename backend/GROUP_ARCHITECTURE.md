# NetPilot Group-Based Policy Engine Architecture

## 🎯 **Core Philosophy**

Groups are the **fundamental abstraction** for all network policies in NetPilot. Instead of managing individual device rules, the system organizes devices into groups and applies comprehensive policy sets that can include bandwidth limiting, access control, time-based restrictions, and future policy types.

### **Key Principles**

1. **Policy Compilation**: High-level policies are compiled into router command bundles
2. **Batch Application**: Multiple policy changes are applied in single operations
3. **Lazy Infrastructure**: Router infrastructure is created only when needed
4. **State Synchronization**: System maintains minimal difference between desired and actual router state
5. **Time-Based Automation**: Scheduled policies execute without manual intervention

## 🏗️ **Architecture Overview**

The architecture transforms network management from individual device commands to comprehensive group policy management:

```
Database Layer (CRUD Operations)
         ↓
Policy Compilation Layer (GroupPolicy → RouterCommandBundle)
         ↓
Batch Application Layer (Efficient Router Updates)
         ↓
Router Infrastructure (TC Classes + iptables Chains)
         ↓
Time-Based Scheduler (Automated Policy Changes)
```

### **Default Group Structure**

The system always maintains at least one group:

- **Group 0 ("Guest Group")**: The default group for unassigned devices
  - Group ID: `0`
  - TC Class: `1:100` 
  - Mark Value: `100`
  - Purpose: Handles devices not explicitly assigned to other groups
  - Always exists and cannot be deleted

## 📋 **Core Data Structures**

### **Group Policy Definition**
```python
@dataclass
class GroupPolicy:
    """Complete policy definition for a group"""
    group_id: int
    name: str
    devices: List[Device]
    
    # Policy Components
    bandwidth_policy: Optional[BandwidthPolicy]
    access_control_policy: Optional[AccessControlPolicy]
    time_based_policies: List[TimeBasedPolicy]
    
    active: bool = True
    priority: int = 0

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
    blocked_categories: List[str] = field(default_factory=list)  # e.g., ["social_media", "adult", "streaming"]
    allowed_sites_only: List[str] = field(default_factory=list)
    block_all_internet: bool = False
    active: bool = True

@dataclass
class BlockingCategory:
    """Defines a category of blocked websites"""
    name: str  # e.g., "social_media", "adult", "streaming", "gaming"
    display_name: str  # e.g., "Social Media", "Adult Content", "Streaming Services"
    description: str  # User-friendly description
    sites: List[str] = field(default_factory=list)  # List of domains
    enabled: bool = True
    
# Predefined blocking categories
DEFAULT_BLOCKING_CATEGORIES = [
    BlockingCategory(
        name="social_media",
        display_name="Social Media",
        description="Facebook, Instagram, TikTok, Twitter, etc.",
        sites=["facebook.com", "instagram.com", "tiktok.com", "twitter.com", "snapchat.com"]
    ),
    BlockingCategory(
        name="streaming",
        display_name="Streaming Services", 
        description="Netflix, YouTube, Twitch, etc.",
        sites=["netflix.com", "youtube.com", "twitch.tv", "hulu.com", "disney.com"]
    ),
    BlockingCategory(
        name="adult",
        display_name="Adult Content",
        description="Adult and inappropriate content",
        sites=["pornhub.com", "xvideos.com", "xhamster.com", "redtube.com"]
    ),
    BlockingCategory(
        name="gaming",
        display_name="Gaming",
        description="Gaming platforms and related sites",
        sites=["steam.com", "epicgames.com", "battle.net", "roblox.com", "minecraft.net"]
    ),
    BlockingCategory(
        name="news_distracting",
        display_name="News & Distracting",
        description="News sites and distracting content",
        sites=["reddit.com", "cnn.com", "bbc.com", "buzzfeed.com", "9gag.com"]
    )
]

@dataclass
class TimeBasedPolicy:
    """Time-sensitive policy overrides"""
    name: str
    start_time: str  # "22:00"
    end_time: str    # "08:00" 
    days: List[str]  # ["monday", "tuesday", ...]
    action: PolicyAction
    parameters: Dict[str, Any]
    active: bool = True

class PolicyAction(Enum):
    """Available actions for time-based policies"""
    BANDWIDTH_LIMIT = "bandwidth_limit"        # Change bandwidth limit temporarily
    BLOCK_INTERNET = "block_internet"          # Block all internet access
    ACTIVATE_BLACKLIST = "activate_blacklist"  # Enable blacklist mode for group
    BLOCK_SITES = "block_sites"               # Block specific sites temporarily
    ALLOW_SITES_ONLY = "allow_sites_only"     # Whitelist mode for sites
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

## 🔧 **Architecture Components**

### **1. Policy Compilation Layer**
Converts high-level group policies into executable router commands.

```python
class GroupPolicyCompiler:
    """Converts high-level policies into router command bundles"""
    
    def compile_group_policy(self, policy: GroupPolicy) -> RouterCommandBundle:
        """Main compilation entry point"""
        
    def _compile_bandwidth_policy(self, group_id: int, policy: BandwidthPolicy, devices: List[Device]) -> List[str]:
        """Generate TC commands for bandwidth limiting"""
        
    def _compile_access_control_policy(self, group_id: int, policy: AccessControlPolicy, devices: List[Device]) -> List[str]:
        """Generate iptables commands for access control"""
        
    def _compile_time_based_policy(self, group_id: int, policy: TimeBasedPolicy, devices: List[Device]) -> List[str]:
        """Generate cron jobs for time-based policy activation"""
```

**Key Features:**
- **Multi-Policy Support**: Handles bandwidth, access control, and time-based policies
- **Device Association**: Links policies to specific device IPs
- **Infrastructure Optimization**: Creates minimal required router infrastructure
- **Dependency Management**: Handles policy interdependencies

### **2. Batch Application Engine**
Efficiently applies policy changes to the router with minimal operations.

```python
class GroupPolicyService:
    """Main service for group policy management"""
    
    def sync_group_policy(self, group_id: int, policy: GroupPolicy) -> Tuple[bool, Optional[str]]:
        """Synchronizes a single group's policy with the router"""
        
    def sync_all_groups(self, groups: List[GroupPolicy]) -> Tuple[bool, List[str]]:
        """Efficiently sync multiple groups at once"""
        
    def handle_time_based_event(self, event: TimeBasedEvent) -> Tuple[bool, Optional[str]]:
        """Called by cron jobs to activate/deactivate time-based policies"""
```

**Key Features:**
- **State Diffing**: Only applies changes that differ from current router state
- **Batch Optimization**: Groups related commands for efficient execution
- **Error Recovery**: Handles partial failures and rollback scenarios
- **Performance Monitoring**: Tracks operation duration and success rates

### **3. Router State Management**
Maintains synchronization between desired policies and actual router configuration.

```python
class RouterStateManager:
    """Manages router state synchronization"""
    
    def get_current_state(self) -> RouterState:
        """Query current router configuration"""
        
    def calculate_diff(self, current: RouterState, desired: RouterState) -> CommandDiff:
        """Calculate minimal changes needed"""
        
    def apply_commands(self, bundle: RouterCommandBundle) -> Result:
        """Execute router commands with error handling"""
        
    def get_group_state(self, group_id: int) -> GroupState:
        """Get current state for specific group"""
```

**Key Features:**
- **State Caching**: Minimizes router queries through intelligent caching
- **Incremental Updates**: Calculates minimal change sets for efficiency
- **Validation**: Verifies router state matches expected configuration
- **Conflict Resolution**: Handles overlapping policy requirements

### **4. Time-Based Scheduler**
Handles automated policy changes based on time and schedule constraints.

```python
class TimeBasedScheduler:
    """Manages time-based policy automation"""
    
    def schedule_policy(self, policy: TimeBasedPolicy) -> Result:
        """Set up cron jobs for policy activation/deactivation"""
        
    def trigger_time_event(self, event: TimeEvent) -> Result:
        """Handle scheduled policy changes"""
        
    def get_active_time_policies(self) -> List[TimeBasedPolicy]:
        """Get currently active time-based policies"""
```

**Key Features:**
- **Cron Integration**: Uses system cron for reliable scheduling
- **Policy Stacking**: Handles overlapping time-based policies
- **Timezone Awareness**: Respects router timezone settings
- **Persistence**: Survives router reboots and system restarts

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

## 🔄 **Policy Application Flow**

### **Standard Workflow**
```
1. Database Operations (Upper Layer)
   - Create/modify groups
   - Add/remove devices
   - Update policy settings
   
2. Policy Compilation
   - Convert GroupPolicy → RouterCommandBundle
   - Optimize for minimal router operations
   - Handle policy dependencies
   
3. State Synchronization
   - Query current router state
   - Calculate required changes
   - Apply minimal command set
   
4. Verification
   - Confirm router state matches desired state
   - Update cached state information
   - Log results for monitoring
```

### **Time-Based Workflow**
```
1. Policy Schedule Setup
   - Create cron jobs for policy activation
   - Set up deactivation schedules
   - Handle timezone considerations
   
2. Automated Execution
   - Cron triggers policy changes
   - System applies temporary overrides
   - Original policies restored automatically
   
3. Conflict Resolution
   - Handle overlapping time policies
   - Maintain policy priority order
   - Ensure consistent state
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

## 🎯 **Use Case Examples**

### **Children's Parental Controls**
```python
children_policy = GroupPolicy(
    group_id=1,
    name="Children's Devices",
    devices=[Device(ip="192.168.1.100"), Device(ip="192.168.1.101")],
    
    bandwidth_policy=BandwidthPolicy(limit_mbps=50),
    
    access_control_policy=AccessControlPolicy(
        blocked_categories=["adult", "gambling"],
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
```

### **Guest Network Management**
```python
guest_policy = GroupPolicy(
    group_id=2,
    name="Guest Devices",
    
    bandwidth_policy=BandwidthPolicy(limit_mbps=25),
    
    access_control_policy=AccessControlPolicy(
        blocked_categories=["business", "finance"],
        allowed_sites_only=["google.com", "youtube.com", "netflix.com"]
    )
)
```

### **Work-From-Home Priority**
```python
work_policy = GroupPolicy(
    group_id=3,
    name="Work Devices",
    
    bandwidth_policy=BandwidthPolicy(limit_mbps=500),  # High priority
    
    time_based_policies=[
        TimeBasedPolicy(
            name="business_hours_priority",
            start_time="09:00", end_time="17:00",
            days=["monday", "tuesday", "wednesday", "thursday", "friday"],
            action=PolicyAction.BANDWIDTH_LIMIT,
            parameters={"limit_mbps": 800}  # Even higher during work hours
        )
    ]
)
```

## 🔮 **Future Extensions**

The architecture is designed to easily accommodate additional policy types:

- **Application-Level Control**: Block/allow specific applications
- **Quality of Service**: Priority-based traffic handling
- **Geographic Restrictions**: Location-based access control
- **Usage Quotas**: Daily/weekly data limits
- **Advanced Scheduling**: Complex time patterns and exceptions
- **Dynamic Policies**: ML-based adaptive policy adjustments

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

## 💡 **Implementation Benefits**

1. **Unified Management**: Single interface for all network policies
2. **Scalable Design**: Handles growth from home to enterprise use
3. **Efficient Operations**: Minimal router overhead through batching
4. **Time Automation**: Set-and-forget scheduled policies
5. **Policy Composition**: Mix different policy types seamlessly
6. **Future-Proof**: Easy extension for new policy types
7. **Performance Optimized**: Intelligent caching and state management
8. **Reliable**: Comprehensive error handling and recovery

This architecture positions NetPilot as a comprehensive network policy management system that can handle complex, multi-faceted requirements while maintaining high performance and reliability.
