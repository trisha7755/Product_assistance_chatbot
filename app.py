from flask import Flask, render_template, request
import json
import requests
import openai

# OpenAI API Key
api_key = "openai_api_key"
api_url = 'https://api.openai.com/v1/chat/completions'
app = Flask(__name__)

# Load orders from a JSON file
def load_orders():
    try:
        with open("orders.json", "r") as file:
            return json.load(file)
    except Exception:
        return []

# Save updated orders to the JSON file
def save_orders(orders):
    with open("orders.json", "w") as file:
        json.dump(orders, file, indent=4)

# Search for an order by ID
def search_order(order_id):
    orders = load_orders()
    for order in orders:
        if order["order_id"] == order_id:
            return order
    return None

# Update order details
def update_order(order_id, updates):
    orders = load_orders()
    for order in orders:
        if order["order_id"] == order_id:
            order.update(updates)
            save_orders(orders)
            return order
    return None

# Placeholder function for GPT response generation
def generate_gpt_response(order_details):
    try:
        headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Please rephrase the following order details in a polite and user-friendly manner:"},
                {"role": "user", "content": order_details}],
            "temperature": 0.7
        }
        response = requests.post(api_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            return reply
    except Exception as e:
        return f"I'm sorry, I couldn't process your request due to an error: {e}"

@app.route("/", methods=["GET", "POST"])
def chatbot():
    response = "Hi! How can I assist you today?"
    buttons = [
        "Track Order",
        "Modify Delivery Address",
        "Cancel Order",
        "End Chat",
        "delivery_address"
    ]
    context = ""

    if request.method == "POST":
        context = request.form.get("context", "")
        user_input = request.form.get("user_input", "").strip()

        if user_input == "Track Order" and not context:
            response = generate_gpt_response("Please provide the Order ID you want to track.")
            context = "Track Order"
            buttons = []

        elif context == "Track Order":
            order = search_order(user_input)
            if order:
                response = generate_gpt_response(f"Order ID: {user_input} is currently at {order['current_location']}.")
            else:
                response = generate_gpt_response(f"Order ID: {user_input} not found. Please re-check the ID and try again.")
            buttons = ["Track Another Order", "End Chat"]
            context = ""

        elif user_input == "Modify Delivery Address" and not context:
            response = generate_gpt_response("Please provide the Order ID for its delivery address.")
            context = " Delivery Address"
            buttons = []

        elif context == "Delivery Address":
            order = search_order(user_input)
            if order and order["delivery_address"] not in ["Out for Delivery", "Delivered"]:
                response = generate_gpt_response(f"Order ID: {user_input} is eligible for address modification. Please enter the new address.")
                context = f"Update Address {user_input}"
                buttons = []
            else:
                response = generate_gpt_response(f"Order ID: {user_input} cannot have its address modified. It may already be out for delivery or completed.")
                buttons = ["Modify Another Address", "End Chat"]
                context = ""
        elif user_input == "Modify Delivery Address" and not context:
            response = generate_gpt_response("Please provide the Order ID to modify its delivery address.")
            context = "Modify Delivery Address"
            buttons = []

        elif context == "Modify Delivery Address":
            order = search_order(user_input)
            if order and order["status"] not in ["Out for Delivery", "Delivered"]:
                response = generate_gpt_response(f"Order ID: {user_input} is eligible for address modification. Please enter the new address.")
                context = f"Update Address {user_input}"
                buttons = []
            else:
                response = generate_gpt_response(f"Order ID: {user_input} cannot have its address modified. It may already be out for delivery or completed.")
                buttons = ["Modify Another Address", "End Chat"]
                context = ""

        elif "Update Address" in context:
            order_id = context.split()[-1]
            update_order(order_id, {"delivery_address": user_input})
            response = generate_gpt_response(f"The delivery address for Order ID: {order_id} has been updated successfully.")
            buttons = ["Modify Another Address", "End Chat"]
            context = ""

        elif user_input == "Cancel Order" and not context:
            response = generate_gpt_response("Please provide the Order ID of the order you want to cancel.")
            context = "Cancel Order"
            buttons = []

        elif context == "Cancel Order":
            order = search_order(user_input)
            if order and order["status"] in ["Processing", "Ready for Shipment"]:
                update_order(user_input, {"status": "Cancelled"})
                response = generate_gpt_response(f"Order ID: {user_input} has been successfully cancelled.")
            else:
                response = generate_gpt_response(f"Order ID: {user_input} cannot be cancelled. It may already be shipped or delivered.")
            buttons = ["Cancel Another Order", "End Chat"]
            context = ""

        elif user_input == "End Chat":
            response = "Thank you for using our service. Have a great day!"
            buttons = [
                "Track Order",
                "Modify Delivery Address",
                "Cancel Order",
                "End Chat"
            ]
            context = ""

        else:
            response = generate_gpt_response("I'm sorry, I didn't understand your request. Please try again.")
            buttons = [
                "Track Order",
                "Modify Delivery Address",
                "Cancel Order",
                "End Chat"
            ]

    return render_template("index.html", response=response, buttons=buttons, context=context)

if __name__ == "__main__":
    app.run(debug=True)