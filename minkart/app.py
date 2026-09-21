import os
import sqlite3
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g, jsonify
)
from database.seed_data import SAMPLE_PRODUCTS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "shop.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "minkart_super_secret_dev_key_2026")


def get_db():
    if 'db' not in g:
        # Ensure database directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create database tables and seed initial products if empty."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            price REAL NOT NULL,
            original_price REAL,
            discount_percentage INTEGER DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            rating REAL DEFAULT 4.5,
            review_count INTEGER DEFAULT 0,
            image_url TEXT,
            sku TEXT UNIQUE NOT NULL,
            featured INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            total_amount REAL NOT NULL,
            order_status TEXT DEFAULT 'Processing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create Order Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)

    conn.commit()

    # Seed products if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    if count == 0:
        for p in SAMPLE_PRODUCTS:
            cursor.execute("""
                INSERT INTO products (
                    name, description, category, brand, price, original_price,
                    discount_percentage, stock, rating, review_count, image_url, sku, featured
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["name"], p["description"], p["category"], p["brand"],
                p["price"], p["original_price"], p["discount_percentage"],
                p["stock"], p["rating"], p["review_count"], p["image_url"],
                p["sku"], p["featured"]
            ))
        conn.commit()

    conn.close()


# Initialize database automatically on startup
with app.app_context():
    init_db()


def get_cart_details():
    """Retrieve full product information and calculate cart totals server-side."""
    cart = session.get('cart', {})
    items = []
    subtotal = 0.0
    total_items = 0

    if cart:
        db = get_db()
        placeholders = ','.join(['?'] * len(cart))
        product_ids = [int(pid) for pid in cart.keys()]
        
        cursor = db.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", product_ids)
        products = cursor.fetchall()
        
        product_dict = {str(p['id']): p for p in products}

        for pid_str, qty in list(cart.items()):
            if pid_str in product_dict:
                p = product_dict[pid_str]
                qty = int(qty)
                # Cap quantity at current stock
                if qty > p['stock']:
                    qty = p['stock']
                    cart[pid_str] = qty
                    session.modified = True

                if qty > 0:
                    item_subtotal = round(p['price'] * qty, 2)
                    subtotal += item_subtotal
                    total_items += qty
                    items.append({
                        'product': dict(p),
                        'quantity': qty,
                        'subtotal': item_subtotal
                    })

    # Free shipping on orders over $50, else $10 standard shipping
    shipping = 0.0 if (subtotal >= 50.0 or subtotal == 0.0) else 10.0
    grand_total = round(subtotal + shipping, 2)

    return {
        'items': items,
        'subtotal': round(subtotal, 2),
        'shipping': shipping,
        'grand_total': grand_total,
        'total_items': total_items
    }


@app.context_processor
def inject_cart_count():
    """Make cart item count available to all HTML templates."""
    cart = session.get('cart', {})
    total_count = sum(int(qty) for qty in cart.values())
    return dict(cart_count=total_count)


# --- ROUTES ---

@app.route('/')
def index():
    db = get_db()
    
    # Featured Products
    featured = db.execute("SELECT * FROM products WHERE featured = 1 LIMIT 8").fetchall()
    
    # Best Deals (highest discount)
    best_deals = db.execute("SELECT * FROM products ORDER BY discount_percentage DESC LIMIT 8").fetchall()
    
    # New Arrivals
    new_arrivals = db.execute("SELECT * FROM products ORDER BY id DESC LIMIT 8").fetchall()
    
    # Categories with count
    categories_rows = db.execute("""
        SELECT category, COUNT(*) as count 
        FROM products 
        GROUP BY category 
        ORDER BY count DESC
    """).fetchall()

    return render_template(
        'index.html',
        featured_products=featured,
        best_deals=best_deals,
        new_arrivals=new_arrivals,
        categories=categories_rows
    )


@app.route('/products')
def products():
    db = get_db()
    
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    brand = request.args.get('brand', '').strip()
    min_price = request.args.get('min_price', '').strip()
    max_price = request.args.get('max_price', '').strip()
    min_rating = request.args.get('min_rating', '').strip()
    sort = request.args.get('sort', 'relevance').strip()

    sql = "SELECT * FROM products WHERE 1=1"
    params = []

    if query:
        sql += " AND (name LIKE ? OR brand LIKE ? OR category LIKE ? OR description LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term, term])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if brand:
        sql += " AND brand = ?"
        params.append(brand)

    if min_price:
        try:
            sql += " AND price >= ?"
            params.append(float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            sql += " AND price <= ?"
            params.append(float(max_price))
        except ValueError:
            pass

    if min_rating:
        try:
            sql += " AND rating >= ?"
            params.append(float(min_rating))
        except ValueError:
            pass

    # Sorting logic
    if sort == 'price_low':
        sql += " ORDER BY price ASC"
    elif sort == 'price_high':
        sql += " ORDER BY price DESC"
    elif sort == 'rating':
        sql += " ORDER BY rating DESC"
    elif sort == 'newest':
        sql += " ORDER BY id DESC"
    elif sort == 'discount':
        sql += " ORDER BY discount_percentage DESC"
    else:  # relevance
        sql += " ORDER BY featured DESC, rating DESC, id DESC"

    products_list = db.execute(sql, params).fetchall()

    # Get distinct categories and brands for filter sidebar
    all_categories = db.execute("SELECT DISTINCT category FROM products ORDER BY category ASC").fetchall()
    all_brands = db.execute("SELECT DISTINCT brand FROM products ORDER BY brand ASC").fetchall()

    return render_template(
        'products.html',
        products=products_list,
        categories=[c['category'] for c in all_categories],
        brands=[b['brand'] for b in all_brands],
        selected_query=query,
        selected_category=category,
        selected_brand=brand,
        selected_min_price=min_price,
        selected_max_price=max_price,
        selected_min_rating=min_rating,
        selected_sort=sort,
        total_results=len(products_list)
    )


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    
    if not product:
        flash("Product not found.", "error")
        return render_template("404.html"), 404

    # Related products from same category
    related = db.execute(
        "SELECT * FROM products WHERE category = ? AND id != ? LIMIT 4",
        (product['category'], product_id)
    ).fetchall()

    return render_template('product.html', product=product, related_products=related)


@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    
    if not product:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Product not found.'}), 404
        flash("Product not found.", "error")
        return redirect(url_for('products'))

    try:
        qty_to_add = int(request.form.get('quantity', 1))
        if qty_to_add < 1:
            qty_to_add = 1
    except ValueError:
        qty_to_add = 1

    cart = session.get('cart', {})
    pid_str = str(product_id)
    current_qty = int(cart.get(pid_str, 0))
    new_qty = current_qty + qty_to_add

    if new_qty > product['stock']:
        msg = f"Cannot add more items. Only {product['stock']} unit(s) available in stock."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, "warning")
        return redirect(request.referrer or url_for('product_detail', product_id=product_id))

    cart[pid_str] = new_qty
    session['cart'] = cart
    session.modified = True

    msg = f"Added '{product['name']}' to your cart!"
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        total_count = sum(int(q) for q in cart.values())
        return jsonify({'success': True, 'message': msg, 'cart_count': total_count})

    flash(msg, "success")
    return redirect(request.referrer or url_for('cart'))


@app.route('/cart')
def cart():
    cart_data = get_cart_details()
    return render_template('cart.html', cart=cart_data)


@app.route('/update-cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = session.get('cart', {})
    pid_str = str(product_id)

    if pid_str in cart:
        try:
            new_qty = int(request.form.get('quantity', 1))
        except ValueError:
            new_qty = 1

        db = get_db()
        product = db.execute("SELECT stock, name FROM products WHERE id = ?", (product_id,)).fetchone()

        if new_qty <= 0:
            del cart[pid_str]
            flash(f"Removed '{product['name']}' from cart.", "info") if product else None
        elif product and new_qty > product['stock']:
            cart[pid_str] = product['stock']
            flash(f"Adjusted quantity to max available stock ({product['stock']}).", "warning")
        else:
            cart[pid_str] = new_qty
            flash("Cart updated.", "success")

        session['cart'] = cart
        session.modified = True

    return redirect(url_for('cart'))


@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    pid_str = str(product_id)
    if pid_str in cart:
        del cart[pid_str]
        session['cart'] = cart
        session.modified = True
        flash("Item removed from cart.", "info")
    return redirect(url_for('cart'))


@app.route('/clear-cart')
def clear_cart():
    session.pop('cart', None)
    flash("Cart cleared.", "info")
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_data = get_cart_details()
    
    if not cart_data['items']:
        flash("Your cart is empty. Please add items before checking out.", "warning")
        return redirect(url_for('products'))

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        postal_code = request.form.get('postal_code', '').strip()
        payment_method = request.form.get('payment_method', 'Cash on Delivery').strip()

        # Input Validation
        if not all([customer_name, email, phone, address, city, state, postal_code]):
            flash("Please fill in all required customer fields.", "error")
            return render_template('checkout.html', cart=cart_data)

        db = get_db()

        try:
            # Transactional Order Creation and Stock Verification
            db.execute("BEGIN TRANSACTION")

            # Re-check stock for all cart items
            for item in cart_data['items']:
                p_id = item['product']['id']
                req_qty = item['quantity']
                
                curr_p = db.execute("SELECT stock, name FROM products WHERE id = ?", (p_id,)).fetchone()
                if not curr_p or curr_p['stock'] < req_qty:
                    db.execute("ROLLBACK")
                    flash(f"Insufficient stock for product '{item['product']['name']}'. Available: {curr_p['stock'] if curr_p else 0}.", "error")
                    return redirect(url_for('cart'))

            # Insert Order Record
            cursor = db.execute("""
                INSERT INTO orders (
                    customer_name, email, phone, address, city, state, postal_code,
                    payment_method, total_amount, order_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Processing')
            """, (
                customer_name, email, phone, address, city, state, postal_code,
                payment_method, cart_data['grand_total']
            ))
            order_id = cursor.lastrowid

            # Insert Order Items & Deduct Stock
            for item in cart_data['items']:
                p_id = item['product']['id']
                req_qty = item['quantity']
                price = item['product']['price']
                subtotal = item['subtotal']

                db.execute("""
                    INSERT INTO order_items (order_id, product_id, product_name, quantity, price, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (order_id, p_id, item['product']['name'], req_qty, price, subtotal))

                db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (req_qty, p_id))

            db.commit()
            
            # Clear session cart after successful order
            session.pop('cart', None)
            flash("Order placed successfully!", "success")
            return redirect(url_for('order_success', order_id=order_id))

        except Exception as e:
            db.execute("ROLLBACK")
            app.logger.error(f"Order checkout failed: {str(e)}")
            flash("An error occurred while processing your order. Please try again.", "error")
            return render_template('checkout.html', cart=cart_data)

    return render_template('checkout.html', cart=cart_data)


@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    
    if not order:
        flash("Order not found.", "error")
        return render_template("404.html"), 404

    order_items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()

    return render_template('success.html', order=order, items=order_items)


# Custom Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
