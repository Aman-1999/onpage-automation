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
    
def render_audit_results(results):
    """
    Renders the new vertical-friendly card layout for audit results.
    """
    if not results: return
    
    # Run Summary
    passed = sum(1 for r in results if not r.get('Has_Critical_Issues', False) and r.get('Status_Code') == 200)
    failed_fetch = sum(1 for r in results if r.get('Status_Code') != 200)
    issues_found = len(results) - passed - failed_fetch
    
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Passed Health Check", passed)
    c2.metric("⚠️ Needs Review", issues_found)
    c3.metric("❌ Failed Fetch", failed_fetch)
    
    st.markdown("---")
    
    for i, res in enumerate(results):
        # Card Header
        status_color = "green" if res.get('Status_Code') == 200 else "red"
        has_issues = res.get('Has_Critical_Issues', False)
        icon = "⚠️" if has_issues else "✅"
        if res.get('Status_Code') != 200: icon = "❌"
        
        # Display Name
        client_label = f"[{res.get('Client')}] " if 'Client' in res else ""
        
        with st.container():
            # Summary Line (Always Visible)
            col_main, col_stat = st.columns([4, 1])
            with col_main:
                st.markdown(f"**{icon} {client_label}[{res.get('url')}]({res.get('url')})**")
            with col_stat:
                st.caption(f"Status: {res.get('Status_Code')}")

            # Expandable Details
            # Default expanded if there are issues or error
            start_expanded = has_issues or res.get('Status_Code') != 200
            
            with st.expander("🔻 View Analysis Details", expanded=start_expanded):
                
                # SECTION: MISSING / ISSUES REPORT (Vertical List)
                if has_issues:
                    st.error("🚨 **Critical Issues Detected:**")
                    issues = res.get('Issues_List', [])
                    if isinstance(issues, list):
                        for issue in issues:
                            st.markdown(f"- {issue}")
                    else:
                        st.write(str(issues))
                elif res.get('Status_Code') == 200:
                    st.success("✅ No critical on-page issues detected.")
                
                st.divider()
                
                # SECTION: DETAILED METRICS GRID
                g1, g2, g3 = st.columns(3)
                
                with g1:
                    st.markdown("##### 📝 Meta Data")
                    st.write(f"**Title**: {res.get('Title', 'N/A')}")
                    st.caption(f"Length: {res.get('Title_Length', 0)}")
                    st.write(f"**Desc**: {res.get('Meta_Description', 'N/A')}")
                    st.caption(f"Length: {res.get('Meta_Desc_Length', 0)}")
                    st.write(f"**Canon**: {res.get('Canonical_Type', 'N/A')}")
                
                with g2:
                    st.markdown("##### 📄 Content")
                    st.write(f"**Words**: {res.get('Word_Count', 0)}")
                    st.write(f"**H1**: {res.get('H1', 'N/A')}")
                    st.write(f"**Images**: {res.get('Images', 0)}")
                    if res.get('Missing_Alt_Count', 0) > 0:
                        st.caption(f"⚠️ {res['Missing_Alt_Count']} missing alt")
                    st.write(f"**Links**: {res.get('Internal_Links', 0)}")
                    
                with g3:
                    st.markdown("##### 🔑 Keywords")
                    pk = res.get('Primary_Keyword', 'N/A')
                    st.write(f"**Target**: `{pk}`")
                    
                    # Mini checks for primary
                    checks = []
                    if res.get('Primary_in_Title') == 'Yes': checks.append("Title")
                    if res.get('Primary_in_H1') == 'Yes': checks.append("H1")
                    if res.get('Primary_in_Content') == 'Yes': checks.append("Body")
                    st.write(f"**Found In**: {', '.join(checks) if checks else 'None'}")
                    
                    st.write("**Secondary**:")
                    sec_found = res.get('Secondary_in_Content_List', 'None')
                    st.caption(sec_found)

            st.write("") # Spacer between cards

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
            st.session_state['run_global'] = False
            
    if st.button("🗑️ Clear All Data", type="secondary"):
        dm.save_data({}) # Wipe file
        st.session_state.clear() # Clear session
        st.rerun()

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
            combined_res['Client'] = client # Keep Client Name
            # combined_res['Your_Secondary_Keywords'] removed to avoid duplication
            
            results_list.append(combined_res)
            
            # Update Timestamp (Save to file)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            dm.update_url_status(client, url_idx, "last_audit", now_str)
            
            progress_bar.progress((idx + 1) / len(all_tasks))
            
        status_text.text("Global Analysis Complete! ✅")
        
        if results_list:
            # Render New UI
            render_audit_results(results_list)
            
            # Prepare CSV Download
            df = pd.DataFrame(results_list)
            st.download_button("📥 Download Master Report", df.to_csv(index=False).encode('utf-8'), f"global_audit_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

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
                    # combined_res['Your_Secondary_Keywords'] removed to avoid duplication
                    
                    results_list.append(combined_res)
                    
                    # Update 'Last Audit'
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    dm.update_url_status(selected_client_view, i, "last_audit", now_str)
                    
                    progress_bar.progress((i + 1) / total)
                
                status_text.text("Analysis Complete! ✅")
                time.sleep(1)
                
                # --- Results Display ---
                if results_list:
                    st.subheader("📊 Audit Results")
                    
                    # Render New UI
                    render_audit_results(results_list)
                    
                    df = pd.DataFrame(results_list)
                    
                    # Clean up columns for export
                    # Clean up columns for export
                    cols_to_drop = ['secondary_keywords', 'Config_Secondary_Keywords', 'Missing_Alt_Files', 'notes', 'Your_Secondary_Keywords']
                    for c in cols_to_drop:
                        if c in df.columns:
                            df = df.drop(columns=[c])

                    st.download_button(
                        label="📥 Download Excel Report",
                        data=df.to_csv(index=False).encode('utf-8'),
                        file_name=f"audit_report_{selected_client_view}_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

