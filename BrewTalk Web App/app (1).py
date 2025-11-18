# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import config         # Import our config
import database as db # Import our database functions
import os

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# --- THIS IS IMPORTANT ---
# This checks if the database file exists. If not, it creates it.
# This saves you from having to run a command manually.
if not os.path.exists(config.DB_NAME):
    print("Database not found. Initializing...")
    db.init_db()
    print("Database initialized.")


# A context processor to inject the watsonx widget into all templates
@app.context_processor
def inject_watsonx_widget():
    # Since we aren't using cloud env variables, we need to add your keys here
    # or read them from a .env file (if you add python-dotenv)
    # For now, let's hardcode them for simplicity.
    # !! WARNING: Do not share this if your keys are real.
    watsonx_id = "b060395c-5e61-4bdc-978c-afdb98e5f01d" # From your original code
    watsonx_region = "us-east"
    watsonx_sid = "8ab991dd-9341-417d-a1e2-a4e684c1f53f"
    
    widget_html = f'''
<script>
window.watsonAssistantChatOptions = {{
  integrationID: "{watsonx_id}",
  region: "{watsonx_region}",
  serviceInstanceID: "{watsonx_sid}",
  onLoad: function(instance) {{ instance.render(); }}
}};
setTimeout(function(){{
  const t=document.createElement('script');
  t.src="https://web-chat.global.assistant.watson.app.domain.cloud/versions/" + (window.watsonAssistantChatOptions.clientVersion || 'latest') + "/WatsonAssistantChatEntry.js";
  document.head.appendChild(t);
}});
</script>
'''
    return dict(watsonx_widget=widget_html)

# --- ROUTES ---
# (All your @app.route functions go here: / , /menu, /order, etc.)
# (Copy them from the previous app.py I gave you, they are perfect)

@app.route('/')
def index():
    """Home dashboard - shows pending order count."""
    pending_count = db.get_pending_orders_count()
    return render_template('index.html', pending_count=pending_count)

@app.route('/menu', methods=['GET', 'POST'])
def menu():
    """Menu management page - list items and add new ones."""
    if request.method == 'POST':
        name = request.form['name'].strip().title()
        try:
            price = float(request.form['price'])
        except ValueError:
            flash("Price must be a number.")
            return redirect(url_for('menu'))
        
        in_stock = 'in_stock' in request.form
        success, message = db.add_menu_item(name, price, in_stock)
        flash(message)
        return redirect(url_for('menu'))

    menu_items = db.get_menu_items()
    return render_template('menu.html', menu_items=menu_items)

@app.route('/order', methods=['GET', 'POST'])
def order():
    """Place order page."""
    if request.method == 'POST':
        total = db.process_new_order(request.form)
        if total is None:
            flash("Please select at least one item.")
            return redirect(url_for('order'))
        else:
            flash(f"Order placed successfully! Total: ₹{total:.2f}")
            return redirect(url_for('index'))

    menu_items = db.get_menu_items()
    return render_template('order.html', menu_items=menu_items)


@app.route('/manage-orders')
def manage_orders():
    """Show all pending orders."""
    pending_orders = db.get_pending_orders()
    return render_template('manage_orders.html', orders=pending_orders)


@app.route('/complete-order/<int:order_id>')
def complete_order(order_id):
    """Mark an order as complete."""
    db.mark_order_complete(order_id)
    flash(f"Order #{order_id} marked as completed!")
    return redirect(url_for('manage_orders'))

# We don't need the "if __name__ == '__main__':" block
# PythonAnywhere does not use it.