# Dialogflow Setup for UMA Food Chatbot

This document provides all the necessary information to set up Dialogflow for the UMA Food Chatbot, 

## Step 1:
- Go to [Dialogflow ](https://cloud.google.com/dialogflow?hl=en).
- Scroll down to the "Editions" section and Click "Go to console" of "Dialogflow ES (Essentials)"
- Create an account

## Step 2: 
Create a new agent and name it `uma_food_chatbot`.
Click "Save".

## Step 3: 
- Define entities, intents, contexts, events, training phrases, actions and parameters, and responses.

### Entities
- Check : 
    - Define synonyms
    - Allow automated expansion
    - Fuzzy matching
- Add Entities: 
    - **food-item**:
        - **Salmon Sushi** : Salmon Sushi, Salmon sushi, Salmen sushi, Salmin sushi, Salmon sushy, Salmon sushe, Salmon sishi, Salomon sushi, salmon, salmn, salmons, Salom sishi, Salom sushi, Sush salmon
        - **Tuna Sushi** : Tuna Sushi, Tuma sushi, Tuns sushi, Tuan sushi, Tuna sushy, Tuna sushi, Tun sushi, Tuna sushe, Tunna sushi, Tuna sushe, Tun sushi, Tunna sushi, Tonno sushi, Tuna suhi, Tuna sishi, Tuna sush, tuna, tunas
        - **Chirasi** : Chirasi, Chirashi sushi, Chirashi bowl, Chirashi don, Chirashi donburi, Chirashi, Chirrasu, Chirashi suhi, Chirassu sushi, Chirashi sushi, Chirashi susi, Chirrasii sushi, Chirashy sushi, Chirshii sushi, Chirashi sush, Chirshii su, Chirashi, chirsi, chirasimi
    - **confirmation**:
        - **True** : Confirm, Complete, I don't want to cancel, Proceed, Process, Comfirm, Finish, Submit my order, Finalize my order, Complete transaction, Go ahead, Shoot, Order confirmation, Finalize and confirm, Confirm my purchase
        - **False** :  Cancel, Remove, Delete, I  don't want to complete, Cancle, I don't want to confirm, Delete my order, Stop my order, Void my order, Abort my order
- Click "Save"

### Intents

#### Default Welcome Intent
- **Event**: `WELCOME`
- **Training Phrases**:
    - What's up
    - Hello
    - Hi
    - Hey
    - Good morning
    - Good evening
    - Is anyone there?
    - Can someone help me
    - How are you doing today
    - Hello there
    - Yo
    - Hiya
    - What’s good
    - What's happening
    - What's going on
    - Greetings
- **Responses**: Hi👋 This is UMA Bot. How can I help you today? You can say 'Order' 🍱, 'Status' 🔍 or 'Hours' 🕒.
- Click "Save"

**Note**: To ensure the starter message appears when the user visits the chat for the first time, follow these steps:
    - Enable DialogFlow Messenger in the Integrations section of DialogFlow and copy the integration script.
    - Paste the script into app/templates/index.html where you want the chatbot.


#### Default Fallback Intent
- **Action**: input.unknown
- **Responses**: I didn't understand 😕. For the list, say 'Menu' 📜. You can also say 'Order' 🍣, 'Status'🔍, or 'Hours'🕒 .
- Click "Save"


#### new.order
- **Context**:
    - Output context : `ongoing-order` (Lifespan : 5)
- **Training Phrases**:
    - I want to place a new order
    - Can I order some food?
    - I'd like to make a new order
    - I want to order
    - I need to order food
    - Can I start a new order?
    - I want to order something
    - Let me place a new order
    - I'd like to order now
    - How do I place a new order?
    - Can I make a new order?
    - I want to order more food
    - I need to make a new order
    - I want to order 
    - Can I order some 
    - I'd like to place an order for 
    - I'd like to order some
    - I want to get some 
    - Can I get some food?
    - How do I start a new order?
    - I want to order food now
    - How do I place an order?
    - I need to order something
    - Can I start an order?
    - I'd like to get some food
    - Help me place an order
    - I’d like to buy some food
    - Can I make an order now?
    - I want to purchase some food
    - Order food
    - I want to place an order for sushi
    - How can I order food?
    - Place a new order for me
    - I’d like to order something to eat
    - Order something for me
    - How do I order from here?
    - I want to get 
    - Can I order dinner?
    - I want to make an order
    - Place an order
- **Fulfillment**: Activate 'Enable Webhook call for this intent'
- Click "Save"

#### get.menu - context: ongoing-order
- **Context**:
    - Input context : `ongoing-order`
    - Output context : `ongoing-order` (Lifespan : 5)
- **Training Phrases**:
    - Menu
    - Show me the menu
    - What's in the menu?
    - Can I see the menu?
    - Menu options
    - What can I order?
    - Tell me the menu
    - What's for lunch/dinner/breakfast?
    - What's on offer?
    - What's for sale?
    - What dishes do you have?
    - Show me what you have
    - What's cooking?
    - List the menu
- **Fulfillment**: Activate 'Enable Webhook call for this intent'
- Click "Save"

#### order.add - context: ongoing-order
- **Context**:
    - Input context : `ongoing-order`
    - Output context : `ongoing-order` (Lifespan : 5)
- **Action and parameters**:
    - Parameter Name : `food-item`
        - Entity : `@food-item`, 
        - Value : `$food-item`, 
        - IS LIST : checked
    - Parameter Name : `qty`, 
        - Entity : `@sys.number`, 
        - Value : `$qty`, 
        - IS LIST : checked
- **Training Phrases**:
    - Give me 2 Tuna Sushi, one cheese salmon Sushi
    - I'd like to order two plates of chirasi,  one cheese salmon Sushi, and 3 Tuna Sushi, please.
    - Can you please get me two servings of chirasi, one Tuna Sushi, and one salmon Sushi?
    - Please prepare 2 portions of chirasi, along with one Tuna Sushi and 1 salmon Sushi for me
    - 6 Tuna Sushi, 6 salmon Sushi, 1 chirasi
    - Can I get 2 plates of chirasi, along with one Tuna Sushi and 1 salmon Sushi?
    - I'll take 2 orders of Tuna Sushi, one chirasi, and 1 salmon Sushi, if you don't mind
    - I want 1 Tuna Sushi, 2 salmon Sushi and one chirasi, do it fast plz
    - In addition, add 1 Tuna Sushi and 2 salmon Sushi
    - Moreover, include 2 chirasi
    - Also, please give me 2 chirasi
    - Additionally, I'd like 2 Tuna Sushi.
    - 2 Tuna Sushi and ok lets add one salmon Sushi too
    - 3 chirasi
    - Oh yes, add one chirasi as well
    - Please add 4 tunas
    - Add 3 salmons
    - Chirasi
    - Tuna
    - Salmons
    - 4 salmons, 1 tuna and 3 chirasi
- **Fulfillment**: Activate 'Enable Webhook call for this intent'
- Click "Save"

#### order.affirmative_response - context: ongoing-order
- **Context**:
    - Input context : `ongoing-order`
    - Output context : `ongoing-order` (Lifespan : 5)
- **Training Phrases**:
    - Yes
    - Yeah
    - Yes please
    - Yup
    - Yep
    - Sure
    - Absolutely
    - Of course
    - Definitely
    - Why not
    - Certainly
    - Okay
    - Affirmative
    - Indeed
- **Responses**: What would you like to add? You can say "Menu" to show list of items 🍣.
- Click "Save"

#### order.remove - context: ongoing-order
- **Context**:
    - Input context : `ongoing-order`
    - Output context : `ongoing-order` (Lifespan : 5)
- **Action and parameters**:
    - Parameter Name : `food-item`
        - Required : checked, 
        - Entity : `@food-item`, 
        - Value : `$food-item`, 
        - is list : checked, 
        - Prompts : Please specify the food item (e.g. remove Tuna Sushi)
    - Parameter Name : `qty`, 
        - Entity : `@sys.number`, 
        - Value : `$qty`, 
        - is list : checked
- **Training Phrases**:
    - No Salmon Sushi and Tuna Sushi in my order. please remove.
    - Kindly take Tuna Sushi and chirasi off the order, please.
    - I'd like to exclude salmon Sushi and chirasi, please
    - I no longer want the Tuna Sushi in my order, please remove it
    - Kindly exclude the salmon Sushi from my order
    - I would like to remove the chirasi from my order
    - Please take the chirasi off my order
    - delete Tuna Sushi from my order
    - hey, plz get rid of Tuna Sushi and chirasi
    - I don't want Tuna Sushi
    - remove Tuna Sushi from my order
    - can you remove salmon Sushi?
- **Fulfillment**: Activate 'Enable Webhook call for this intent'
- Click "Save"

#### order.prompt_confirm - context: ongoing-order
- **Context**:
    - Input context : `ongoing-order`
    - Output context : `ongoing-order` (Lifespan : 5)
- **Action and parameters**:
    - Parameter Name : `confirmation`
        - Entity : `@confirmation`,
        - Value : `$confirmation`,
        - is list : unchecked
- **Training Phrases**:
    - Nope
    - Nah
    - Not really
    - I'm fine, thanks
    - That's all I needed
    - No that's all
    - No that's it
    - No I'm okay
    - No I'm good
    - Done
    - That's it
    - No more
    - That's everything
    - That's all I want
    - I'm good with my order
    - No, I don't need anything else
    - No, that’s enough
    - No, I’m done
    - No, I’ve got everything I need
    - No, I'm sorted
- **Fulfillment**: Activate 'Enable Webhook call for this intent'
- Click "Save"
- **Add follow-up intent**: order.complete_confirm - context: ongoing-order

#### order.complete_confirm - context: ongoing-order
- **Context**:
    - Input context : `ongoing-tracking` (Lifespan : 5)
- **Training Phrases**:
    - Confirm
    - Cancel
    - Yes confirm
    - Yes cancel
    - Complete
    - Yes complete
    - Confirm, please
    - Cancel, please
    - Yes, confirm order
    - Okay, confirm
    - Confirm it
    - Process my order
    - Go ahead
    - Finish the order
    - Finalize and confirm
    - Delete my order
    - Order confirmation
    - Finish the purchase
    - Stop the order
- **Fulfillment**: Activate 'Enable Webhook call for this intent'
- Click "Save"

#### track.order - context: ongoing-tracking
- **Context**:
    - Output context : `ongoing-tracking` (Lifespan : 5)
- **Training Phrases**:
    - Can I check the status of my order?
    - Track my order
    - Where is my order?
    - Order status
    - Can you tell me the status of my order?
    - I need to track my order
    - What's the status of my order?
    - How is my order doing?
    - Can I get an update on my order?
    - Check my order status
    - Is my order on the way?
    - When will my order arrive?
    - Can I see where my order is?
    - Update me on my order
    - Has my order been shipped?
    - Is my order out for delivery?
    - Can you track my order?
    - How long until my order arrives?
    - Where's my order?
    - I want to know where my order is
    - Give me an update on my order
    - What's happening with my order?
    - Find my order
    - Tell me the status of my order
    - Check the progress of my order
    - Where is my food?
    - Track my food delivery
    - Is my food on its way?
    - When will my food be here?
    - How can I track my order?
    - Look up my order status
    - Show me my order status
    - Has my order been dispatched?
    - Can you check on my order?
    - Where's my delivery?
    - Track the order I placed
    - Any updates on my order?
    - How much longer for my order?
    - What’s the delivery status of my order?
- **Responses**:
    - 👍 Definitely. What is your order id?📝
    - 👍 Sure. Please enter your order id 📝
- Click "Save"

#### track.order - context: ongoing-tracking
- **Context**:
    - Input context : `ongoing-tracking`
    - Output context : `ongoing-tracking` (Lifespan : 5)
- **Action and parameters**:
    - Parameter Name : `order_id`
        - Required : checked, 
        - Entity : `@sys.number`, 
        - Value : `$order_id`, 
        - Prompts : Please enter your order id📝
- **Training Phrases**:
    - The order ID is 341
    - Track order ID 341
    - ID for my order is 341
    - Track my order with ID 341
    - My order number is 341
    - This is my order ID: 341
    - I want to track order ID 341
    - Can you check order ID 341?
    - I need to track order number 341
    - Here's the ID: 341
    - Order ID for tracking: 341
    - Order tracking ID 341
    - Look up order 341
    - Please track order ID 341
    - Order reference 341"
    - Track my order number 341
- **Fulfillment**: Activate 'Enable Webhook call for this intent'
- Click "Save"

#### store.hours
- **Training Phrases**:
    - When are you open?
    - What are your store hours?
    - When do you close?
    - When is the store open?
    - store hours
    - store
    - When is the store open today?
    - What are the hours of operation?
    - What are your business hours?
    - Closing hours
    - Opening hours
    - Business hours
    - When do you open and close?
    - What time do you close?
    - What time do you open?
    - Can you tell me the store hours?
- **Responses**:
    - 🕑 Our business hours are 9 AM to 9 PM Monday through Saturday, and 10 AM to 6 PM on Sunday. Have a great day! 🌞
    - ⏰ We are open from 9 AM to 9 PM on weekdays and from 10 AM to 6 PM on weekends. See you soon! 😊
    - 🕒 Our store is open from 9 AM to 9 PM from Monday to Saturday, and from 10 AM to 6 PM on Sundays. 🛒
- Click "Save"

## Step 4:
- Add the HTTPS URL in the Fulfillment settings of Dialogflow:
    - Navigate to the agent's Fulfillment settings.
    - Enable the Webhook and add the HTTPS URL:
        - If you are using ngrok to generate the HTTPS URL:
            - This URL is the forwarding address provided by ngrok when you run the `ngrok http 8000` command. It securely exposes your local FastAPI server to the internet.
            - Refer to the `ngrok_setup.md` file for detailed instructions.
            - Example: https://your-custom-domain.ngrok-free.app
        - If you are not using ngrok (e.g., in production):
            - Use the HTTPS URL of your deployed FastAPI server.
            - Ensure the server is accessible over the internet and has a valid SSL certificate.
- Click "Save" to update the fulfillment settings.