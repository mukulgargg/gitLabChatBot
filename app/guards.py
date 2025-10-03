DISALLOWED = ["personal data", "passwords", "credentials"]

def is_safe(user_q: str) -> tuple[bool,str]:
    q = user_q.lower()
    if any(k in q for k in DISALLOWED):
        return False, "I can’t help with sensitive information (e.g., credentials). Try a policy/process question instead."
    return True, ""
