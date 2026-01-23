import depthai as dai

print("Searching for devices...")
devices = dai.Device.getAllAvailableDevices()

if len(devices) == 0:
    print("❌ No devices found. It is a physical connection issue.")
    print("   1. Try a different USB cable (many are charging-only).")
    print("   2. Try a different USB port or remove USB Hubs.")
else:
    print(f"✅ Found {len(devices)} device(s):")
    for device in devices:
        print(f"   - MxId: {device.getMxId()} | State: {device.state}")