import re

def extract_session_id(session_str: str) -> str:
    """
    Extract the session ID from the session string.

    Args:
        session_str (str): The session string containing the session ID.

    Returns:
        str: The extracted session ID or None if not found.
    """
    # Regular expression to extract session ID
    match = re.search(r'/sessions/(.*?)/contexts/', session_str)
    if match:
        return match.group(1)
    return None

def get_order_items_qty(active_order_sessions: dict, session_id: str) -> str:
    """
    Generate a string listing the quantity of each item in the order for the given session ID.

    Args:
        active_order_sessions (dict): The dictionary of active orders.
        session_id (str): The session ID for which to retrieve the order.

    Returns:
        str: A string listing the quantities and items in the order.
    """
    # Retrieve the dictionary of food items for the given session ID
    order = active_order_sessions.get(session_id, {})
    if not order:
        return "No items in the order."

    # Generate the order_items_qty string
    order_items_qty = ", ".join([f"{quantity} {item}" for item, quantity in order.items()])

    return order_items_qty

# Check functions built above
if __name__ == "__main__":
    session_str_example = "projects/eva-for-food-gvja/agent/sessions/38602c10-82bf-8fa5-2078-8cb7c0083939/contexts/ongoing-order"
    active_order_sessions_example = {
        'e270a470-1d17-c3fe-581d-a27dbf30538e': {'Tuna Sushi': 1, 'Salmon Sushi': 2, 'Chirasi': 1},
        '6f46e14d-a6f5-e12b-70e9-40b5e9e53363': {'Chirasi': 2, 'Tuna Sushi': 7}
    }
    session_id_example = 'e270a470-1d17-c3fe-581d-a27dbf30538e'

    # Test extract_session_id function
    print(extract_session_id(session_str_example))

    # Test get_order_items_qty function
    print(get_order_items_qty(active_order_sessions_example, session_id_example))
