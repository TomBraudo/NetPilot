# NetPilot Commands-Server Groups Implementation Plan

## 🎯 **Overview**

This plan outlines the implementation of group-based policy management in the commands-server over a 2-week sprint. The implementation follows a phased approach: establishing base infrastructure, then adding group support to existing features, and finally implementing new group-enabled features.

## ⏱️ **Timeline: 2-Week Sprint**

- **Week 1**: Phases 1-3 (Base infrastructure + existing feature integration)
- **Week 2**: Phases 4-5 (New features + testing/optimization)

## 📋 **Working Guidelines**

**Critical Development Principles:**

1. **🚫 No Sequential Thinking MCP**: Do not use the sequential thinking MCP tool. Think and plan before implementing, but make decisions directly and implement without using sequential thinking tools.

2. **🎯 Step-by-Step Execution**: Work methodically through each task in order. Complete one subtask fully before moving to the next.

3. **🔍 Targeted Changes**: Make focused, specific changes that address exactly what is requested. Avoid scope creep or unnecessary modifications.

4. **📌 Stay On Task**: Perform only what is explicitly asked for in each subtask. Do not add extra features, optimizations, or "improvements" unless specifically required.

5. **✅ Complete Before Moving**: Mark each checkbox only when the subtask is fully implemented and tested.

6. **🧪 Test Immediately**: Test each component as soon as it's implemented, before moving to dependent components. Create unit tests in the `tests/` folder with proper structure: `tests/unit/` for unit tests, `tests/integration/` for integration tests.

---

## 📋 **Phase 1: Base Classes and Data Structures** 
*Duration: Days 1-2*

### **1.1 Core Data Structures** 
- [x] Create `DeviceInfo` dataclass
- [x] Create `GroupState` dataclass 
- [x] Create `GroupPolicySummary` dataclass
- [x] Create `GroupSyncRequest` dataclass
- [x] Create `DeviceVerificationResult` dataclass
- [x] Create `DeviceChanges` dataclass
- [x] Create `RouterCommandBundle` dataclass
- [x] Add policy-related dataclasses (`BandwidthPolicy`, `AccessControlPolicy`, `TimeBasedPolicy`)
- [x] Create `PolicyAction` enum

### **1.2 State File Manager Base Class**
- [x] Create `StateFileManager` class with basic file I/O operations
- [x] Implement `load_state()` method
- [x] Implement `save_group_state()` method
- [x] Implement `delete_group_state()` method
- [x] Implement `get_group_state()` method
- [x] Add TC class allocation methods (`allocate_tc_class`, `release_tc_class`)

### **1.3 Device Management Methods**
- [x] Implement `verify_devices()` method for device validation
- [x] Implement `update_group_devices()` method
- [x] Implement `get_device_changes()` method
- [x] Add device validation logic (IP/MAC format, duplicates)

---

## 🎯 **Phase 1 Completion Summary**

**✅ PHASE 1 COMPLETED** - All foundational components implemented and tested.

### Key Achievements:
- **Complete Data Architecture**: All 9 dataclasses created with proper typing and validation
- **StateFileManager Singleton**: 750+ line centralized state manager with comprehensive CRUD operations
- **New State Format**: Group-based JSON structure replacing legacy format entirely
- **TC Class Management**: Automatic allocation/release system for traffic control classes (1:100+)
- **Device Validation**: IP/MAC format validation, duplicate prevention across groups
- **Group 0 Protection**: Guest Group (ID 0) pre-configured and deletion-protected
- **Infrastructure Integration**: Updated `infrastructure_setup.py` to use new StateFileManager

### Architecture Decisions Made:
- **No Backward Compatibility**: Legacy services will be completely replaced due to IP marking conflicts
- **Bandwidth Policy**: `null` = unrestricted, `<number>` = TC rule applied to all group members
- **Request-Scoped StateFileManager**: Each request gets its own StateFileManager instance via Flask's `g` object to prevent race conditions
- **Group-Based Paradigm**: Eliminates whitelist/blacklist mode separation in favor of per-group policies

### Critical Race Condition Fix Required:
**ISSUE IDENTIFIED**: Current singleton StateFileManager has race condition in multi-router environment:
- Shared `_cached_state` across all requests can mix router data
- Single instance serves multiple concurrent router requests
- Thread switching can cause Router X data to be written to Router Y

**SOLUTION**: Request-scoped StateFileManager instances:
- Create StateFileManager per request in Flask's `g` object  
- Each instance has isolated cache for its router
- RouterConnectionManager already handles router routing via `g.router_id`
- No shared state between concurrent requests

### Technical Foundation:
- **20+ Unit Tests**: Full test coverage with mocking for router operations
- **Comprehensive Validation**: Device format checking, duplicate detection, state structure validation
- **Error Handling**: Graceful fallbacks with default state creation
- **Performance Optimized**: Cached state with timestamp validation

**Ready for Phase 2**: State file infrastructure migration and Group 0 setup.

---

## 📋 **Phase 2: State File Infrastructure**
*Duration: Days 2-3*

### **2.1 State File Schema Migration**
- [ ] **CRITICAL: Fix StateFileManager race condition** - Convert from singleton to request-scoped instances
- [ ] Create `get_state_manager()` helper function using Flask's `g` object
- [ ] Update all StateFileManager usage to use `get_state_manager()` instead of direct instantiation
- [ ] Update unit tests to mock Flask's `g` object properly
- [ ] Design new state file JSON schema with groups structure
- [ ] Create migration script from current state file format
- [ ] Implement backup mechanism for state file changes
- [ ] Add state file versioning for future migrations

### **2.2 Group 0 (Guest Group) Setup**
- [ ] Ensure Group 0 always exists in state file
- [ ] Implement Group 0 default configuration
- [ ] Add Group 0 protection (cannot be deleted)
- [ ] Set up TC class `1:100` and mark value `100` for Group 0

### **2.3 Infrastructure Tracking** 
- [ ] Add infrastructure status tracking in state file
- [ ] Implement available TC classes pool management
- [ ] Add base setup completion tracking
- [ ] Implement next mark value allocation logic

---

## 📋 **Phase 3: Existing Feature Integration**
*Duration: Days 4-6*

### **3.1 Bandwidth Limiting Group Support**
- [ ] Modify existing bandwidth limiting to work with groups
- [ ] Update TC commands generation for group-specific classes
- [ ] Implement device-to-group marking in iptables
- [ ] Test bandwidth limiting with multiple groups
- [ ] Add group-specific bandwidth policy compilation

### **3.2 API Service Layer**
- [ ] Create `GroupAPIService` class
- [ ] Implement `sync_group()` endpoint handler
- [ ] Implement `update_group_policy()` endpoint handler  
- [ ] Implement `delete_group()` endpoint handler
- [ ] Implement `get_group_status()` endpoint handler
- [ ] Add `sync_all_groups()` batch endpoint handler
- [ ] Implement `get_infrastructure_status()` endpoint handler

### **3.3 Policy Compilation Layer**
- [ ] Create `GroupPolicyCompiler` class
- [ ] Implement `compile_sync_request()` main method
- [ ] Implement `_compile_bandwidth_policy()` method
- [ ] Implement `_calculate_state_diff()` method
- [ ] Add device change detection in compilation
- [ ] Implement minimal command generation (only changed components)

### **3.4 Router Operations Engine**
- [ ] Create `RouterOperationsEngine` class
- [ ] Implement `apply_command_bundle()` method
- [ ] Implement `create_group_infrastructure()` method
- [ ] Implement `cleanup_group_infrastructure()` method
- [ ] Add `verify_router_state()` method
- [ ] Implement lazy infrastructure creation logic

---

## 📋 **Phase 4: New Features Implementation**
*Duration: Days 7-10*

### **4.1 Website/Content Blocking**
- [ ] Implement DNS-based blocking infrastructure
- [ ] Create predefined blocking categories structure
- [ ] Implement `_compile_access_control_policy()` method
- [ ] Add device-specific DNS redirection rules
- [ ] Implement DNS bypass prevention (DoT/DoH blocking)
- [ ] Create category management functions
- [ ] Add group-specific dnsmasq configuration generation

### **4.2 Time-Based Policies**
- [ ] Implement `_compile_time_based_policy()` method
- [ ] Add cron job management for time-based activation
- [ ] Implement policy override and restoration logic
- [ ] Add time-based chain creation (NETPILOT_NIGHT_MODE, etc.)
- [ ] Implement timezone awareness
- [ ] Add overlapping policy conflict resolution

### **4.3 Advanced Infrastructure Management**
- [ ] Implement specialized iptables chains creation
- [ ] Add group-specific chain management (NETPILOT_GROUP_{id})
- [ ] Implement time-based chain lifecycle management
- [ ] Add chain cleanup on group deletion
- [ ] Implement infrastructure optimization strategies

---

## 📋 **Phase 5: Testing, Integration & Optimization**
*Duration: Days 11-14*

### **5.1 API Integration Testing**
- [ ] Create unit tests for `GroupAPIService` class in `tests/unit/test_group_api_service.py`
- [ ] Create unit tests for all API endpoint handlers
- [ ] Test complete group sync workflow
- [ ] Test device addition/removal scenarios
- [ ] Test policy update operations
- [ ] Test group deletion and cleanup
- [ ] Test batch synchronization operations
- [ ] Validate API response formats and error handling

### **5.2 Router State Validation**
- [ ] Create unit tests for `RouterOperationsEngine` class in `tests/unit/test_router_operations_engine.py`
- [ ] Create unit tests for `GroupPolicyCompiler` class in `tests/unit/test_group_policy_compiler.py`
- [ ] Test infrastructure creation and cleanup
- [ ] Validate TC classes and iptables rules
- [ ] Test DNS configuration generation
- [ ] Verify cron job creation and cleanup
- [ ] Test state file consistency after operations

### **5.3 Performance Optimization**
- [ ] Implement command batching optimization
- [ ] Add router state caching mechanisms
- [ ] Optimize state file I/O operations
- [ ] Test performance with multiple groups and devices
- [ ] Implement operation timing and monitoring

### **5.4 Error Handling & Recovery**
- [ ] Add comprehensive error handling for all operations
- [ ] Implement rollback mechanisms for failed operations
- [ ] Add operation logging and audit trails
- [ ] Test error scenarios and recovery procedures
- [ ] Implement health check mechanisms

### **5.5 Documentation & Examples**
- [ ] Create API documentation with examples
- [ ] Add inline code documentation
- [ ] Create troubleshooting guide
- [ ] Document state file format and migration procedures
- [ ] Add performance tuning guidelines

---

## 🔄 **Integration Points**

### **Existing System Integration**
- [ ] Integrate with current bandwidth limiting system
- [ ] Maintain compatibility with existing state file
- [ ] Ensure backwards compatibility for existing API endpoints
- [ ] Migrate existing device rules to Group 0

### **Upper Layer Integration** 
- [ ] Define clear API contract for upper layer communication
- [ ] Implement request validation and sanitization
- [ ] Add authentication/authorization hooks for API endpoints
- [ ] Create integration examples for upper layer consumption

---

## ⚠️ **Risk Mitigation**

### **Technical Risks**
- [ ] Create comprehensive backup procedures before state file changes
- [ ] Implement gradual rollout mechanism for infrastructure changes
- [ ] Add extensive logging for debugging complex group interactions
- [ ] Create automated testing for critical paths

### **Operational Risks**
- [ ] Implement graceful degradation when state file is corrupted
- [ ] Add monitoring for router infrastructure health
- [ ] Create manual recovery procedures for failed operations
- [ ] Implement configuration validation before applying changes

---

## 📊 **Success Criteria**

### **Functional Requirements**
- [ ] Multiple groups can be created, modified, and deleted
- [ ] Device membership can be updated dynamically
- [ ] Bandwidth policies apply correctly per group
- [ ] Website blocking works with category-based filtering
- [ ] Time-based policies activate and deactivate automatically
- [ ] API responses include detailed operation results

### **Performance Requirements**  
- [ ] Group sync operations complete within 500ms
- [ ] Infrastructure creation completes within 800ms
- [ ] State file operations remain under 200ms
- [ ] System supports at least 10 concurrent groups
- [ ] Batch operations show significant performance improvement

### **Reliability Requirements**
- [ ] State file remains consistent after all operations
- [ ] Router infrastructure matches state file records
- [ ] Failed operations do not leave partial configurations
- [ ] System recovers gracefully from router communication failures
- [ ] All operations are properly logged for audit purposes

---

## 🎯 **Post-Sprint Activities**

### **Monitoring & Maintenance**
- [ ] Set up operational monitoring dashboards
- [ ] Create automated health checks
- [ ] Establish performance baseline metrics
- [ ] Document operational procedures

### **Future Enhancements**
- [ ] Plan for additional policy types (QoS, quotas, etc.)
- [ ] Design scalability improvements for larger deployments  
- [ ] Consider advanced features (ML-based policies, etc.)
- [ ] Plan integration with network monitoring systems
