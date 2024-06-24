# app/main.py

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import db_helper, generic_helper

# Decorator definition
def print_active_sessions(func):
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        print(f"Active sessions: {active_orders_sessions}")
        return result
    return wrapper

# Create a FastAPI app instance
app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# A dictionary to keep track of current orders in progress, mapped by session IDs.
active_orders_sessions = {}

@app.get("/")
async def read_root(request: Request):
    """
    Render the index.html template.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/learn_more.html")
async def read_learn_more(request: Request):
    """
    Render the learn_more.html template.
    """
    return templates.TemplateResponse("learn_more.html", {"request": request})

# Define a route for the webhook endpoint
@app.post("/")
async def webhook_handler(request: Request):
    """
    Webhook handler for incoming requests.
    Extracts information from the incoming request and delegates the 
    processing to the appropriate handler based on the intent name.

    Args:
        request (Request): The incoming HTTP request containing the webhook payload.

    Returns:
        dict: A dictionary containing the fulfillment text response.
    """
    try:
        # Retrieve the JSON data from the incoming webhook request
        payload = await request.json()

        # Extract the necessary information from the payload
        query_result = payload.get('queryResult', {})
        intent_name = query_result.get('intent', {}).get('displayName', '')
        parameters = query_result.get('parameters', {})


        # Extract the session id
        outputs_contexts = query_result.get('outputContexts', [{}])[0].get('name', '')
        session_id = generic_helper.extract_session_id(outputs_contexts)
        print(f"Session id: {session_id}")  # Debugging

        # Map intent names to their respective handler functions.
        intent_handlers = {
            'new.order': new_order,
            'get.menu - context: ongoing-order': get_menu,
            'order.add - context: ongoing-order': add_order,
            'order.remove - context: ongoing-order': remove_order,
            'order.complete - context: ongoing-order': complete_order,
            'track.order - context: ongoing-tracking': track_order,
        }

        # Call the appropriate handler function based on the intent name.
        if intent_name in intent_handlers:
            print(f"Webhook call: {intent_name} is successful.")  # Debugging
            return await intent_handlers[intent_name](session_id, parameters)

        # Default response if the intent is not recognized.
        return {"fulfillmentText": "Sorry, I didn't understand that request."}
    except Exception as e:
        print(f"Error in webhook_handler: {e}")
        return {"fulfillmentText": "There was an error processing the request. Please try again."}

async def get_menu(session_id: str = None, parameters: dict = None) -> dict:
    """
    Handle the 'get.menu - context: ongoing-order' intent.
    Returns the current menu items to the user.

    Args: NA

    Returns:
        dict: A dictionary containing the fulfillment text response.
    """
    try:
        menu_items = db_helper.get_menu_items()
        fulfillment_text = (
            f" Menu 🍣: {', '.join(menu_items)}."
            " Specify items and quantities (e.g., 2 Tuna Sushi, 1 Chirasi)."
        )
        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        print(f"Error in get_menu: {e}")
        return {"fulfillmentText": "There was an error retrieving the menu. Please try again."}

@print_active_sessions
async def new_order(session_id: str, parameters: dict = None) -> dict:
    """
    Handle the 'new.order' intent by clearing the current session and starting a new order.

    Args:
        session_id (str): The session id for the current order.

    Returns:
        dict: A dictionary containing the fulfillment text response.
    """
    try:
        print(f"Order before clearing session: {active_orders_sessions.get(session_id, 'No existing session')}") # Debugging

        # Clear the current session
        active_orders_sessions[session_id] = {}
        print(f"Order after clearing session: {active_orders_sessions.get(session_id)}") # Debugging

        # Start the new order message
        menu_response = db_helper.get_menu_items()
        fulfillment_text = (
            "New order started 🍱. What can I get for you?"
            f" Here is the menu 🍣: {', '.join(menu_response)} "
        )
        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        print(f"Error in new_order: {e}")
        return {"fulfillmentText": "There was an error starting a new order. Please try again."}

@print_active_sessions
async def add_order(session_id: str, parameters: dict) -> dict:
    """
    Handle the 'order.add - context: ongoing-order' intent by adding items to the current order.

    Args:
        session_id (str): The session ID for the current order.
        parameters (dict): Parameters from the request, including food items and quantities.

    Returns:
        dict: A dictionary containing the fulfillment text response.
    """
    try:
        # Extract food-items and quantities from parameters
        food_items = parameters.get('food-item', [])
        add_qty = parameters.get('qty', [])

        # If food items or quantities are missing, prompt the user to specify them
        if not food_items or not add_qty:
            return {
                "fulfillmentText": "Please specify the food item along with the quantity (e.g., 2 Tuna Sushi, 1 Chirasi) 🍣",
            }

        # Initialize a list to store non-existing items in database
        non_existing_items_in_db = []

        # Initialize a dictionary to store valid food items and their quantities
        valid_food_items = {}

        if len(food_items) != len(add_qty):
            return {"fulfillmentText": "Please specify items and quantities (e.g., 2 Tuna Sushi, 1 Chirasi)."}

        add_qty = [int(q) for q in add_qty]  # Convert quantities to integers
        food_dict = dict(zip(food_items, add_qty))  # Create the food dictionary

        # Iterate over the food items and their corresponding quantities
        for item, qty in food_dict.items():
            if db_helper.does_food_item_exist(item):
                valid_food_items[item] = int(qty)
            else:
                non_existing_items_in_db.append(item)

        print(f"Valid Food Items: {valid_food_items}")  # Debugging
        print(f"None Valid Food Items: {non_existing_items_in_db}")  # Debugging

        fulfillment_text = ""

        # Check if there are non-existing items
        if non_existing_items_in_db:
            fulfillment_text = (
                f"Sorry, these items aren't available: 🚫{', '.join(non_existing_items_in_db)}."
                " You can say 'Menu'🍣 to show list of items."
            )

        # Check if there are valid food items
        if valid_food_items:
            # Check if the session_id exists
            if session_id in active_orders_sessions:
                # Update the session with new items and quantities
                active_orders_sessions[session_id].update(valid_food_items)
            else:
                # Add a new entry with the provided session_id and food dictionary
                active_orders_sessions[session_id] = valid_food_items

            print(f"Order: {active_orders_sessions.get(session_id)}")  # Debugging

            # Get the order items and quantities
            order_items_qty = generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            fulfillment_text += (
                f" So far, you have in your cart: 🍣 {order_items_qty}."
                " Do you need something else?"
            )

        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        print(f"Error in add_order: {e}")
        return {"fulfillmentText": "There was an error adding items to the order. Please try again."}

@print_active_sessions
async def remove_order(session_id: str, parameters: dict) -> dict:
    """
    Handle the 'order.remove - context: ongoing-order' intent by removing items from the current order.

    Args:
        session_id (str): The session ID for the current order.
        parameters (dict): Parameters from the request, including food items.

    Returns:
        dict: A dictionary containing the fulfillment text response.
    """
    try:
        if session_id not in active_orders_sessions:
            return {"fulfillmentText": "Couldn't find an active order. Please start a new one by saying 'New Order'🍱."}

        # Retrieve the current order
        current_order = active_orders_sessions.get(session_id)

        # Extract the food items to remove
        items_to_remove = parameters.get('food-item', [])

        # Lists to track items to remove and items not found in the order
        removed_items = []
        not_found_items = []

        # Iterate over each food item to remove
        for item in items_to_remove:
            # Check if the food item exists in the current order
            if item in current_order:
                # Add it to the removed_items list
                removed_items.append(item)
                # Delete the food item from the current order
                del current_order[item]
            else:
                # Add it to the not_found_items list
                not_found_items.append(item)

        print(f"Order: {current_order}")  # Debugging
        print(f"{len(not_found_items)} items not found: {not_found_items}")  # Debugging
        print(f"{len(removed_items)} items removed: {removed_items}")  # Debugging
        print(f"Order updated:{current_order}")  # Debugging

        # Initialize fulfillment_text
        fulfillment_text = ""

        existing_items_in_db = []
        non_existing_items_in_db = []

        # Check if there are any items that were not found in the current order
        if not_found_items:
            for item in not_found_items:
                # Check if there are any items doesn't exist in db
                if db_helper.does_food_item_exist(item):
                    existing_items_in_db.append(item)
                else:
                    non_existing_items_in_db.append(item)

            if non_existing_items_in_db:
                fulfillment_text = (
                    f"These items aren't available: 🚫{', '.join(non_existing_items_in_db)}."
                    " You can say 'Menu'🍣 to show list of items."
                )

            if existing_items_in_db:
                fulfillment_text += (f"Your current order does not have: {', '.join(existing_items_in_db)}.")

        # Check if there are any items that were successfully removed from the current order
        if removed_items:
            fulfillment_text += f" Removed {', '.join(removed_items)} from your order."

        # Check if the current order is now empty
        if not current_order:  # len(current_order.keys()) == 0
            fulfillment_text += " Your order is empty."
        else:
            # Get the quantity of items remaining in the order
            order_items_qty = generic_helper.get_order_items_qty(
                active_orders_sessions, session_id)
            fulfillment_text += (
                f" So far, you have in your cart: 🍣 {order_items_qty}."
                " Do you need something else?"
            )

        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        print(f"Error in remove_order: {e}")
        return {"fulfillmentText": "There was an error removing items from the order. Please try again."}

@print_active_sessions
async def complete_order(session_id: str, parameters: dict) -> dict:
    """
    Handle the 'complete.order - context: ongoing-order' intent by finalizing the current order.

    Args:
        session_id (str): The session ID for the current order.
        parameters (dict): Parameters from the request.

    Returns:
        dict: A dictionary containing the fulfillment text response.
    """
    try:
        # Check if the session_id exists
        if session_id not in active_orders_sessions:
            return {"fulfillmentText": "I can't find your order. Sorry! Please say 'New Order' to place it again."}

        # Retrieve the current order
        current_order = active_orders_sessions.get(session_id)
        print(f"Order to insert in db: {current_order}")  # Debugging

        # Save the order into the database
        new_order_id = db_helper.save_order_to_db(current_order)

        if new_order_id:
            # If the order is saved, calculate the total price
            total_order_price = db_helper.calculate_order_total_price(new_order_id)
            # Clear the session after saving the order
            del active_orders_sessions[session_id]

            # Set the fulfillment text with order details
            fulfillment_text = (
                f"Awesome 🎉! We have placed your order id {new_order_id}. "
                f" Your order total is ${total_order_price:.2f} which you can pay at the time of delivery 📦."
            )
        else:
            # If there was an error saving the order, inform the user
            fulfillment_text = "Error placing order. Please try again. Say 'New Order.'"

        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        print(f"Error in complete_order: {e}")
        return {"fulfillmentText": "There was an error completing the order. Please try again."}

@print_active_sessions
async def track_order(session_id: str, parameters: dict) -> dict:
    """
    Handle the 'track.order - context: ongoing-tracking' intent by providing the status of a specific order.

    Args:
        session_id (str): The session ID for the current order.
        parameters (dict): Parameters from the request, including the order ID.

    Returns:
        dict: A dictionary containing the fulfillment text response.
    """
    try:
        order_id = int(parameters['order_id'])
        order_status = db_helper.get_order_status(order_id)

        print(f"Order ID: {order_id}")  # Debugging
        print(f"Order Status {order_status}")  # Debugging

        if order_status:
            fulfillment_text = f"The order {order_id} is {order_status}."
        else:
            fulfillment_text = f"The order {order_id} doesn't exist."

        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        print(f"Error in track_order: {e}")
        return {"fulfillmentText": "There was an error tracking the order. Please try again."}
