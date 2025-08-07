from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key')

# Database config
db_config = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME'),
}

# ---------------- ROOT ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('stocks'))
    else:
        return redirect(url_for('login'))


# ---------------- LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session['username'] = user['username']
                flash('Login successful', 'success')
                return redirect(url_for('stocks'))  # Adjust if needed
            else:
                flash('Invalid username or password', 'danger')

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'danger')

    return render_template('login.html')

# ---------------- LOGOUT ------------------
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

# ---------------- STOCKS PAGE ------------------
@app.route('/stocks')
def stocks():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
        cursor.close()
        conn.close()

        total_value = sum(item['quantity'] * item['subtotal'] for item in items)
        return render_template('stocks.html', items=items, total_value=total_value)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return render_template('stocks.html', items=[], total_value=0)

# ---------------- STOCK ACTION PAGE ------------------
@app.route('/stock/<int:item_id>/<action>', methods=['GET', 'POST'])
def stock_action(item_id, action):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM items WHERE item_id = %s", (item_id,))
        item = cursor.fetchone()

        if not item:
            flash('Item not found.', 'warning')
            return redirect(url_for('stocks'))

        if request.method == 'POST':
            try:
                qty = int(request.form['quantity'])
                selected_action = request.form['action']

                if selected_action == 'add':
                    new_qty = item['quantity'] + qty
                elif selected_action == 'remove':
                    new_qty = item['quantity'] - qty
                    if new_qty < 0:
                        flash('Not enough stock to remove that amount.', 'danger')
                        return redirect(request.url)
                else:
                    flash('Invalid action.', 'warning')
                    return redirect(url_for('stocks'))

                cursor.execute("UPDATE items SET quantity = %s WHERE item_id = %s", (new_qty, item_id))
                conn.commit()
                flash(f"Stock successfully {selected_action}ed.", 'success')
                return redirect(url_for('stocks'))

            except ValueError:
                flash('Invalid quantity. Please enter a valid number.', 'danger')

        return render_template('stock_action.html', item=item, action=action)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('stocks'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ---------------- MAIN ------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
