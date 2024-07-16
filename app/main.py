# app/main.py

import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app import db_helper, generic_helper
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Debugging purpose
def print_orders_sessions(func):
    """
    Wrapper to print active sessions before calling the decorated function
    """
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        logging.info(f"Orders Sessions: {active_orders_sessions}")
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
            logging.info(f"Session {session_id} has been cleaned up due to inactivity.")

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
            logging.info(f"Unexpected error during shutdown: {e}")

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
        session_id = await generic_helper.extract_session_id(outputs_contexts)
        logging.info(f"My Session: {session_id}")  # Debugging

        # Map intent names to their respective handler functions
        intent_handlers = {
            'new.order': new_order,
            'order.add - context: ongoing-order': add_item_to_order,
            'order.remove - context: ongoing-order': remove_item_from_order,
            'order.prompt_confirm - context: ongoing-order': prompt_confirm_order,
            'order.cancel - context: ongoing-order': cancel_order,
            'order.complete - context: ongoing-order': complete_order,
            'track.order - context: ongoing-tracking': track_order,
        }

        # Call the appropriate handler function based on the intent name
        if intent_name in intent_handlers:
            logging.info(f"Webhook call: {intent_name} is successful.")  # Debugging
            return await intent_handlers[intent_name](session_id, parameters)

        # Default response if the intent is not recognized
        return {"fulfillmentText": "Sorry, I didn't understand that request."}
    except Exception as e:
        logging.info(f"Error in webhook_handler: {e}")
        return {"fulfillmentText": "❗There was an error processing the request. Please try again."}

@print_orders_sessions
async def new_order(session_id: str, parameters: dict = None) -> dict:
    """
    Starts a new order or retrieves an existing order for the session
    """
    try:
        if session_id in active_orders_sessions and active_orders_sessions[session_id]:
            order_items_qty = await generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            fulfillment_text = f"🛒 You have an existing order: {order_items_qty}. Do you need something else?"
            options = [{"text": "Yes"}, {"text": "No"}, {"text": "Show Menu 📋"}]
        else:
            fulfillment_text = "New order started 🛒. What can I get for you?"
            options = [{"text": "Show Menu 📋"}]

        return {
            "fulfillmentMessages": [
                {"text": {"text": [fulfillment_text]}},
                {"payload": {"richContent": [[{"type": "chips", "options": options}]]}}
            ]
        }
    except Exception as e:
        logging.info(f"Error in new_order: {e}")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["❗There was an error tracking the order. Please try again."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Order 🛒"}, {"text": "Menu 📋"}]}]]}}
            ]
        }

@print_orders_sessions
async def add_item_to_order(session_id: str, parameters: dict) -> dict:
    """
    Adds items to the current order for the session
    """
    try:
        current_time = time.time()  # Track current time
        food_items = parameters.get('food-item', [])
        add_qty = parameters.get('qty', [])

        if len(food_items) != len(add_qty):
            return {
                "fulfillmentMessages": [
                    {"text": {"text": ["Please specify items and quantities 🍣 (e.g., 2 Tuna Sushi, 1 Chirasi)."]}}
                ]
            }

        add_qty = [int(q) for q in add_qty]  # Convert quantities to integers
        food_dict = dict(zip(food_items, add_qty))  # Create the food dictionary

        valid_food_items = {item: qty for item, qty in food_dict.items() if await db_helper.does_food_item_exist(item)}
        non_existing_items = [item for item in food_dict if item not in valid_food_items]

        logging.info(f"Valid Food Items: {valid_food_items} - Non-existing Food Items: {non_existing_items} ")  # Debugging

        fulfillment_text = ""
        if non_existing_items:
            fulfillment_text += f"Sorry, these items aren't available: 🚫{', '.join(non_existing_items)}."

        if valid_food_items:
            if session_id in active_orders_sessions:
                active_orders_sessions[session_id].update(valid_food_items)
            else:
                active_orders_sessions[session_id] = valid_food_items

            logging.info(f"Order: {active_orders_sessions[session_id]}")  # Debugging
            last_activity_times[session_id] = current_time  # Update the last activity time

        order_items_qty = await generic_helper.get_order_items_qty(active_orders_sessions, session_id)
        fulfillment_text += f" So far, you have in your cart: 🛒 {order_items_qty}. Do you need something else?"

        return {
            "fulfillmentMessages": [
                {"text": {"text": [fulfillment_text]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Yes"}, {"text": "No"}, {"text": "Show Menu"}]}]]}}
            ]
        }
    except Exception as e:
        logging.info(f"Error in add_item_to_order: {e}")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["❗There was an error adding items to the order. Please try again."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Order 🛒"}, {"text": "Menu 📋"}]}]]}}
            ]
        }

async def remove_item_from_order(session_id: str, parameters: dict) -> dict:
    """
    Removes items from the current order for the session
    """
    try:
        if session_id not in active_orders_sessions:
            return {
                "fulfillmentMessages": [
                    {"text": {"text": ["Couldn't find an active order. Please start a new one 🍣."]}},
                    {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "New Order 🛒"}, {"text": "Show Menu 📋"}]}]]}}
                ]
            }

        current_order = active_orders_sessions.get(session_id)  # Retrieve the current order
        items_to_remove = parameters.get('food-item', [])  # Extract the food items to remove

        removed_items = [item for item in items_to_remove if item in current_order]
        not_found_items = [item for item in items_to_remove if item not in current_order]

        logging.info(f"Items not found: {not_found_items} - Items removed: {removed_items}")  # Debugging
        logging.info(f"Order Updated:{current_order}")  # Debugging

        for item in removed_items:
            del current_order[item]

        existing_items_in_db = [item for item in not_found_items if await db_helper.does_food_item_exist(item)]
        non_existing_items_in_db = [item for item in not_found_items if not await db_helper.does_food_item_exist(item)]

        fulfillment_text = ""
        if non_existing_items_in_db:
            fulfillment_text = f"These items aren't available: 🚫{', '.join(non_existing_items_in_db)}."
        if existing_items_in_db:
            fulfillment_text += f" Your current order 🛒 does not have: {', '.join(existing_items_in_db)}."
        if removed_items:
            fulfillment_text += f" 🗑️ Removed {', '.join(removed_items)} from your order."

        if not current_order:
            fulfillment_text += " Your order is empty. Do you need something else?"
        else:
            order_items_qty = await generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            fulfillment_text += f" So far, you have in your cart: 🍣 {order_items_qty}. Do you need something else?"

        return {
            "fulfillmentMessages": [
                {"text": {"text": [fulfillment_text]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Yes"}, {"text": "No"}, {"text": "Show the menu 📋"}]}]]}}
            ]
        }
    except Exception as e:
        logging.info(f"Error in remove_item_from_order: {e}")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["❗There was an error removing items from the order. Please try again."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Order 🛒"}, {"text": "Menu 📋"}]}]]}}
            ]
        }

async def prompt_confirm_order(session_id: str, parameters: dict) -> dict:
    """
    Prompts the user to confirm the order
    """
    try:
        if session_id not in active_orders_sessions:
            return {
                "fulfillmentMessages": [
                    {"text": {"text": ["I can't find your order. Sorry! 😔 Please place it again."]}},
                    {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "New Order 🛒"}, {"text": "Menu 📋"}]}]]}}
                ]
            }

        current_order = active_orders_sessions.get(session_id)  # Retrieve the order

        # Determine fulfillment text and options based on the order status
        if not current_order:
            fulfillment_text = "Your order is empty. Do you need something else?"
            options = [{"text": "I need something else"}, {"text": "Show Menu 📋"}]
        else:
            order_items_qty = await generic_helper.get_order_items_qty(active_orders_sessions, session_id)
            fulfillment_text = f"All right! 🛒 You have {order_items_qty} in your cart. Please confirm your order."
            options = [{"text": "Confirm ✅"}, {"text": "Cancel ❌"}]

        return {
            "fulfillmentMessages": [
                {"text": {"text": [fulfillment_text]}},
                {"payload": {"richContent": [[{"type": "chips", "options": options}]]}}
            ]
        }
    except Exception as e:
        logging.info(f"Error in prompt_confirm_order: {e}")
        return {
            "fulfillmentMessages": [
                {"text": {"text": ["❗There was an error confirming the order. Please try again."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Order 🛒"}, {"text": "Menu 📋"}]}]]}}
            ]
        }

async def cancel_order(session_id: str, parameters: dict) -> dict:
    """
    Cancels the order for the given session
    """
    try:
        current_order = active_orders_sessions.get(session_id)  # Retrieve the order

        # Define response templates
        empty_order_response = {
            "fulfillmentMessages": [
                {"text": {"text": ["Your order is empty. Please add items to your cart."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Menu 📋"}]}]]}}
            ]
        }

        non_empty_order_response = {
            "fulfillmentMessages": [
                {"text": {"text": ["🛒Your order has not been confirmed: {order_items_qty}. Do you need something else?"]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Yes"}, {"text": "No"}, {"text": "Menu 📋"}]}]]}}
            ]
        }

        error_response = {
            "fulfillmentMessages": [
                {"text": {"text": ["❗There was an error cancelling the order. Please try again."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Order 🛒"}, {"text": "Menu 📋"}]}]]}}
            ]
        }

        if not current_order:
            return empty_order_response

        order_items_qty = await generic_helper.get_order_items_qty(active_orders_sessions, session_id)
        non_empty_order_response["fulfillmentMessages"][0]["text"]["text"][0] = non_empty_order_response["fulfillmentMessages"][0]["text"]["text"][0].format(order_items_qty=order_items_qty)
        return non_empty_order_response

    except Exception as e:
        logging.info(f"Error in cancel_order: {e}")
        return error_response

async def complete_order(session_id: str, parameters: dict) -> dict:
    """
    Completes the order for the given session
    """
    try:
        current_order = active_orders_sessions.get(session_id)  # Retrieve the order 
        logging.info(f"Order to insert in db: {current_order}")  # Debugging

        # Define response templates
        empty_order_response = {
            "fulfillmentMessages": [
                {"text": {"text": ["Your order is empty. Please add items to your cart before completing the order."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Menu 📋"}]}]]}}
            ]
        }

        success_response_template = {
            "fulfillmentMessages": [
                {"text": {"text": ["Awesome 🎉! We have placed your order id {order_id}. Your order total is ${total_price:.2f} which you can pay at the time of delivery 📦."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Menu 📋"}, {"text": "New order 🛒"}, {"text": "Track status 🚚"}, {"text": "Opening hours 🕒"}]}]]}}
            ]
        }

        error_response_template = {
            "fulfillmentMessages": [
                {"text": {"text": ["❗Error placing order. Please try again."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Order 🛒"}, {"text": "Menu 📋"}]}]]}}
            ]
        }

        general_error_response = {
            "fulfillmentMessages": [
                {"text": {"text": ["❗There was an error completing the order. Please try again."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Order 🛒"}, {"text": "Menu 📋"}]}]]}}
            ]
        }

        if not current_order:
            return empty_order_response

        # Save the order into the database
        new_order_id, total_order_price = await db_helper.save_order_to_db(current_order)

        if new_order_id:
            del active_orders_sessions[session_id]  # Clear the session
            success_response_template["fulfillmentMessages"][0]["text"]["text"][0] = success_response_template["fulfillmentMessages"][0]["text"]["text"][0].format(order_id=new_order_id, total_price=total_order_price)
            return success_response_template
        else:
            return error_response_template

    except Exception as e:
        logging.info(f"Error in complete_order: {e}")
        return general_error_response

async def track_order(session_id: str, parameters: dict) -> dict:
    """
    Provide the status of a specific order ID
    """
    try:
        order_id = int(parameters['order_id'])
        order_status = await db_helper.get_order_status(order_id)

        # Determine the fulfillment text based on order status
        fulfillment_text = f"📦 The order {order_id} is {order_status}." if order_status else f"📦 The order {order_id} doesn't exist."

        # Define response templates
        response = {
            "fulfillmentMessages": [
                {"text": {"text": [fulfillment_text]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Menu 📋"}, {"text": "New order 🛒"}, {"text": "Order status 🚚"}, {"text": "Opening hours 🕒"}]}]]}}
            ]
        }

        return response

    except Exception as e:
        logging.info(f"Error in track_order: {e}")
        error_response = {
            "fulfillmentMessages": [
                {"text": {"text": ["❗There was an error tracking the order. Please try again."]}},
                {"payload": {"richContent": [[{"type": "chips", "options": [{"text": "Status 🚚"}, {"text": "Order 🛒"}]}]]}}
            ]
        }
        return error_response
