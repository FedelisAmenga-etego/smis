# stores_dashboard.py - Navrongo Health Research Centre Store Management System
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import hashlib
import warnings
from supabase import create_client, Client
import os
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

# ========== SUPABASE CONFIGURATION ==========
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))
    
    if not url or not key:
        st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in secrets or environment variables.")
        st.stop()
    
    return create_client(url, key)

supabase = init_supabase()

# ========== DATABASE OPERATIONS ==========
class DatabaseManager:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    # User operations
    def get_users(self):
        """Get all users"""
        try:
            response = self.supabase.table('users').select('*').execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error fetching users: {e}")
            return pd.DataFrame()
    
    def get_user(self, username):
        """Get user by username"""
        try:
            response = self.supabase.table('users').select('*').eq('username', username).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            st.error(f"Error fetching user: {e}")
            return None
    
    def create_user(self, user_data):
        """Create new user"""
        try:
            response = self.supabase.table('users').insert(user_data).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)
    
    def update_user(self, username, updates):
        """Update user"""
        try:
            response = self.supabase.table('users').update(updates).eq('username', username).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)
    
    def delete_user(self, username):
        """Delete user"""
        try:
            response = self.supabase.table('users').delete().eq('username', username).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)
    
    # Inventory operations
    def get_inventory(self):
        """Get all inventory items"""
        try:
            response = self.supabase.table('inventory').select('*').execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error fetching inventory: {e}")
            return pd.DataFrame()
    
    def create_inventory_item(self, item_data):
        """Create new inventory item"""
        try:
            response = self.supabase.table('inventory').insert(item_data).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)
    
    def update_inventory_item(self, item_id, updates):
        """Update inventory item"""
        try:
            response = self.supabase.table('inventory').update(updates).eq('item_id', item_id).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)
    
    def delete_inventory_item(self, item_id):
        """Delete inventory item"""
        try:
            response = self.supabase.table('inventory').delete().eq('item_id', item_id).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)
    
    # Receipts operations
    def get_receipts(self):
        """Get all receipts"""
        try:
            response = self.supabase.table('receipts').select('*').order('date', desc=True).execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error fetching receipts: {e}")
            return pd.DataFrame()
    
    def create_receipt(self, receipt_data):
        """Create new receipt"""
        try:
            response = self.supabase.table('receipts').insert(receipt_data).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)
    
    # Issues operations
    def get_issues(self):
        """Get all issues"""
        try:
            response = self.supabase.table('issues').select('*').order('date', desc=True).execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error fetching issues: {e}")
            return pd.DataFrame()
    
    def create_issue(self, issue_data):
        """Create new issue"""
        try:
            response = self.supabase.table('issues').insert(issue_data).execute()
            return True, response.data
        except Exception as e:
            return False, str(e)

# Initialize database manager
db = DatabaseManager(supabase)

# ========== AUTHENTICATION SYSTEM ==========
class SupabaseAuth:
    def __init__(self, db_manager):
        self.db = db_manager
        self.session_key = 'logged_in'
        self.username_key = 'username'
        
        # Initialize default admin user if not exists
        self.init_default_admin()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def init_default_admin(self):
        """Initialize default admin user if no users exist"""
        users_df = self.db.get_users()
        if users_df.empty:
            admin_data = {
                'username': 'admin',
                'password': self.hash_password('NHRC@26'),
                'full_name': 'System Administrator',
                'role': 'admin',
                'department': 'General Stores',
                'created_at': datetime.now().isoformat(),
                'created_by': 'system'
            }
            self.db.create_user(admin_data)
    
    def authenticate(self, username, password):
        """Authenticate user"""
        user = self.db.get_user(username)
        if user and user['password'] == self.hash_password(password):
            return user
        return None
    
    def check_auth(self):
        """Check if user is authenticated"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = False
            st.session_state[self.username_key] = ''
            st.session_state['user_data'] = {}
        
        if not st.session_state[self.session_key]:
            self.show_login_interface()
            st.stop()
        else:
            return st.session_state['user_data']
    
    def show_login_interface(self):
        """Display login interface"""
        st.markdown(
            f"""
            <div style='text-align:center;padding:6px 0 12px 0;background:transparent;'>
                <h3 style='margin:0;color:#2E7D32;'>Navrongo Health Research Centre</h3>
                <h4 style='margin:0;color:#2E7D32;'>General Stores Department</h4>
            </div>
            <hr style='border:1px solid rgba(0,0,0,0.08);margin-bottom:18px;'>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<h3 style='text-align:center;'>🔐 Login</h3>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Login", type="primary")
                
                if login_btn:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        with st.spinner("🔐 Authenticating..."):
                            user_info = self.authenticate(username, password)
                            
                            if user_info:
                                st.session_state[self.session_key] = True
                                st.session_state[self.username_key] = username
                                st.session_state['user_data'] = user_info
                                
                                st.success(f"✅ Signed in as {user_info['full_name']}")
                                st.rerun()
                            else:
                                st.error("❌ Invalid username or password")
    
    def logout(self):
        """Logout user"""
        for key in list(st.session_state.keys()):
            if key not in ['_theme', '_pages']:
                del st.session_state[key]
        st.rerun()
    
    def is_admin(self):
        """Check if current user is admin"""
        return st.session_state.get('user_data', {}).get('role') == 'admin'
    
    def add_user(self, user_data, created_by):
        """Add new user"""
        # Check if username exists
        existing = self.db.get_user(user_data['username'])
        if existing:
            return False, "Username already exists"
        
        # Hash password
        user_data['password'] = self.hash_password(user_data['password'])
        user_data['created_at'] = datetime.now().isoformat()
        user_data['created_by'] = created_by
        
        # Create user
        success, result = self.db.create_user(user_data)
        if success:
            return True, "User added successfully"
        else:
            return False, f"Error creating user: {result}"

# Initialize authentication
auth = SupabaseAuth(db)

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="NHRC Stores Management System",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary: #2E7D32;    /* Green theme for stores */
        --secondary: #1B5E20;  /* Darker green */
        --accent: #4CAF50;     /* Light green */
        --warning: #FF9800;    /* Amber */
        --danger: #D32F2F;     /* Red */
        --info: #1976D2;       /* Blue */
        --light: #F5F5F5;      /* Light gray */
        --dark: #212121;       /* Dark gray */
        --sidebar-bg: #f8f9fa; /* Light grey for sidebar */
        --sidebar-text: #333333; /* Dark text for sidebar */
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid #dee2e6;
    }
    
    [data-testid="stSidebar"] * {
        color: var(--sidebar-text) !important;
    }
    
    /* Main navigation tabs styling */
    .stRadio > div[role='radiogroup'] {
        display: flex;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 25px;
        padding: 10px 0;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .stRadio > div[role='radiogroup'] label {
        background: #f8f9fa !important;
        border-radius: 10px !important;
        padding: 12px 20px !important;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06) !important;
        transition: all .2s ease !important;
        font-weight: 600 !important;
        color: #495057 !important;
        border: 1px solid rgba(0,0,0,0.08) !important;
        margin: 5px !important;
    }
    
    .stRadio > div[role='radiogroup'] label:hover { 
        transform: translateY(-3px) scale(1.02) !important; 
        box-shadow: 0 8px 20px rgba(0,0,0,0.12) !important; 
        cursor: pointer !important;
        background: #e9ecef !important;
    }
    
    .stRadio > div[role='radiogroup'] input:checked + div { 
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important; 
        color: white !important; 
        box-shadow: 0 6px 15px rgba(46, 125, 50, 0.2) !important;
        border-color: var(--primary) !important;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        border-left: 6px solid var(--primary);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.12);
    }
    
    .metric-icon {
        font-size: 2.2rem;
        margin-bottom: 0.8rem;
        color: var(--primary);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--dark);
        margin: 0.3rem 0;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        font-size: 0.95rem;
        color: #64748b;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Form styling */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input, 
    .stTextArea>div>textarea, 
    .stSelectbox>div>div>div,
    .stDateInput>div>div>input {
        border-radius: 10px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 10px 14px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        min-height: 48px !important;
        box-sizing: border-box !important;
    }
    
    .stTextInput>div>div>input:focus, 
    .stNumberInput>div>div>input:focus, 
    .stTextArea>div>textarea:focus, 
    .stSelectbox>div>div>div:focus,
    .stDateInput>div>div>input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.1) !important;
        outline: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== CHECK AUTHENTICATION ==========
user = auth.check_auth()

# ========== LOAD DATA FROM SUPABASE ==========
@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_inventory_data():
    """Load inventory data from Supabase"""
    return db.get_inventory()

@st.cache_data(ttl=60)
def load_receipts_data():
    """Load receipts data from Supabase"""
    return db.get_receipts()

@st.cache_data(ttl=60)
def load_issues_data():
    """Load issues data from Supabase"""
    return db.get_issues()

# Load data
inventory_df = load_inventory_data()
receipts_df = load_receipts_data()
issues_df = load_issues_data()

# ========== SIDEBAR USER INFO ==========
with st.sidebar:
    st.markdown("### 👤 User Information")
    
    user_info_html = f"""
    <div style='background: rgba(0, 0, 0, 0.03); padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
        <p style='margin: 0.3rem 0;'><strong>Username:</strong> {user['username']}</p>
        <p style='margin: 0.3rem 0;'><strong>Name:</strong> {user['full_name']}</p>
        <p style='margin: 0.3rem 0;'><strong>Role:</strong> {user['role'].title()}</p>
        <p style='margin: 0.3rem 0;'><strong>Department:</strong> {user['department']}</p>
    </div>
    """
    st.markdown(user_info_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh Data", use_container_width=True, type="secondary"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        auth.logout()

# ========== MAIN HEADER ==========
st.markdown(
    f"""
    <div style='text-align:center;padding:6px 0 12px 0;background:transparent;'>
        <h3 style='margin:0;color:#2E7D32;'>Navrongo Health Research Centre</h3>
        <h4 style='margin:0;color:#2E7D32;'>General Stores</h4>
    </div>
    <hr style='border:1px solid rgba(0,0,0,0.08);margin-bottom:18px;'>
    """,
    unsafe_allow_html=True
)

# ========== MAIN NAVIGATION TABS ==========
tabs = ["🏠 Dashboard", "📦 Inventory", "📥 Stock In", "📤 Stock Out", "⏰ Expiry", "📝 Reports", "⚙️ Settings"]

selected_tab = st.radio(
    "Navigation",
    tabs,
    horizontal=True,
    label_visibility="collapsed"
)

# DASHBOARD TAB
if selected_tab == "🏠 Dashboard":
    st.markdown('<div class="section-header"><h2>Dashboard Overview</h2></div>', unsafe_allow_html=True)
    
    # Calculate expiry metrics
    if not inventory_df.empty and 'expiry_date' in inventory_df.columns:
        inventory_df['expiry_date_dt'] = pd.to_datetime(inventory_df['expiry_date'], errors='coerce')
        current_date = pd.Timestamp.now()
        inventory_df['days_to_expiry'] = (inventory_df['expiry_date_dt'] - current_date).dt.days
        
        expired_count = (inventory_df['days_to_expiry'] <= 0).sum()
        expiring_30_count = ((inventory_df['days_to_expiry'] > 0) & (inventory_df['days_to_expiry'] <= 30)).sum()
    else:
        expired_count = 0
        expiring_30_count = 0
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    metrics_data = [
        ("Total Items", len(inventory_df) if not inventory_df.empty else 0, "📦", "Total number of unique items"),
        ("Total Units", f"{inventory_df['quantity'].sum():,}" if not inventory_df.empty and 'quantity' in inventory_df.columns else "0", "📈", "Total units across all items"),
        ("Low Stock", len(inventory_df[(inventory_df['quantity'] <= inventory_df['reorder_level']) & (inventory_df['quantity'] > 0)]) if not inventory_df.empty and 'quantity' in inventory_df.columns and 'reorder_level' in inventory_df.columns else 0, "⚠️", "Items at or below reorder level"),
        ("Expiring Soon", expiring_30_count, "⏰", "Items expiring within 30 days")
    ]
    
    for col, (label, value, icon, tooltip) in zip([col1, col2, col3, col4], metrics_data):
        with col:
            st.markdown(f"""
                <div class="metric-card" title="{tooltip}">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Row
    if not inventory_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Units by Category")
            if 'category' in inventory_df.columns and 'quantity' in inventory_df.columns:
                category_units = inventory_df.groupby('category')['quantity'].sum().reset_index()
                if not category_units.empty:
                    fig = px.bar(
                        category_units,
                        x='category',
                        y='quantity',
                        color='quantity',
                        color_continuous_scale='Viridis',
                        text='quantity'
                    )
                    fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white')
                    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 📦 Stock Distribution")
            if 'category' in inventory_df.columns and 'quantity' in inventory_df.columns:
                fig = px.pie(
                    inventory_df,
                    values='quantity',
                    names='category',
                    hole=0.4
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Low Stock Alert
    st.markdown("#### ⚠️ Low Stock Items Requiring Attention")
    
    if not inventory_df.empty and 'quantity' in inventory_df.columns and 'reorder_level' in inventory_df.columns:
        low_stock_items = inventory_df[inventory_df['quantity'] <= inventory_df['reorder_level']]
        
        if not low_stock_items.empty:
            display_cols = ['item_name', 'category', 'quantity', 'unit', 'reorder_level']
            display_df = low_stock_items[[col for col in display_cols if col in low_stock_items.columns]].copy()
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.success("✅ No low stock items at the moment!")

# INVENTORY TAB
elif selected_tab == "📦 Inventory":
    st.markdown('<div class="section-header"><h2>📦 Inventory Management</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Inventory", "Add Item", "Edit/Delete Item"])
    
    with tab1:
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search = st.text_input("🔍 Search items", placeholder="Name or ID...")
        with col2:
            categories = ["All"]
            if not inventory_df.empty and 'category' in inventory_df.columns:
                categories += sorted(inventory_df['category'].unique().tolist())
            category_filter = st.selectbox("Filter by Category", categories)
        with col3:
            status_filter = st.selectbox("Stock Status", ["All", "Adequate", "Low", "Critical"])
        with col4:
            expiry_filter = st.selectbox("Expiry Status", 
                                       ["All", "Expired", "≤ 30 Days", "≤ 90 Days", "> 90 Days", "No Expiry"])
        
        # Apply filters
        filtered = inventory_df.copy()
        if search and not inventory_df.empty:
            if 'item_name' in inventory_df.columns:
                filtered = filtered[filtered['item_name'].str.contains(search, case=False, na=False)]
        
        if category_filter != "All" and 'category' in filtered.columns:
            filtered = filtered[filtered['category'] == category_filter]
        
        # Calculate days to expiry for filtering
        if not filtered.empty and 'expiry_date' in filtered.columns:
            filtered['expiry_date_dt'] = pd.to_datetime(filtered['expiry_date'], errors='coerce')
            current_date = pd.Timestamp.now()
            filtered['days_to_expiry'] = (filtered['expiry_date_dt'] - current_date).dt.days
        
        # Apply stock status filter
        if status_filter != "All" and 'quantity' in filtered.columns and 'reorder_level' in filtered.columns:
            if status_filter == "Low":
                filtered = filtered[filtered['quantity'] <= filtered['reorder_level']]
            elif status_filter == "Critical":
                filtered = filtered[filtered['quantity'] == 0]
            elif status_filter == "Adequate":
                filtered = filtered[filtered['quantity'] > filtered['reorder_level']]
        
        # Apply expiry status filter
        if expiry_filter != "All" and 'days_to_expiry' in filtered.columns:
            if expiry_filter == "Expired":
                filtered = filtered[filtered['days_to_expiry'] <= 0]
            elif expiry_filter == "≤ 30 Days":
                filtered = filtered[(filtered['days_to_expiry'] > 0) & (filtered['days_to_expiry'] <= 30)]
            elif expiry_filter == "≤ 90 Days":
                filtered = filtered[(filtered['days_to_expiry'] > 0) & (filtered['days_to_expiry'] <= 90)]
            elif expiry_filter == "> 90 Days":
                filtered = filtered[filtered['days_to_expiry'] > 90]
            elif expiry_filter == "No Expiry":
                filtered = filtered[pd.isna(filtered['expiry_date'])]
        
        # Display with formatting
        if not filtered.empty:
            display_cols = ['item_id', 'item_name', 'category', 'quantity', 'unit']
            if 'storage_location' in filtered.columns:
                display_cols.append('storage_location')
            if 'expiry_date' in filtered.columns:
                display_cols.append('expiry_date')
            
            display_df = filtered[[col for col in display_cols if col in filtered.columns]].copy()
            
            # Format expiry date
            if 'expiry_date' in display_df.columns:
                display_df['expiry_date'] = pd.to_datetime(display_df['expiry_date']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True)
            
            # Export
            csv = filtered.to_csv(index=False)
            st.download_button(
                "📥 Export Filtered Data",
                data=csv,
                file_name="filtered_inventory.csv",
                mime="text/csv"
            )
        else:
            st.info("No items match your filters or inventory is empty.")
    
    with tab2:
        st.markdown("#### ➕ Add New Item")
        
        with st.form("add_item_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                item_name = st.text_input("Item Name*", placeholder="e.g., A4 Duplicating Paper")
                category = st.selectbox("Category*", 
                                      ["Stationery", "Comp/Printer/Accessories", "Miscellaneous", 
                                       "Electrical Items", "Motor Parts", "Vehicle Parts - Toyota Hilux",
                                       "Fuel & Lubricants", "Laboratory Items", "Medical Supplies", "Office Equipment"])
                quantity = st.number_input("Quantity (Units)*", min_value=0, value=0, step=1)
            
            with col2:
                unit = st.selectbox("Unit*", ["Units", "Pieces", "Reams", "Packets", "Boxes", 
                                            "Bottles", "Litre", "Gallon", "Pairs", "Tin", "Rolls", "Cartons"])
                storage_location = st.selectbox("Storage Location", 
                                              ["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive", "Warehouse"])
                
                expiry_option = st.radio("Has expiry date?", ["No", "Yes"])
                if expiry_option == "Yes":
                    expiry_date = st.date_input("Expiry Date", 
                                              value=datetime.now() + timedelta(days=365)).isoformat()
                else:
                    expiry_date = None
                
                reorder_level = st.number_input("Reorder Level*", min_value=1, value=10)
            
            notes = st.text_area("Notes")
            supplier = st.text_input("Supplier", value="Standard Supplier")
            
            submitted = st.form_submit_button("➕ Add Item", type="primary")
            
            if submitted:
                if not item_name:
                    st.error("Item Name is required!")
                else:
                    item_id = f"STR-{category[:3].upper()}-{datetime.now().strftime('%Y%m%d')}-{len(inventory_df)+1:04d}"
                    
                    item_data = {
                        'item_id': item_id,
                        'item_name': item_name,
                        'category': category,
                        'quantity': quantity,
                        'unit': unit,
                        'storage_location': storage_location,
                        'reorder_level': reorder_level,
                        'supplier': supplier,
                        'notes': notes,
                        'created_date': datetime.now().isoformat(),
                        'created_by': user['username']
                    }
                    
                    if expiry_date:
                        item_data['expiry_date'] = expiry_date
                    
                    success, result = db.create_inventory_item(item_data)
                    
                    if success:
                        st.success(f"✅ Item '{item_name}' added successfully!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ Error adding item: {result}")
    
    with tab3:
        st.markdown("#### ✏️ Edit/Delete Inventory Item")
        
        if not inventory_df.empty:
            item_to_edit = st.selectbox("Select item to edit/delete", 
                                       inventory_df['item_name'].unique())
            
            if item_to_edit:
                item_data = inventory_df[inventory_df['item_name'] == item_to_edit].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    with st.form("edit_item_form"):
                        st.markdown(f"**Editing: {item_to_edit}**")
                        
                        current_qty = item_data.get('quantity', 0)
                        new_quantity = st.number_input("Quantity (Units)", 
                                                     min_value=0, 
                                                     value=int(current_qty))
                        
                        locations = ["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive", "Warehouse"]
                        current_location = item_data.get('storage_location', 'Main Store')
                        new_location = st.selectbox("Storage Location", 
                                                  locations,
                                                  index=locations.index(current_location) if current_location in locations else 0)
                        
                        categories = ["Stationery", "Comp/Printer/Accessories", "Miscellaneous", 
                                     "Electrical Items", "Motor Parts", "Vehicle Parts - Toyota Hilux",
                                     "Fuel & Lubricants", "Laboratory Items", "Medical Supplies", "Office Equipment"]
                        current_category = item_data.get('category', 'Miscellaneous')
                        new_category = st.selectbox("Category", 
                                                  categories,
                                                  index=categories.index(current_category) if current_category in categories else 0)
                        
                        new_reorder_level = st.number_input("Reorder Level (Units)", 
                                                          min_value=1, 
                                                          value=int(item_data.get('reorder_level', 10)))
                        
                        new_supplier = st.text_input("Supplier", value=item_data.get('supplier', 'Standard Supplier'))
                        new_notes = st.text_area("Notes", value=item_data.get('notes', ''))
                        
                        submitted = st.form_submit_button("💾 Save Changes", type="primary")
                        
                        if submitted:
                            updates = {
                                'quantity': new_quantity,
                                'storage_location': new_location,
                                'category': new_category,
                                'reorder_level': new_reorder_level,
                                'supplier': new_supplier,
                                'notes': new_notes,
                                'updated_at': datetime.now().isoformat(),
                                'updated_by': user['username']
                            }
                            
                            success, result = db.update_inventory_item(item_data['item_id'], updates)
                            
                            if success:
                                st.success("✅ Item updated successfully!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"❌ Error updating item: {result}")
                
                with col2:
                    st.markdown("### 🗑️")
                    st.markdown("##### Delete Item")
                    
                    st.warning(f"You are about to delete: **{item_to_edit}**")
                    st.info(f"Current stock: {item_data.get('quantity', 0)} units")
                    
                    delete_confirmed = st.checkbox("I confirm deletion")
                    
                    if st.button("🗑️ Delete Item", 
                                disabled=not delete_confirmed,
                                use_container_width=True,
                                type="primary"):
                        
                        success, result = db.delete_inventory_item(item_data['item_id'])
                        
                        if success:
                            st.success(f"✅ Item '{item_to_edit}' deleted successfully!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Error deleting item: {result}")

# STOCK IN TAB
elif selected_tab == "📥 Stock In":
    st.markdown('<div class="section-header"><h2>📥 Stock Receipts Management</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Record Receipt", "Receipt History"])
    
    with tab1:
        st.markdown("#### 📝 Record New Stock Receipt")
        
        # Initialize session state for selected item
        if 'selected_receipt_item' not in st.session_state:
            st.session_state.selected_receipt_item = None
        
        with st.form("receipt_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                receipt_date = st.date_input("Date Received*", value=datetime.now())
                supplier = st.text_input("Supplier Name*", placeholder="e.g., Office Supplies Ltd.")
                project_code = st.selectbox("Project/Source of Funds", 
                                          ["General Funds", "Research Grant A", "Research Grant B", "Donor Funds", "Other"])
                reference = st.text_input("Delivery Note/Invoice No.", placeholder="DN-2024-001")
            
            with col2:
                if not inventory_df.empty:
                    # Create a list of item names for selection
                    item_names = inventory_df['item_name'].tolist()
                    
                    # Item selection with callback to update session state
                    def on_item_change():
                        st.session_state.selected_receipt_item = st.session_state.receipt_item_selector
                    
                    selected_item = st.selectbox(
                        "Select Item*", 
                        item_names,
                        key="receipt_item_selector",
                        on_change=on_item_change
                    )
                    
                    # Get current stock for selected item
                    if selected_item:
                        item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                        current_stock = int(item_data.get('quantity', 0))  # Convert to Python int
                        unit = item_data.get('unit', 'units')
                        st.info(f"**Current Stock:** {current_stock} {unit}")
                    else:
                        current_stock = 0
                        unit = 'units'
                else:
                    st.warning("No items in inventory. Please add items first.")
                    selected_item = None
                    current_stock = 0
                    unit = 'units'
                
                quantity = st.number_input("Quantity Received*", min_value=1, value=1)
                unit_cost = st.number_input("Unit Cost (GHS)*", min_value=0.0, value=0.0, step=0.01, format="%.2f")
                total_value = quantity * unit_cost
                st.metric("Total Value", f"GHS {total_value:,.2f}")
            
            received_by = st.text_input("Received By*", value=user['full_name'])
            notes = st.text_area("Additional Notes")
            
            submitted = st.form_submit_button("📥 Record Receipt", type="primary")
            
            if submitted:
                if not all([supplier, selected_item, received_by]):
                    st.error("Please fill all required fields (*)!")
                elif unit_cost <= 0:
                    st.error("Unit cost must be greater than 0!")
                elif selected_item is None:
                    st.error("No item selected!")
                else:
                    # Get fresh item data
                    item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                    
                    # Update inventory - convert numpy types to Python native types
                    new_quantity = int(current_stock) + int(quantity)
                    updates = {
                        'quantity': new_quantity,  # Already converted to Python int
                        'updated_at': datetime.now().isoformat(),
                        'updated_by': str(user['username'])  # Ensure string
                    }
                    
                    success, result = db.update_inventory_item(str(item_data['item_id']), updates)
                    
                    if success:
                        # Add to receipts - convert all numpy types to Python native types
                        receipt_data = {
                            'date': receipt_date.isoformat(),
                            'item_id': str(item_data['item_id']),
                            'item_name': str(selected_item),
                            'supplier': str(supplier),
                            'quantity': int(quantity),
                            'unit_cost': float(unit_cost),  # Convert to Python float
                            'total_value': float(total_value),  # Convert to Python float
                            'project_code': str(project_code),
                            'reference': str(reference) if reference else '',
                            'received_by': str(received_by),
                            'notes': str(notes) if notes else '',
                            'created_at': datetime.now().isoformat()
                        }
                        
                        success2, result2 = db.create_receipt(receipt_data)
                        
                        if success2:
                            st.success(f"✅ Receipt recorded successfully! Stock updated to {new_quantity} units.")
                            # Clear selection from session state
                            st.session_state.selected_receipt_item = None
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Error recording receipt: {result2}")
                    else:
                        st.error(f"❌ Error updating inventory: {result}")
    
    with tab2:
        st.markdown("#### 📋 Receipt History")
        
        if not receipts_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("To Date", value=datetime.now())
            
            # Convert dates for filtering
            filtered_receipts = receipts_df.copy()
            filtered_receipts['date'] = pd.to_datetime(filtered_receipts['date'], errors='coerce')
            mask = (filtered_receipts['date'] >= pd.Timestamp(start_date)) & \
                   (filtered_receipts['date'] <= pd.Timestamp(end_date))
            filtered_receipts = filtered_receipts[mask]
            
            if not filtered_receipts.empty:
                total_receipts = len(filtered_receipts)
                total_quantity = int(filtered_receipts['quantity'].sum())  # Convert to Python int
                total_value = float(filtered_receipts['total_value'].sum())  # Convert to Python float
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Receipts", total_receipts)
                with col2:
                    st.metric("Total Quantity", f"{total_quantity:,}")
                with col3:
                    st.metric("Total Value", f"GHS {total_value:,.2f}")
                
                display_df = filtered_receipts.copy()
                display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
                
                st.dataframe(display_df, use_container_width=True)
                
                csv = filtered_receipts.to_csv(index=False)
                st.download_button(
                    "📥 Export Receipts",
                    data=csv,
                    file_name=f"receipts_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No receipts found for the selected period.")
        else:
            st.info("No receipts recorded yet.")

# STOCK OUT TAB
elif selected_tab == "📤 Stock Out":
    st.markdown('<div class="section-header"><h2>📤 Stock Issues Management</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Issue Stock", "Issue History"])
    
    with tab1:
        st.markdown("#### 📝 Issue Stock to Department")
        
        # Initialize session state for selected item
        if 'selected_issue_item' not in st.session_state:
            st.session_state.selected_issue_item = None
        
        with st.form("issue_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                issue_date = st.date_input("Issue Date*", value=datetime.now())
                department = st.selectbox("Receiving Department*", 
                                        ["Biomedical", "Microbiology", "Parasitology", 
                                         "Clinical Lab", "Research", "Administration", "IT", "Field Team", "Maintenance"])
                purpose = st.text_input("Purpose/Project", placeholder="e.g., Research Project, Daily Operations")
            
            with col2:
                if not inventory_df.empty:
                    # Create a list of item names for selection
                    item_names = inventory_df['item_name'].tolist()
                    
                    # Item selection with callback to update session state
                    def on_item_change():
                        st.session_state.selected_issue_item = st.session_state.issue_item_selector
                    
                    selected_item = st.selectbox(
                        "Select Item*", 
                        item_names,
                        key="issue_item_selector",
                        on_change=on_item_change
                    )
                    
                    # Get current stock for selected item
                    if selected_item:
                        item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                        current_stock = int(item_data.get('quantity', 0))  # Convert to Python int
                        unit = item_data.get('unit', 'units')
                        st.info(f"**Current Stock:** {current_stock} {unit}")
                        
                        # Set max value for quantity input
                        max_quantity = current_stock
                    else:
                        current_stock = 0
                        unit = 'units'
                        max_quantity = 0
                else:
                    st.warning("No items in inventory. Please add items first.")
                    selected_item = None
                    current_stock = 0
                    unit = 'units'
                    max_quantity = 0
                
                quantity = st.number_input(
                    "Quantity to Issue*", 
                    min_value=1, 
                    value=1, 
                    max_value=max_quantity if max_quantity > 0 else 1
                )
                
                issued_by = st.text_input("Issued By*", value=user['full_name'])
            
            notes = st.text_area("Additional Notes")
            
            submitted = st.form_submit_button("📤 Issue Stock", type="primary")
            
            if submitted:
                if not all([department, selected_item, issued_by]):
                    st.error("Please fill all required fields (*)!")
                elif selected_item is None:
                    st.error("No item selected!")
                elif quantity > current_stock:
                    st.error(f"Cannot issue {quantity} units. Only {current_stock} available!")
                else:
                    # Get fresh item data
                    item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                    
                    # Update inventory - convert numpy types to Python native types
                    new_quantity = int(current_stock) - int(quantity)
                    updates = {
                        'quantity': new_quantity,  # Already converted to Python int
                        'updated_at': datetime.now().isoformat(),
                        'updated_by': str(user['username'])  # Ensure string
                    }
                    
                    success, result = db.update_inventory_item(str(item_data['item_id']), updates)
                    
                    if success:
                        # Add to issues - convert all numpy types to Python native types
                        issue_data = {
                            'date': issue_date.isoformat(),
                            'item_id': str(item_data['item_id']),
                            'item_name': str(selected_item),
                            'department': str(department),
                            'quantity': int(quantity),
                            'purpose': str(purpose) if purpose else '',
                            'issued_by': str(issued_by),
                            'notes': str(notes) if notes else '',
                            'created_at': datetime.now().isoformat()
                        }
                        
                        success2, result2 = db.create_issue(issue_data)
                        
                        if success2:
                            st.success(f"✅ Stock issued successfully! Remaining stock: {new_quantity} units.")
                            # Clear selection from session state
                            st.session_state.selected_issue_item = None
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Error recording issue: {result2}")
                    else:
                        st.error(f"❌ Error updating inventory: {result}")
    
    with tab2:
        st.markdown("#### 📋 Issue History")
        
        if not issues_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("To Date", value=datetime.now())
            
            # Convert dates for filtering
            filtered_issues = issues_df.copy()
            filtered_issues['date'] = pd.to_datetime(filtered_issues['date'], errors='coerce')
            mask = (filtered_issues['date'] >= pd.Timestamp(start_date)) & \
                   (filtered_issues['date'] <= pd.Timestamp(end_date))
            filtered_issues = filtered_issues[mask]
            
            if not filtered_issues.empty:
                total_issues = len(filtered_issues)
                total_quantity = int(filtered_issues['quantity'].sum())  # Convert to Python int
                departments = int(filtered_issues['department'].nunique())  # Convert to Python int
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Issues", total_issues)
                with col2:
                    st.metric("Total Quantity", f"{total_quantity:,}")
                with col3:
                    st.metric("Departments", departments)
                
                display_df = filtered_issues.copy()
                display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
                
                st.dataframe(display_df, use_container_width=True)
                
                csv = filtered_issues.to_csv(index=False)
                st.download_button(
                    "📥 Export Issues",
                    data=csv,
                    file_name=f"issues_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No issues found for the selected period.")
        else:
            st.info("No issues recorded yet.")

# EXPIRY TAB
elif selected_tab == "⏰ Expiry":
    st.markdown('<div class="section-header"><h2>⏰ Expiry Management</h2></div>', unsafe_allow_html=True)
    
    if not inventory_df.empty and 'expiry_date' in inventory_df.columns:
        inventory_df['expiry_date_dt'] = pd.to_datetime(inventory_df['expiry_date'], errors='coerce')
        current_date = pd.Timestamp.now()
        inventory_df['days_to_expiry'] = (inventory_df['expiry_date_dt'] - current_date).dt.days
        
        expiry_items = inventory_df[pd.notna(inventory_df['expiry_date'])]
        
        if not expiry_items.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            expired = (expiry_items['days_to_expiry'] <= 0).sum()
            expiring_30 = ((expiry_items['days_to_expiry'] > 0) & 
                          (expiry_items['days_to_expiry'] <= 30)).sum()
            expiring_90 = ((expiry_items['days_to_expiry'] > 30) & 
                          (expiry_items['days_to_expiry'] <= 90)).sum()
            expiring_180 = ((expiry_items['days_to_expiry'] > 90) & 
                           (expiry_items['days_to_expiry'] <= 180)).sum()
            
            with col1:
                st.metric("Expired", expired)
            with col2:
                st.metric("< 30 Days", expiring_30)
            with col3:
                st.metric("30-90 Days", expiring_90)
            with col4:
                st.metric("90-180 Days", expiring_180)
            
            st.markdown("#### 🚨 Expired Items")
            expired_items = expiry_items[expiry_items['days_to_expiry'] <= 0]
            if not expired_items.empty:
                st.dataframe(expired_items[['item_name', 'category', 'quantity', 'unit', 'expiry_date']], use_container_width=True)
            else:
                st.success("✅ No expired items!")
            
            st.markdown("#### ⚠️ Items Expiring Soon (≤ 30 days)")
            expiring_soon = expiry_items[(expiry_items['days_to_expiry'] > 0) & 
                                         (expiry_items['days_to_expiry'] <= 30)]
            if not expiring_soon.empty:
                st.dataframe(expiring_soon[['item_name', 'category', 'quantity', 'unit', 'expiry_date', 'days_to_expiry']].sort_values('days_to_expiry'), use_container_width=True)
            else:
                st.info("No items expiring within 30 days.")
        else:
            st.info("No items with expiry dates found in inventory.")
    else:
        st.info("No expiry data available. Add expiry dates to items in the Inventory tab.")

# REPORTS TAB
elif selected_tab == "📝 Reports":
    st.markdown('<div class="section-header"><h2>📈 Reports & Analytics</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Summary Report", "Export Data"])
    
    with tab1:
        st.markdown("#### 📅 Stores Summary Report")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Items", len(inventory_df) if not inventory_df.empty else 0)
        with col2:
            total_units = inventory_df['quantity'].sum() if not inventory_df.empty and 'quantity' in inventory_df.columns else 0
            st.metric("Total Units", f"{total_units:,}")
        with col3:
            total_receipts = receipts_df['quantity'].sum() if not receipts_df.empty and 'quantity' in receipts_df.columns else 0
            st.metric("Total Received", f"{total_receipts:,}")
        with col4:
            total_issues = issues_df['quantity'].sum() if not issues_df.empty and 'quantity' in issues_df.columns else 0
            st.metric("Total Issued", f"{total_issues:,}")
        
        if st.button("🔄 Generate Report", type="primary"):
            st.success("Report generated successfully!")
    
    with tab2:
        st.markdown("#### 📤 Export Data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not inventory_df.empty:
                csv = inventory_df.to_csv(index=False)
                st.download_button(
                    "📦 Export Inventory",
                    data=csv,
                    file_name="inventory_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if not receipts_df.empty:
                csv = receipts_df.to_csv(index=False)
                st.download_button(
                    "📥 Export Receipts",
                    data=csv,
                    file_name="receipts_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col3:
            if not issues_df.empty:
                csv = issues_df.to_csv(index=False)
                st.download_button(
                    "📤 Export Issues",
                    data=csv,
                    file_name="issues_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )

# SETTINGS TAB (Admin only)
elif selected_tab == "⚙️ Settings":
    if not auth.is_admin():
        st.error("⛔ Administrator access required for settings.")
        st.info("Only administrators can access system settings.")
        st.stop()
    
    st.markdown('<div class="section-header"><h2>⚙️ System Settings</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["User Management", "System Info"])
    
    with tab1:
        st.markdown("#### 👥 User Management")
        
        users_df = db.get_users()
        
        st.markdown("##### 📋 All System Users")
        
        if not users_df.empty:
            st.dataframe(users_df[['username', 'full_name', 'role', 'department', 'created_at']], use_container_width=True)
        
        st.markdown("##### ➕ Add New User")
        
        with st.form("add_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username*", placeholder="e.g., store_officer")
                new_fullname = st.text_input("Full Name*", placeholder="e.g., Store Officer")
                new_role = st.selectbox("Role*", ["user", "manager", "admin"])
            
            with col2:
                new_department = st.selectbox("Department*",
                                            ["General Stores", "Finance", "Research", "Administration", "IT"])
                new_password = st.text_input("Initial Password*", type="password")
                confirm_password = st.text_input("Confirm Password*", type="password")
            
            submitted = st.form_submit_button("➕ Create User", type="primary")
            
            if submitted:
                if not all([new_username, new_fullname, new_password, confirm_password]):
                    st.error("All fields marked with * are required!")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long!")
                else:
                    user_data = {
                        'username': new_username.strip(),
                        'full_name': new_fullname.strip(),
                        'password': new_password,
                        'role': new_role,
                        'department': new_department
                    }
                    
                    success, message = auth.add_user(user_data, user['username'])
                    
                    if success:
                        st.success(f"✅ User '{new_username}' created successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    with tab2:
        st.markdown("#### ℹ️ System Information")
        
        st.info(f"""
        **System Details:**
        - **Version:** 2.0.0 (Supabase Edition)
        - **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
        - **Database:** Supabase (PostgreSQL)
        - **Total Users:** {len(users_df) if not users_df.empty else 0}
        
        **Inventory Statistics:**
        - Total Items: {len(inventory_df)}
        - Total Categories: {inventory_df['category'].nunique() if not inventory_df.empty and 'category' in inventory_df.columns else 0}
        - Total Receipts: {len(receipts_df)}
        - Total Issues: {len(issues_df)}
        
        **Support Contact:**
        - Email: f.amengaetego@gmail.com
        - Phone: +233 54 754 8200
        """)

# ========== FOOTER ==========
st.markdown("---")
st.markdown(
    "<p style='text-align:center;font-size:13px;color:gray;margin-top:25px;'>"
    "© 2026 Navrongo Health Research Centre – Stores Management System (Supabase Edition)<br>"
    "Built by Amenga-etego Fedelis</p>",
    unsafe_allow_html=True
)

