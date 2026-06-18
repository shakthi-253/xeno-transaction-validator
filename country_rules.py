"""
Configurable country-specific validation rules.
Add a new country by adding one line here — no other code changes needed.
"""

COUNTRY_PHONE_RULES = {
    "India": 10,
    "Singapore": 8,
    "USA": 10,
    "UK": 10,
    "UAE": 9,
    "Australia": 9,
}

VALID_PAYMENT_MODES = ["Card", "UPI", "Cash", "NetBanking", "Wallet"]

DATE_FORMAT = "%Y-%m-%d"
