import streamlit as st
import os
from dotenv import load_dotenv
import snowflake.connector
import pandas as pd
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()

def create_conn():
    conn = snowflake.connector.connect(
        user=os.environ.get("SNOWFLAKE_USER"),
        password=os.environ.get("SNOWFLAKE_PASSWORD"),
        account=os.environ.get("SNOWFLAKE_ACCOUNT"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("SNOWFLAKE_DATABASE"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA"),
    )
    return conn

def get_context_data(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    headers = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    df = pd.DataFrame(rows, columns=headers)
    return df

def main():
    st.title("OpenAI Report Viewer")
    
    # Connect to Snowflake and fetch the data
    conn = create_conn()
    query = "SELECT * FROM openai_report"
    df = get_context_data(conn, query)
    
    if df.empty:
        st.write("No reports found.")
        return

    # Create a display label for each report combining the report date and type
    report_labels = df.apply(lambda row: f"{row['REPORT_DATE']} - {row['REPORT_TYPE']}", axis=1)
    
    # Let the user select a report
    selected_index = st.selectbox("Select a report", options=df.index, format_func=lambda idx: report_labels[idx])
    selected_report = df.loc[selected_index]
    
    # Display selected report details
    st.subheader("Report Details")
    st.write(f"**Report Date:** {selected_report['REPORT_DATE']}")
    st.write(f"**Report Type:** {selected_report['REPORT_TYPE']}")
    
    # Render the HTML report using Streamlit's HTML component
    components.html(selected_report['REPORT'], height=15000)

if __name__ == '__main__':
    main()
