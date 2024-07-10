import re

def extract_session_id(session_str: str) -> str:
    """
    Extract and return the session ID from the session string.
    """
    match = re.search(r'/sessions/(.*?)/contexts/', session_str)
    if match:
        return match.group(1)
    return None

def get_order_items_qty(active_order_sessions: dict, session_id: str) -> str:
    """
    Generate a string listing the quantity of each item in the order for the given session ID.
    """
    # Retrieve the dictionary of food items for the given session ID
    order = active_order_sessions.get(session_id, {})
    if not order:
        return "No items in the order."

    if 'confirmed' in order:
        del order['confirmed']

    # Generate the order_items_qty string
    order_items_qty = ", ".join([f"{quantity} {item}" for item, quantity in order.items()])

    return order_items_qty