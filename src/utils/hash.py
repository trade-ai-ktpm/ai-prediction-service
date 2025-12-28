import hashlib
import json
from typing import Any, Dict

def generate_hash(data: Dict[str, Any]) -> str:
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()
