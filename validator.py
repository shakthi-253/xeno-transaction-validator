"""
Core validation logic for transaction data.
Each validator returns (is_valid: bool, error_message: str or None)
"""
import re
from datetime import datetime
from country_rules import COUNTRY_PHONE_RULES, VALID_PAYMENT_MODES, DATE_FORMAT

REQUIRED_FIELDS = ["order_id", "product_name", "quantity", "price", "payment_mode", "phone_number", "country", "order_date"]


def validate_phone(phone, country):
    expected_digits = COUNTRY_PHONE_RULES.get(country)
    if expected_digits is None:
        return False, f"Unknown country '{country}' — no phone rule configured"

    digits_only = re.sub(r'\D', '', str(phone))  # strip everything except digits
    if len(digits_only) != expected_digits:
        return False, f"Phone must have {expected_digits} digits for {country}, got {len(digits_only)}"
    return True, None


def validate_date(date_str):
    try:
        datetime.strptime(str(date_str).strip(), DATE_FORMAT)
        return True, None
    except ValueError:
        return False, f"Invalid date '{date_str}', expected format {DATE_FORMAT}"


def validate_payment_mode(mode):
    if str(mode).strip() not in VALID_PAYMENT_MODES:
        return False, f"Unknown payment mode '{mode}'"
    return True, None


def validate_number(value, field_name):
    try:
        num = float(value)
        if num <= 0:
            return False, f"{field_name} must be positive"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} is not a valid number"


def validate_row(row: dict) -> tuple[bool, list[str]]:
    """
    Validates a single transaction row (a dict of column -> value).
    Returns (is_valid, list_of_error_messages)
    """
    errors = []

    # 1. Required fields present and not empty
    for field in REQUIRED_FIELDS:
        value = row.get(field, "")
        if value is None or str(value).strip() in ("", "nan"):
            errors.append(f"Missing required field: {field}")

    # If core fields are missing, skip deeper checks (avoid noisy duplicate errors)
    if errors:
        return False, errors

    # 2. Phone number — country-specific
    valid, msg = validate_phone(row["phone_number"], row["country"])
    if not valid:
        errors.append(msg)

    # 3. Date format
    valid, msg = validate_date(row["order_date"])
    if not valid:
        errors.append(msg)

    # 4. Payment mode
    valid, msg = validate_payment_mode(row["payment_mode"])
    if not valid:
        errors.append(msg)

    # 5. Quantity and price must be valid positive numbers
    valid, msg = validate_number(row["quantity"], "Quantity")
    if not valid:
        errors.append(msg)

    valid, msg = validate_number(row["price"], "Price")
    if not valid:
        errors.append(msg)

    return len(errors) == 0, errors
