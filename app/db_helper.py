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
    result = await execute_query(query, params)
    return result is not None

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
    connection = await get_db_connection()
    if connection is None:
        return 0, 0

    try:
        async with connection.cursor() as cursor:
            # Get the new order ID
            query = "SELECT COALESCE(MAX(order_id), 0) + 1 FROM orders"
            await cursor.execute(query)
            result = await cursor.fetchone()
            new_order_id = result[0]

            # Collect all queries for batch insertion
            order_queries = []
            total_order_price = 0

            for item_name, quantity in order.items():
                query = "SELECT item_id, price FROM food_items WHERE name = %s"
                await cursor.execute(query, (item_name,))
                result = await cursor.fetchone()
                if not result:
                    return 0, 0

                item_id, price = result
                total_price = price * quantity
                total_order_price += total_price

                order_queries.append((new_order_id, item_id, quantity, total_price))

            # Insert all orders in a batch
            insert_query = """
                INSERT INTO orders (order_id, item_id, quantity, total_price)
                VALUES (%s, %s, %s, %s)
            """
            await cursor.executemany(insert_query, order_queries)

            # Insert order tracking
            tracking_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
            await cursor.execute(tracking_query, (new_order_id, 'in progress'))

        await connection.commit()
        return new_order_id, total_order_price
    except aiomysql.Error as error:
        print("Error saving order to DB:", error)
        return 0, 0
    finally:
        connection.close()

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
