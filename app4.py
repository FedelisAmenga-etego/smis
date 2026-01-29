# stores_dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import os

st.set_page_config(
    page_title="NHRC Stores Management System",
    page_icon="🏪",
    layout="wide"
)

# ================== SESSION SAFETY ==================
def init_session():
    defaults = {
        "logged_in": False,
        "user": None,
        "active_tab": "🏠 Dashboard"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ================== AUTH ==================
USERS_FILE = "store_users.csv"

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        df = pd.DataFrame([{
            "username": "admin",
            "password": hash_pw("NHRC@26"),
            "full_name": "System Administrator",
            "role": "admin",
            "department": "General Stores"
        }])
        df.to_csv(USERS_FILE, index=False)
    return pd.read_csv(USERS_FILE)

def authenticate(u, p):
    df = load_users()
    user = df[df.username == u]
    if not user.empty and user.iloc[0].password == hash_pw(p):
        return user.iloc[0].to_dict()
    return None

def login_ui():
    st.markdown("### 🔐 Login")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            user = authenticate(u, p)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

if not st.session_state.logged_in:
    login_ui()
    st.stop()

# ================== DATA ==================
INV_FILE = "inventory.csv"
REC_FILE = "receipts.csv"
ISS_FILE = "issues.csv"

def load_df(path, cols):
    if not os.path.exists(path):
        return pd.DataFrame(columns=cols)
    return pd.read_csv(path)

def save_df(df, path):
    df.to_csv(path, index=False)

def inventory():
    return load_df(INV_FILE, [
        "item_id","item_name","category","quantity","unit",
        "reorder_level","supplier","expiry_date"
    ])

def receipts():
    return load_df(REC_FILE, [
        "date","item_id","item_name","quantity","unit_cost","total"
    ])

def issues():
    return load_df(ISS_FILE, [
        "date","item_id","item_name","quantity","department"
    ])

# ================== NAV ==================
tabs = ["🏠 Dashboard","📦 Inventory","📥 Stock In","📤 Stock Out","⚙️ Settings"]
st.session_state.active_tab = st.radio(
    "Navigation", tabs,
    index=tabs.index(st.session_state.active_tab),
    horizontal=True
)

tab = st.session_state.active_tab

# ================== INVENTORY ==================
if tab == "📦 Inventory":
    df = inventory()
    st.dataframe(df, use_container_width=True)

    with st.form("add_item"):
        name = st.text_input("Item Name")
        qty = st.number_input("Quantity", 0)
        if st.form_submit_button("Add"):
            new = {
                "item_id": f"STR-{int(datetime.now().timestamp())}",
                "item_name": name,
                "category": "General",
                "quantity": int(qty),
                "unit": "Units",
                "reorder_level": 10,
                "supplier": "",
                "expiry_date": ""
            }
            df = pd.concat([df, pd.DataFrame([new])])
            save_df(df, INV_FILE)
            st.success("Item added")
            st.rerun()

# ================== STOCK IN ==================
elif tab == "📥 Stock In":
    inv = inventory()
    rec = receipts()

    item = st.selectbox("Item", inv.item_name)
    qty = st.number_input("Qty", 1)
    cost = st.number_input("Unit Cost", 0.0)

    total = float(qty) * float(cost)
    st.metric("Total", f"GHS {total:,.2f}")

    if st.button("Record Receipt"):
        idx = inv[inv.item_name == item].index[0]
        inv.loc[idx,"quantity"] += int(qty)
        save_df(inv, INV_FILE)

        rec = pd.concat([rec, pd.DataFrame([{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "item_id": inv.loc[idx,"item_id"],
            "item_name": item,
            "quantity": int(qty),
            "unit_cost": float(cost),
            "total": total
        }])])
        save_df(rec, REC_FILE)
        st.success("Stock updated")
        st.rerun()

# ================== STOCK OUT ==================
elif tab == "📤 Stock Out":
    inv = inventory()
    iss = issues()

    item = st.selectbox("Item", inv.item_name)
    qty = st.number_input("Qty", 1)

    idx = inv[inv.item_name == item].index[0]
    if qty > inv.loc[idx,"quantity"]:
        st.error("Insufficient stock")
    elif st.button("Issue"):
        inv.loc[idx,"quantity"] -= int(qty)
        save_df(inv, INV_FILE)

        iss = pd.concat([iss, pd.DataFrame([{
            "date": datetime.now().strftime("%Y-%m-%d"),
            "item_id": inv.loc[idx,"item_id"],
            "item_name": item,
            "quantity": int(qty),
            "department": "General"
        }])])
        save_df(iss, ISS_FILE)
        st.success("Stock issued")
        st.rerun()
