import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

st.set_page_config(page_title="MSME Enterprise POS", page_icon="⚡", layout="wide")

# -----------------------------
# ENTERPRISE UI STYLING
# -----------------------------
def apply_enterprise_css():
    st.markdown("""
    <style>
    /* Soft App Background */
    .stApp { background-color: #f4f7f6; }
    
    /* Beautiful Metric Cards */
    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-left: 6px solid #2e66ff;
    }
    
    /* Gradient Primary Buttons */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #2e66ff 0%, #003cc7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: transform 0.2s;
    }
    .stButton>button[kind="primary"]:hover {
        transform: scale(1.02);
    }
    
    /* Card Containers */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------
# CORE HELPERS
# -----------------------------
def force_rerun():
    if hasattr(st, "rerun"): st.rerun()
    else: st.experimental_rerun()

def init_session_state():
    defaults = {
        "users": {
            "shanmukh": {"password": "owner123", "role": "Owner"},
            "manager": {"password": "manager123", "role": "Manager"},
            "staff": {"password": "staff123", "role": "Staff"}
        },
        "logged_in": False, "current_user": None, "inventory": [],
        "cart": [], "sales": [], "staff_list": [], "transfers": [], "returns": []
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def generate_id(): return str(uuid.uuid4())[:8]
def total_stock(): return sum(item["quantity"] for item in st.session_state.inventory)
def total_products(): return len(st.session_state.inventory)
def total_sales(): return sum(sale["total"] for sale in st.session_state.sales)

apply_enterprise_css()
init_session_state()

# -----------------------------
# LOGIN
# -----------------------------
def login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.title("⚡ Enterprise POS")
        st.caption("Sign in to your workspace")
        
        with st.container(border=True):
            username = st.text_input("Username", placeholder="e.g. shanmukh").strip().lower()
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            if st.button("Authenticate", type="primary", use_container_width=True):
                user = st.session_state.users.get(username)
                if user and user["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"username": username, "role": user["role"]}
                    st.toast("Welcome back!")
                    force_rerun()
                else:
                    st.error("Invalid credentials. Try again.")

# -----------------------------
# SIDEBAR
# -----------------------------
def sidebar():
    role = st.session_state.current_user["role"]
    username = st.session_state.current_user["username"].title()
    
    with st.sidebar:
        st.markdown(f"### 👋 Hi, {username}")
        st.caption(f"Role: {role}")
        st.divider()

        menu = {"📊 Dashboard": "Dashboard", "📦 Inventory": "Inventory"}
        if role in ["Owner", "Manager", "Staff"]:
            menu.update({"🛒 Point of Sale": "POS", "🚚 Transfers": "Transfers", "↩️ Returns": "Returns"})
        if role in ["Owner", "Manager"]:
            menu["👥 Staff": "Staff"]
        if role == "Owner":
            menu["📈 Analytics": "Analytics"]
        menu["🚪 Logout"] = "Logout"

        choice = st.radio("Navigation", list(menu.keys()), label_visibility="collapsed")
        return menu[choice]

# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard():
    st.title("📊 Overview")
    
    # Top Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Active Products", total_products())
    c2.metric("Total Units in Stock", total_stock())
    c3.metric("Gross Revenue", f"₹{total_sales():,.2f}")
    
    st.markdown("---")
    
    # Charts
    c_left, c_right = st.columns([2, 1])
    
    with c_left:
        st.subheader("Inventory Levels")
        if st.session_state.inventory:
            df = pd.DataFrame(st.session_state.inventory)
            st.bar_chart(df.set_index("name")["quantity"], color="#2e66ff")
        else:
            st.info("No data to display.")
            
    with c_right:
        st.subheader("Recent Activity")
        if st.session_state.sales:
            st.dataframe(pd.DataFrame(st.session_state.sales)[["date", "total"]].tail(5), use_container_width=True, hide_index=True)
        else:
            st.info("No recent sales.")

# -----------------------------
# INVENTORY
# -----------------------------
def inventory():
    st.title("📦 Inventory Control")
    
    # Hidden form to keep UI clean
    with st.expander("➕ Add New Product"):
        with st.form("add_product_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Product Name*")
            sku = c2.text_input("SKU / Barcode*")
            price = c1.number_input("Unit Price (₹)", min_value=0.0)
            qty = c2.number_input("Initial Quantity", min_value=0)
            
            if st.form_submit_button("Save Product", type="primary"):
                if name and sku:
                    st.session_state.inventory.append({
                        "id": generate_id(), "name": name, "sku": sku, "price": price, "quantity": int(qty)
                    })
                    st.toast(f"Added {name}!")
                    force_rerun()
                else:
                    st.error("Name and SKU are required.")

    # Inventory Table
    st.subheader("Current Stock")
    if st.session_state.inventory:
        df = pd.DataFrame(st.session_state.inventory)
        # Highlight low stock
        def highlight_low_stock(val):
            return 'color: red; font-weight: bold' if isinstance(val, int) and val < 5 else ''
        
        st.dataframe(df.style.map(highlight_low_stock, subset=['quantity']), use_container_width=True, hide_index=True)
        
        # Delete tool
        c1, c2 = st.columns([1, 4])
        del_id = c1.text_input("Product ID to Remove")
        if c1.button("🗑️ Delete", use_container_width=True):
            st.session_state.inventory = [p for p in st.session_state.inventory if p["id"] != del_id]
            st.toast("Product deleted.")
            force_rerun()
    else:
        st.info("Inventory is empty.")

# -----------------------------
# POINT OF SALE (GRID LAYOUT)
# -----------------------------
def pos():
    st.title("🛒 Register")
    
    if not st.session_state.inventory:
        st.warning("Add products to inventory first.")
        return

    col_products, col_cart = st.columns([2.2, 1])

    # Left Side: Product Grid
    with col_products:
        st.subheader("Tap to Add")
        grid_cols = st.columns(3)
        for index, product in enumerate(st.session_state.inventory):
            with grid_cols[index % 3]:
                with st.container(border=True):
                    st.markdown(f"**{product['name']}**")
                    st.caption(f"Stock: {product['quantity']} | SKU: {product['sku']}")
                    st.markdown(f"### ₹{product['price']:,.2f}")
                    
                    qty = st.number_input("Qty", min_value=1, max_value=max(product["quantity"], 1), key=f"q_{product['id']}", label_visibility="collapsed")
                    
                    if st.button("➕ Add", key=f"btn_{product['id']}", type="primary", use_container_width=True):
                        if product["quantity"] >= qty:
                            item = next((i for i in st.session_state.cart if i["id"] == product["id"]), None)
                            if item:
                                item["quantity"] += qty
                                item["subtotal"] = item["price"] * item["quantity"]
                            else:
                                st.session_state.cart.append({
                                    "id": product["id"], "name": product["name"], 
                                    "price": product["price"], "quantity": qty, 
                                    "subtotal": product["price"] * qty
                                })
                            force_rerun()
                        else:
                            st.error("Low stock!")

    # Right Side: Active Cart
    with col_cart:
        with st.container(border=True):
            st.subheader("🧾 Current Order")
            if not st.session_state.cart:
                st.info("Cart is empty.")
            else:
                for item in st.session_state.cart:
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"{item['quantity']}x **{item['name']}**")
                    c2.write(f"₹{item['subtotal']:,.2f}")
                
                st.divider()
                grand_total = sum(i["subtotal"] for i in st.session_state.cart)
                st.markdown(f"## Total: ₹{grand_total:,.2f}")
                
                cust_name = st.text_input("Customer Name (Optional)", placeholder="Walk-in")
                
                if st.button("💳 Checkout", type="primary", use_container_width=True):
                    sale = {
                        "sale_id": generate_id(), "customer": cust_name or "Walk-in", 
                        "items": len(st.session_state.cart), "total": grand_total, 
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    
                    inv_dict = {p["id"]: p for p in st.session_state.inventory}
                    for c_item in st.session_state.cart:
                        if c_item["id"] in inv_dict:
                            inv_dict[c_item["id"]]["quantity"] -= c_item["quantity"]

                    st.session_state.sales.append(sale)
                    st.session_state.cart.clear()
                    st.toast("✅ Payment Successful!")
                    st.balloons()
                    force_rerun()
                
                if st.button("🗑️ Clear Cart", use_container_width=True):
                    st.session_state.cart.clear()
                    force_rerun()

# -----------------------------
# TRANSFERS
# -----------------------------
def transfers():
    st.title("🚚 Transfers")
    with st.expander("Initiate Transfer"):
        if st.session_state.inventory:
            p_dict = {p["name"]: p["id"] for p in st.session_state.inventory}
            c1, c2 = st.columns(2)
            s_name = c1.selectbox("Product", list(p_dict.keys()))
            dest = c2.text_input("Destination")
            qty = c1.number_input("Qty", min_value=1)
            
            if st.button("Transfer", type="primary"):
                p = next((x for x in st.session_state.inventory if x["id"] == p_dict[s_name]), None)
                if p and p["quantity"] >= qty and dest:
                    p["quantity"] -= int(qty)
                    st.session_state.transfers.append({
                        "id": generate_id(), "product": s_name, "destination": dest, "qty": int(qty), "date": datetime.now().strftime("%Y-%m-%d")
                    })
                    st.toast("Transfer logged.")
                    force_rerun()
    
    st.subheader("Log")
    if st.session_state.transfers: st.dataframe(pd.DataFrame(st.session_state.transfers), use_container_width=True, hide_index=True)

# -----------------------------
# RETURNS
# -----------------------------
def returns():
    st.title("↩️ Returns")
    with st.expander("Process Return"):
        if st.session_state.inventory:
            p_dict = {p["name"]: p["id"] for p in st.session_state.inventory}
            s_name = st.selectbox("Product", list(p_dict.keys()))
            c1, c2 = st.columns(2)
            qty = c1.number_input("Qty", min_value=1)
            reason = c2.text_input("Reason")
            
            if st.button("Return to Stock", type="primary"):
                p = next((x for x in st.session_state.inventory if x["id"] == p_dict[s_name]), None)
                if p:
                    p["quantity"] += int(qty)
                    st.session_state.returns.append({
                        "id": generate_id(), "product": s_name, "qty": int(qty), "reason": reason, "date": datetime.now().strftime("%Y-%m-%d")
                    })
                    st.toast("Returned to inventory.")
                    force_rerun()
                    
    st.subheader("Log")
    if st.session_state.returns: st.dataframe(pd.DataFrame(st.session_state.returns), use_container_width=True, hide_index=True)

# -----------------------------
# STAFF
# -----------------------------
def staff():
    st.title("👥 Staff Directory")
    with st.expander("➕ Add Staff Member"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full Name")
        role = c2.selectbox("Role", ["Cashier", "Storekeeper", "Manager"])
        if st.button("Save", type="primary"):
            st.session_state.staff_list.append({"id": generate_id(), "name": name, "role": role})
            st.toast("Staff added.")
            force_rerun()
            
    if st.session_state.staff_list:
        st.dataframe(pd.DataFrame(st.session_state.staff_list), use_container_width=True, hide_index=True)

# -----------------------------
# ANALYTICS
# -----------------------------
def analytics():
    st.title("📈 Performance Analytics")
    
    if not st.session_state.sales:
        st.info("Not enough data to generate analytics yet. Make some sales!")
        return

    df_sales = pd.DataFrame(st.session_state.sales)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"₹{df_sales['total'].sum():,.2f}")
    c2.metric("Total Transactions", len(df_sales))
    c3.metric("Avg Order Value", f"₹{df_sales['total'].mean():,.2f}")
    
    st.markdown("---")
    st.subheader("Revenue Timeline")
    # Group by date
    timeline = df_sales.groupby('date')['total'].sum()
    st.line_chart(timeline, color="#00c853")

# -----------------------------
# APP ROUTING
# -----------------------------
if not st.session_state.logged_in:
    login()
else:
    page = sidebar()
    pages = {
        "Dashboard": dashboard, "Inventory": inventory, "POS": pos,
        "Transfers": transfers, "Returns": returns, "Staff": staff, "Analytics": analytics
    }
    
    if page in pages:
        pages[page]()
    elif page == "Logout":
        st.session_state.logged_in = False
        st.session_state.current_user = None
        force_rerun()
