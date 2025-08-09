import json
from typing import Optional, Dict

def safe_json_parse(txt: str) -> Optional[Dict]:
    s = txt.strip()
    if s.startswith("```"):
        # strip leading/backtick fences conservatively
        s = s.strip("`")
        i = s.find("{")
        if i != -1:
            s = s[i:]
    j = s.rfind("}")
    if j != -1:
        s = s[: j + 1]
    try:
        return json.loads(s)
    except Exception:
        return None
