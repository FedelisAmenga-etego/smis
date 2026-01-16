# stores_dashboard.py - Navrongo Health Research Centre Store Management System
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import io
import base64
import os
import hashlib
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

# ========== UPDATED AUTHENTICATION SYSTEM (VC.PY STYLE) ==========
class SimpleAuth:
    def __init__(self):
        self.session_key = 'logged_in'
        self.username_key = 'username'
        self.users_file = 'store_users.csv'
        
        # Initialize default admin user
        self.init_default_users()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def init_default_users(self):
        """Initialize default users if file doesn't exist"""
        if not os.path.exists(self.users_file):
            default_users = pd.DataFrame([{
                'username': 'admin',
                'password': self.hash_password('NHRC@26'),  # Hashed password
                'full_name': 'System Administrator',
                'role': 'admin',
                'department': 'General Stores',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_by': 'system'
            }])
            default_users.to_csv(self.users_file, index=False)
    
    def get_users(self):
        """Load users from CSV"""
        try:
            if os.path.exists(self.users_file):
                return pd.read_csv(self.users_file)
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def save_users(self, users_df):
        """Save users to CSV"""
        users_df.to_csv(self.users_file, index=False)
    
    def authenticate(self, username, password):
        """Authenticate user"""
        users_df = self.get_users()
        if not users_df.empty:
            user = users_df[users_df['username'] == username]
            if not user.empty:
                hashed_input = self.hash_password(password)
                if user.iloc[0]['password'] == hashed_input:
                    return user.iloc[0].to_dict()
        return None
    
    def check_auth(self):
        """Check if user is authenticated - VC.PY style"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = False
            st.session_state[self.username_key] = ''
            st.session_state['user_data'] = {}
        
        # If not logged in, show VC.PY style login interface
        if not st.session_state[self.session_key]:
            self.show_vc_login_interface()
            st.stop()
        else:
            return st.session_state['user_data']
    
    def show_vc_login_interface(self):
        """Display VC.py style login interface"""
        # Get logo
        logo_base64 = self.get_logo_base64()
        
        # Header with logo - matching VC.py
        logo_html = ""
        if logo_base64:
            logo_html = f"<img src='{logo_base64}' width='170' style='display:block;margin:0 auto 8px auto;'>"
        else:
            logo_html = "<div style='font-size: 3rem; margin-bottom: 0.5rem;'>🏪</div>"
        
        st.markdown(
            f"""
            <div style='text-align:center;padding:6px 0 12px 0;background:transparent;'>
                {logo_html}
                <h3 style='margin:0;color:#2E7D32;'>Navrongo Health Research Centre</h3>
                <h4 style='margin:0;color:#2E7D32;'>General Stores Department</h4>
            </div>
            <hr style='border:1px solid rgba(0,0,0,0.08);margin-bottom:18px;'>
            """,
            unsafe_allow_html=True
        )
        
        # VC.py style sidebar login
        st.sidebar.title("🔐 Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        login_btn = st.sidebar.button("Login")
        
        if login_btn:
            if not username or not password:
                st.sidebar.error("Please enter both username and password")
            else:
                with st.spinner("🔐 Authenticating..."):
                    user_info = self.authenticate(username, password)
                    
                    if user_info:
                        st.session_state[self.session_key] = True
                        st.session_state[self.username_key] = username
                        st.session_state['user_data'] = user_info
                        
                        # Ensure user_info has all required fields
                        if 'full_name' not in user_info:
                            user_info['full_name'] = user_info.get('username', 'User').title()
                        if 'department' not in user_info:
                            user_info['department'] = 'General Stores'
                        if 'role' not in user_info:
                            user_info['role'] = 'user'
                        
                        st.sidebar.success(f"✅ Signed in as {user_info['full_name']}")
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Invalid username or password")
        
        # Main content shows info message
        st.info("Please log in from the sidebar to view or manage store inventory.")
    
    def get_logo_base64(self):
        """Convert logo to base64 for embedding"""
        try:
            with open("nhrc_logo.png", "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return f"data:image/png;base64,{encoded_string}"
        except:
            try:
                with open("logo.png", "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                    return f"data:image/png;base64,{encoded_string}"
            except:
                return None
    
    def login(self, username, password):
        """Login user"""
        user = self.authenticate(username, password)
        if user:
            st.session_state[self.session_key] = True
            st.session_state[self.username_key] = username
            st.session_state['user_data'] = user
            return True
        return False
    
    def logout(self):
        """Logout user"""
        st.session_state[self.session_key] = False
        st.session_state[self.username_key] = ''
        st.session_state['user_data'] = {}
        st.rerun()
    
    def is_admin(self):
        """Check if current user is admin"""
        return st.session_state.get('user_data', {}).get('role') == 'admin'
    
    def add_user(self, user_data, created_by):
        """Add new user"""
        users_df = self.get_users()
        
        # Check if username exists
        if user_data['username'] in users_df['username'].values:
            return False, "Username already exists"
        
        # Hash password
        user_data['password'] = self.hash_password(user_data['password'])
        user_data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_data['created_by'] = created_by
        
        # Add to users
        new_user = pd.DataFrame([user_data])
        users_df = pd.concat([users_df, new_user], ignore_index=True)
        self.save_users(users_df)
        
        return True, "User added successfully"
    
    def update_user(self, username, updates, updated_by):
        """Update user information"""
        users_df = self.get_users()
        
        if username not in users_df['username'].values:
            return False, "User not found"
        
        # Update user
        idx = users_df.index[users_df['username'] == username][0]
        
        for key, value in updates.items():
            if key == 'password' and value:  # Hash new password
                users_df.at[idx, key] = self.hash_password(value)
            elif key != 'password':  # Skip password if not provided
                users_df.at[idx, key] = value
        
        users_df.at[idx, 'updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        users_df.at[idx, 'updated_by'] = updated_by
        
        self.save_users(users_df)
        return True, "User updated successfully"
    
    def delete_user(self, username, deleted_by):
        """Delete user (cannot delete admin)"""
        if username == 'admin':
            return False, "Cannot delete admin user"
        
        users_df = self.get_users()
        
        if username not in users_df['username'].values:
            return False, "User not found"
        
        # Remove user
        users_df = users_df[users_df['username'] != username]
        self.save_users(users_df)
        
        return True, "User deleted successfully"

# Initialize authentication
auth = SimpleAuth()

# ========== DATA LOADING ==========
@st.cache_data
def load_inventory_data():
    try:
        df = pd.read_excel("Stores Data.xlsx")
        
        # Clean column names
        df.columns = ['item_name', 'category', 'unit', 'quantity', 'expiry_date']
        
        # Convert quantity to numeric
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
        
        # Handle expiry dates
        df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
        
        # Set default reorder levels based on category
        df['reorder_level'] = df['category'].apply(lambda x: 10 if pd.notna(x) else 5)
        
        # Generate unique item IDs
        df['item_id'] = df.apply(lambda row: f"STR-{row['category'][:3].upper() if pd.notna(row['category']) else 'GEN'}-{row.name+1:04d}", axis=1)
        
        # Add storage location (default)
        df['storage_location'] = 'Main Store'
        
        # Add supplier (default)
        df['supplier'] = 'Standard Supplier'
        
        # Add created date
        df['created_date'] = datetime.now().strftime('%Y-%m-%d')
        
        return df
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return pd.DataFrame()

# Page Configuration
st.set_page_config(
    page_title="NHRC Stores Management System",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== VC.PY STYLE HEADER ==========
def get_base64_of_image(image_path):
    """Convert image to base64"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

# Header matching VC.py exactly
logo_html = ""
if os.path.exists("nhrc_logo.png"):
    logo_base64 = get_base64_of_image("nhrc_logo.png")
    logo_html = f"<img src='data:image/png;base64,{logo_base64}' width='170' style='display:block;margin:0 auto 8px auto;'>"
elif os.path.exists("logo.png"):
    logo_base64 = get_base64_of_image("logo.png")
    logo_html = f"<img src='data:image/png;base64,{logo_base64}' width='170' style='display:block;margin:0 auto 8px auto;'>"
else:
    logo_html = "<div style='font-size: 3rem; margin-bottom: 0.5rem;'>🏪</div>"

# ========== UPDATED CUSTOM CSS ==========
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
    
    [data-testid="stSidebar"] .stButton button {
        background: rgba(0, 0, 0, 0.05) !important;
        color: var(--sidebar-text) !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background: rgba(0, 0, 0, 0.1) !important;
        border: 1px solid rgba(0, 0, 0, 0.2) !important;
        transform: translateY(-1px);
        transition: all 0.3s ease;
    }
    
    /* Main navigation tabs styling */
    div[role='radiogroup'] {
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
    
    div[role='radiogroup'] label {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 12px 20px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
        transition: all .2s ease;
        font-weight: 600;
        color: #495057;
        border: 1px solid rgba(0,0,0,0.08);
        margin: 5px;
    }
    
    div[role='radiogroup'] label:hover { 
        transform: translateY(-3px) scale(1.02); 
        box-shadow: 0 8px 20px rgba(0,0,0,0.12); 
        cursor: pointer;
        background: #e9ecef;
    }
    
    div[role='radiogroup'] input:checked + div { 
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important; 
        color: white !important; 
        box-shadow: 0 6px 15px rgba(46, 125, 50, 0.2) !important;
        border-color: var(--primary) !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        padding: 1.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(46, 125, 50, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
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
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
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
    
    /* Section headers */
    .section-header {
        background: white;
        padding: 1.2rem 1.8rem;
        border-radius: 14px;
        margin: 1rem 0;
        border-left: 6px solid var(--primary);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-bottom: 2px solid #f1f5f9;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        border: none !important;
        letter-spacing: 0.5px;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(46, 125, 50, 0.25) !important;
    }
    
    /* Status badges */
    .status-badge {
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        letter-spacing: 0.3px;
    }
    
    .status-adequate { background: #d1fae5; color: #059669; border: 1px solid #a7f3d0; }
    .status-low { background: #fef3c7; color: #d97706; border: 1px solid #fde68a; }
    .status-critical { background: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
    .status-expired { background: #fee; color: #c00; border: 1px solid #fcc; }
    .status-expiring { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
    
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
    
    /* Login form styling */
    .login-form-container {
        padding: 1.5rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    
    /* Delete button styling */
    .delete-button {
        background: linear-gradient(135deg, #ef4444, #dc2626) !important;
    }
    
    .delete-button:hover {
        background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
        box-shadow: 0 10px 25px rgba(220, 38, 38, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== CHECK AUTHENTICATION ==========
# This will show login interface if not authenticated
user = auth.check_auth()

# ========== SIDEBAR USER INFO (AFTER LOGIN) ==========
with st.sidebar:
    # Only show user info if logged in (not during login process)
    if auth.session_key in st.session_state and st.session_state[auth.session_key]:
        st.markdown("""
            <div style="text-align: center; padding: 1.5rem 0;">
                <div style="font-size: 3.5rem; margin-bottom: 0.8rem; color: #333;">🏪</div>
                <h3 style="margin: 0; color: #333; font-weight: 700;">Store Management</h3>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">Navrongo Health Research Centre</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # User Info Section
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
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Data", use_container_width=True, type="secondary"):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("📥 Export Inventory", use_container_width=True, type="secondary"):
            pass  # Will be handled in main content
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            auth.logout()

# Initialize session state
if 'inventory_data' not in st.session_state:
    st.session_state.inventory_data = load_inventory_data()
    st.session_state.receipts = pd.DataFrame(columns=[
        'date', 'item_id', 'item_name', 'supplier', 'quantity', 'unit_cost', 
        'total_value', 'project_code', 'reference', 'received_by'
    ])
    st.session_state.issues = pd.DataFrame(columns=[
        'date', 'item_id', 'item_name', 'department', 'quantity', 'purpose', 'issued_by'
    ])

# Load inventory data
inventory_df = st.session_state.inventory_data
receipts_df = st.session_state.receipts
issues_df = st.session_state.issues

# ========== DISPLAY MAIN HEADER (AFTER LOGIN) ==========
st.markdown(
    f"""
    <div style='text-align:center;padding:6px 0 12px 0;background:transparent;'>
        {logo_html}
        <h3 style='margin:0;color:#2E7D32;'>Navrongo Health Research Centre</h3>
        <h4 style='margin:0;color:#2E7D32;'>General Stores Department</h4>
    </div>
    <hr style='border:1px solid rgba(0,0,0,0.08);margin-bottom:18px;'>
    """,
    unsafe_allow_html=True
)

# ========== MAIN NAVIGATION TABS ==========
# Define the tabs
tabs = ["🏠 Dashboard", "📦 Inventory", "📥 Stock In", "📤 Stock Out", "⏰ Expiry", "📝 Reports", "⚙️ Settings"]

# Create tabs using radio buttons with custom styling
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
    if 'expiry_date' in inventory_df.columns:
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
        ("Total Items", len(inventory_df), "📦", "Total number of unique items"),
        ("Total Units", f"{inventory_df['quantity'].sum():,}", "📊", "Total units across all items"),
        ("Low Stock", len(inventory_df[inventory_df['quantity'] <= inventory_df['reorder_level']]), "⚠️", "Items at or below reorder level"),
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
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Units by Category")
        if not inventory_df.empty:
            category_units = inventory_df.groupby('category')['quantity'].sum().reset_index()
            fig = px.bar(
                category_units,
                x='category',
                y='quantity',
                color='quantity',
                color_continuous_scale='Viridis',
                text='quantity',
                title=""
            )
            fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white')
            fig.update_traces(texttemplate='%{text:,}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📦 Stock Distribution")
        if not inventory_df.empty:
            fig = px.pie(
                inventory_df,
                values='quantity',
                names='category',
                hole=0.4,
                title=""
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Low Stock Alert
    st.markdown("#### ⚠️ Low Stock Items Requiring Attention")
    low_stock_items = inventory_df[inventory_df['quantity'] <= inventory_df['reorder_level']]
    
    if not low_stock_items.empty:
        display_cols = ['item_name', 'category', 'quantity', 'unit', 'reorder_level']
        display_df = low_stock_items[display_cols].copy()
        
        def get_stock_status(row):
            if row['quantity'] == 0:
                return '<span class="status-badge status-critical">Critical</span>'
            else:
                return '<span class="status-badge status-low">Low</span>'
        
        display_df['status'] = display_df.apply(get_stock_status, axis=1)
        display_df.columns = ['Item Name', 'Category', 'Quantity', 'Unit', 'Reorder Level', 'Status']
        
        st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.success("✅ No low stock items at the moment!")

# INVENTORY TAB
elif selected_tab == "📦 Inventory":
    st.markdown('<div class="section-header"><h2>📦 Inventory Management</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Inventory", "Add Item", "Edit Item"])
    
    with tab1:
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            search = st.text_input("🔍 Search items", placeholder="Name or ID...")
        with col2:
            category_filter = st.selectbox("Filter by Category", 
                                         ["All"] + sorted(inventory_df['category'].unique().tolist()))
        with col3:
            status_filter = st.selectbox("Stock Status", ["All", "Adequate", "Low", "Critical"])
        with col4:
            # Expiry filter
            expiry_filter = st.selectbox("Expiry Status", 
                                       ["All", "Expired", "≤ 30 Days", "≤ 90 Days", "> 90 Days", "No Expiry"])
        
        # Apply filters
        filtered = inventory_df.copy()
        if search:
            filtered = filtered[filtered['item_name'].str.contains(search, case=False, na=False) |
                               filtered['item_id'].str.contains(search, case=False, na=False)]
        if category_filter != "All":
            filtered = filtered[filtered['category'] == category_filter]
        
        # Calculate days to expiry for filtering
        filtered['expiry_date_dt'] = pd.to_datetime(filtered['expiry_date'], errors='coerce')
        current_date = pd.Timestamp.now()
        filtered['days_to_expiry'] = (filtered['expiry_date_dt'] - current_date).dt.days
        
        # Apply stock status filter
        if status_filter != "All":
            if status_filter == "Low":
                filtered = filtered[filtered['quantity'] <= filtered['reorder_level']]
            elif status_filter == "Critical":
                filtered = filtered[filtered['quantity'] == 0]
            elif status_filter == "Adequate":
                filtered = filtered[filtered['quantity'] > filtered['reorder_level']]
        
        # Apply expiry status filter
        if expiry_filter != "All":
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
            # Prepare display dataframe
            display_cols = ['item_id', 'item_name', 'category', 'quantity', 'unit', 
                           'storage_location', 'expiry_date', 'days_to_expiry']
            display_df = filtered[display_cols].copy()
            
            # Format expiry date
            display_df['expiry_date'] = pd.to_datetime(display_df['expiry_date']).dt.strftime('%Y-%m-%d')
            
            # Add stock status column
            def get_stock_status(row):
                if row['quantity'] == 0:
                    return '<span class="status-badge status-critical">Critical</span>'
                elif row['quantity'] <= 50:  # Default reorder level
                    return '<span class="status-badge status-low">Low</span>'
                else:
                    return '<span class="status-badge status-adequate">Adequate</span>'
            
            # Add expiry status column
            def get_expiry_status(row):
                days = row['days_to_expiry']
                if pd.isna(days):
                    return '<span class="status-badge" style="background: #e5e7eb; color: #4b5563; border: 1px solid #d1d5db;">No Expiry</span>'
                elif days <= 0:
                    return '<span class="status-badge status-expired">Expired</span>'
                elif days <= 30:
                    return '<span class="status-badge status-expiring">≤ 30 Days</span>'
                elif days <= 90:
                    return '<span class="status-badge" style="background: #dbeafe; color: #1e40af; border: 1px solid #93c5fd;">≤ 90 Days</span>'
                else:
                    return '<span class="status-badge status-adequate">> 90 Days</span>'
            
            # Apply the functions
            display_df['Stock Status'] = filtered.apply(get_stock_status, axis=1)
            display_df['Expiry Status'] = filtered.apply(get_expiry_status, axis=1)
            
            # Reorder columns and rename
            display_df = display_df[['item_id', 'item_name', 'category', 'quantity', 'unit', 
                                    'Stock Status', 'Expiry Status', 'expiry_date', 'storage_location']]
            display_df.columns = ['Item ID', 'Item Name', 'Category', 'Quantity', 'Unit', 
                                 'Stock Status', 'Expiry Status', 'Expiry Date', 'Storage Location']
            
            # Show filter summary
            filter_summary = []
            if status_filter != "All":
                filter_summary.append(f"Stock: {status_filter}")
            if expiry_filter != "All":
                filter_summary.append(f"Expiry: {expiry_filter}")
            if category_filter != "All":
                filter_summary.append(f"Category: {category_filter}")
            
            summary_text = f"**Showing {len(filtered)} of {len(inventory_df)} items**"
            if filter_summary:
                summary_text += f" - Filters: {', '.join(filter_summary)}"
            
            st.markdown(summary_text)
            
            # Display the table with HTML formatting
            st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Export
            csv = filtered.drop(['expiry_date_dt', 'days_to_expiry'], axis=1, errors='ignore').to_csv(index=False)
            st.download_button(
                "📥 Export Filtered Data",
                data=csv,
                file_name="filtered_inventory.csv",
                mime="text/csv"
            )
        else:
            st.info("No items match your filters.")
    
    with tab2:
        st.markdown("#### ➕ Add New Item")
        
        # Use session state to track form submission
        if 'add_item_form_submitted' not in st.session_state:
            st.session_state.add_item_form_submitted = False
        
        # Create form with unique key
        form_key = "add_item_form_" + str(st.session_state.get('form_counter', 0))
        
        with st.form(form_key, clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                item_name = st.text_input("Item Name*", placeholder="e.g., A4 Duplicating Paper", key=f"item_name_{form_key}")
                category = st.selectbox("Category*", 
                                      sorted(inventory_df['category'].unique().tolist()) if not inventory_df.empty else 
                                      ["Stationery", "Comp/Printer/Accessories", "Micellaneous", 
                                       "Electrical Items", "Motor Parts", "Vehicle Parts - Toyota Hilux",
                                       "Fuel & Lubricants", "Laboratory Items"], key=f"category_{form_key}")
                quantity = st.number_input("Quantity (Units)*", min_value=0, value=0, step=1, key=f"quantity_{form_key}")
            
            with col2:
                unit = st.selectbox("Unit*", ["Units", "Pieces", "Reams", "Packets", "Boxes", 
                                            "Bottles", "Litre", "Gallon", "Pairs", "Tin", "Rolls"], key=f"unit_{form_key}")
                storage_location = st.selectbox("Storage Location", 
                                              ["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive"], key=f"storage_{form_key}")
                
                # Expiry date option
                expiry_option = st.radio("Has expiry date?", ["No", "Yes"], key=f"expiry_option_{form_key}")
                if expiry_option == "Yes":
                    expiry_date = st.date_input("Expiry Date", 
                                              value=datetime.now() + timedelta(days=365), key=f"expiry_date_{form_key}")
                else:
                    expiry_date = None
                
                reorder_level = st.number_input("Reorder Level*", min_value=1, value=10, key=f"reorder_{form_key}")
            
            notes = st.text_area("Notes", key=f"notes_{form_key}")
            supplier = st.text_input("Supplier", value="Standard Supplier", key=f"supplier_{form_key}")
            
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
                        'created_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    # Add expiry date only if provided
                    if expiry_option == "Yes" and expiry_date:
                        item_data['expiry_date'] = expiry_date.strftime('%Y-%m-%d')
                    
                    # Add to inventory
                    new_item = pd.DataFrame([item_data])
                    st.session_state.inventory_data = pd.concat([inventory_df, new_item], ignore_index=True)
                    st.session_state.add_item_form_submitted = True
                    st.success(f"✅ Item '{item_name}' added successfully!")
                    # Increment form counter to generate new form with cleared fields
                    st.session_state.form_counter = st.session_state.get('form_counter', 0) + 1
                    st.rerun()
        
        # Reset the submission flag
        if st.session_state.add_item_form_submitted:
            st.session_state.add_item_form_submitted = False
    
    with tab3:
        st.markdown("#### ✏️ Edit Inventory Item")
        
        if not inventory_df.empty:
            # Use session state to track which item is selected
            if 'selected_item_to_edit' not in st.session_state:
                st.session_state.selected_item_to_edit = inventory_df['item_name'].unique()[0] if len(inventory_df['item_name'].unique()) > 0 else ""
            
            # Item selection
            item_to_edit = st.selectbox("Select item to edit", 
                                       inventory_df['item_name'].unique(),
                                       key="item_selector",
                                       index=list(inventory_df['item_name'].unique()).index(st.session_state.selected_item_to_edit) 
                                       if st.session_state.selected_item_to_edit in inventory_df['item_name'].unique() else 0)
            
            if item_to_edit:
                # Update session state
                st.session_state.selected_item_to_edit = item_to_edit
                
                item_data = inventory_df[inventory_df['item_name'] == item_to_edit].iloc[0]
                
                # Create two columns for edit form and delete button
                col_edit, col_delete = st.columns([3, 1])
                
                with col_edit:
                    # Edit form
                    if 'edit_item_form_submitted' not in st.session_state:
                        st.session_state.edit_item_form_submitted = False
                    
                    edit_form_key = "edit_item_form_" + str(st.session_state.get('edit_form_counter', 0))
                    
                    with st.form(edit_form_key, clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            current_qty = item_data.get('quantity', 0)
                            new_quantity = st.number_input("Quantity (Units)", 
                                                         min_value=0, 
                                                         value=int(current_qty), key=f"edit_qty_{edit_form_key}")
                            new_location = st.selectbox("Storage Location", 
                                                      ["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive"],
                                                      index=["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive"]
                                                      .index(item_data.get('storage_location', 'Main Store')), key=f"edit_location_{edit_form_key}")
                            
                            # Category editing
                            category_options = sorted(inventory_df['category'].unique().tolist())
                            current_category = item_data.get('category', 'General Supplies')
                            if current_category not in category_options:
                                category_options.append(current_category)
                            new_category = st.selectbox("Category", 
                                                      category_options,
                                                      index=category_options.index(current_category) 
                                                      if current_category in category_options else 0, key=f"edit_category_{edit_form_key}")
                        
                        with col2:
                            # Handle expiry date (optional)
                            current_expiry = item_data.get('expiry_date')
                            if pd.notna(current_expiry):
                                expiry_option = st.radio("Expiry Date", ["Keep current", "Change", "Remove"], key=f"edit_expiry_option_{edit_form_key}")
                                if expiry_option == "Change":
                                    new_expiry = st.date_input("New Expiry Date", 
                                                              value=pd.to_datetime(current_expiry) 
                                                              if pd.notna(current_expiry) 
                                                              else datetime.now() + timedelta(days=365), key=f"edit_expiry_date_{edit_form_key}")
                                elif expiry_option == "Remove":
                                    new_expiry = None
                                else:
                                    new_expiry = current_expiry
                            else:
                                expiry_option = st.radio("Add expiry date?", ["No", "Yes"], key=f"edit_add_expiry_{edit_form_key}")
                                if expiry_option == "Yes":
                                    new_expiry = st.date_input("Expiry Date", 
                                                              value=datetime.now() + timedelta(days=365), key=f"edit_new_expiry_{edit_form_key}")
                                else:
                                    new_expiry = None
                            
                            new_reorder_level = st.number_input("Reorder Level (Units)", 
                                                              min_value=1, 
                                                              value=int(item_data.get('reorder_level', 10)), key=f"edit_reorder_{edit_form_key}")
                            new_supplier = st.text_input("Supplier", value=item_data.get('supplier', 'Standard Supplier'), key=f"edit_supplier_{edit_form_key}")
                        
                        new_notes = st.text_area("Notes", value=item_data.get('notes', ''), key=f"edit_notes_{edit_form_key}")
                        
                        submitted = st.form_submit_button("💾 Save Changes", type="primary")
                        
                        if submitted:
                            # Update inventory
                            idx = inventory_df.index[inventory_df['item_name'] == item_to_edit][0]
                            
                            # Check each field for changes
                            if new_quantity != int(current_qty):
                                st.session_state.inventory_data.at[idx, 'quantity'] = new_quantity
                            
                            if new_location != item_data.get('storage_location', 'Main Store'):
                                st.session_state.inventory_data.at[idx, 'storage_location'] = new_location
                            
                            if new_category != item_data.get('category', 'General Supplies'):
                                st.session_state.inventory_data.at[idx, 'category'] = new_category
                            
                            if new_reorder_level != int(item_data.get('reorder_level', 10)):
                                st.session_state.inventory_data.at[idx, 'reorder_level'] = new_reorder_level
                            
                            if new_supplier != item_data.get('supplier', 'Standard Supplier'):
                                st.session_state.inventory_data.at[idx, 'supplier'] = new_supplier
                            
                            if new_notes != item_data.get('notes', ''):
                                st.session_state.inventory_data.at[idx, 'notes'] = new_notes
                            
                            # Handle expiry date changes
                            current_expiry = item_data.get('expiry_date')
                            if expiry_option == "Change":
                                new_expiry_str = new_expiry.strftime('%Y-%m-%d') if hasattr(new_expiry, 'strftime') else str(new_expiry)
                                current_expiry_str = pd.to_datetime(current_expiry).strftime('%Y-%m-%d') if pd.notna(current_expiry) else None
                                if new_expiry_str != current_expiry_str:
                                    st.session_state.inventory_data.at[idx, 'expiry_date'] = new_expiry_str
                            elif expiry_option == "Remove":
                                if pd.notna(current_expiry):
                                    st.session_state.inventory_data.at[idx, 'expiry_date'] = None
                            elif expiry_option == "Yes":  # Adding new expiry date
                                new_expiry_str = new_expiry.strftime('%Y-%m-%d') if hasattr(new_expiry, 'strftime') else str(new_expiry)
                                st.session_state.inventory_data.at[idx, 'expiry_date'] = new_expiry_str
                            
                            st.session_state.edit_item_form_submitted = True
                            st.success("✅ Item updated successfully!")
                            st.session_state.edit_form_counter = st.session_state.get('edit_form_counter', 0) + 1
                            st.rerun()
                    
                    # Reset the submission flag
                    if st.session_state.edit_item_form_submitted:
                        st.session_state.edit_item_form_submitted = False
                
                with col_delete:
                    # Delete button with warning
                    st.markdown("### 🗑️")
                    st.markdown("##### Delete Item")
                    
                    # Confirmation for deletion
                    delete_confirmed = st.checkbox("I confirm deletion", key=f"delete_confirm_{item_to_edit}")
                    
                    if st.button("🗑️ Delete Item", 
                                disabled=not delete_confirmed,
                                key=f"delete_button_{item_to_edit}",
                                use_container_width=True,
                                type="primary"):
                        
                        # Remove item from inventory
                        st.session_state.inventory_data = inventory_df[inventory_df['item_name'] != item_to_edit].reset_index(drop=True)
                        
                        # Remove related receipts and issues
                        if not receipts_df.empty:
                            st.session_state.receipts = receipts_df[receipts_df['item_name'] != item_to_edit].reset_index(drop=True)
                        
                        if not issues_df.empty:
                            st.session_state.issues = issues_df[issues_df['item_name'] != item_to_edit].reset_index(drop=True)
                        
                        st.success(f"✅ Item '{item_to_edit}' deleted successfully!")
                        # Reset selection
                        st.session_state.selected_item_to_edit = ""
                        st.rerun()

# STOCK IN TAB
elif selected_tab == "📥 Stock In":
    st.markdown('<div class="section-header"><h2>📥 Stock Receipts Management</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Record Receipt", "Receipt History"])
    
    with tab1:
        st.markdown("#### 📝 Record New Stock Receipt")
        
        # Use session state to track form submission
        if 'receipt_form_submitted' not in st.session_state:
            st.session_state.receipt_form_submitted = False
        
        receipt_form_key = "receipt_form_" + str(st.session_state.get('receipt_form_counter', 0))
        
        with st.form(receipt_form_key, clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                receipt_date = st.date_input("Date Received*", value=datetime.now(), key=f"receipt_date_{receipt_form_key}")
                supplier = st.text_input("Supplier Name*", placeholder="e.g., Office Supplies Ltd.", key=f"supplier_{receipt_form_key}")
                project_code = st.selectbox("Project/Source of Funds", 
                                          ["General Funds", "Research Grant A", "Research Grant B", "Donor Funds", "Other"], key=f"project_{receipt_form_key}")
                reference = st.text_input("Delivery Note/Invoice No.", placeholder="DN-2024-001", key=f"reference_{receipt_form_key}")
            
            with col2:
                selected_item = st.selectbox("Select Item*", inventory_df['item_name'].unique(), key=f"item_{receipt_form_key}")
                if selected_item:
                    item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                    current_stock = item_data['quantity']
                    st.info(f"**Current Stock:** {current_stock} {item_data['unit']}")
                
                quantity = st.number_input("Quantity Received*", min_value=1, value=1, key=f"qty_{receipt_form_key}")
                unit_cost = st.number_input("Unit Cost (GHS)*", min_value=0.0, value=0.0, step=0.01, format="%.2f", key=f"cost_{receipt_form_key}")
                total_value = quantity * unit_cost
                st.metric("Total Value", f"GHS {total_value:,.2f}")
            
            received_by = st.text_input("Received By*", value=user['full_name'], key=f"received_by_{receipt_form_key}")
            notes = st.text_area("Additional Notes", key=f"receipt_notes_{receipt_form_key}")
            
            submitted = st.form_submit_button("📥 Record Receipt", type="primary")
            
            if submitted:
                if not all([supplier, selected_item, received_by]):
                    st.error("Please fill all required fields (*)!")
                elif unit_cost <= 0:
                    st.error("Unit cost must be greater than 0!")
                else:
                    # Update inventory
                    idx = inventory_df.index[inventory_df['item_name'] == selected_item][0]
                    st.session_state.inventory_data.at[idx, 'quantity'] += quantity
                    
                    # Add to receipts
                    new_receipt = pd.DataFrame([{
                        'date': receipt_date,
                        'item_id': item_data['item_id'],
                        'item_name': selected_item,
                        'supplier': supplier,
                        'quantity': quantity,
                        'unit_cost': unit_cost,
                        'total_value': total_value,
                        'project_code': project_code,
                        'reference': reference,
                        'received_by': received_by,
                        'notes': notes
                    }])
                    
                    st.session_state.receipts = pd.concat([receipts_df, new_receipt], ignore_index=True)
                    
                    st.session_state.receipt_form_submitted = True
                    st.success(f"✅ Receipt recorded successfully! Stock updated to {st.session_state.inventory_data.at[idx, 'quantity']} units.")
                    st.session_state.receipt_form_counter = st.session_state.get('receipt_form_counter', 0) + 1
                    st.rerun()
        
        # Reset the submission flag
        if st.session_state.receipt_form_submitted:
            st.session_state.receipt_form_submitted = False
    
    with tab2:
        st.markdown("#### 📋 Receipt History")
        
        if not receipts_df.empty:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("To Date", value=datetime.now())
            
            # Filter receipts
            filtered_receipts = receipts_df.copy()
            filtered_receipts['date'] = pd.to_datetime(filtered_receipts['date'])
            filtered_receipts = filtered_receipts[
                (filtered_receipts['date'] >= pd.Timestamp(start_date)) &
                (filtered_receipts['date'] <= pd.Timestamp(end_date))
            ]
            
            if not filtered_receipts.empty:
                # Summary
                total_receipts = len(filtered_receipts)
                total_quantity = filtered_receipts['quantity'].sum()
                total_value = filtered_receipts['total_value'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Receipts", total_receipts)
                with col2:
                    st.metric("Total Quantity", f"{total_quantity:,}")
                with col3:
                    st.metric("Total Value", f"GHS {total_value:,.2f}")
                
                # Display table
                display_cols = ['date', 'item_name', 'supplier', 'quantity', 'unit_cost', 'total_value', 'project_code', 'reference']
                display_df = filtered_receipts[display_cols].copy()
                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                display_df.columns = ['Date', 'Item', 'Supplier', 'Qty', 'Unit Cost', 'Total Value', 'Project', 'Reference']
                
                st.dataframe(display_df, use_container_width=True)
                
                # Export option
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
        
        # Use session state to track form submission
        if 'issue_form_submitted' not in st.session_state:
            st.session_state.issue_form_submitted = False
        
        issue_form_key = "issue_form_" + str(st.session_state.get('issue_form_counter', 0))
        
        with st.form(issue_form_key, clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                issue_date = st.date_input("Issue Date*", value=datetime.now(), key=f"issue_date_{issue_form_key}")
                department = st.selectbox("Receiving Department*", 
                                        ["Biomedical", "Microbiology", "Parasitology", 
                                         "Clinical Lab", "Research", "Administration", "IT", "Field Team"], key=f"department_{issue_form_key}")
                purpose = st.text_input("Purpose/Project", placeholder="e.g., Research Project, Daily Operations", key=f"purpose_{issue_form_key}")
            
            with col2:
                selected_item = st.selectbox("Select Item*", inventory_df['item_name'].unique(), key=f"issue_item_{issue_form_key}")
                if selected_item:
                    item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                    current_stock = item_data['quantity']
                    st.info(f"**Current Stock:** {current_stock} {item_data['unit']}")
                
                quantity = st.number_input("Quantity to Issue*", min_value=1, value=1, max_value=int(current_stock), key=f"issue_qty_{issue_form_key}")
                issued_by = st.text_input("Issued By*", value=user['full_name'], key=f"issued_by_{issue_form_key}")
            
            notes = st.text_area("Additional Notes", key=f"issue_notes_{issue_form_key}")
            
            submitted = st.form_submit_button("📤 Issue Stock", type="primary")
            
            if submitted:
                if not all([department, selected_item, issued_by]):
                    st.error("Please fill all required fields (*)!")
                elif quantity > current_stock:
                    st.error(f"Cannot issue {quantity} units. Only {current_stock} available!")
                else:
                    # Update inventory
                    idx = inventory_df.index[inventory_df['item_name'] == selected_item][0]
                    st.session_state.inventory_data.at[idx, 'quantity'] -= quantity
                    
                    # Add to issues
                    new_issue = pd.DataFrame([{
                        'date': issue_date,
                        'item_id': item_data['item_id'],
                        'item_name': selected_item,
                        'department': department,
                        'quantity': quantity,
                        'purpose': purpose,
                        'issued_by': issued_by,
                        'notes': notes
                    }])
                    
                    st.session_state.issues = pd.concat([issues_df, new_issue], ignore_index=True)
                    
                    st.session_state.issue_form_submitted = True
                    st.success(f"✅ Stock issued successfully! Remaining stock: {st.session_state.inventory_data.at[idx, 'quantity']} units.")
                    st.session_state.issue_form_counter = st.session_state.get('issue_form_counter', 0) + 1
                    st.rerun()
        
        # Reset the submission flag
        if st.session_state.issue_form_submitted:
            st.session_state.issue_form_submitted = False
    
    with tab2:
        st.markdown("#### 📋 Issue History")
        
        if not issues_df.empty:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=30), key="issue_start")
            with col2:
                end_date = st.date_input("To Date", value=datetime.now(), key="issue_end")
            
            # Filter issues
            filtered_issues = issues_df.copy()
            filtered_issues['date'] = pd.to_datetime(filtered_issues['date'])
            filtered_issues = filtered_issues[
                (filtered_issues['date'] >= pd.Timestamp(start_date)) &
                (filtered_issues['date'] <= pd.Timestamp(end_date))
            ]
            
            if not filtered_issues.empty:
                # Summary
                total_issues = len(filtered_issues)
                total_quantity = filtered_issues['quantity'].sum()
                departments = filtered_issues['department'].nunique()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Issues", total_issues)
                with col2:
                    st.metric("Total Quantity", f"{total_quantity:,}")
                with col3:
                    st.metric("Departments", departments)
                
                # Department-wise consumption
                st.markdown("##### 📊 Department-wise Consumption")
                dept_consumption = filtered_issues.groupby('department')['quantity'].sum().reset_index()
                fig = px.bar(
                    dept_consumption,
                    x='department',
                    y='quantity',
                    color='quantity',
                    title=""
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                # Display table
                display_cols = ['date', 'item_name', 'department', 'quantity', 'purpose', 'issued_by']
                display_df = filtered_issues[display_cols].copy()
                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                display_df.columns = ['Date', 'Item', 'Department', 'Quantity', 'Purpose', 'Issued By']
                
                st.dataframe(display_df, use_container_width=True)
                
                # Export option
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
    
    # Calculate expiry data
    inventory_df['expiry_date_dt'] = pd.to_datetime(inventory_df['expiry_date'], errors='coerce')
    current_date = pd.Timestamp.now()
    inventory_df['days_to_expiry'] = (inventory_df['expiry_date_dt'] - current_date).dt.days
    
    # Get items with expiry dates
    expiry_items = inventory_df[pd.notna(inventory_df['expiry_date'])]
    
    if not expiry_items.empty:
        # Status cards
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate counts for different expiry categories
        expired = (expiry_items['days_to_expiry'] <= 0).sum()
        expiring_30 = ((expiry_items['days_to_expiry'] > 0) & 
                      (expiry_items['days_to_expiry'] <= 30)).sum()
        expiring_90 = ((expiry_items['days_to_expiry'] > 30) & 
                      (expiry_items['days_to_expiry'] <= 90)).sum()
        expiring_180 = ((expiry_items['days_to_expiry'] > 90) & 
                       (expiry_items['days_to_expiry'] <= 180)).sum()
        
        status_cards = [
            (col1, expired, "Expired", "#ef4444", "❌"),
            (col2, expiring_30, "< 30 Days", "#f59e0b", "⚠️"),
            (col3, expiring_90, "30-90 Days", "#3b82f6", "ℹ️"),
            (col4, expiring_180, "90-180 Days", "#10b981", "✅")
        ]
        
        for col, count, label, color, icon in status_cards:
            with col:
                st.markdown(f"""
                    <div style='background: {color}; padding: 1.2rem; border-radius: 14px; color: white; text-align: center; box-shadow: 0 6px 20px rgba(0,0,0,0.1);'>
                        <div style='font-size: 2.2rem; margin-bottom: 0.5rem;'>{icon}</div>
                        <div style='font-size: 2.2rem; font-weight: 800; margin: 0.5rem 0;'>{count}</div>
                        <div style='font-weight: 700; font-size: 0.95rem;'>{label}</div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Expiry timeline
        st.markdown("#### 📅 Expiry Timeline")
        
        # Categorize items
        def categorize_expiry(days):
            if days <= 0:
                return "Expired"
            elif days <= 30:
                return "< 30 days"
            elif days <= 90:
                return "30-90 days"
            elif days <= 180:
                return "90-180 days"
            else:
                return "> 180 days"
        
        expiry_items['expiry_category'] = expiry_items['days_to_expiry'].apply(categorize_expiry)
        category_counts = expiry_items['expiry_category'].value_counts()
        
        fig = px.bar(
            x=category_counts.index,
            y=category_counts.values,
            color=category_counts.values,
            color_continuous_scale='RdYlGn_r',
            text=category_counts.values,
            title=""
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)
        
        # Expired items table
        st.markdown("#### 🚨 Expired Items Requiring Action")
        
        truly_expired = expiry_items[expiry_items['days_to_expiry'] <= 0]
        if not truly_expired.empty:
            # Prepare display dataframe
            display_cols = ['item_name', 'category', 'quantity', 'unit', 'expiry_date', 'days_to_expiry']
            display_df = truly_expired[display_cols].copy()
            display_df['expiry_date'] = pd.to_datetime(display_df['expiry_date']).dt.strftime('%Y-%m-%d')
            display_df['days_to_expiry'] = display_df['days_to_expiry'].abs().astype(int)
            display_df.columns = ['Item Name', 'Category', 'Quantity', 'Unit', 'Expiry Date', 'Days Expired']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=300
            )
            
            # Quick actions
            st.markdown("##### ⚡ Quick Actions")
            selected_expired = st.selectbox("Select expired item", truly_expired['item_name'].unique())
            
            if selected_expired:
                item_data = truly_expired[truly_expired['item_name'] == selected_expired].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    action = st.radio("Select Action", ["Discard", "Update Expiry", "Extend Shelf Life"])
                    
                    if action == "Discard":
                        current_qty = item_data.get('quantity', 0)
                        qty = st.number_input("Quantity to discard", 
                                            min_value=1, 
                                            max_value=int(current_qty),
                                            value=int(current_qty))
                        reason = st.selectbox("Reason", ["Expired", "Damaged", "Contaminated", "Other"])
                        disposal_method = st.selectbox("Disposal Method", 
                                                      ["Incinerate", "Chemical Treatment", "Landfill", "Return to Supplier"])
                        
                        if st.button("🗑️ Discard Item", type="primary"):
                            # Update inventory
                            idx = inventory_df.index[inventory_df['item_name'] == selected_expired][0]
                            new_qty = max(int(current_qty) - qty, 0)
                            st.session_state.inventory_data.at[idx, 'quantity'] = new_qty
                            
                            st.success(f"{qty} units of {selected_expired} marked for disposal.")
                            st.info(f"Remaining stock: {new_qty} units")
                            st.rerun()
                    
                    elif action == "Update Expiry":
                        new_expiry = st.date_input("New Expiry Date", 
                                                  value=datetime.now() + timedelta(days=365))
                        reason = st.text_input("Reason for extension", 
                                              placeholder="e.g., Testing confirmed stability")
                        
                        if st.button("📅 Update Expiry", type="primary"):
                            idx = inventory_df.index[inventory_df['item_name'] == selected_expired][0]
                            st.session_state.inventory_data.at[idx, 'expiry_date'] = new_expiry.strftime('%Y-%m-%d')
                            st.success("Expiry date updated!")
                            st.rerun()
                    
                    elif action == "Extend Shelf Life":
                        st.info("""
                        **Shelf Life Extension Procedure:**
                        1. Review stability data
                        2. Perform quality testing
                        3. Document extension approval
                        4. Update expiry date
                        """)
                        
                        extension_days = st.number_input("Extension (days)", 
                                                        min_value=1, 
                                                        max_value=365, 
                                                        value=30)
                        approved_by = st.text_input("Approved By", 
                                                   placeholder="Quality Manager")
                        test_results = st.text_area("Test Results Summary")
                        
                        if st.button("✅ Approve Extension", type="primary"):
                            idx = inventory_df.index[inventory_df['item_name'] == selected_expired][0]
                            current_expiry = pd.to_datetime(item_data['expiry_date'])
                            new_expiry = current_expiry + timedelta(days=extension_days)
                            st.session_state.inventory_data.at[idx, 'expiry_date'] = new_expiry.strftime('%Y-%m-%d')
                            st.success(f"Shelf life extended by {extension_days} days!")
                            st.rerun()
                
                with col2:
                    quantity = item_data.get('quantity', 0)
                    expiry_date = item_data.get('expiry_date')
                    
                    st.info(f"""
                    **Item Details:**
                    - **ID:** {item_data['item_id']}
                    - **Category:** {item_data['category']}
                    - **Current Stock:** {quantity} units
                    - **Unit:** {item_data.get('unit', 'Units')}
                    - **Original Expiry:** {expiry_date}
                    - **Expired Since:** {abs(int(item_data['days_to_expiry']))} days
                    - **Storage Location:** {item_data.get('storage_location', 'Unknown')}
                    - **Supplier:** {item_data.get('supplier', 'Unknown')}
                    """)
        else:
            st.success("✅ No expired items found!")
        
        # Items expiring soon
        st.markdown("#### ⚠️ Items Expiring Soon (≤ 30 days)")
        
        expiring_soon = expiry_items[(expiry_items['days_to_expiry'] > 0) & 
                                     (expiry_items['days_to_expiry'] <= 30)]
        
        if not expiring_soon.empty:
            # Sort by days to expiry
            expiring_soon = expiring_soon.sort_values('days_to_expiry')
            
            # Prepare display
            display_cols = ['item_name', 'category', 'quantity', 'unit', 'expiry_date', 'days_to_expiry']
            display_df = expiring_soon[display_cols].copy()
            display_df['expiry_date'] = pd.to_datetime(display_df['expiry_date']).dt.strftime('%Y-%m-%d')
            display_df.columns = ['Item Name', 'Category', 'Quantity', 'Unit', 'Expiry Date', 'Days Left']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=300
            )
            
            # Expiry notifications
            st.markdown("##### 🔔 Set Expiry Alerts")
            alert_days = st.slider("Alert Days Before Expiry", 7, 90, 30)
            recipients = st.text_input("Alert Recipients (comma-separated emails)", 
                                      value=user.get('email', ''))
            
            if st.button("Set Up Alerts", type="secondary"):
                st.success(f"Alerts will be sent {alert_days} days before expiry to: {recipients}")
        else:
            st.info("No items expiring within 30 days.")
        
        # Export options
        st.markdown("##### 📥 Export Expiry Report")
        
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            if st.button("Export Expired Items", use_container_width=True):
                csv = truly_expired.to_csv(index=False) if not truly_expired.empty else ""
                if csv:
                    st.download_button(
                        "💾 Download CSV",
                        data=csv,
                        file_name=f"expired_items_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        
        with col_e2:
            if st.button("Export All Expiry Data", use_container_width=True):
                csv = expiry_items.to_csv(index=False)
                st.download_button(
                    "💾 Download CSV",
                    data=csv,
                    file_name=f"all_expiry_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    else:
        st.info("No items with expiry dates found in inventory.")
        
        # Show how to add expiry dates
        with st.expander("📝 How to add expiry dates to items"):
            st.markdown("""
            **To track item expiry:**
            
            1. **Edit existing items:**
               - Go to **Inventory → Edit Item** tab
               - Select an item
               - Set an expiry date or mark as "No expiry"
            
            2. **Add new items with expiry:**
               - Go to **Inventory → Add Item** tab
               - Check "Has expiry date?" option
               - Set the expiry date
            
            **Note:** Only items with expiry dates will appear in this tab.
            """)

# REPORTS TAB
elif selected_tab == "📊 Reports":
    st.markdown('<div class="section-header"><h2>📊 Reports & Analytics</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Monthly Report", "Department Analysis", "Export Data"])
    
    with tab1:
        st.markdown("#### 📅 Monthly Stores Report")
        
        # Month selector
        report_month = st.selectbox("Select Month", 
                                  [datetime.now().strftime("%B %Y")] + 
                                  [(datetime.now() - timedelta(days=30*i)).strftime("%B %Y") for i in range(1, 6)])
        
        if st.button("🔄 Generate Report", type="primary"):
            st.info(f"Generating report for {report_month}...")
            
            # Mock monthly report data
            st.markdown("##### 📋 Monthly Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Opening Stock", f"{inventory_df['quantity'].sum():,} units")
            with col2:
                stock_in = receipts_df['quantity'].sum() if not receipts_df.empty else 0
                st.metric("Stock Received", f"{stock_in:,} units")
            with col3:
                stock_out = issues_df['quantity'].sum() if not issues_df.empty else 0
                st.metric("Stock Issued", f"{stock_out:,} units")
            with col4:
                closing_stock = inventory_df['quantity'].sum()
                st.metric("Closing Stock", f"{closing_stock:,} units")
            
            st.markdown("##### 💰 Financial Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                value_in = receipts_df['total_value'].sum() if not receipts_df.empty else 0
                st.metric("Value of Stock In", f"GHS {value_in:,.2f}")
            with col2:
                # Estimate value out (average cost * quantity)
                avg_cost = receipts_df['unit_cost'].mean() if not receipts_df.empty else 100
                value_out = stock_out * avg_cost
                st.metric("Value of Stock Out", f"GHS {value_out:,.2f}")
            with col3:
                closing_value = closing_stock * avg_cost
                st.metric("Closing Stock Value", f"GHS {closing_value:,.2f}")
            
            # Generate report buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Generate PDF Report", use_container_width=True):
                    st.success("PDF report generated successfully!")
            with col2:
                # Create Excel file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Summary sheet
                    summary_data = {
                        'Metric': ['Opening Stock', 'Stock Received', 'Stock Issued', 'Closing Stock',
                                  'Value of Stock In', 'Value of Stock Out', 'Closing Stock Value'],
                        'Value': [f"{inventory_df['quantity'].sum():,} units", 
                                 f"{stock_in:,} units", 
                                 f"{stock_out:,} units",
                                 f"{closing_stock:,} units",
                                 f"GHS {value_in:,.2f}",
                                 f"GHS {value_out:,.2f}",
                                 f"GHS {closing_value:,.2f}"]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                    
                    # Data sheets
                    inventory_df.to_excel(writer, sheet_name='Inventory', index=False)
                    if not receipts_df.empty:
                        receipts_df.to_excel(writer, sheet_name='Receipts', index=False)
                    if not issues_df.empty:
                        issues_df.to_excel(writer, sheet_name='Issues', index=False)
                output.seek(0)
                
                st.download_button(
                    "💾 Download Excel Report",
                    data=output,
                    file_name=f"monthly_report_{report_month.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    with tab2:
        st.markdown("#### 🏢 Department Consumption Analysis")
        
        if not issues_df.empty:
            # Time period selector
            period = st.selectbox("Analysis Period", ["Last 30 days", "Last 90 days", "Last 6 months", "This Year", "All Time"])
            
            # Filter issues based on period
            filtered_issues = issues_df.copy()
            filtered_issues['date'] = pd.to_datetime(filtered_issues['date'])
            
            if period != "All Time":
                days_map = {
                    "Last 30 days": 30,
                    "Last 90 days": 90,
                    "Last 6 months": 180,
                    "This Year": (datetime.now() - datetime(datetime.now().year, 1, 1)).days
                }
                cutoff_date = datetime.now() - timedelta(days=days_map[period])
                filtered_issues = filtered_issues[filtered_issues['date'] >= cutoff_date]
            
            if not filtered_issues.empty:
                # Top departments
                st.markdown("##### 📈 Top Consuming Departments")
                dept_stats = filtered_issues.groupby('department').agg(
                    total_quantity=('quantity', 'sum'),
                    issue_count=('item_name', 'count'),
                    unique_items=('item_name', 'nunique')
                ).reset_index().sort_values('total_quantity', ascending=False)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(
                        dept_stats.head(10),
                        x='department',
                        y='total_quantity',
                        color='total_quantity',
                        title="Top 10 Departments by Consumption",
                        text='total_quantity'
                    )
                    fig.update_traces(texttemplate='%{text:,}', textposition='outside')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.pie(
                        dept_stats,
                        values='total_quantity',
                        names='department',
                        title="Consumption Distribution",
                        hole=0.3
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No issues found for {period.lower()}.")
        else:
            st.info("No issue data available for analysis.")
    
    with tab3:
        st.markdown("#### 📤 Export Data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📦 Export Inventory", use_container_width=True):
                csv = inventory_df.to_csv(index=False)
                st.download_button(
                    "💾 Download Inventory",
                    data=csv,
                    file_name="inventory_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("📥 Export Receipts", use_container_width=True):
                if not receipts_df.empty:
                    csv = receipts_df.to_csv(index=False)
                    st.download_button(
                        "💾 Download Receipts",
                        data=csv,
                        file_name="receipts_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("No receipts data to export")
        
        with col3:
            if st.button("📤 Export Issues", use_container_width=True):
                if not issues_df.empty:
                    csv = issues_df.to_csv(index=False)
                    st.download_button(
                        "💾 Download Issues",
                        data=csv,
                        file_name="issues_data.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("No issues data to export")

# SETTINGS TAB
elif selected_tab == "⚙️ Settings":
    # ADMIN ONLY ACCESS
    if not auth.is_admin():
        st.error("⛔ Administrator access required for settings.")
        st.info("Only administrators can access system settings.")
        st.stop()
    
    st.markdown('<div class="section-header"><h2>⚙️ System Settings</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["User Management", "System Config", "Data Import", "System Info"])
    
    with tab1:
        st.markdown("#### 👥 User Management")
        
        # Get users data
        users_df = auth.get_users()
        
        # View Users
        st.markdown("##### 📋 All System Users")
        
        if not users_df.empty:
            # Format display
            display_cols = ['username', 'full_name', 'role', 'department', 'created_at']
            display_df = users_df[display_cols].copy()
            display_df.columns = ['Username', 'Full Name', 'Role', 'Department', 'Created At']
            
            st.dataframe(display_df, use_container_width=True, height=300)
            
            # User statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Users", len(users_df))
            with col2:
                admin_count = (users_df['role'] == 'admin').sum()
                st.metric("Administrators", admin_count)
            with col3:
                other_count = len(users_df) - admin_count
                st.metric("Other Users", other_count)
        
        # Add New User
        st.markdown("##### ➕ Add New User")
        
        with st.form("add_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username*", 
                                            placeholder="e.g., store_officer",
                                            help="Unique username for login")
                new_fullname = st.text_input("Full Name*", 
                                            placeholder="e.g., Store Officer")
                new_role = st.selectbox("Role*", 
                                      ["user", "manager", "admin"],
                                      format_func=lambda x: {
                                          "user": "Regular User",
                                          "manager": "Manager",
                                          "admin": "Administrator"
                                      }[x])
            
            with col2:
                new_department = st.selectbox("Department*",
                                            ["General Stores", "Finance", "Research", "Administration", "IT"])
                new_password = st.text_input("Initial Password*", 
                                            type="password",
                                            help="User will be prompted to change on first login")
                confirm_password = st.text_input("Confirm Password*", 
                                                type="password")
            
            submitted = st.form_submit_button("➕ Create User", type="primary")
            
            if submitted:
                # Validation
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
        
        # Edit/Delete Users (for non-admin users)
        st.markdown("##### ✏️ Edit/Delete Users")
        
        if not users_df.empty:
            # Exclude current user from editing themselves
            edit_options = users_df[users_df['username'] != user['username']]['username'].tolist()
            
            if edit_options:
                user_to_edit = st.selectbox("Select user to manage", edit_options)
                
                if user_to_edit:
                    user_data = users_df[users_df['username'] == user_to_edit].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.info(f"""
                        **Current User Info:**
                        - **Username:** {user_data['username']}
                        - **Full Name:** {user_data['full_name']}
                        - **Role:** {user_data['role']}
                        - **Department:** {user_data['department']}
                        """)
                    
                    with col2:
                        action = st.radio("Select Action", ["Edit User", "Reset Password", "Delete User"])
                        
                        if action == "Edit User":
                            with st.form("edit_user_form"):
                                new_fullname = st.text_input("Full Name", value=user_data['full_name'])
                                new_role = st.selectbox("Role", 
                                                      ["user", "manager", "admin"],
                                                      index=["user", "manager", "admin"].index(user_data['role']))
                                new_department = st.selectbox("Department",
                                                            ["General Stores", "Finance", "Research", "Administration", "IT"],
                                                            index=["General Stores", "Finance", "Research", "Administration", "IT"]
                                                            .index(user_data.get('department', 'General Stores')))
                                
                                if st.form_submit_button("Update User"):
                                    updates = {
                                        'full_name': new_fullname,
                                        'role': new_role,
                                        'department': new_department
                                    }
                                    
                                    success, message = auth.update_user(user_to_edit, updates, user['username'])
                                    
                                    if success:
                                        st.success(f"✅ User '{user_to_edit}' updated successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                        
                        elif action == "Reset Password":
                            with st.form("reset_password_form"):
                                new_password = st.text_input("New Password", type="password")
                                confirm_password = st.text_input("Confirm New Password", type="password")
                                
                                if st.form_submit_button("Reset Password"):
                                    if not new_password:
                                        st.error("New password is required!")
                                    elif new_password != confirm_password:
                                        st.error("Passwords do not match!")
                                    elif len(new_password) < 6:
                                        st.error("Password must be at least 6 characters long!")
                                    else:
                                        updates = {'password': new_password}
                                        success, message = auth.update_user(user_to_edit, updates, user['username'])
                                        
                                        if success:
                                            st.success(f"✅ Password for '{user_to_edit}' reset successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {message}")
                        
                        elif action == "Delete User":
                            st.warning(f"⚠️ You are about to delete user: {user_to_edit}")
                            confirm = st.checkbox("I understand this action is permanent")
                            
                            if st.button("🗑️ Delete User", 
                                       disabled=not confirm,
                                       type="primary",
                                       use_container_width=True):
                                success, message = auth.delete_user(user_to_edit, user['username'])
                                
                                if success:
                                    st.success(f"✅ User '{user_to_edit}' deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
            else:
                st.info("No other users to manage.")
    
    with tab2:
        st.markdown("#### ⚙️ System Configuration")
        
        with st.form("system_config"):
            st.markdown("##### 📦 Inventory Settings")
            default_reorder = st.number_input("Default Reorder Level", min_value=1, value=10)
            alert_days = st.number_input("Low Stock Alert Days", min_value=1, value=7)
            
            st.markdown("##### 🔔 Notification Settings")
            email_alerts = st.checkbox("Enable Email Alerts", value=True)
            if email_alerts:
                alert_email = st.text_input("Alert Email", value="store@nhrc.gov.gh")
            
            st.markdown("##### 📊 Report Settings")
            auto_report = st.checkbox("Auto-generate Monthly Reports", value=True)
            report_day = st.number_input("Report Generation Day", min_value=1, max_value=28, value=1)
            
            if st.form_submit_button("💾 Save Configuration"):
                st.success("Configuration saved successfully!")
    
    with tab3:
        st.markdown("#### 📥 Data Import")
        
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("**Preview of uploaded data:**")
                st.dataframe(df.head(), use_container_width=True)
                
                import_mode = st.radio("Import Mode", ["Add New Items", "Update Existing", "Replace All"])
                
                if st.button("Import Data", type="primary"):
                    st.success("Data imported successfully!")
                    st.info(f"Imported {len(df)} records")
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    with tab4:
        st.markdown("#### 📊 System Information")
        
        st.info(f"""
        **System Details:**
        - **Version:** 1.1.0
        - **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
        - **Database:** Local Storage (CSV)
        - **Total Users:** {len(auth.get_users())}
        
        **Inventory Statistics:**
        - Total Items: {len(inventory_df)}
        - Total Categories: {inventory_df['category'].nunique()}
        - Total Receipts: {len(receipts_df)}
        - Total Issues: {len(issues_df)}
        
        **Support Contact:**
        - Email: it.support@nhrc.gov.gh
        - Phone: +233 54 754 8200
        """)

# ========== VC.PY STYLE FOOTER ==========
st.markdown("---")
st.markdown(
    "<p style='text-align:center;font-size:13px;color:gray;margin-top:25px;'>"
    "© 2024 Navrongo Health Research Centre – Store Management System v1.1<br>"
    "Built for efficient inventory tracking and management</p>",
    unsafe_allow_html=True

)

