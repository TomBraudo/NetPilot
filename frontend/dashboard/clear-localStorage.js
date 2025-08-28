// Simple script to clear old localStorage data and test the new flow
// Run this in the browser console on the devices page

console.log("🧹 Clearing old localStorage data...");

// Clear old device groups
const oldGroups = localStorage.getItem("deviceGroups");
if (oldGroups) {
    console.log("📦 Found old device groups:", JSON.parse(oldGroups).length);
    localStorage.removeItem("deviceGroups");
    console.log("✅ Cleared device groups");
} else {
    console.log("ℹ️ No old device groups found");
}

// Clear old scanned devices  
const oldDevices = localStorage.getItem("scannedDevices");
if (oldDevices) {
    console.log("📱 Found old scanned devices:", JSON.parse(oldDevices).length);
    localStorage.removeItem("scannedDevices");
    console.log("✅ Cleared scanned devices");
} else {
    console.log("ℹ️ No old scanned devices found");
}

// Clear scan time
localStorage.removeItem("lastScanTime");

console.log("🔄 Now refresh the page and try scanning again!");
console.log("📋 Steps to test:");
console.log("1. Go to Scan page");
console.log("2. Click 'Scan Network'");
console.log("3. Wait for scan to complete");
console.log("4. Go to Devices page");
console.log("5. Try creating a group");

// Show current routerId for reference
const routerId = localStorage.getItem("routerId");
console.log("🆔 Current Router ID:", routerId || "Not set");

