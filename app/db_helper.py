import mysql.connector


def get_db_connection():
    """
    Establish a connection to the database.

    Returns:
        conn: A MySQL connection object.
    """
    # Database connection details
    db_config = {
        'user': 'root',
        'password': 'root',
        'host': 'localhost',
        'database': 'uma_food_chatbot'
    }
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as error:
        print("Error connecting to MySQL database:", error)
        return None


def execute_query(query, params=None):
    """
    Execute a query and return the result.

    Args:
        query (str): The SQL query to execute.
        params (tuple): The parameters for the query.

    Returns:
        list: The fetched results.
    """
    connection = get_db_connection()
    if connection is None:
        return None
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        connection.commit()
        return result
    except mysql.connector.Error as error:
        print("Error executing query:", error)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def execute_non_query(query, params=None):
    """
    Execute a non-query command (e.g., INSERT, UPDATE, DELETE).

    Args:
        query (str): The SQL query to execute.
        params (tuple): The parameters for the query.

    Returns:
        bool: True if the execution is successful, False otherwise.
    """
    connection = get_db_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        return True
    except mysql.connector.Error as error:
        print("Error executing non-query:", error)
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_menu_items():
    """
    Fetch the list of available menu items from the database.

    Returns:
        list: A list of menu item names.
    """
    # SQL query to select the names of all food items from the food_items table
    query = "SELECT name FROM food_items"

    # Execute the query and store the result
    result = execute_query(query)

    # Return a list of menu item names if the result is not empty, otherwise return an empty list
    return [item[0] for item in result] if result else []


def does_food_item_exist(food_item: str) -> bool:
    """
    Check if the given food item exists in the food_items table.

    Args:
        food_item (str): The name of the food item to check.

    Returns:
        bool: True if the food item exists, False otherwise.
    """
    # SQL query to check if the food item exists in the food_items table
    query = "SELECT name FROM food_items WHERE name = %s"
    
    # Execute the query with the food_item as a parameter
    result = execute_query(query, (food_item,))

    # Return True if the item exists, False otherwise
    return bool(result)


def save_order_to_db(order: dict) -> int:
    """
    Save the order details to the database.

    Args:
        order (dict): A dictionary where keys are item names and values are quantities.

    Returns:
        int: The new order ID if the operation is successful, 0 otherwise.
    """
    # Get the current maximum order_id from the orders table
    query = "SELECT MAX(order_id) FROM orders"
    result = execute_query(query)
    max_order_id = result[0][0] if result else None
    new_order_id = 1 if max_order_id is None else max_order_id + 1 # None means the orders table is empty

    # Iterate over the order dictionary and process each item
    for item_name, quantity in order.items():
        # Get the item_id and price for the current item
        query = "SELECT item_id, price FROM food_items WHERE name = %s"
        result = execute_query(query, (item_name,))
        if not result:
            return 0

        item_id, price = result[0]
        total_price = price * quantity

        # Insert the new order into the orders table
        query = "INSERT INTO orders (order_id, item_id, quantity, total_price) VALUES (%s, %s, %s, %s)"
        if not execute_non_query(query, (new_order_id, item_id, quantity, total_price)):
            print(f"Failed to insert order for item '{item_name}'")
            return 0

        print(f"{item_name} : ID({item_id}), Price: ${price}, Quantity : {quantity}, Total Price : {total_price}")

    # Insert the new order into the order_tracking table with status 'in progress'
    query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    if not execute_non_query(query, (new_order_id, 'in progress')):
        print(f"Failed to insert order tracking for order ID '{new_order_id}'")
        return 0

    return new_order_id


def calculate_order_total_price(order_id: int) -> float:
    """
    Calculate the total price for the given order_id and update the orders table.

    Args:
        order_id (int): The order ID for which to calculate the total price.

    Returns:
        float: The total price of the order if the operation is successful, 0 otherwise.
    """
    query = "SELECT item_id, quantity FROM orders WHERE order_id = %s"
    items = execute_query(query, (order_id,))
    if not items:
        return 0

    total_order_price = 0

    for item_id, quantity in items:
        query = "SELECT price FROM food_items WHERE item_id = %s"
        result = execute_query(query, (item_id,))
        if not result:
            return 0
        price = result[0][0]
        total_price = price * quantity
        total_order_price += total_price

    return total_order_price


def get_order_status(order_id):
    """
    Get the status of an order.

    Args:
        order_id (int): The order ID.

    Returns:
        str: The status of the order, or None if not found.
    """
    query = "SELECT status FROM order_tracking WHERE order_id = %s"
    result = execute_query(query, (order_id,))
    if result:
        return result[0][0]  # Return the status value
    else:
        return None
