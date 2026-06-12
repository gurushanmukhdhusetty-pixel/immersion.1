import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

st.set_page_config(page_title="MSME POS", page_icon="🛍️", layout="wide")

# -----------------------------
# CUSTOM CSS FOR UI POLISH
# -----------------------------
def apply_custom_css():
    st.markdown("""
    <style>
    /* Metric Cards Styling */
    [data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.05);
        border: 1px solid rgba(28, 131, 225, 0.1);
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    /* Button Hover Effects */
    .stButton>button {
        border-radius: 6px;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
    }
    /* Dataframe container padding */
    [data-testid="stDataFrame"] {
        margin-top: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# COMPATIBILITY HELPER
# -----------------------------
def force_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# -----------------------------
# SESSION STATE INIT
# -----------------------------
def init_session_state():
    defaults = {
        "users": {
            "shanmukh": {"password": "owner123", "role": "Owner"},
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

apply_custom_css()
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

def render_table(data):
    """Helper to render clean, full-width tables without index"""
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No data available to display.")

# -----------------------------
# LOGIN
# -----------------------------
def login():
    st.title("🛍️ MSME Inventory & POS")
    st.caption("Welcome back! Please log in to continue.")
    
    with st.container():
        st.info("💡 **Default Owner Login** -> Username: `shanmukh` | Password: `owner123`")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Username").strip().lower()
            password = st.text_input("Password", type="password")
            
            if st.button("Secure Login", use_container_width=True):
                user = st.session_state.users.get(username)
                if user and user["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"username": username, "role": user["role"]}
                    st.toast("✅ Login successful!")
                    force_rerun()
                else:
                    st.error("❌ Invalid username or password")

# -----------------------------
# SIDEBAR
# -----------------------------
def sidebar():
    st.sidebar.title("🧭 Navigation")
    role = st.session_state.current_user["role"]
    st.sidebar.caption(f"Logged in as: **{st.session_state.current_user['username'].title()}** ({role})")
    st.sidebar.divider()

    menu = {"📊 Dashboard": "Dashboard", "📦 Inventory": "Inventory"}

    if role in ["Owner", "Manager", "Staff"]:
        menu.update({
            "🛒 Point of Sale": "POS", 
            "🚚 Transfers": "Transfers", 
            "↩️ Returns": "Returns", 
            "🗑️ Write-Off": "Write-Off", 
            "🔍 Barcode Lookup": "Barcode"
        })

    if role in ["Owner", "Manager"]:
        menu["👥 Staff Management"] = "Staff"

    if role == "Owner":
        menu["📈 Analytics"] = "Analytics"

    menu["🚪 Logout"] = "Logout"

    choice_label = st.sidebar.radio("Go to", list(menu.keys()), label_visibility="collapsed")
    return menu[choice_label]

# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard():
    st.title("📊 Business Dashboard")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total Products", total_products())
    col2.metric("📋 Total Stock Units", total_stock())
    col3.metric("💰 Total Revenue", f"₹{total_sales():,.2f}")

    st.write("---")
    st.subheader("⏱️ Recent Sales Activity")
    render_table(st.session_state.sales)

# -----------------------------
# INVENTORY
# -----------------------------
def inventory():
    st.title("📦 Inventory Management")
    st.divider()

    tab1, tab2 = st.tabs(["➕ Add New Product", "📋 View & Edit Inventory"])

    with tab1:
        col1, col2 = st.columns(2)
        name = col1.text_input("Product Name")
        sku = col2.text_input("SKU / Barcode")
        price = col1.number_input("Unit Price (₹)", min_value=0.0)
        quantity = col2.number_input("Initial Quantity", min_value=0)

        if st.button("Add to Inventory", type="primary"):
            if name and sku:
                st.session_state.inventory.append({
                    "id": generate_id(),
                    "name": name,
                    "sku": sku,
                    "price": price,
                    "quantity": int(quantity)
                })
                st.toast(f"✅ '{name}' added to inventory!")
            else:
                st.error("⚠️ Please enter a valid Name and SKU.")

    with tab2:
        render_table(st.session_state.inventory)

        st.divider()
        col1, col2 = st.columns([3, 1])
        delete_id = col1.text_input("Enter Product ID to Delete")
        if col2.button("🗑️ Delete Product", use_container_width=True):
            initial_len = len(st.session_state.inventory)
            st.session_state.inventory = [p for p in st.session_state.inventory if p["id"] != delete_id]
            if len(st.session_state.inventory) < initial_len:
                st.toast("🗑️ Product removed permanently.")
                force_rerun()
            else:
                st.error("❌ Product ID not found.")

# -----------------------------
# POS SYSTEM
# -----------------------------
def pos():
    st.title("🛒 Point of Sale")
    st.divider()

    if not st.session_state.inventory:
        st.warning("⚠️ No inventory available. Please add products first.")
        return

    tab1, tab2, tab3 = st.tabs(["🛍️ Browse & Add", "🛒 Current Cart", "📜 Sales History"])

    with tab1:
        for product in st.session_state.inventory:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                col1.write(f"**{product['name']}**")
                col2.write(f"₹{product['price']:,.2f}")
                col3.write(f"📦 Stock: {product['quantity']}")

                qty = col4.number_input("Qty", min_value=1, max_value=max(product["quantity"], 1), key=f"qty_{product['id']}", label_visibility="collapsed")

                if col5.button("➕ Add", key=f"add_{product['id']}", use_container_width=True):
                    if product["quantity"] >= qty:
                        existing_item = next((item for item in st.session_state.cart if item["id"] == product["id"]), None)
                        if existing_item:
                            existing_item["quantity"] += qty
                            existing_item["subtotal"] = existing_item["price"] * existing_item["quantity"]
                        else:
                            st.session_state.cart.append({
                                "id": product["id"], "name": product["name"], 
                                "price": product["price"], "quantity": qty, 
                                "subtotal": product["price"] * qty
                            })
                        st.toast(f"🛒 Added {qty}x {product['name']}")
                    else:
                        st.error("❌ Insufficient stock")
            st.divider()

    with tab2:
        if st.session_state.cart:
            render_table(st.session_state.cart)
            grand_total = sum(item["subtotal"] for item in st.session_state.cart)
            
            col1, col2 = st.columns([2, 1])
            col2.metric("Grand Total", f"₹{grand_total:,.2f}")

            st.write("---")
            st.subheader("Checkout Details")
            c1, c2 = st.columns(2)
            customer_name = c1.text_input("Customer Name")
            remove_id = c2.text_input("Remove Item (Enter ID)")
            
            if remove_id and st.button("🗑️ Remove from Cart"):
                st.session_state.cart = [item for item in st.session_state.cart if item["id"] != remove_id]
                st.toast("Item removed.")
                force_rerun()

            if st.button("💳 Process Payment & Checkout", type="primary", use_container_width=True):
                if not customer_name:
                    st.error("⚠️ Customer name required for checkout.")
                else:
                    sale_id = generate_id()
                    sale_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    sale = {"sale_id": sale_id, "customer": customer_name, "items": len(st.session_state.cart), "total": grand_total, "date": sale_date}
                    
                    inventory_dict = {p["id"]: p for p in st.session_state.inventory}
                    for cart_item in st.session_state.cart:
                        if cart_item["id"] in inventory_dict:
                            inventory_dict[cart_item["id"]]["quantity"] -= cart_item["quantity"]

                    st.session_state.sales.append(sale)
                    st.success(f"🎉 Payment successful! Invoice ID: {sale_id}")
                    st.balloons()
                    st.session_state.cart.clear()
        else:
            st.info("🛒 Your cart is currently empty.")

    with tab3:
        render_table(st.session_state.sales)

# -----------------------------
# TRANSFERS
# -----------------------------
def transfers():
    st.title("🚚 Warehouse Transfers")
    st.divider()

    if not st.session_state.inventory:
        st.warning("⚠️ No products available")
        return

    col1, col2 = st.columns(2)
    product_dict = {p["name"]: p["id"] for p in st.session_state.inventory}
    selected_name = col1.selectbox("Select Product", list(product_dict.keys()))
    selected_id = product_dict[selected_name]
    
    destination = col2.text_input("Destination Warehouse")
    qty = col1.number_input("Transfer Quantity", min_value=1)

    if st.button("🚚 Initiate Transfer", type="primary"):
        if not destination:
            st.error("Please enter a destination.")
        else:
            product = next((p for p in st.session_state.inventory if p["id"] == selected_id), None)
            if product and product["quantity"] >= qty:
                product["quantity"] -= int(qty)
                st.session_state.transfers.append({
                    "id": generate_id(), "product": selected_name, "destination": destination, "qty": int(qty), "date": datetime.now().strftime("%Y-%m-%d")
                })
                st.toast("✅ Transfer successfully logged.")
            else:
                st.error("❌ Not enough stock for this transfer.")

    st.write("---")
    st.subheader("Recent Transfers")
    render_table(st.session_state.transfers)

# -----------------------------
# RETURNS
# -----------------------------
def returns():
    st.title("↩️ Returns Management")
    st.divider()

    if not st.session_state.inventory:
        st.warning("⚠️ No products available")
        return

    col1, col2 = st.columns(2)
    product_dict = {p["name"]: p["id"] for p in st.session_state.inventory}
    selected_name = col1.selectbox("Product Returned", list(product_dict.keys()))
    selected_id = product_dict[selected_name]
    
    qty = col2.number_input("Quantity Returned", min_value=1)
    reason = st.text_input("Reason for Return")

    if st.button("Process Return", type="primary"):
        product = next((p for p in st.session_state.inventory if p["id"] == selected_id), None)
        if product:
            product["quantity"] += int(qty)
            st.session_state.returns.append({
                "id": generate_id(), "product": selected_name, "qty": int(qty), "reason": reason, "date": datetime.now().strftime("%Y-%m-%d")
            })
            st.toast("✅ Inventory updated with returned stock.")

    st.write("---")
    st.subheader("Return Logs")
    render_table(st.session_state.returns)

# -----------------------------
# WRITE OFFS
# -----------------------------
def write_off():
    st.title("🗑️ Stock Write-Off")
    st.caption("Log damaged or expired stock to deduct from inventory safely.")
    st.divider()

    if not st.session_state.inventory:
        st.warning("⚠️ No products available")
        return

    col1, col2 = st.columns(2)
    product_dict = {p["name"]: p["id"] for p in st.session_state.inventory}
    selected_name = col1.selectbox("Select Product to Write-Off", list(product_dict.keys()))
    selected_id = product_dict[selected_name]
    
    qty = col2.number_input("Quantity Damaged/Lost", min_value=1)
    reason = st.text_input("Reason")

    if st.button("Confirm Write-Off", type="primary"):
        product = next((p for p in st.session_state.inventory if p["id"] == selected_id), None)
        if product and product["quantity"] >= qty:
            product["quantity"] -= int(qty)
            st.toast("🗑️ Stock successfully written off.")
        else:
            st.error("❌ Cannot write off more stock than you currently hold.")

# -----------------------------
# BARCODE LOOKUP
# -----------------------------
def barcode_lookup():
    st.title("🔍 Quick Barcode Lookup")
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    sku = col2.text_input("📷 Scan or Type SKU / Barcode").strip()

    if sku:
        product = next((p for p in st.session_state.inventory if str(p["sku"]).lower() == sku.lower()), None)
        if product:
            col2.success(f"✅ Found: **{product['name']}**")
            col2.json(product)
        else:
            col2.error("❌ Product not found in database.")

# -----------------------------
# STAFF
# -----------------------------
def staff():
    st.title("👥 Staff Management")
    st.divider()

    col1, col2 = st.columns(2)
    name = col1.text_input("Staff Full Name")
    role = col2.selectbox("System Role", ["Cashier", "Storekeeper", "Manager"])

    if st.button("➕ Add Team Member", type="primary"):
        if name:
            st.session_state.staff_list.append({"id": generate_id(), "name": name, "role": role})
            st.toast("✅ Staff member added.")
        else:
            st.error("⚠️ Please enter a name.")

    st.write("---")
    render_table(st.session_state.staff_list)

# -----------------------------
# ANALYTICS
# -----------------------------
def analytics():
    st.title("📈 Owner Analytics & Insights")
    st.divider()

    revenue = total_sales()
    stock_value = sum(item["price"] * item["quantity"] for item in st.session_state.inventory)
    total_items_sold = sum(sale["items"] for sale in st.session_state.sales)
    estimated_profit = revenue * 0.25 # Assuming 25% margin

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gross Revenue", f"₹{revenue:,.2f}")
    col2.metric("Total Items Sold", total_items_sold)
    col3.metric("Est. Profit (25%)", f"₹{estimated_profit:,.2f}")
    col4.metric("Capital in Inventory", f"₹{stock_value:,.2f}")

    st.write("---")
    st.subheader("📦 Current Inventory Valuation Snapshot")
    render_table(st.session_state.inventory)

# -----------------------------
# MAIN APP ROUTING
# -----------------------------
if not st.session_state.logged_in:
    login()
else:
    page = sidebar()

    pages = {
        "Dashboard": dashboard, "Inventory": inventory, "POS": pos,
        "Transfers": transfers, "Returns": returns, "Write-Off": write_off,
        "Barcode": barcode_lookup, "Staff": staff, "Analytics": analytics
    }

    if page in pages:
        pages[page]()
    elif page == "Logout":
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.toast("👋 Successfully logged out.")
        force_rerun()
