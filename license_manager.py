import json
import os
from datetime import datetime, timedelta

LICENSE_FILE = "licenses.json"

def init_licenses():
    if not os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "w") as f:
            json.dump({}, f)

def load_licenses():
    init_licenses()
    with open(LICENSE_FILE, "r") as f:
        return json.load(f)

def save_licenses(licenses):
    with open(LICENSE_FILE, "w") as f:
        json.dump(licenses, f, indent=4)

def generate_key(user_name, days=30):
    import uuid
    key = str(uuid.uuid4())[:8].upper()
    full_key = f"PACPL-{user_name[:3].upper()}-{key}"
    
    expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    licenses = load_licenses()
    licenses[full_key] = {
        "user": user_name,
        "expiry": expiry_date,
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    save_licenses(licenses)
    return full_key, expiry_date

def validate_license(key, device_id=None):
    licenses = load_licenses()
    if key not in licenses:
        return False, "Invalid License Key"
    
    lic = licenses[key]
    expiry_str = lic["expiry"]
    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
    
    if datetime.now() > expiry_date:
        return False, "License Expired"
    
    # Device Locking Logic
    if device_id:
        if "device_id" not in lic:
            # First time use, lock to this device
            lic["device_id"] = device_id
            save_licenses(licenses)
            return True, "Success (Locked to Device)"
        elif lic["device_id"] != device_id:
            # Different device trying to use same key
            return False, "Key already in use on another device"
    
    return True, "Success"
