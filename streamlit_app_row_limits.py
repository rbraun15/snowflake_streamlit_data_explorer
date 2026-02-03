# =============================================================================
# HIGHER EDUCATION DATA EXPLORER
# Streamlit in Snowflake Application
# =============================================================================
# This application allows business users to explore higher education data
# across multiple schemas and tables with dynamic filtering and visualizations.
# =============================================================================

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Higher Ed Data Explorer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM STYLING
# =============================================================================

st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1e3a5f;
        --secondary-color: #3d7ea6;
        --accent-color: #f4a261;
        --background-light: #f8f9fa;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #3d7ea6 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(30, 58, 95, 0.2);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        font-size: 2rem;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.25rem;
        border-radius: 10px;
        border-left: 4px solid #3d7ea6;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin-bottom: 1rem;
    }
    
    .metric-card h3 {
        color: #1e3a5f;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0 0 0.5rem 0;
    }
    
    .metric-card .value {
        color: #3d7ea6;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
    }
    
    /* Filter section */
    .filter-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
    
    /* Table info badge */
    .table-badge {
        display: inline-block;
        background: #e8f4f8;
        color: #1e3a5f;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }
    
    /* Data table styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Button styling */
    .stDownloadButton button {
        background: linear-gradient(135deg, #f4a261 0%, #e76f51 100%);
        color: white;
        border: none;
        font-weight: 600;
    }
    
    /* Divider */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, #3d7ea6 0%, transparent 100%);
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATABASE CONNECTION & HELPER FUNCTIONS
# =============================================================================

@st.cache_resource
def get_session():
    """Get the active Snowflake session."""
    return get_active_session()

@st.cache_data(ttl=600)
def get_schemas(_session, database: str) -> list:
    """Retrieve all schemas in the database (excluding system schemas)."""
    query = f"""
        SELECT SCHEMA_NAME 
        FROM {database}.INFORMATION_SCHEMA.SCHEMATA 
        WHERE SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA', 'PUBLIC')
        ORDER BY SCHEMA_NAME
    """
    df = _session.sql(query).to_pandas()
    return df['SCHEMA_NAME'].tolist()

@st.cache_data(ttl=600)
def get_tables(_session, database: str, schema: str) -> list:
    """Retrieve all tables in the specified schema."""
    query = f"""
        SELECT TABLE_NAME 
        FROM {database}.INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """
    df = _session.sql(query).to_pandas()
    return df['TABLE_NAME'].tolist()

@st.cache_data(ttl=600)
def get_column_metadata(_session, database: str, schema: str, table: str) -> pd.DataFrame:
    """Retrieve column metadata for the specified table."""
    query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            ORDINAL_POSITION
        FROM {database}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}'
        AND TABLE_NAME = '{table}'
        ORDER BY ORDINAL_POSITION
    """
    return _session.sql(query).to_pandas()

@st.cache_data(ttl=300)
def get_table_data(_session, database: str, schema: str, table: str) -> pd.DataFrame:
    """Retrieve all data from the specified table."""
    query = f'SELECT * FROM {database}.{schema}.{table}'
    return _session.sql(query).to_pandas()

@st.cache_data(ttl=300)
def get_distinct_values(_session, database: str, schema: str, table: str, column: str) -> list:
    """Get distinct values for a column (for dropdown filters)."""
    query = f"""
        SELECT DISTINCT {column} 
        FROM {database}.{schema}.{table} 
        WHERE {column} IS NOT NULL
        ORDER BY {column}
    """
    df = _session.sql(query).to_pandas()
    return df[column].tolist()

def classify_column_type(data_type: str) -> str:
    """Classify column data type for filter type determination."""
    data_type = data_type.upper()
    
    if any(t in data_type for t in ['INT', 'NUMBER', 'DECIMAL', 'FLOAT', 'DOUBLE', 'REAL']):
        return 'numeric'
    elif any(t in data_type for t in ['DATE', 'TIME', 'TIMESTAMP']):
        return 'date'
    elif any(t in data_type for t in ['BOOL']):
        return 'boolean'
    else:
        return 'categorical'

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply all active filters to the dataframe."""
    filtered_df = df.copy()
    
    for column, filter_config in filters.items():
        if column not in filtered_df.columns:
            continue
            
        filter_type = filter_config.get('type')
        value = filter_config.get('value')
        
        if value is None:
            continue
            
        if filter_type == 'categorical':
            if isinstance(value, list) and len(value) > 0:
                filtered_df = filtered_df[filtered_df[column].isin(value)]
        elif filter_type == 'numeric':
            if isinstance(value, tuple) and len(value) == 2:
                min_val, max_val = value
                filtered_df = filtered_df[
                    (filtered_df[column] >= min_val) & 
                    (filtered_df[column] <= max_val)
                ]
        elif filter_type == 'date':
            if isinstance(value, tuple) and len(value) == 2:
                start_date, end_date = value
                # Convert column to datetime if not already
                filtered_df[column] = pd.to_datetime(filtered_df[column])
                filtered_df = filtered_df[
                    (filtered_df[column] >= pd.to_datetime(start_date)) & 
                    (filtered_df[column] <= pd.to_datetime(end_date))
                ]
        elif filter_type == 'boolean':
            if value != 'All':
                bool_val = value == 'True'
                filtered_df = filtered_df[filtered_df[column] == bool_val]
    
    return filtered_df

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    # Database configuration
    DATABASE = "DEMO_HE_STREAMLIT"
    
    # Get session
    session = get_session()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Higher Education Data Explorer</h1>
        <p>Explore student data across Finance, Student Services, and Advising systems</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==========================================================================
    # SIDEBAR - Schema and Table Selection
    # ==========================================================================
    
    with st.sidebar:
        st.markdown("### 📊 Data Selection")
        st.markdown("---")
        
        # Get available schemas
        try:
            schemas = get_schemas(session, DATABASE)
        except Exception as e:
            st.error(f"Error connecting to database: {str(e)}")
            st.info("Please ensure the database 'DEMO_HE_STREAMLIT' exists and you have access.")
            return
        
        if not schemas:
            st.warning("No schemas found in the database.")
            return
        
        # Schema selection
        selected_schema = st.selectbox(
            "🗂️ Select Schema",
            options=schemas,
            help="Choose a schema to explore its tables"
        )
        
        # Get tables for selected schema
        tables = get_tables(session, DATABASE, selected_schema)
        
        if not tables:
            st.warning(f"No tables found in schema '{selected_schema}'.")
            return
        
        # Table selection
        selected_table = st.selectbox(
            "📋 Select Table",
            options=tables,
            help="Choose a table to view and filter its data"
        )
        
        st.markdown("---")
        
        # Table info
        st.markdown("### ℹ️ Table Information")
        column_metadata = get_column_metadata(session, DATABASE, selected_schema, selected_table)
        
        st.markdown(f"""
        <div class="metric-card">
            <h3>Columns</h3>
            <p class="value">{len(column_metadata)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📝 Column Details", expanded=False):
            for _, row in column_metadata.iterrows():
                col_type = classify_column_type(row['DATA_TYPE'])
                type_icon = {
                    'numeric': '🔢',
                    'date': '📅',
                    'categorical': '🏷️',
                    'boolean': '✅'
                }.get(col_type, '📝')
                st.markdown(f"{type_icon} **{row['COLUMN_NAME']}** - `{row['DATA_TYPE']}`")
    
    # ==========================================================================
    # MAIN CONTENT AREA
    # ==========================================================================
    
    # Load table data
    with st.spinner(f"Loading data from {selected_schema}.{selected_table}..."):
        df = get_table_data(session, DATABASE, selected_schema, selected_table)
    
    # Display table context
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        st.markdown(f'<span class="table-badge">Schema: {selected_schema}</span>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<span class="table-badge">Table: {selected_table}</span>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<span class="table-badge">Total Records: {len(df):,}</span>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # DYNAMIC FILTERS
    # ==========================================================================
    
    st.markdown("### 🔍 Filter Data")
    
    filters = {}
    
    # Create filter columns based on number of filterable columns
    filter_columns = column_metadata.head(12)  # Limit to first 12 columns for UI
    
    # Group columns by type for organized display
    numeric_cols = []
    date_cols = []
    categorical_cols = []
    boolean_cols = []
    
    for _, row in filter_columns.iterrows():
        col_name = row['COLUMN_NAME']
        col_type = classify_column_type(row['DATA_TYPE'])
        
        if col_type == 'numeric':
            numeric_cols.append(col_name)
        elif col_type == 'date':
            date_cols.append(col_name)
        elif col_type == 'boolean':
            boolean_cols.append(col_name)
        else:
            categorical_cols.append(col_name)
    
    # Categorical filters (dropdowns)
    if categorical_cols:
        st.markdown("#### 🏷️ Categorical Filters")
        cat_filter_cols = st.columns(min(3, len(categorical_cols)))
        
        for idx, col_name in enumerate(categorical_cols[:6]):  # Limit to 6 categorical filters
            with cat_filter_cols[idx % 3]:
                unique_values = df[col_name].dropna().unique().tolist()
                
                # Only show multiselect if there are reasonable number of unique values
                if len(unique_values) <= 50:
                    selected_values = st.multiselect(
                        f"{col_name}",
                        options=sorted(unique_values, key=str),
                        default=[],
                        key=f"cat_{col_name}"
                    )
                    if selected_values:
                        filters[col_name] = {'type': 'categorical', 'value': selected_values}
    
    # Numeric filters (sliders)
    if numeric_cols:
        st.markdown("#### 🔢 Numeric Filters")
        num_filter_cols = st.columns(min(3, len(numeric_cols)))
        
        for idx, col_name in enumerate(numeric_cols[:6]):  # Limit to 6 numeric filters
            with num_filter_cols[idx % 3]:
                col_data = df[col_name].dropna()
                if len(col_data) > 0:
                    min_val = float(col_data.min())
                    max_val = float(col_data.max())
                    
                    if min_val < max_val:
                        # Determine step based on data type
                        if col_data.dtype in ['int64', 'int32']:
                            step = 1.0
                        else:
                            step = (max_val - min_val) / 100
                        
                        selected_range = st.slider(
                            f"{col_name}",
                            min_value=min_val,
                            max_value=max_val,
                            value=(min_val, max_val),
                            step=step,
                            key=f"num_{col_name}"
                        )
                        
                        # Only add filter if range is modified
                        if selected_range != (min_val, max_val):
                            filters[col_name] = {'type': 'numeric', 'value': selected_range}
    
    # Date filters (date range)
    if date_cols:
        st.markdown("#### 📅 Date Filters")
        date_filter_cols = st.columns(min(3, len(date_cols)))
        
        for idx, col_name in enumerate(date_cols[:3]):  # Limit to 3 date filters
            with date_filter_cols[idx % 3]:
                col_data = pd.to_datetime(df[col_name].dropna())
                if len(col_data) > 0:
                    min_date = col_data.min().date()
                    max_date = col_data.max().date()
                    
                    date_range = st.date_input(
                        f"{col_name}",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key=f"date_{col_name}"
                    )
                    
                    if isinstance(date_range, tuple) and len(date_range) == 2:
                        if date_range != (min_date, max_date):
                            filters[col_name] = {'type': 'date', 'value': date_range}
    
    # Boolean filters
    if boolean_cols:
        st.markdown("#### ✅ Boolean Filters")
        bool_filter_cols = st.columns(min(3, len(boolean_cols)))
        
        for idx, col_name in enumerate(boolean_cols[:3]):
            with bool_filter_cols[idx % 3]:
                selected_bool = st.radio(
                    f"{col_name}",
                    options=['All', 'True', 'False'],
                    horizontal=True,
                    key=f"bool_{col_name}"
                )
                if selected_bool != 'All':
                    filters[col_name] = {'type': 'boolean', 'value': selected_bool}
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # ==========================================================================
    # APPLY FILTERS AND DISPLAY DATA
    # ==========================================================================
    
    # Apply filters
    filtered_df = apply_filters(df, filters)
    
    # Display filter summary
    if filters:
        st.info(f"🔍 **Active Filters:** {len(filters)} | Showing {len(filtered_df):,} of {len(df):,} records")
    
    # ==========================================================================
    # DATA DISPLAY
    # ==========================================================================
    
    st.markdown("### 📊 Data View")
    
    # Data display options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Row limit selector
        row_limit_options = {
            "5 rows": 5,
            "20 rows": 20,
            "50 rows": 50,
            "100 rows": 100,
            "All rows": None
        }
        selected_limit = st.selectbox(
            "📏 Display Limit",
            options=list(row_limit_options.keys()),
            index=1,  # Default to 20 rows
            help="Choose how many rows to display in the data view"
        )
        row_limit = row_limit_options[selected_limit]
    
    with col3:
        # Export button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"{selected_schema}_{selected_table}_export.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Apply row limit for display
    if row_limit is not None:
        display_df = filtered_df.head(row_limit)
        st.caption(f"Showing {len(display_df):,} of {len(filtered_df):,} filtered records")
    else:
        display_df = filtered_df
        st.caption(f"Showing all {len(filtered_df):,} filtered records")
    
    # Display dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )
    
    # ==========================================================================
    # VISUALIZATIONS
    # ==========================================================================
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📈 Quick Insights")
    
    viz_col1, viz_col2 = st.columns(2)
    
    # Find good columns for visualization
    viz_categorical = [c for c in categorical_cols if len(filtered_df[c].unique()) <= 15 and len(filtered_df[c].unique()) > 1]
    viz_numeric = [c for c in numeric_cols if filtered_df[c].notna().sum() > 0]
    
    with viz_col1:
        if viz_categorical:
            selected_cat_viz = st.selectbox(
                "Select categorical column for distribution:",
                options=viz_categorical,
                key="viz_cat_select"
            )
            
            if selected_cat_viz:
                cat_counts = filtered_df[selected_cat_viz].value_counts().head(10)
                st.bar_chart(cat_counts)
                st.caption(f"Distribution of {selected_cat_viz} (Top 10)")
        else:
            st.info("No suitable categorical columns for visualization")
    
    with viz_col2:
        if viz_numeric and viz_categorical:
            selected_num_viz = st.selectbox(
                "Select numeric column for aggregation:",
                options=viz_numeric,
                key="viz_num_select"
            )
            
            selected_group_viz = st.selectbox(
                "Group by:",
                options=viz_categorical,
                key="viz_group_select"
            )
            
            if selected_num_viz and selected_group_viz:
                agg_data = filtered_df.groupby(selected_group_viz)[selected_num_viz].mean().head(10)
                st.bar_chart(agg_data)
                st.caption(f"Average {selected_num_viz} by {selected_group_viz} (Top 10)")
        elif viz_numeric:
            selected_num_viz = st.selectbox(
                "Select numeric column for histogram:",
                options=viz_numeric,
                key="viz_num_hist"
            )
            if selected_num_viz:
                st.bar_chart(filtered_df[selected_num_viz].value_counts().sort_index().head(20))
                st.caption(f"Distribution of {selected_num_viz}")
        else:
            st.info("No suitable numeric columns for visualization")
    
    # ==========================================================================
    # SUMMARY STATISTICS
    # ==========================================================================
    
    if viz_numeric:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📉 Summary Statistics")
        
        # Select columns for statistics
        stats_cols = st.multiselect(
            "Select numeric columns for statistics:",
            options=viz_numeric,
            default=viz_numeric[:3] if len(viz_numeric) >= 3 else viz_numeric,
            key="stats_cols"
        )
        
        if stats_cols:
            stats_df = filtered_df[stats_cols].describe()
            st.dataframe(stats_df, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #6c757d; font-size: 0.85rem;'>"
        "Higher Education Data Explorer | Powered by Streamlit in Snowflake"
        "</p>",
        unsafe_allow_html=True
    )

# =============================================================================
# RUN APPLICATION
# =============================================================================

if __name__ == "__main__":
    main()
