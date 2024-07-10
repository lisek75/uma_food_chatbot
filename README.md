# 🍣 Uma Chatbot for food

This chatbot, designed for a Japanese restaurant named UMA, leverages Dialogflow's Natural Language Processing (NLP) capabilities to assist users in managing their orders seamlessly. The chatbot supports adding or removing items, completing orders, and tracking order status in real-time, making the ordering process efficient and interactive.

## 📂 Project Structure

uma_food_chatbot/
- `app/`: Main application code.
  - `main.py`: FastAPI app instance and endpoint handlers.
  - `db_helper.py`: Database helper functions for interacting with the database.
  - `generic_helper.py`: Generic helper functions used across the application..
  - `static/`: Static files (CSS and images).
  - `templates/`: HTML files.
- `setup/`: Setup documentation (DiaogFlow, ngrok, and sql).
- `run.py`: Entry point for running the FastAPI application using Uvicorn.
- `README.md`: Project overview, setup instructions, and usage information.


## 🛠️ Setup

### 📚 Prerequisites

- Python 3.7 or higher
- Proficiency in Python programming
- Familiarity with FastAPI
- Basic knowledge of MySQL
- Understanding of Dialogflow and handling JSON data


### 📥 Installation

1. **Clone the repository**:

    ```sh
    git clone https://github.com/lisek75/uma_food_chatbot.git
    cd uma_food_chatbot
    ```

2. **Create and activate a virtual environment**:

    ```sh
    python -m venv .venv
    .venv/Scripts/activate # On MacOS/Linux source .venv/bin/activate
    ```

3. **Install the dependencies**:

    ```sh
    pip install -r requirements.txt
    ```


### 🗄️MySQL Setup

1. **Install MySQL**:

    Download and install MySQL from the [official website](https://dev.mysql.com/downloads/installer/). MySQL Workbench is included in the MySQL installer package.


3. **Import the Database Schema**:

    - Open MySQL Workbench and connect to your MySQL server. Create a new MySQL server with username `root`, password `root`, and host `localhost` if working locally.
    - Update `app/db_helper.py` in the `get_db_connection()` function to match your configuration:

        ```python
        db_config = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'database': 'uma_food_chatbot'
        }
        ```
    - Import `uma_food_chatbot.sql` from the `setup` folder:
        - Go to `Server > Data Import`.
        - Select `Import from Self-Contained File`.
        - Browse and select the `uma_food_chatbot.sql` file.
        - Click `Start Import` to import the database with all tables.


### 🚀 Running the Application

1. **Start the FastAPI application**:

    ```sh
    python run.py
    ```
    The application will be available at `http://127.0.0.1:<port>`, where `<port>` is the port number you specified (e.g., 8000).


2. **Install and setup Dialogflow and ngrok**:

    Refer to the `setup/dialogflow_setup.md` and `setup/ngrok_setup.md` files for detailed instructions on setting up Dialogflow and ngrok.

3. **Run ngrok**:
    Use this if you are running the application locally and do not have HTTPS.

    ```sh
    ngrok http --domain=your-custom-domain.ngrok-free.app 8000
    ```

    Example:

    ```sh
    ngrok http --domain=classic-intensely-seal.ngrok-free.app 8000
    ```

4. **Access the application**:

    Go to `http://127.0.0.1:<port>`, for example: `http://127.0.0.1:8000`.

## 💻 Usage

  - The application serves static files like CSS and images.
  - It renders the index.html template, which includes an embedded chatbot iframe.
  - Users can interact with the chatbot to add or remove items, complete their orders, and track their order status.
