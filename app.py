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
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# ---------------- ROOT ------------------
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

            # Use 'password_hash' to match your table schema
            if user and check_password_hash(user['password_hash'], password):
                session['username'] = user['username']
                flash('Login successful', 'success')
                return redirect(url_for('stocks'))
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

        # Adjust this if your DB uses a different field than 'subtotal'
        total_value = sum(item['quantity'] * item['subtotal'] for item in items)
        return render_template('stocks.html', items=items, total_value=total_value)

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return render_template('stocks.html', items=[], total_value=0)

# ---------------- STOCK HISTORY PAGE ------------------
@app.route('/stock_history/<int:item_id>')
def stock_history(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT sh.*, i.item_name
            FROM stock_history sh
            JOIN items i ON sh.item_id = i.item_id
            WHERE sh.item_id = %s
            ORDER BY sh.change_date DESC
        """, (item_id,))
        history = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('stock_history.html', history=history)
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        return redirect(url_for('stocks'))

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

                # Update stock
                cursor.execute("UPDATE items SET quantity = %s WHERE item_id = %s", (new_qty, item_id))

                # Log change
                cursor.execute("""
                    INSERT INTO stock_history (item_id, item_name, change_type, quantity_changed, changed_by)
                    VALUES (%s, %s, %s, %s, %s)
                """, (item['item_id'], item['item_name'], selected_action, qty, session['username']))

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