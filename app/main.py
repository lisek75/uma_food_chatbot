# app/main.py

import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import db_helper, generic_helper

# Debugging purpose
def print_orders_sessions(func):
    """
    Wrapper to print active sessions before calling the decorated function
    """
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        print(f"Orders Sessions: {active_orders_sessions}")
        return result
    return wrapper

# Dictionary for active orders and last activity times
active_orders_sessions = {}
last_activity_times = {}

async def cleanup_inactive_sessions():
    """
    Periodically removes inactive sessions from active sessions 
    and last activity times dictionaries to manage resources.
    """
    while True:
        await asyncio.sleep(60 * 15)  # Run every 15 minutes
        current_time = time.time()
        timeout = 60 * 30  # 30 minutes of inactivity
        inactive_sessions = [session_id for session_id, last_activity in last_activity_times.items() if current_time - last_activity > timeout]
        for session_id in inactive_sessions:
            del active_orders_sessions[session_id]
            del last_activity_times[session_id]
            print(f"Session {session_id} has been cleaned up due to inactivity.")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifespan of the FastAPI app, starting the cleanup task on startup
    and properly handling its shutdown.
    """
    # Startup
    cleanup_task = asyncio.create_task(cleanup_inactive_sessions())
    try:
        yield
    finally:
        # Shutdown
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Unexpected error during shutdown: {e}")

# Create a FastAPI app instance
app = FastAPI(lifespan=lifespan)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

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
    Handles incoming webhook requests, extracts necessary information, 
    and delegates processing to the appropriate handler
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
        print(f"My Session: {session_id}")  # Debugging

        # Map intent names to their respective handler functions
        intent_handlers = {
            'new.order': new_order,
            'get.menu - context: ongoing-order': get_menu,
            'order.add - context: ongoing-order': add_item_to_order,
            'order.remove - context: ongoing-order': remove_item_from_order,
            'order.prompt_confirm - context: ongoing-order': prompt_confirm_order,
            'order.complete_confirm - context: ongoing-order': complete_order,
            'track.order - context: ongoing-tracking': track_order,
        }

        # Call the appropriate handler function based on the intent name
        if intent_name in intent_handlers:
            print(f"Webhook call: {intent_name} is successful.")  # Debugging
            return await intent_handlers[intent_name](session_id, parameters)

        # Default response if the intent is not recognized
        return {"fulfillmentText": "Sorry, I didn't understand that request."}
    except Exception as e:
        print(f"Error in webhook_handler: {e}")
        return {"fulfillmentText": "There was an error processing the request. Please try again."}

async def get_menu(session_id: str = None, parameters: dict = None) -> dict:
    """
    Retrieves the menu items from the database and returns them in a formatted response
    """
    try:
        menu_items = db_helper.get_menu_items()
        fulfillment_text = (
            f" Menu 🍣: {', '.join(menu_items)}."
            " Specify items and quantities (e.g., 2 Tuna Sushi, 1 Chirasi)."
        )
        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        # Handle any exceptions that occur and return an error message
        print(f"Error in get_menu: {e}")
        return {"fulfillmentText": "There was an error retrieving the menu. Please try again."}

@print_orders_sessions
async def new_order(session_id: str, parameters: dict = None) -> dict:
    """
    Starts a new order or retrieves an existing order for the session
    """
    try:
        # Check if there is an existing order for the session ID
        if session_id in active_orders_sessions and active_orders_sessions[session_id]:
            # Get the order items and quantities
            order_items_qty = generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            fulfillment_text = (
                f" 🛒 You have an existing order: 🍣 {order_items_qty}."
                " Do you need something else?"
            )
        else:
            # If no existing order, get the menu items from the database
            menu_response = db_helper.get_menu_items()
            fulfillment_text = (
                "New order started 🍱. What can I get for you?"
                f" Here is the menu 🍣: {', '.join(menu_response)} "
            )
        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        # Handle any exceptions that occur and return an error message
        print(f"Error in new_order: {e}")
        return {"fulfillmentText": "There was an error starting a new order. Please try again."}

@print_orders_sessions
async def add_item_to_order(session_id: str, parameters: dict) -> dict:
    """
    Adds items to the current order for the session
    """
    try:
        current_time = time.time()  # Track current time

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

            print(f"Current Order: {active_orders_sessions.get(session_id)}")  # Debugging

            # Update the last activity time
            last_activity_times[session_id] = current_time

            # Get the order items and quantities
            order_items_qty = generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            fulfillment_text += (
                f" So far, you have in your cart: 🍣 {order_items_qty}."
                " Do you need something else?"
            )

        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        # Handle any exceptions that occur and return an error message
        print(f"Error in add_item_to_order: {e}")
        return {"fulfillmentText": "There was an error adding items to the order. Please try again."}

async def remove_item_from_order(session_id: str, parameters: dict) -> dict:
    """
    Removes items from the current order for the session
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
                removed_items.append(item)
                # Delete the food item from the current order
                del current_order[item]
            else:
                not_found_items.append(item)

        print(f"Current Order: {current_order}")  # Debugging
        print(f"{len(not_found_items)} items not found: {not_found_items}")  # Debugging
        print(f"{len(removed_items)} items removed: {removed_items}")  # Debugging
        print(f"Current Order updated:{current_order}")  # Debugging

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
            order_items_qty = generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            fulfillment_text += (
                f" So far, you have in your cart: 🍣 {order_items_qty}."
                " Do you need something else?"
            )

        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        # Handle any exceptions that occur and return an error message
        print(f"Error in remove_item_from_order: {e}")
        return {"fulfillmentText": "There was an error removing items from the order. Please try again."}

async def prompt_confirm_order(session_id: str, parameters: dict) -> dict:
    """
    Prompts the user to confirm the order
    """
    try:
        if session_id not in active_orders_sessions:
            return {"fulfillmentText": "I can't find your order. Sorry! Please say 'New Order' to place it again."}
        else:
            order_items_qty = generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            fulfillment_text = (
                f"All right! 🛒 In your cart: {order_items_qty}. Please confirm your order by saying 'Confirm' or 'Cancel'?"
            )
        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        # Handle any exceptions that occur and return an error message
        print(f"Error in complete_order: {e}")
        return {"fulfillmentText": "There was an error confirming the order. Please try again."}

async def complete_order(session_id: str, parameters: dict) -> dict:
    """
    Completes the order for the session after confirmation
    """
    try:
        if session_id not in active_orders_sessions:
            return {"fulfillmentText": "I can't find your order. Sorry! Please say 'New Order' to place it again."}

        # Retrieve confirmation parameter from user's response
        confirmation = parameters.get('confirmation')

        # Check if the confirmation value is true or false
        if confirmation == 'true':
            active_orders_sessions[session_id]['confirmed'] = True
        else:
            active_orders_sessions[session_id]['confirmed'] = False
            order_items_qty = generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            return {"fulfillmentText": f"Your order has not been confirmed 🛒: {order_items_qty}. Do you need something else?"}

        # Retrieve the current order 
        current_order = active_orders_sessions.get(session_id)

        # Remove the 'confirmed' key from the order before saving to the database
        if 'confirmed' in current_order:
            del current_order['confirmed']
        print(f"Order to insert in db: {current_order}")  # Debugging

        # Save the order into the database
        new_order_id, total_order_price  = db_helper.save_order_to_db(current_order)

        if new_order_id:
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
        # Handle any exceptions that occur and return an error message
        print(f"Error in complete_order: {e}")
        return {"fulfillmentText": "There was an error completing the order. Please try again."}

async def track_order(session_id: str, parameters: dict) -> dict:
    """
    Provide the status of a specific order based on the provided order ID.
    """
    try:
        order_id = int(parameters['order_id'])
        order_status = db_helper.get_order_status(order_id)

        if order_status:
            fulfillment_text = f"The order {order_id} is {order_status}."
        else:
            fulfillment_text = f"The order {order_id} doesn't exist."

        return {"fulfillmentText": fulfillment_text}
    except Exception as e:
        print(f"Error in track_order: {e}")
        return {"fulfillmentText": "There was an error tracking the order. Please try again."}
