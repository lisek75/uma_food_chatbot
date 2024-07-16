import os
from dotenv import load_dotenv
import aiomysql
import asyncio

# Load environment variables from .env file
load_dotenv()

async def get_db_connection():
    """
    Establish a connection to the database and return an aiomysql connection object.
    """
    # Database connection details
    db_config = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'db': os.getenv('DB_NAME')
    }
    try:
        connection = await aiomysql.connect(**db_config)
        return connection
    except aiomysql.Error as error:
        print("Error connecting to MySQL database:", error)
        return None

async def execute_query(query, params=None):
    """
    Execute a query and return the result.
    """
    connection = await get_db_connection()
    if connection is None:
        return None
    try:
        async with connection.cursor() as cursor:
            await cursor.execute(query, params)
            result = await cursor.fetchall()
            await connection.commit()
        return result
    except aiomysql.Error as error:
        print("Error executing query:", error)
        return None
    finally:
        connection.close()

async def execute_non_query(query, params=None):
    """
    Execute a non-query command (e.g., INSERT, UPDATE, DELETE) 
    and return a bool: True if the execution is successful, False otherwise.
    """
    connection = await get_db_connection()
    if connection is None:
        return False
    try:
        async with connection.cursor() as cursor:
            await cursor.execute(query, params)
            await connection.commit()
        return True
    except aiomysql.Error as error:
        print("Error executing non-query:", error)
        return False
    finally:
        connection.close()

async def does_food_item_exist(food_item: str) -> bool:
    """
    Check if the given food item exists in the food_items table,
    and return a bool: True if the food item exists, False otherwise.
    """
    query = "SELECT name FROM food_items WHERE name = %s"
    result = await execute_query(query, (food_item,))
    return bool(result)

async def save_order_to_db(order: dict) -> tuple:
    """
    Save the order details to the database, 
    and return a tuple: (The new order ID, Total order price) if the operation is successful, (0, 0) otherwise.
    """
    query = "SELECT MAX(order_id) FROM orders"
    result = await execute_query(query)
    max_order_id = result[0][0] if result else None
    new_order_id = 1 if max_order_id is None else max_order_id + 1

    total_order_price = 0
    for item_name, quantity in order.items():
        query = "SELECT item_id, price FROM food_items WHERE name = %s"
        result = await execute_query(query, (item_name,))
        if not result:
            return 0, 0

        item_id, price = result[0]
        total_price = price * quantity
        total_order_price += total_price

        query = "INSERT INTO orders (order_id, item_id, quantity, total_price) VALUES (%s, %s, %s, %s)"
        if not await execute_non_query(query, (new_order_id, item_id, quantity, total_price)):
            print(f"Failed to insert order for item '{item_name}'")
            return 0, 0

        print(f"{item_name} : ID({item_id}), Price: ${price}, Quantity : {quantity}, Total Price : {total_price}")

    query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    if not await execute_non_query(query, (new_order_id, 'in progress')):
        print(f"Failed to insert order tracking for order ID '{new_order_id}'")
        return 0, 0

    return new_order_id, total_order_price

async def get_order_status(order_id):
    """
    Get the status of an order, 
    and return a str: The status of the order, or None if not found.
    """
    query = "SELECT status FROM order_tracking WHERE order_id = %s"
    result = await execute_query(query, (order_id,))
    if result:
        return result[0][0]
    return None
