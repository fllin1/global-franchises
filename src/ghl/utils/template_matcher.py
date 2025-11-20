import re
from loguru import logger

def is_template_message(body_clean: str) -> bool:
    """
    Check if the message matches the standard outreach template.
    
    Template:
    Hi [FirstName], Nice seeing you at the convention. Is it possible to mail me available territories and the hot markets to present to my clients please. Thank you Best, Manoj Soans
    
    The regex allows for:
    - Variable greeting (Hi/Hello/Dear Name)
    - Slight variations in whitespace/punctuation
    - Case insensitive matching
    """
    if not body_clean:
        return False
        
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', body_clean).strip()
    
    # Pattern parts
    # 1. Greeting: Hi/Hello [Name],?
    # 2. "Nice seeing you at the convention" (optional or slight variation)
    # 3. "Is it possible to mail me available territories"
    # 4. "hot markets to present to my clients please"
    # 5. Sign off: "Thank you Best, Manoj Soans"
    
    # Robust pattern:
    # Matches "Is it possible to mail me available territories" AND "Manoj Soans"
    # This avoids complex regex for the variable name part while ensuring it's our template
    
    pattern = r"Is it possible to mail me available territories.*present to my clients please.*Manoj Soans"
    
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    return bool(match)

