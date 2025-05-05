import unittest
import os
import sys
import tempfile
import shutil
from tinydb import TinyDB, Query
from unittest.mock import patch, MagicMock

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We'll mock the db_client, not try to create a real one
from db.schema_initializer import initialize_default_group, initialize_predefined_rules, initialize_all_tables, reset_all_tables

class TestDatabaseBehavior(unittest.TestCase):
    """Test cases for TinyDB behavior in the application."""
    
    def setUp(self):
        """Set up a temporary database for tests."""
        # Create a temp directory for our test database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_db.json")
        
        # Create a real TinyDB instance for testing
        self.db = TinyDB(self.db_path)
        
        # Create all the tables we need
        self.devices = self.db.table('devices')
        self.device_groups = self.db.table('device_groups')
        self.group_members = self.db.table('group_members')
        self.rules = self.db.table('rules')
        self.device_rules = self.db.table('device_rules')
        
        # Create a mock db_client
        self.mock_db_client = MagicMock()
        self.mock_db_client.devices = self.devices
        self.mock_db_client.device_groups = self.device_groups
        self.mock_db_client.group_members = self.group_members
        self.mock_db_client.rules = self.rules
        self.mock_db_client.device_rules = self.device_rules
        self.mock_db_client.clear_all.side_effect = lambda: [table.truncate() for table in 
                                                           [self.devices, self.device_groups, 
                                                            self.group_members, self.rules, 
                                                            self.device_rules]]
        
        # Patch the db_client to use our mock
        self.patcher = patch('db.schema_initializer.db_client', self.mock_db_client)
        self.mock_db = self.patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.patcher.stop()
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_default_group_initialization(self):
        """Test that the default 'general' group is created."""
        # First make sure the group doesn't exist
        Group = Query()
        self.assertIsNone(self.device_groups.get(Group.name == 'general'))
        
        # Initialize the default group
        initialize_default_group()
        
        # Verify the group now exists
        result = self.device_groups.get(Group.name == 'general')
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'general')
    
    def test_predefined_rules_initialization(self):
        """Test that predefined rules are correctly initialized."""
        initialize_predefined_rules()
        
        # Check all expected rules exist
        expected_rules = ['block', 'limit_bandwidth', 'schedule', 'priority']
        Rule = Query()
        
        for rule_name in expected_rules:
            rule = self.rules.get(Rule.name == rule_name)
            self.assertIsNotNone(rule, f"Rule '{rule_name}' not found")
    
    def test_initialize_all_tables(self):
        """Test full initialization of all tables."""
        initialize_all_tables()
        
        # Verify default group exists
        Group = Query()
        result = self.device_groups.get(Group.name == 'general')
        self.assertIsNotNone(result)
        
        # Verify predefined rules exist
        rules = self.rules.all()
        self.assertGreater(len(rules), 0)
    
    def test_reset_all_tables(self):
        """Test resetting all tables to default state."""
        # Add some test data
        self.devices.insert({"mac": "00:11:22:33:44:55", "name": "Test Device"})
        
        # Verify data exists
        self.assertEqual(len(self.devices.all()), 1)
        
        # Reset tables
        reset_all_tables()
        
        # Verify device data is gone
        self.assertEqual(len(self.devices.all()), 0)
        
        # Verify default group and rules are back
        Group = Query()
        self.assertIsNotNone(self.device_groups.get(Group.name == 'general'))
        self.assertGreater(len(self.rules.all()), 0)
    
    def test_device_insertion_and_retrieval(self):
        """Test inserting and retrieving device data."""
        test_device = {
            "mac": "AA:BB:CC:DD:EE:FF",
            "name": "Test Device",
            "ip": "192.168.1.100",
            "vendor": "Test Vendor"
        }
        
        # Insert device
        self.devices.insert(test_device)
        
        # Retrieve device
        Device = Query()
        retrieved_device = self.devices.get(Device.mac == "AA:BB:CC:DD:EE:FF")
        
        # Verify retrieved data
        self.assertIsNotNone(retrieved_device)
        self.assertEqual(retrieved_device["name"], "Test Device")
        self.assertEqual(retrieved_device["ip"], "192.168.1.100")
        self.assertEqual(retrieved_device["vendor"], "Test Vendor")
    
    def test_device_group_membership(self):
        """Test device group membership operations."""
        # Create test device
        test_device = {"mac": "11:22:33:44:55:66", "name": "Group Test Device"}
        self.devices.insert(test_device)
        
        # Ensure default group exists
        initialize_default_group()
        
        # Add device to group
        membership = {"device_mac": "11:22:33:44:55:66", "group_name": "general"}
        self.group_members.insert(membership)
        
        # Verify membership
        Member = Query()
        result = self.group_members.get(
            (Member.device_mac == "11:22:33:44:55:66") & 
            (Member.group_name == "general")
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["device_mac"], "11:22:33:44:55:66")
        self.assertEqual(result["group_name"], "general")

if __name__ == '__main__':
    unittest.main() 