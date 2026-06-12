import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

st.set_page_config(page_title="MSME Inventory & POS", layout="wide")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
def init_session_state():
    defaults = {
        "users": {
            "owner": {"password": "owner123", "role": "Owner"},
            "manager": {"password": "manager123", "role": "Manager"},
            "staff": {"password": "staff123", "role": "Staff"}
        },
        "logged_in": False,
        "current_user": None,
        "inventory": [],
        "cart": [],
        "sales": [],
        "staff_list": [],
        "transfers": [],
        "returns": []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# -----------------------------
# HELPERS
# -----------------------------
def generate_id():
    return str(uuid.uuid4())[:8]

def total_stock():
    return sum(item["quantity"] for item in st.session_state.inventory)

def total_products():
    return len(st.session_state.inventory)

def total_sales():
    return sum(sale["total"] for sale in st.session_state.sales)

# -----------------------------
# LOGIN
# -----------------------------
def login():
    st.title("MSME Inventory & POS System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = st.session_state.users.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = {
                "username": username,
                "role": user["role"]
            }
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")

# -----------------------------
# SIDEBAR
# -----------------------------
def sidebar():
    st.sidebar.title("Navigation")
    role = st.session_state.current_user["role"]

    menu = ["Dashboard", "Inventory"]

    # Access levels based on role
    if role in ["Owner", "Manager", "Staff"]:
        menu.extend(["POS", "Transfers", "Returns", "Write-Off", "Barcode"])

    if role in ["Owner", "Manager"]:
        menu.append("Staff")

    if role == "Owner":
        menu.append("Analytics")

    menu.append("Logout")

    return st.sidebar.radio("Select", menu)

# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard():
    st.title("Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("Products", total_products())
    col2.metric("Stock", total_stock())
    col3.metric("Revenue", f"₹{total_sales()}")

    st.subheader("Recent Sales")
    if st.session_state.sales:
        st.dataframe(pd.DataFrame(st.session_state.sales))
    else:
        st.info("No sales yet")

# -----------------------------
# INVENTORY
# -----------------------------
def inventory():
    st.title("Inventory Management")

    tab1, tab2 = st.tabs(["Add Product", "View Products"])

    with tab1:
        name = st.text_input("Product Name")
        sku = st.text_input("SKU")
        price = st.number_input("Price", min_value=0.0)
        quantity = st.number_input("Quantity", min_value=0)

        if st.button("Add Product"):
            st.session_state.inventory.append({
                "id": generate_id(),
                "name": name,
                "sku": sku,
                "price": price,
                "quantity": quantity
            })
            st.success("Product added")

    with tab2:
        if st.session_state.inventory:
            st.dataframe(pd.DataFrame(st.session_state.inventory))

            delete_id = st.text_input("Enter Product ID to Delete")
            if st.button("Delete Product"):
                initial_len = len(st.session_state.inventory)
                st.session_state.inventory = [p for p in st.session_state.inventory if p["id"] != delete_id]
                
                if len(st.session_state.inventory) < initial_len:
                    st.success("Product deleted")
                    st.rerun()
                else:
                    st.error("Product ID not found")
        else:
            st.info("No products available")

# -----------------------------
# POS SYSTEM
# -----------------------------
def pos():
    st.title("Point of Sale")

    if not st.session_state.inventory:
        st.warning("No inventory available")
        return

    tab1, tab2, tab3 = st.tabs(["Browse Products", "Cart", "Sales History"])

    # --- TAB 1: BROWSE ---
    with tab1:
        st.subheader("Available Products")
        for product in st.session_state.inventory:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                col1.write(product["name"])
                col2.write(f"₹{product['price']}")
                col3.write(f"Stock: {product['quantity']}")

                qty = col4.number_input(
                    f"Qty {product['id']}",
                    min_value=1,
                    max_value=max(product["quantity"], 1),
                    key=f"qty_{product['id']}"
                )

                if st.button("Add to Cart", key=f"add_{product['id']}"):
                    if product["quantity"] >= qty:
                        # Find existing item cleanly
                        existing_item = next((item for item in st.session_state.cart if item["id"] == product["id"]), None)
                        
                        if existing_item:
                            existing_item["quantity"] += qty
                            existing_item["subtotal"] = existing_item["price"] * existing_item["quantity"]
                        else:
                            st.session_state.cart.append({
                                "id": product["id"],
                                "name": product["name"],
                                "price": product["price"],
                                "quantity": qty,
                                "subtotal": product["price"] * qty
                            })
                        st.success("Added to cart")
                    else:
                        st.error("Insufficient stock")

    # --- TAB 2: CART ---
    with tab2:
        st.subheader("Current Cart")
        if st.session_state.cart:
            st.dataframe(pd.DataFrame(st.session_state.cart))

            grand_total = sum(item["subtotal"] for item in st.session_state.cart)
            st.metric("Grand Total", f"₹{grand_total}")

            remove_id = st.text_input("Enter Product ID to Remove")
            if st.button("Remove Item"):
                st.session_state.cart = [item for item in st.session_state.cart if item["id"] != remove_id]
                st.success("Item removed")
                st.rerun()

            customer_name = st.text_input("Customer Name")

            if st.button("Checkout"):
                if not customer_name:
                    st.error("Customer name required")
                else:
                    sale_id = generate_id()
                    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    sale = {
                        "sale_id": sale_id,
                        "customer": customer_name,
                        "items": len(st.session_state.cart),
                        "total": grand_total,
                        "date": sale_date
                    }

                    # Optimize stock deduction (O(1) lookups instead of nested O(N^2) loops)
                    inventory_dict = {p["id"]: p for p in st.session_state.inventory}
                    for cart_item in st.session_state.cart:
                        if cart_item["id"] in inventory_dict:
                            inventory_dict[cart_item["id"]]["quantity"] -= cart_item["quantity"]

                    st.session_state.sales.append(sale)
                    st.success("Checkout complete")

                    st.subheader("Invoice")
                    st.write(f"Invoice ID: {sale_id}\nCustomer: {customer_name}\nDate: {sale_date}")
                    st.dataframe(pd.DataFrame(st.session_state.cart))
                    st.write(f"**Total Amount: ₹{grand_total}**")
                    
                    st.balloons()
                    st.session_state.cart.clear()
        else:
            st.info("Cart is empty")

    # --- TAB 3: SALES HISTORY ---
    with tab3:
        st.subheader("Sales History")
        if st.session_state.sales:
            st.dataframe(pd.DataFrame(st.session_state.sales))
        else:
            st.info("No sales found")

# -----------------------------
# TRANSFERS
# -----------------------------
def transfers():
    st.title("Warehouse Transfers")
    if not st.session_state.inventory:
        st.warning("No products available")
        return

    product_ids = [p["id"] for p in st.session_state.inventory]
    selected_id = st.selectbox("Select Product", product_ids)
    destination = st.text_input("Destination Warehouse")
    qty = st.number_input("Transfer Quantity", min_value=1)

    if st.button("Transfer Stock"):
        # Optimize finding the product
        product = next((p for p in st.session_state.inventory if p["id"] == selected_id), None)
        
        if product and product["quantity"] >= qty:
            product["quantity"] -= qty
            st.session_state.transfers.append({
                "transfer_id": generate_id(),
                "product_id": selected_id,
                "destination": destination,
                "quantity": qty,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success("Transfer completed")
        else:
            st.error("Not enough stock")

    if st.session_state.transfers:
        st.subheader("Transfer History")
        st.dataframe(pd.DataFrame(st.session_state.transfers))

# -----------------------------
# RETURNS
# -----------------------------
def returns():
    st.title("Returns Management")
    product_ids = [p["id"] for p in st.session_state.inventory]

    if not product_ids:
        st.warning("No products found")
        return

    selected_id = st.selectbox("Return Product", product_ids)
    qty = st.number_input("Return Quantity", min_value=1)
    reason = st.text_input("Reason")

    if st.button("Process Return"):
        product = next((p for p in st.session_state.inventory if p["id"] == selected_id), None)
        
        if product:
            product["quantity"] += qty
            st.session_state.returns.append({
                "return_id": generate_id(),
                "product_id": selected_id,
                "quantity": qty,
                "reason": reason,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.success("Return processed")

    if st.session_state.returns:
        st.subheader("Return History")
        st.dataframe(pd.DataFrame(st.session_state.returns))

# -----------------------------
# WRITE OFFS
# -----------------------------
def write_off():
    st.title("Write-Off Management")
    product_ids = [p["id"] for p in st.session_state.inventory]

    if not product_ids:
        st.warning("No products found")
        return

    selected_id = st.selectbox("Select Product for Write-Off", product_ids)
    qty = st.number_input("Damaged Quantity", min_value=1)
    reason = st.text_input("Damage Reason")

    if st.button("Write Off Stock"):
        product = next((p for p in st.session_state.inventory if p["id"] == selected_id), None)
        
        if product:
            if product["quantity"] >= qty:
                product["quantity"] -= qty
                st.success("Stock written off")
            else:
                st.error("Not enough stock")

# -----------------------------
# BARCODE LOOKUP
# -----------------------------
def barcode_lookup():
    st.title("Barcode Lookup")
    sku = st.text_input("Enter Barcode / SKU")

    if sku:
        # Optimize search
        product = next((p for p in st.session_state.inventory if p["sku"] == sku), None)
        if product:
            st.success("Product Found")
            st.json(product)
        else:
            st.error("Product not found")

# -----------------------------
# STAFF
# -----------------------------
def staff():
    st.title("Staff Management")
    name = st.text_input("Staff Name")
    role = st.selectbox("Role", ["Cashier", "Storekeeper"])

    if st.button("Add Staff"):
        st.session_state.staff_list.append({
            "id": generate_id(),
            "name": name,
            "role": role
        })
        st.success("Staff added")

    if st.session_state.staff_list:
        st.dataframe(pd.DataFrame(st.session_state.staff_list))

# -----------------------------
# ANALYTICS
# -----------------------------
def analytics():
    st.title("Owner Analytics")

    revenue = total_sales()
    stock_value = sum(item["price"] * item["quantity"] for item in st.session_state.inventory)
    total_items_sold = sum(sale["items"] for sale in st.session_state.sales)
    estimated_profit = revenue * 0.25

    col1, col2 = st.columns(2)
    col1.metric("Revenue", f"₹{revenue}")
    col2.metric("Inventory Value", f"₹{stock_value}")

    col3, col4 = st.columns(2)
    col3.metric("Items Sold", total_items_sold)
    col4.metric("Estimated Profit", f"₹{estimated_profit}")

    st.subheader("Inventory Snapshot")
    if st.session_state.inventory:
        st.dataframe(pd.DataFrame(st.session_state.inventory))

# -----------------------------
# MAIN APP ROUTING
# -----------------------------
if not st.session_state.logged_in:
    login()
else:
    page = sidebar()

    # Routing mapping
    pages = {
        "Dashboard": dashboard,
        "Inventory": inventory,
        "POS": pos,
        "Transfers": transfers,
        "Returns": returns,
        "Write-Off": write_off,
        "Barcode": barcode_lookup,
        "Staff": staff,
        "Analytics": analytics
    }

    if page in pages:
        pages[page]()
    elif page == "Logout":
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.success("Logged out")
        st.rerun()
