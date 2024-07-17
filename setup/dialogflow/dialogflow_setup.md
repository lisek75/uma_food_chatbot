# Dialogflow Setup for UMA Food Chatbot

This document provides all the necessary information to set up Dialogflow for the UMA Food Chatbot, 

## Step 1:
- Go to [Dialogflow ](https://cloud.google.com/dialogflow?hl=en).
- Scroll down to the "Editions" section and Click "Go to console" of "Dialogflow ES (Essentials)"
- Create an account

## Step 2: 
Create a new agent and name it `uma_bot`.
Click "Save".

## Step 3: 
- Go to the settings of the chatbot (the settings icon ⚙️ near the chatbot name).
- Navigate to the "Export and Import" tab.
- Click "Import from ZIP" and upload the `uma_bot.zip` file shared in the `setup/dialogflow` folder.

## Step 4:
- Add the HTTPS URL in the Fulfillment settings of Dialogflow:
    - Navigate to the agent's Fulfillment settings.
    - Enable the Webhook and add the HTTPS URL:
        - If you are using ngrok to generate the HTTPS URL:
            - This URL is the forwarding address provided by ngrok when you run the `ngrok http 8000` command. It securely exposes your local FastAPI server to the internet.
            - Refer to the `ngrok_setup.md` file for detailed instructions.
            - Example: https://your-custom-domain.ngrok-free.app
        - If you are not using ngrok :
            - Use the HTTPS URL of your deployed FastAPI server.
            - Ensure the server is accessible over the internet and has a valid SSL certificate.
- Click "Save" to update the fulfillment settings.