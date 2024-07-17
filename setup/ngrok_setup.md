# Ngrok Setup for UMA Food Chatbot

Ngrok is necessary if you do not have an HTTPS URL, as Dialogflow requires a secure (HTTPS) webhook endpoint.

## Step-by-Step Guide

### Step 1: Create an Account

1. Go to the [Ngrok website](https://ngrok.com) and sign up for an account if you don't already have one.

### Step 2: Setup and Installation

1. Download Ngrok from the setup and installation page.
2. Extract the downloaded file and place the `ngrok.exe` file in the `uma_food_chatbot/` directory.

### Step 3: Run Ngrok

1. Double-click on `ngrok.exe` to open a terminal.
2. In the terminal, run the following command, making sure to replace `your_auth_token` with your Ngrok authentication token:
    ```sh
    ngrok authtoken your_auth_token
    ```

### Step 4: Set Up a Custom Domain (Optional)

1. Go to the Ngrok dashboard and navigate to **Cloud Edge** > **Domains**.
2. Create a new domain.
3. Copy and paste the generated command into the Ngrok terminal, updating the port number to match your FastAPI server's port (e.g., 8000):
    ```sh
    ngrok http --domain=your-custom-domain.ngrok-free.app 8000
    ```

### Step 5: Get the HTTPS URL

1. Once Ngrok is running, it will display the forwarding addresses.
2. Note the HTTPS forwarding URL, for example:
    ```
    https://your-custom-domain.ngrok-free.app
    ```

### Step 6: Update Dialogflow Fulfillment

1. Go to the Dialogflow console.
2. Navigate to your agent's **Fulfillment** settings.
3. Update the webhook URL with the HTTPS URL provided by Ngrok, for example:
    ```
    https://your-custom-domain.ngrok-free.app/webhook
    ```

By following these steps, you will be able to expose your local FastAPI server to the internet using Ngrok and use it with Dialogflow.

### Note:
- Ensure your FastAPI server is running locally before starting Ngrok. by running the command :
    ```sh
    python run.py
    ```
- Ngrok free plan allows the creation of custom domains only in the `ngrok-free.app` domain.

## Troubleshooting

If you encounter issues, ensure that:
- Your local FastAPI server is running and accessible.
- You have the correct port number in the Ngrok command.
- The Ngrok terminal displays active status and provides the forwarding URL.

For more detailed troubleshooting, refer to the [Ngrok documentation](https://ngrok.com/docs).
