"""
Machine ID Generator
Generates a unique hardware-based machine ID
"""
import hashlib
import platform
import uuid


def get_machine_id():
    """
    Generate a unique machine ID based on hardware information
    """
    try:
        # Get MAC address
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                       for elements in range(0, 2 * 6, 2)][::-1])
        
        # Get system information
        system = platform.system()
        node = platform.node()
        machine = platform.machine()
        processor = platform.processor()
        
        # Combine all information
        combined = f"{mac}|{system}|{node}|{machine}|{processor}"
        
        # Generate hash
        machine_id = hashlib.sha256(combined.encode()).hexdigest()
        
        return machine_id
    except Exception as e:
        print(f"Error generating machine ID: {e}")
        # Fallback to UUID
        return str(uuid.uuid4())


def get_system_info():
    """
    Get system information for activation
    """
    return {
        'hostname': platform.node(),
        'os_info': f"{platform.system()} {platform.release()}",
        'machine': platform.machine(),
        'processor': platform.processor()
    }


if __name__ == "__main__":
    print("Machine ID:", get_machine_id())
    print("System Info:", get_system_info())
