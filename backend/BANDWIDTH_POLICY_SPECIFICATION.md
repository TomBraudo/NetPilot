# NetPilot Groups Bandwidth Policy Specification

## Overview
NetPilot's group-based architecture replaces the traditional whitelist/blacklist mode separation with per-group bandwidth and access policies.

## Bandwidth Policy Behavior

### Policy Field
Each group has a `bandwidth_limit_mbps` field in its `GroupPolicySummary`:
- **Type**: `Optional[int]` (can be `None` or a positive integer)
- **Unit**: Megabits per second (Mbps)

### Implementation Rules

#### Case 1: `bandwidth_limit_mbps = None`
- **Behavior**: No traffic control rules are applied
- **TC Rule**: No TC class bandwidth limit is set
- **iptables**: No packet marking or forwarding restrictions
- **Result**: All group members have unrestricted internet access

#### Case 2: `bandwidth_limit_mbps = <number>`
- **Behavior**: Traffic control rules are applied to limit bandwidth
- **TC Rule**: The group's TC class (e.g., `1:101`) is configured with the specified rate limit
- **iptables**: Packets from group members are marked with the group's mark value
- **Forwarding**: All marked packets are directed to the limited TC class
- **Result**: All group members are collectively limited to the specified Mbps

## Implementation Architecture

### State File Structure
```json
{
  "groups": {
    "0": {
      "name": "Guest Group",
      "tc_class": "1:100",
      "mark_value": 100,
      "policies": {
        "bandwidth_limit_mbps": null  // Unrestricted
      }
    },
    "1": {
      "name": "Limited Users",
      "tc_class": "1:101", 
      "mark_value": 101,
      "policies": {
        "bandwidth_limit_mbps": 50  // 50 Mbps limit
      }
    }
  }
}
```

### Traffic Control Flow
1. **Device Assignment**: Devices are assigned to groups with unique TC classes
2. **Packet Marking**: iptables marks packets based on source IP/MAC matching group membership
3. **Traffic Shaping**: TC classes apply bandwidth limits only when `bandwidth_limit_mbps` is not null
4. **Forwarding**: Marked packets are directed to appropriate TC classes

## Use Cases

### Scenario 1: Mixed Access Policies
- **Group 0** (Guests): `bandwidth_limit_mbps: 15` (15 Mbps limit)
- **Group 1** (VIP Users): `bandwidth_limit_mbps: null` (unlimited)
- **Group 2** (Standard Users): `bandwidth_limit_mbps: 30` (30 Mbps limit)
- **Group 3** (Blocked Users): `block_all_internet: true` (no access)

### Scenario 2: Dynamic Policy Changes
- Groups can have their `bandwidth_limit_mbps` updated at runtime
- Changes require TC class reconfiguration and iptables rule updates
- No service interruption for other groups

## Future Service Requirements

### TC Class Management
- Create TC classes with bandwidth limits only when `bandwidth_limit_mbps` is numeric
- Remove/modify TC class limits when policy changes to/from `null`
- Maintain separate TC classes for each group to enable independent control

### iptables Integration  
- Mark packets based on group membership (IP/MAC matching)
- Direct marked packets to appropriate TC classes
- Handle group membership changes (device additions/removals)

### Policy Synchronization
- Monitor state file changes for bandwidth policy updates
- Apply TC and iptables changes when policies are modified
- Ensure atomic updates to prevent traffic disruption

## Backward Compatibility
This group-based approach **completely replaces** the legacy whitelist/blacklist modes:
- **Legacy Whitelist Mode** → Groups with `block_all_internet: false` and appropriate bandwidth limits
- **Legacy Blacklist Mode** → Groups with `block_all_internet: true` for blocked devices
- **Mixed Policies** → Not possible with legacy system, fully supported with groups

## Legacy System Deprecation

### Services Marked for Replacement
The following legacy services are **redundant** and will be completely replaced:
- `whitelist_service.py` - Replaced by group-based device assignment
- `blacklist_service.py` - Replaced by group-based `block_all_internet` policy
- `mode_activation_service.py` - Replaced by per-group policy activation
- `device_rule_service.py` - Replaced by group-based iptables management
- `router_setup_service.py` - Replaced by group-aware infrastructure setup

### Critical Issue: IP Marking Conflicts
**WARNING**: The legacy system causes ambiguous IP packet marking that breaks functionality:
- Legacy services mark packets globally without group context
- Multiple marking systems create conflicting iptables rules
- Packets can be marked by both legacy and group systems simultaneously
- Traffic control becomes unpredictable with overlapping marks

### Migration Strategy
1. **No Backward Compatibility**: Legacy services will not coexist with group system
2. **Complete Replacement**: All legacy functionality reimplemented with group awareness
3. **Clean Slate**: Remove all legacy iptables rules before group system activation
4. **Atomic Transition**: Switch from legacy to group system must be complete and immediate

This ensures consistent, predictable traffic control without marking conflicts.
