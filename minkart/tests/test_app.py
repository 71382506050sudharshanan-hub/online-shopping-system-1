import os
import sqlite3
import pytest
from app import app, init_db, get_db

@pytest.fixture
def client(tmp_path):
    """Set up test client with a temporary SQLite database."""
    test_db_path = tmp_path / "test_shop.db"
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    # Override database path for testing
    import app as app_module
    app_module.DB_PATH = str(test_db_path)

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


def test_homepage(client):
    """Test homepage loads successfully with branding and sections."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"MINKART" in response.data
    assert b"Everything You Need" in response.data
    assert b"Shop by Category" in response.data


def test_products_catalog(client):
    """Test products catalog page loads with seed items."""
    response = client.get('/products')
    assert response.status_code == 200
    assert b"Product Catalog" in response.data
    assert b"Apple MacBook Air M2" in response.data


def test_search_by_name(client):
    """Test search functionality matching product names."""
    response = client.get('/products?q=MacBook')
    assert response.status_code == 200
    assert b"Apple MacBook Air M2" in response.data


def test_search_by_category(client):
    """Test filtering by category."""
    response = client.get('/products?category=Electronics')
    assert response.status_code == 200
    assert b"Electronics" in response.data


def test_search_no_results(client):
    """Test search with query matching zero items."""
    response = client.get('/products?q=NonExistentSuperItem12345')
    assert response.status_code == 200
    assert b"No Products Found" in response.data


def test_product_detail_success(client):
    """Test single product detail page for valid ID."""
    response = client.get('/product/1')
    assert response.status_code == 200
    assert b"Apple MacBook Air M2" in response.data
    assert b"Add to Shopping Cart" in response.data


def test_product_detail_404(client):
    """Test product detail for invalid product ID."""
    response = client.get('/product/999999')
    assert response.status_code == 404
    assert b"Page Not Found" in response.data


def test_cart_workflow(client):
    """Test adding items, updating quantity, and removing items from session cart."""
    # 1. Add item to cart
    res_add = client.post('/add-to-cart/1', data={'quantity': 2}, follow_redirects=True)
    assert res_add.status_code == 200
    assert b"Apple MacBook Air M2" in res_add.data

    # 2. View cart
    res_cart = client.get('/cart')
    assert res_cart.status_code == 200
    assert b"Apple MacBook Air M2" in res_cart.data
    assert "₹210942.00".encode('utf-8') in res_cart.data  # 105471.00 * 2

    # 3. Update quantity
    res_update = client.post('/update-cart/1', data={'quantity': 1}, follow_redirects=True)
    assert res_update.status_code == 200
    assert b"Cart updated." in res_update.data

    # 4. Remove item
    res_remove = client.get('/remove-from-cart/1', follow_redirects=True)
    assert res_remove.status_code == 200
    assert b"Item removed from cart." in res_remove.data

    # 5. Clear cart
    client.post('/add-to-cart/1', data={'quantity': 1})
    res_clear = client.get('/clear-cart', follow_redirects=True)
    assert res_clear.status_code == 200
    assert b"Your Cart is Empty" in res_clear.data


def test_checkout_empty_cart(client):
    """Test checkout redirect when cart is empty."""
    response = client.get('/checkout', follow_redirects=True)
    assert response.status_code == 200
    assert b"Your cart is empty" in response.data


def test_checkout_and_order_creation(client):
    """Test full checkout flow, order database entry, item insertion, and stock deduction."""
    # 1. Add product #1 to cart (Initial stock = 15)
    client.post('/add-to-cart/1', data={'quantity': 2})

    # 2. Perform checkout POST
    checkout_data = {
        'customer_name': 'Jane Doe',
        'email': 'jane.doe@example.com',
        'phone': '555-123-4567',
        'address': '742 Evergreen Terrace',
        'city': 'Springfield',
        'state': 'IL',
        'postal_code': '62701',
        'payment_method': 'Cash on Delivery'
    }

    res_checkout = client.post('/checkout', data=checkout_data, follow_redirects=True)
    assert res_checkout.status_code == 200
    assert b"Order Placed Successfully!" in res_checkout.data
    assert b"Jane Doe" in res_checkout.data

    # 3. Verify Database Records
    with app.app_context():
        db = get_db()
        
        # Check order record
        order = db.execute("SELECT * FROM orders WHERE email = 'jane.doe@example.com'").fetchone()
        assert order is not None
        assert order['customer_name'] == 'Jane Doe'
        assert order['payment_method'] == 'Cash on Delivery'

        # Check order items
        order_item = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order['id'],)).fetchone()
        assert order_item is not None
        assert order_item['product_id'] == 1
        assert order_item['quantity'] == 2

        # Check stock deduction
        product = db.execute("SELECT stock FROM products WHERE id = 1").fetchone()
        assert product['stock'] == 13
