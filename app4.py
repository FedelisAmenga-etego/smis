# stores_dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import os

# --------------------------------------------------
# PAGE CONFIG (MUST BE FIRST)
# --------------------------------------------------
st.set_page_config(
    page_title="NHRC Stores Management System",
    page_icon="🏪",
    layout="wide"
)

# --------------------------------------------------
# FILE PATHS
# --------------------------------------------------
USERS_FILE = "users.csv"
INVENTORY_FILE = "inventory.csv"
RECEIPTS_FILE = "receipts.csv"
ISSUES_FILE = "issues.csv"

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_csv(path, columns):
    if path not in st.session_state:
        if os.path.exists(path):
            st.session_state[path] = pd.read_csv(path)
        else:
            st.session_state[path] = pd.DataFrame(columns=columns)
    return st.session_state[path]

def save_csv(path):
    st.session_state[path].to_csv(path, index=False)

# --------------------------------------------------
# AUTH SETUP
# --------------------------------------------------
if not os.path.exists(USERS_FILE):
    pd.DataFrame([{
        "username": "admin",
        "password": hash_password("NHRC@26"),
        "full_name": "System Administrator",
        "role": "admin"
    }]).to_csv(USERS_FILE, index=False)

def authenticate(username, password):
    users = pd.read_csv(USERS_FILE)
    u = users[users.username == username]
    if not u.empty and u.iloc[0].password == hash_password(password):
        return u.iloc[0].to_dict()
    return None

# --------------------------------------------------
# SESSION INIT
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
if not st.session_state.logged_in:
    st.title("🔐 NHRC Stores Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("Login")

        if login:
            user = authenticate(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid username or password")

    st.stop()

user = st.session_state.user

# --------------------------------------------------
# LOAD DATA (ONCE)
# --------------------------------------------------
inventory = load_csv(
    INVENTORY_FILE,
    ["item_id", "item_name", "category", "quantity", "unit", "reorder_level"]
)

receipts = load_csv(
    RECEIPTS_FILE,
    ["date", "item_id", "item_name", "quantity", "unit_cost", "total_value", "received_by"]
)

issues = load_csv(
    ISSUES_FILE,
    ["date", "item_id", "item_name", "quantity", "department", "issued_by"]
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown(f"### 👤 {user['full_name']}")
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------
tab = st.radio(
    "Navigation",
    ["Dashboard", "Inventory", "Stock In", "Stock Out", "Reports"],
    horizontal=True
)

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if tab == "Dashboard":
    st.header("📊 Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Items", len(inventory))
    col2.metric(
        "Total Units",
        int(inventory.quantity.astype(int).sum()) if not inventory.empty else 0
    )
    col3.metric("Low Stock Items",
        len(inventory[inventory.quantity.astype(int) <= inventory.reorder_level.astype(int)])
        if not inventory.empty else 0
    )

# --------------------------------------------------
# INVENTORY
# --------------------------------------------------
elif tab == "Inventory":
    st.header("📦 Inventory Management")

    with st.form("add_item"):
        st.subheader("➕ Add Item")
        name = st.text_input("Item Name")
        category = st.text_input("Category")
        qty = st.number_input("Quantity", min_value=0, step=1)
        unit = st.text_input("Unit")
        reorder = st.number_input("Reorder Level", min_value=1, step=1)

        if st.form_submit_button("Add Item"):
            inventory.loc[len(inventory)] = [
                f"STR-{len(inventory)+1}",
                name,
                category,
                int(qty),
                unit,
                int(reorder)
            ]
            save_csv(INVENTORY_FILE)
            st.success("Item added successfully")

    st.subheader("📋 Current Inventory")
    st.dataframe(inventory, use_container_width=True)

# --------------------------------------------------
# STOCK IN
# --------------------------------------------------
elif tab == "Stock In":
    st.header("📥 Stock In")

    if inventory.empty:
        st.warning("No inventory items available")
    else:
        with st.form("stock_in"):
            item = st.selectbox("Item", inventory.item_name)
            qty = st.number_input("Quantity Received", min_value=1, step=1)
            cost = st.number_input("Unit Cost (GHS)", min_value=0.01, step=0.01)

            if st.form_submit_button("Receive Stock"):
                idx = inventory.index[inventory.item_name == item][0]

                qty = int(qty)
                cost = float(cost)
                total = qty * cost

                inventory.at[idx, "quantity"] += qty

                receipts.loc[len(receipts)] = [
                    datetime.now().strftime("%Y-%m-%d"),
                    inventory.at[idx, "item_id"],
                    item,
                    qty,
                    cost,
                    total,
                    user["full_name"]
                ]

                save_csv(INVENTORY_FILE)
                save_csv(RECEIPTS_FILE)

                st.success(f"Stock received. Total value: GHS {total:,.2f}")

# --------------------------------------------------
# STOCK OUT
# --------------------------------------------------
elif tab == "Stock Out":
    st.header("📤 Stock Out")

    if inventory.empty:
        st.warning("No inventory items available")
    else:
        with st.form("stock_out"):
            item = st.selectbox("Item", inventory.item_name)
            dept = st.text_input("Receiving Department")
            qty = st.number_input("Quantity Issued", min_value=1, step=1)

            if st.form_submit_button("Issue Stock"):
                idx = inventory.index[inventory.item_name == item][0]
                available = int(inventory.at[idx, "quantity"])

                if qty > available:
                    st.error("Insufficient stock")
                else:
                    inventory.at[idx, "quantity"] -= int(qty)

                    issues.loc[len(issues)] = [
                        datetime.now().strftime("%Y-%m-%d"),
                        inventory.at[idx, "item_id"],
                        item,
                        int(qty),
                        dept,
                        user["full_name"]
                    ]

                    save_csv(INVENTORY_FILE)
                    save_csv(ISSUES_FILE)

                    st.success("Stock issued successfully")

# --------------------------------------------------
# REPORTS
# --------------------------------------------------
elif tab == "Reports":
    st.header("📝 Reports")

    st.subheader("📥 Receipts Log")
    st.dataframe(receipts, use_container_width=True)

    st.subheader("📤 Issues Log")
    st.dataframe(issues, use_container_width=True)
