import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

st.set_page_config(page_title="MSME POS", page_icon="🛍️", layout="wide")

# -----------------------------
# ADVANCED SAAS CSS INJECTION
# -----------------------------
def apply_pro_css():
    st.markdown("""
    <style>
    /* 1. Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 2. Main Background & Typography */
    .stApp {
        background-color: #F3F4F6;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* 3. Dark Mode Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111827;
        padding-top: 2rem;
    }
    [data-testid="stSidebar"] * {
        color: #E5E7EB !important;
    }
    /* Sidebar Navigation Radio Buttons */
    div[role="radiogroup"] > label {
        padding: 10px 15px;
        border-radius: 8px;
        transition: background 0.2s ease;
    }
    div[role="radiogroup"] > label:hover {
        background-color: #374151;
    }

    /* 4. Floating Metric Cards (SaaS Style) */
    [data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 20px 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-top: 4px solid #4F46E5; /* Indigo Accent */
        transition: transform 0.2s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
    }
    [data-testid="stMetricValue"] {
        color: #111827;
        font-weight: 700;
        font-size: 2rem;
    }

    /* 5. Gradient Primary Buttons */
    button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        border: none;
        box-shadow: 0 4px 6px rgba(79, 70, 229, 0.3);
        border-radius: 8px;
        color: white !important;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(79, 70, 229, 0.4);
    }

    /* 6. Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #FFFFFF;
        padding: 10px 10px 0 10px;
        border-radius: 12px 12px 0 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-bottom: 15px;
        font-weight: 600;
        color: #6B7280;
    }
    .stTabs [aria-selected="true"] {
        color: #4F46E5 !important;
        border-bottom-color: #4F46E5 !important;
    }

    /* 7. Inputs & Dataframes */
    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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

apply_pro_css()
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
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No data available to display.")

# -----------------------------
# LOGIN
# -----------------------------
def login():
    st.markdown("<h1 style='text-align: center; color: #111827; padding-top: 50px;'>Dhusetty Enterprise POS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; margin-bottom: 40px;'>Secure Access Portal</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container():
            st.info("💡 **Admin:** `shanmukh` | **Pass:** `owner123`")
            username = st.text_input("System Username").strip().lower()
            password = st.text_input("Password", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Authenticate System", type="primary", use_container_width=True):
                user = st.session_state.users.get(username)
                if user and user["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"username": username, "role": user["role"]}
                    st.toast("✅ Authentication successful")
                    force_rerun()
                else:
                    st.error("❌ Invalid credentials. Access denied.")

# -----------------------------
# SIDEBAR
# -----------------------------
def sidebar():
    st.sidebar.markdown("## Shanmukh Dhusetty \n**Enterprise POS**")
    role = st.session_state.current_user["role"]
    st.sidebar.caption(f"Active User: **{st.session_state.current_user['username'].title()}** ({role})")
    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    menu = {"📊 Overview Dashboard": "Dashboard", "📦 Inventory Master": "Inventory"}

    if role in ["Owner", "Manager", "Staff"]:
        menu.update({
            "🛒 Point of Sale": "POS", 
            "🚚 Stock Transfers": "Transfers", 
            "↩️ Return Processing": "Returns", 
            "🗑️ Write-Off Protocol": "Write-Off", 
            "🔍 Barcode Scanner": "Barcode"
        })

    if role in ["Owner", "Manager"]:
        menu["👥 Staff Roster"] = "Staff"

    if role == "Owner":
        menu["📈 Financial Analytics"] = "Analytics"

    menu["🚪 Terminate Session"] = "Logout"

    choice_label = st.sidebar.radio("Navigation", list(menu.keys()), label_visibility="collapsed")
    return menu[choice_label]

# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard():
    st.markdown("<h2 style='color: #111827;'>📊 Executive Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total SKU Count", total_products())
    col2.metric("Active Stock Units", total_stock())
    col3.metric("Gross Revenue", f"₹{total_sales():,.2f}")

    st.markdown("<br><br><h4 style='color: #374151;'>⏱️ Recent Transaction Log</h4>", unsafe_allow_html=True)
    render_table(st.session_state.sales)

# -----------------------------
# INVENTORY
# -----------------------------
def inventory():
    st.markdown("<h2 style='color: #111827;'>📦 Inventory Master</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Register New SKU", "📋 Active Database"])

    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        name = col1.text_input("Item Designation (Name)")
        sku = col2.text_input("Barcode / SKU")
        price = col1.number_input("Retail Price (₹)", min_value=0.0)
        quantity = col2.number_input("Initial Intake Quantity", min_value=0)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Publish to Inventory", type="primary"):
            if name and sku:
                st.session_state.inventory.append({
                    "id": generate_id(), "name": name, "sku": sku, "price": price, "quantity": int(quantity)
                })
                st.toast(f"✅ Registered: {name}")
            else:
                st.error("⚠️ Designation and SKU are mandatory fields.")

    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        render_table(st.session_state.inventory)

        st.markdown("<br><hr><br>", unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        delete_id = col1.text_input("Target ID for Deletion")
        if col2.button("🗑️ Execute Deletion", use_container_width=True):
            initial_len = len(st.session_state.inventory)
            st.session_state.inventory = [p for p in st.session_state.inventory if p["id"] != delete_id]
            if len(st.session_state.inventory) < initial_len:
                st.toast("🗑️ Record purged.")
                force_rerun()
            else:
                st.error("❌ Invalid ID target.")

# -----------------------------
# POS SYSTEM
# -----------------------------
def pos():
    st.markdown("<h2 style='color: #111827;'>🛒 Terminal Operations</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.inventory:
        st.warning("⚠️ Terminal locked: Zero inventory registered.")
        return

    tab1, tab2, tab3 = st.tabs(["🛍️ Scanner/Browse", "🛒 Active Cart", "📜 Ledger"])

    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        for product in st.session_state.inventory:
            with st.container():
                col1, col2, col3, col4, col5 = st
