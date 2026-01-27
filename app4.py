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

# ========== FIXED AUTHENTICATION SYSTEM ==========
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
        """Check if user is authenticated"""
        # Initialize session state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = False
            st.session_state[self.username_key] = ''
            st.session_state['user_data'] = {}
        
        # If not logged in, show login interface
        if not st.session_state[self.session_key]:
            self.show_login_interface()
            st.stop()
        else:
            return st.session_state['user_data']
    
    def show_login_interface(self):
        """Display login interface"""
        # Header
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
        
        # Login form in main area
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
                                
                                # Ensure user_info has all required fields
                                if 'full_name' not in user_info:
                                    user_info['full_name'] = user_info.get('username', 'User').title()
                                if 'department' not in user_info:
                                    user_info['department'] = 'General Stores'
                                if 'role' not in user_info:
                                    user_info['role'] = 'user'
                                
                                st.success(f"✅ Signed in as {user_info['full_name']}")
                                st.rerun()
                            else:
                                st.error("❌ Invalid username or password")
    
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
        for key in list(st.session_state.keys()):
            if key not in ['_theme', '_pages']:  # Preserve theme and pages
                del st.session_state[key]
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

# ========== FIXED DATA MANAGEMENT ==========
def load_inventory_data():
    """Load inventory data from CSV"""
    try:
        # Try to load from session state first
        if 'inventory_df' in st.session_state:
            return st.session_state.inventory_df
        
        # Try to load from file
        if os.path.exists("inventory_data.csv"):
            df = pd.read_csv("inventory_data.csv")
            # Ensure required columns exist
            required_cols = ['item_id', 'item_name', 'category', 'quantity', 'unit', 
                            'reorder_level', 'storage_location', 'supplier', 'notes']
            for col in required_cols:
                if col not in df.columns:
                    if col == 'item_id':
                        df['item_id'] = df.apply(lambda row: f"STR-{str(row['category'])[:3].upper() if pd.notna(row.get('category')) else 'GEN'}-{row.name+1:04d}", axis=1)
                    elif col == 'reorder_level':
                        df['reorder_level'] = 10
                    else:
                        df[col] = ''
            
            # Handle expiry dates
            if 'expiry_date' in df.columns:
                df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
            
            # Convert quantity to numeric
            if 'quantity' in df.columns:
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0)
            
            st.session_state.inventory_df = df
            return df
        else:
            # Create empty inventory
            df = pd.DataFrame(columns=[
                'item_id', 'item_name', 'category', 'quantity', 'unit',
                'reorder_level', 'storage_location', 'supplier', 'notes', 'expiry_date'
            ])
            st.session_state.inventory_df = df
            return df
    except Exception as e:
        st.error(f"Error loading inventory: {e}")
        # Create empty inventory
        df = pd.DataFrame(columns=[
            'item_id', 'item_name', 'category', 'quantity', 'unit',
            'reorder_level', 'storage_location', 'supplier', 'notes', 'expiry_date'
        ])
        st.session_state.inventory_df = df
        return df

def save_inventory_data(df):
    """Save inventory data to CSV and session state"""
    try:
        df.to_csv("inventory_data.csv", index=False)
        st.session_state.inventory_df = df
        return True
    except Exception as e:
        st.error(f"Error saving inventory: {e}")
        return False

def load_receipts_data():
    """Load receipts data"""
    try:
        if 'receipts_df' in st.session_state:
            return st.session_state.receipts_df
        
        if os.path.exists("receipts_data.csv"):
            df = pd.read_csv("receipts_data.csv")
            st.session_state.receipts_df = df
            return df
        else:
            df = pd.DataFrame(columns=[
                'date', 'item_id', 'item_name', 'supplier', 'quantity', 
                'unit_cost', 'total_value', 'project_code', 'reference', 
                'received_by', 'notes'
            ])
            st.session_state.receipts_df = df
            return df
    except Exception as e:
        st.error(f"Error loading receipts: {e}")
        df = pd.DataFrame(columns=[
            'date', 'item_id', 'item_name', 'supplier', 'quantity', 
            'unit_cost', 'total_value', 'project_code', 'reference', 
            'received_by', 'notes'
        ])
        st.session_state.receipts_df = df
        return df

def save_receipts_data(df):
    """Save receipts data"""
    try:
        df.to_csv("receipts_data.csv", index=False)
        st.session_state.receipts_df = df
        return True
    except Exception as e:
        st.error(f"Error saving receipts: {e}")
        return False

def load_issues_data():
    """Load issues data"""
    try:
        if 'issues_df' in st.session_state:
            return st.session_state.issues_df
        
        if os.path.exists("issues_data.csv"):
            df = pd.read_csv("issues_data.csv")
            st.session_state.issues_df = df
            return df
        else:
            df = pd.DataFrame(columns=[
                'date', 'item_id', 'item_name', 'department', 'quantity', 
                'purpose', 'issued_by', 'notes'
            ])
            st.session_state.issues_df = df
            return df
    except Exception as e:
        st.error(f"Error loading issues: {e}")
        df = pd.DataFrame(columns=[
            'date', 'item_id', 'item_name', 'department', 'quantity', 
            'purpose', 'issued_by', 'notes'
        ])
        st.session_state.issues_df = df
        return df

def save_issues_data(df):
    """Save issues data"""
    try:
        df.to_csv("issues_data.csv", index=False)
        st.session_state.issues_df = df
        return True
    except Exception as e:
        st.error(f"Error saving issues: {e}")
        return False

# Page Configuration
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
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        border: none !important;
        letter-spacing: 0.5px !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px) !important;
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
</style>
""", unsafe_allow_html=True)

# ========== CHECK AUTHENTICATION ==========
user = auth.check_auth()

# ========== SIDEBAR USER INFO (AFTER LOGIN) ==========
with st.sidebar:
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
        # Clear cache and reload data
        if 'inventory_df' in st.session_state:
            del st.session_state.inventory_df
        if 'receipts_df' in st.session_state:
            del st.session_state.receipts_df
        if 'issues_df' in st.session_state:
            del st.session_state.issues_df
        st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        auth.logout()

# Load data
inventory_df = load_inventory_data()
receipts_df = load_receipts_data()
issues_df = load_issues_data()

# ========== DISPLAY MAIN HEADER ==========
st.markdown(
    f"""
    <div style='text-align:center;padding:6px 0 12px 0;background:transparent;'>
        <div style='font-size: 3rem; margin-bottom: 0.5rem;'>🏪</div>
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

# Create tabs using radio buttons
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
        ("Total Units", f"{inventory_df['quantity'].sum():,}" if not inventory_df.empty and 'quantity' in inventory_df.columns else "0", "📊", "Total units across all items"),
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
    
    # Charts Row 1
    if not inventory_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Units by Category")
            if 'category' in inventory_df.columns and 'quantity' in inventory_df.columns:
                category_units = inventory_df.groupby('category')['quantity'].sum().reset_index()
                if not category_units.empty:
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
            if 'category' in inventory_df.columns and 'quantity' in inventory_df.columns:
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
    
    if not inventory_df.empty and 'quantity' in inventory_df.columns and 'reorder_level' in inventory_df.columns:
        low_stock_items = inventory_df[inventory_df['quantity'] <= inventory_df['reorder_level']]
        
        if not low_stock_items.empty:
            display_cols = ['item_name', 'category', 'quantity', 'unit', 'reorder_level']
            display_df = low_stock_items[[col for col in display_cols if col in low_stock_items.columns]].copy()
            
            def get_stock_status(row):
                if row['quantity'] == 0:
                    return '<span class="status-badge status-critical">Critical</span>'
                else:
                    return '<span class="status-badge status-low">Low</span>'
            
            display_df['status'] = display_df.apply(get_stock_status, axis=1)
            
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
            if 'item_id' in inventory_df.columns:
                filtered = filtered[filtered['item_id'].str.contains(search, case=False, na=False)]
        
        if category_filter != "All" and 'category' in filtered.columns:
            filtered = filtered[filtered['category'] == category_filter]
        
        # Calculate days to expiry for filtering
        if not inventory_df.empty and 'expiry_date' in inventory_df.columns:
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
            # Prepare display dataframe
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
                
                # Expiry date option
                expiry_option = st.radio("Has expiry date?", ["No", "Yes"])
                if expiry_option == "Yes":
                    expiry_date = st.date_input("Expiry Date", 
                                              value=datetime.now() + timedelta(days=365))
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
                        'created_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    # Add expiry date only if provided
                    if expiry_option == "Yes" and expiry_date:
                        item_data['expiry_date'] = expiry_date.strftime('%Y-%m-%d')
                    
                    # Add to inventory
                    new_item = pd.DataFrame([item_data])
                    inventory_df = pd.concat([inventory_df, new_item], ignore_index=True)
                    save_inventory_data(inventory_df)
                    st.success(f"✅ Item '{item_name}' added successfully!")
                    st.rerun()
    
    with tab3:
        st.markdown("#### ✏️ Edit/Delete Inventory Item")
        
        if not inventory_df.empty:
            # Item selection
            item_to_edit = st.selectbox("Select item to edit/delete", 
                                       inventory_df['item_name'].unique())
            
            if item_to_edit:
                item_data = inventory_df[inventory_df['item_name'] == item_to_edit].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Edit form
                    with st.form("edit_item_form"):
                        st.markdown(f"**Editing: {item_to_edit}**")
                        
                        current_qty = item_data.get('quantity', 0)
                        new_quantity = st.number_input("Quantity (Units)", 
                                                     min_value=0, 
                                                     value=int(current_qty))
                        
                        if 'storage_location' in item_data:
                            locations = ["Main Store", "Lab A", "Lab B", "Cold Room", "Quarantine", "Archive", "Warehouse"]
                            current_location = item_data.get('storage_location', 'Main Store')
                            new_location = st.selectbox("Storage Location", 
                                                      locations,
                                                      index=locations.index(current_location) if current_location in locations else 0)
                        
                        if 'category' in item_data:
                            categories = ["Stationery", "Comp/Printer/Accessories", "Miscellaneous", 
                                         "Electrical Items", "Motor Parts", "Vehicle Parts - Toyota Hilux",
                                         "Fuel & Lubricants", "Laboratory Items", "Medical Supplies", "Office Equipment"]
                            current_category = item_data.get('category', 'Miscellaneous')
                            new_category = st.selectbox("Category", 
                                                      categories,
                                                      index=categories.index(current_category) if current_category in categories else 0)
                        
                        # Handle expiry date
                        current_expiry = item_data.get('expiry_date')
                        if pd.notna(current_expiry):
                            expiry_option = st.radio("Expiry Date", ["Keep current", "Change", "Remove"])
                            if expiry_option == "Change":
                                new_expiry = st.date_input("New Expiry Date", 
                                                          value=pd.to_datetime(current_expiry) 
                                                          if pd.notna(current_expiry) 
                                                          else datetime.now() + timedelta(days=365))
                            elif expiry_option == "Remove":
                                new_expiry = None
                            else:
                                new_expiry = current_expiry
                        else:
                            expiry_option = st.radio("Add expiry date?", ["No", "Yes"])
                            if expiry_option == "Yes":
                                new_expiry = st.date_input("Expiry Date", 
                                                          value=datetime.now() + timedelta(days=365))
                            else:
                                new_expiry = None
                        
                        new_reorder_level = st.number_input("Reorder Level (Units)", 
                                                          min_value=1, 
                                                          value=int(item_data.get('reorder_level', 10)))
                        
                        if 'supplier' in item_data:
                            new_supplier = st.text_input("Supplier", value=item_data.get('supplier', 'Standard Supplier'))
                        
                        if 'notes' in item_data:
                            new_notes = st.text_area("Notes", value=item_data.get('notes', ''))
                        
                        submitted = st.form_submit_button("💾 Save Changes", type="primary")
                        
                        if submitted:
                            # Update inventory
                            idx = inventory_df.index[inventory_df['item_name'] == item_to_edit][0]
                            
                            # Check each field for changes
                            inventory_df.at[idx, 'quantity'] = new_quantity
                            inventory_df.at[idx, 'storage_location'] = new_location
                            inventory_df.at[idx, 'category'] = new_category
                            inventory_df.at[idx, 'reorder_level'] = new_reorder_level
                            inventory_df.at[idx, 'supplier'] = new_supplier
                            inventory_df.at[idx, 'notes'] = new_notes
                            
                            # Handle expiry date changes
                            if expiry_option == "Change" and new_expiry:
                                inventory_df.at[idx, 'expiry_date'] = new_expiry.strftime('%Y-%m-%d') if hasattr(new_expiry, 'strftime') else str(new_expiry)
                            elif expiry_option == "Remove":
                                inventory_df.at[idx, 'expiry_date'] = None
                            elif expiry_option == "Yes" and new_expiry:
                                inventory_df.at[idx, 'expiry_date'] = new_expiry.strftime('%Y-%m-%d') if hasattr(new_expiry, 'strftime') else str(new_expiry)
                            
                            save_inventory_data(inventory_df)
                            st.success("✅ Item updated successfully!")
                            st.rerun()
                
                with col2:
                    # Delete button with warning
                    st.markdown("### 🗑️")
                    st.markdown("##### Delete Item")
                    
                    st.warning(f"You are about to delete: **{item_to_edit}**")
                    st.info(f"Current stock: {item_data.get('quantity', 0)} units")
                    
                    # Confirmation for deletion
                    delete_confirmed = st.checkbox("I confirm deletion")
                    
                    if st.button("🗑️ Delete Item", 
                                disabled=not delete_confirmed,
                                use_container_width=True,
                                type="primary"):
                        
                        # Remove item from inventory
                        inventory_df = inventory_df[inventory_df['item_name'] != item_to_edit].reset_index(drop=True)
                        save_inventory_data(inventory_df)
                        
                        st.success(f"✅ Item '{item_to_edit}' deleted successfully!")
                        st.rerun()

# STOCK IN TAB
elif selected_tab == "📥 Stock In":
    st.markdown('<div class="section-header"><h2>📥 Stock Receipts Management</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Record Receipt", "Receipt History"])
    
    with tab1:
        st.markdown("#### 📝 Record New Stock Receipt")
        
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
                    selected_item = st.selectbox("Select Item*", inventory_df['item_name'].unique())
                    if selected_item:
                        item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                        current_stock = item_data.get('quantity', 0)
                        st.info(f"**Current Stock:** {current_stock} {item_data.get('unit', 'units')}")
                    else:
                        current_stock = 0
                else:
                    st.warning("No items in inventory. Please add items first.")
                    selected_item = None
                    current_stock = 0
                
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
                    # Update inventory
                    idx = inventory_df.index[inventory_df['item_name'] == selected_item][0]
                    inventory_df.at[idx, 'quantity'] = inventory_df.at[idx, 'quantity'] + quantity
                    save_inventory_data(inventory_df)
                    
                    # Add to receipts
                    new_receipt = pd.DataFrame([{
                        'date': receipt_date.strftime('%Y-%m-%d'),
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
                    
                    receipts_df = pd.concat([receipts_df, new_receipt], ignore_index=True)
                    save_receipts_data(receipts_df)
                    
                    st.success(f"✅ Receipt recorded successfully! Stock updated to {inventory_df.at[idx, 'quantity']} units.")
                    st.rerun()
    
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
            filtered_receipts['date'] = pd.to_datetime(filtered_receipts['date'], errors='coerce')
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
                display_df = filtered_receipts.copy()
                display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
                
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
                    selected_item = st.selectbox("Select Item*", inventory_df['item_name'].unique())
                    if selected_item:
                        item_data = inventory_df[inventory_df['item_name'] == selected_item].iloc[0]
                        current_stock = item_data.get('quantity', 0)
                        st.info(f"**Current Stock:** {current_stock} {item_data.get('unit', 'units')}")
                    else:
                        current_stock = 0
                else:
                    st.warning("No items in inventory. Please add items first.")
                    selected_item = None
                    current_stock = 0
                
                if selected_item:
                    quantity = st.number_input("Quantity to Issue*", min_value=1, value=1, max_value=int(current_stock))
                else:
                    quantity = st.number_input("Quantity to Issue*", min_value=1, value=1)
                
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
                    # Update inventory
                    idx = inventory_df.index[inventory_df['item_name'] == selected_item][0]
                    inventory_df.at[idx, 'quantity'] = inventory_df.at[idx, 'quantity'] - quantity
                    save_inventory_data(inventory_df)
                    
                    # Add to issues
                    new_issue = pd.DataFrame([{
                        'date': issue_date.strftime('%Y-%m-%d'),
                        'item_id': item_data['item_id'],
                        'item_name': selected_item,
                        'department': department,
                        'quantity': quantity,
                        'purpose': purpose,
                        'issued_by': issued_by,
                        'notes': notes
                    }])
                    
                    issues_df = pd.concat([issues_df, new_issue], ignore_index=True)
                    save_issues_data(issues_df)
                    
                    st.success(f"✅ Stock issued successfully! Remaining stock: {inventory_df.at[idx, 'quantity']} units.")
                    st.rerun()
    
    with tab2:
        st.markdown("#### 📋 Issue History")
        
        if not issues_df.empty:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
            with col2:
                end_date = st.date_input("To Date", value=datetime.now())
            
            # Filter issues
            filtered_issues = issues_df.copy()
            filtered_issues['date'] = pd.to_datetime(filtered_issues['date'], errors='coerce')
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
                
                # Display table
                display_df = filtered_issues.copy()
                display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
                
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

# EXPIRY TAB (Simplified for now)
elif selected_tab == "⏰ Expiry":
    st.markdown('<div class="section-header"><h2>⏰ Expiry Management</h2></div>', unsafe_allow_html=True)
    
    if not inventory_df.empty and 'expiry_date' in inventory_df.columns:
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
            
            with col1:
                st.metric("Expired", expired)
            with col2:
                st.metric("< 30 Days", expiring_30)
            with col3:
                st.metric("30-90 Days", expiring_90)
            with col4:
                st.metric("90-180 Days", expiring_180)
            
            # Expired items table
            st.markdown("#### 🚨 Expired Items")
            expired_items = expiry_items[expiry_items['days_to_expiry'] <= 0]
            if not expired_items.empty:
                st.dataframe(expired_items[['item_name', 'category', 'quantity', 'unit', 'expiry_date']], use_container_width=True)
            else:
                st.success("✅ No expired items!")
            
            # Items expiring soon
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

# REPORTS TAB (Simplified)
elif selected_tab == "📝 Reports":
    st.markdown('<div class="section-header"><h2>📊 Reports & Analytics</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Summary Report", "Export Data"])
    
    with tab1:
        st.markdown("#### 📅 Stores Summary Report")
        
        # Summary metrics
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
        
        # Generate report
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
            else:
                st.warning("No inventory data to export")
        
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
            else:
                st.warning("No receipts data to export")
        
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
            else:
                st.warning("No issues data to export")

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
        
        # Get users data
        users_df = auth.get_users()
        
        # View Users
        st.markdown("##### 📋 All System Users")
        
        if not users_df.empty:
            st.dataframe(users_df[['username', 'full_name', 'role', 'department', 'created_at']], use_container_width=True)
        
        # Add New User
        st.markdown("##### ➕ Add New User")
        
        with st.form("add_user_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username*", 
                                            placeholder="e.g., store_officer")
                new_fullname = st.text_input("Full Name*", 
                                            placeholder="e.g., Store Officer")
                new_role = st.selectbox("Role*", 
                                      ["user", "manager", "admin"])
            
            with col2:
                new_department = st.selectbox("Department*",
                                            ["General Stores", "Finance", "Research", "Administration", "IT"])
                new_password = st.text_input("Initial Password*", 
                                            type="password")
                confirm_password = st.text_input("Confirm Password*", 
                                                type="password")
            
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
        st.markdown("#### 📊 System Information")
        
        st.info(f"""
        **System Details:**
        - **Version:** 1.1.0
        - **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
        - **Database:** Local Storage (CSV)
        - **Total Users:** {len(auth.get_users())}
        
        **Inventory Statistics:**
        - Total Items: {len(inventory_df)}
        - Total Categories: {inventory_df['category'].nunique() if not inventory_df.empty and 'category' in inventory_df.columns else 0}
        - Total Receipts: {len(receipts_df)}
        - Total Issues: {len(issues_df)}
        
        **Support Contact:**
        - Email: it.support@nhrc.gov.gh
        - Phone: +233 54 754 8200
        """)

# ========== FOOTER ==========
st.markdown("---")
st.markdown(
    "<p style='text-align:center;font-size:13px;color:gray;margin-top:25px;'>"
    "© 2024 Navrongo Health Research Centre – Store Management System v1.1<br>"
    "Built for efficient inventory tracking and management</p>",
    unsafe_allow_html=True
)
