import streamlit as st
import pandas as pd
from data_manager import DataManager
from analyzer import SEOAnalyzer
from datetime import datetime
import time

st.set_page_config(page_title="SEO Audit Manager", layout="wide", page_icon="🔍")

# --- CSS Styling for "Modern Premium" Look ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #f3f4f6;
    }
    
    /* Headers */
    .main-header {
        font-size: 2.2rem;
        color: #111827;
        font-weight: 800;
        margin-bottom: 0.5rem;
        background: -webkit-linear-gradient(45deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #4b5563;
        margin-bottom: 2rem;
    }

    /* Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        border: 1px solid #e5e7eb;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f2937;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
    }
    
    /* Primary Action Button Gradient */
    div[data-testid="stVerticalBlock"] > div > div > div > div > .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
    }
    div[data-testid="stVerticalBlock"] > div > div > div > div > .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(37, 99, 235, 0.3);
    }

    /* DataFrame Styling */
    div[data-testid="stDataFrame"] {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

</style>
""", unsafe_allow_html=True)

# --- Init Modules ---
dm = DataManager()
analyzer = SEOAnalyzer()

data = dm.load_data()

# --- Sidebar: Client Manager ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2702/2702069.png", width=60)
    st.title("Admin Controls")
    
    st.header("⚡ Operations")
    if st.button("Run Global Audit (All Clients)", type="primary"):
        st.session_state['run_global'] = True
    else:
        if 'run_global' not in st.session_state:
            st.session_state['run_global'] = False
            
    st.divider()
    st.header(" Data Import")
    
    st.markdown("Upload Excel (`.xlsx`) to add or update clients.")
    
    # Template Download
    template_data = {
        'Client_ID': ['C1', 'C1'],
        'Target_URL': ['https://example.com/page1', 'https://example.com/page2'],
        'Primary_Keyword': ['main keyword', 'secondary keyword'],
        'Secondary_Keyword_1': ['kw1', 'kwa'],
        'Secondary_Keyword_2': ['kw2', 'kwb']
    }
    df_template = pd.DataFrame(template_data)
    
    # Convert to Bytes
    from io import BytesIO
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_template.to_excel(writer, index=False)
    
    st.download_button(
        label="📄 Download Excel Template",
        data=buffer.getvalue(),
        file_name="seo_audit_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("Columns: `Client_ID`, `Target_URL`, `Primary_Keyword`, `Secondary_Keyword_1`, etc.")
    
    uploaded_file = st.file_uploader("Choose Excel File", type=['xlsx', 'xls'])
    
    if uploaded_file is not None and st.button("Process Excel Import"):
        try:
            # Clear existing data to enforce "Clean and Fill" behavior
            dm.save_data({})
            
            df_upload = pd.read_excel(uploaded_file)
            
            # Normalize columns to lowercase for easier matching
            df_upload.columns = df_upload.columns.str.strip()
            
            count_clients = 0
            count_urls = 0
            
            for index, row in df_upload.iterrows():
                # Extract basic info
                c_id = str(row.get('Client_ID', '')).strip()
                if not c_id or c_id.lower() == 'nan': continue
                
                t_url = str(row.get('Target_URL', '')).strip()
                p_kw = str(row.get('Primary_Keyword', '')).strip()
                
                # Collect Secondary Keywords (dynamic columns starting with Secondary_Keyword)
                s_kws = []
                for col in df_upload.columns:
                    if 'Secondary_Keyword' in col and pd.notna(row[col]):
                        val = str(row[col]).strip()
                        if val: s_kws.append(val)
                
                # Add Client if missing
                if dm.add_client(c_id):
                    count_clients += 1
                    
                # Add URL
                u_data = {
                    "url": t_url,
                    "primary_keyword": p_kw,
                    "secondary_keywords": s_kws,
                    "status": "Pending",
                    "priority": "Medium",
                    "last_audit": "Never",
                    "notes": ""
                }
                
                # Add URL (Logic handles duplicates inside DataManager)
                if dm.add_url(c_id, u_data):
                    count_urls += 1
                    
            st.success(f"✅ Imported {count_clients} new clients and {count_urls} new URLs!")
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            st.error(f"Error processing file: {e}")
            




# --- Main Content ---
st.markdown('<div class="main-header">🚀 Agency SEO Auditor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated On-Page Analysis & Reporting</div>', unsafe_allow_html=True)

# --- Summary Metrics (Dashboard Top) ---
total_clients = len(data)
total_urls = sum(len(urls) for urls in data.values())
total_audited = sum(1 for urls in data.values() for u in urls if u.get('last_audit') != 'Never')
pending_urls = total_urls - total_audited

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""<div class="metric-card"><div class="metric-value">{total_clients}</div><div class="metric-label">Clients</div></div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="metric-card"><div class="metric-value">{total_urls}</div><div class="metric-label">Target URLs</div></div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="metric-card"><div class="metric-value">{total_audited}</div><div class="metric-label">Audited</div></div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""<div class="metric-card"><div class="metric-value" style="color:#ef4444">{pending_urls}</div><div class="metric-label">Pending</div></div>""", unsafe_allow_html=True)

st.write("") # Spacer

# Logic for Global vs Single
run_global = st.session_state.get('run_global', False)

if run_global:
    st.subheader("🌍 running Global Audit (All Clients)...")
    if st.button("Stop / Return to Dashboard"):
        st.session_state['run_global'] = False
        st.rerun()
    
    # Calculate total for progress
    all_tasks = []
    for client, urls in data.items():
        for i, item in enumerate(urls):
            all_tasks.append((client, i, item))
    
    if not all_tasks:
        st.warning("No URLs found in database.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_list = []
        
        for idx, (client, url_idx, item) in enumerate(all_tasks):
            status_text.text(f"[{idx+1}/{len(all_tasks)}] Analyzing {client}: {item['url']}...")
            
            # Run Analysis
            audit_res = analyzer.analyze_url(item['url'], item['primary_keyword'], item['secondary_keywords'])
            
            # Merge
            combined_res = {**item, **audit_res}
            combined_res['Client'] = client # Add Client Name
            combined_res['Your_Secondary_Keywords'] = ", ".join(item['secondary_keywords'])
            
            results_list.append(combined_res)
            
            # Update Timestamp (Save to file)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            dm.update_url_status(client, url_idx, "last_audit", now_str)
            
            progress_bar.progress((idx + 1) / len(all_tasks))
            
        status_text.text("Global Analysis Complete! ✅")
        
        if results_list:
            df = pd.DataFrame(results_list)
            
            # Structure for Global
            cols_info = ['Client', 'url', 'status', 'Status_Code', 'last_audit', 'priority'] # Added Client
            cols_schema = ['Schema_Present', 'Schema_Types']
            cols_prim = ['Primary_Keyword', 'Primary_in_Title', 'Primary_in_H1', 'Primary_in_First_100']
            cols_sec = ['Secondary_in_H2', 'Secondary_in_Content_List']
            cols_content = ['Word_Count', 'Internal_Links', 'Images', 'Missing_Alt_Count']
            
            priority_order = cols_info + cols_schema + cols_prim + cols_sec + cols_content
            final_cols = [c for c in priority_order if c in df.columns]
            exclude_cols = ['secondary_keywords', 'Your_Secondary_Keywords', 'Config_Secondary_Keywords', 'Missing_Alt_Files']
            remaining_cols = [c for c in df.columns if c not in final_cols and c not in exclude_cols]
            
            df_final = df[final_cols + remaining_cols]
            
            rename_map = {
                'url': 'Url', 'status': 'Status', 'Status_Code': 'Code', 'last_audit': 'Last Check', 
                'priority': 'Prio', 'Schema_Present': 'Schema?', 'Schema_Types': 'Types',
                'Primary_Keyword': 'Keyword', 'Primary_in_Title': 'P_Title', 'Primary_in_H1': 'P_H1', 
                'Primary_in_First_100': 'P_100w', 'Secondary_in_H2': 'Sec_H2', 'Secondary_in_Content_List': 'Sec_Content',
                'Word_Count': 'Words', 'Internal_Links': 'Links', 'Images': 'Imgs', 'Missing_Alt_Count': 'No_Alt'
            }
            
            df_view = df_final.copy()
            if 'Schema_Types' in df_view.columns:
                 df_view['Schema_Types'] = df_view['Schema_Types'].apply(lambda x: x[:30] + '...' if len(str(x)) > 30 else x)
            df_view = df_view.rename(columns=rename_map)
            
            st.dataframe(df_view, use_container_width=True)
            st.download_button("📥 Download Master Report", df_final.to_csv(index=False).encode('utf-8'), f"global_audit_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

elif not data:
    st.info("👋 Welcome! Use the sidebar to add your first client and target URLs.")
else:
    # Client Selection for View
    selected_client_view = st.selectbox("📂 Select Client Workspace", list(data.keys()))
    
    if selected_client_view:
        client_urls = data[selected_client_view]
        
        # --- Workflow / Status View ---
        st.subheader(f"Dashboard: {selected_client_view}")
        
        if not client_urls:
            st.warning("No URLs found for this client. Add one in the sidebar!")
        else:
            # Create a nice layout for the list
            col1_h, col2_h, col3_h, col4_h, col5_h, col6_h = st.columns([3, 1.5, 1, 1, 1.5, 0.5])
            col1_h.markdown("**URL**")
            col2_h.markdown("**Primary Keyword**")
            col3_h.markdown("**Priority**")
            col4_h.markdown("**Status**")
            col5_h.markdown("**Last Audit**")
            col6_h.markdown("**Action**")
            
            st.divider()
            
            # --- URL List with Controls ---
            urls_to_audit = []
            
            for index, item in enumerate(client_urls):
                c1, c2, c3, c4, c5, c6 = st.columns([3, 1.5, 1, 1, 1.5, 0.5])
                
                c1.write(f"🔗 [{item['url']}]({item['url']})")
                c2.write(item['primary_keyword'])
                
                # Priority Edit
                new_prio = c3.selectbox("Priority", ["High", "Medium", "Low"], index=["High", "Medium", "Low"].index(item['priority']), key=f"prio_{selected_client_view}_{index}", label_visibility="collapsed")
                if new_prio != item['priority']:
                    dm.update_url_status(selected_client_view, index, "priority", new_prio)
                    st.rerun()
                
                # Status Edit
                new_status = c4.selectbox("Status", ["Pending", "In Progress", "Optimized", "Review"], index=["Pending", "In Progress", "Optimized", "Review"].index(item['status']), key=f"stat_{selected_client_view}_{index}", label_visibility="collapsed")
                if new_status != item['status']:
                    dm.update_url_status(selected_client_view, index, "status", new_status)
                    st.rerun()
                    
                c5.write(item['last_audit'])
                
                # Delete Button
                if c6.button("🗑️", key=f"del_{selected_client_view}_{index}"):
                    dm.remove_url(selected_client_view, index)
                    st.rerun()

            st.divider()
            
            # --- Audit Action Area (Single Client) ---
            st.subheader("⚡ Run Audit")
            run_btn = st.button(f"Analyze All URLs for {selected_client_view}", type="primary")
            if run_btn and client_urls:
                st.write("Starting analysis...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_list = []
                
                total = len(client_urls)
                
                for i, item in enumerate(client_urls):
                    status_text.text(f"Analyzing {item['url']}...")
                    
                    # Run Analysis
                    audit_res = analyzer.analyze_url(item['url'], item['primary_keyword'], item['secondary_keywords'])
                    
                    # Merge static data (Status, Priority) with Audit Results
                    combined_res = {**item, **audit_res}
                    # We don't want the raw secondary_keywords list in the excel export, join it
                    combined_res['Your_Secondary_Keywords'] = ", ".join(item['secondary_keywords'])
                    
                    results_list.append(combined_res)
                    
                    # Update 'Last Audit'
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    dm.update_url_status(selected_client_view, i, "last_audit", now_str)
                    
                    progress_bar.progress((i + 1) / total)
                
                status_text.text("Analysis Complete! ✅")
                time.sleep(1)
                
                # --- Results Display ---
                if results_list:
                    df = pd.DataFrame(results_list)
                    
                    # --- Report Structure Definition ---
                    # 1. INFO GROUP
                    cols_info = ['url', 'status', 'Status_Code', 'last_audit', 'priority']
                    # 2. SCHEMA GROUP
                    cols_schema = ['Schema_Present', 'Schema_Types']
                    # 3. KEYWORD GROUP (Primary)
                    cols_prim = ['Primary_Keyword', 'Primary_in_Title', 'Primary_in_H1', 'Primary_in_First_100']
                    # 4. KEYWORD GROUP (Secondary - Results Only)
                    cols_sec = ['Secondary_in_H2', 'Secondary_in_Content_List']
                    # 5. CONTENT HEALTH
                    cols_content = ['Word_Count', 'Internal_Links', 'Images', 'Missing_Alt_Count']
                    
                    # Combine all priority columns
                    priority_order = cols_info + cols_schema + cols_prim + cols_sec + cols_content
                    
                    # Filter existing columns
                    final_cols = [c for c in priority_order if c in df.columns]
                    
                    # Add any debug/extra columns at the very end (hidden from main view typically)
                    # We EXCLUDE 'secondary_keywords' and 'Your_Secondary_Keywords' to avoid duplication
                    exclude_cols = ['secondary_keywords', 'Your_Secondary_Keywords', 'Config_Secondary_Keywords', 'Missing_Alt_Files']
                    remaining_cols = [c for c in df.columns if c not in final_cols and c not in exclude_cols]
                    
                    df_final = df[final_cols + remaining_cols]
                    
                    # --- Rename for Layout Compactness ---
                    rename_map = {
                        'url': 'Url',
                        'status': 'Status',
                        'Status_Code': 'Code',
                        'last_audit': 'Last_Check',
                        'priority': 'Prio',
                        'Schema_Present': 'Schema?',
                        'Schema_Types': 'Types',
                        'Primary_Keyword': 'Keyword',
                        'Primary_in_Title': 'P_Title',
                        'Primary_in_H1': 'P_H1',
                        'Primary_in_First_100': 'P_100w',
                        'Secondary_in_H2': 'Sec_H2',
                        'Secondary_in_Content_List': 'Sec_Content',
                        'Word_Count': 'Words',
                        'Internal_Links': 'Links',
                        'Images': 'Imgs',
                        'Missing_Alt_Count': 'No_Alt_Count' # Ensure this is used instead of Files
                    }
                    
                    # Create View DataFrame
                    df_view = df_final.copy()
                    
                    # 1. Truncate Schema Types to avoid horizontal scroll explosion
                    if 'Schema_Types' in df_view.columns:
                        df_view['Schema_Types'] = df_view['Schema_Types'].apply(lambda x: x[:40] + '...' if len(str(x)) > 40 else x)

                    # 2. Remove columns user explicitly doesn't want in view
                    if 'Missing_Alt_Files' in df_view.columns:
                        df_view = df_view.drop(columns=['Missing_Alt_Files'])

                    # Rename
                    df_view = df_view.rename(columns=rename_map)
                    
                    st.subheader("📊 Audit Results")
                    st.dataframe(df_view, use_container_width=True)
                    
                    # Excel Export (Keep full names & full data)
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=df_final.to_csv(index=False).encode('utf-8'),
                        file_name=f"audit_report_{selected_client_view}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

