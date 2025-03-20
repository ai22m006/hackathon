import base64
from PIL import Image
import plotly.express as px
import streamlit as st
import os
from dotenv import load_dotenv
import snowflake.connector
import pandas as pd
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()

def create_conn():
    return snowflake.connector.connect(
        user=os.environ.get("SNOWFLAKE_USER"),
        password=os.environ.get("SNOWFLAKE_PASSWORD"),
        account=os.environ.get("SNOWFLAKE_ACCOUNT"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("SNOWFLAKE_DATABASE"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA"),
    )

def get_context_data(conn, query):
    cur = conn.cursor()
    cur.execute(query)
    headers = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    df = pd.DataFrame(rows, columns=headers)
    return df

def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ---------- SET PAGE CONFIG ----------
st.set_page_config(
    page_title="Caretaker Dashboard",
    layout="wide",
)

# ---------- GLOBAL CSS FOR WHITE CARDS (FORCEFUL!) ----------


# ---------- FUNCTION TO SET BLURRED BACKGROUND + WHITE OVERLAY ----------
def set_blurred_background(image_file, blur_px=6, overlay_opacity=0.4):
    """
    1. Blurs the entire background image.
    2. Adds a semi-transparent white overlay on top of the blurred image.
    3. Leaves text/components crisp.
    """
    with open(image_file, "rb") as f:
        img_data = f.read()
    encoded_img = base64.b64encode(img_data).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: none !important;
        }}
        .stApp:before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -2;
            background: url("data:image/png;base64,{encoded_img}") no-repeat center center fixed;
            background-size: cover;
            filter: blur({blur_px}px);
        }}
        .stApp:after {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            background-color: rgba(255, 255, 255, {overlay_opacity});
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- Call the function with your background image file ---
set_blurred_background("background.jpg", blur_px=6, overlay_opacity=0.4)

# ---------- SIDEBAR WITH LOGO & NAVIGATION ----------
logo_base64 = get_base64("logo.png")

st.sidebar.markdown(
    f"""
    <div style="text-align: center; margin-top: -30px; margin-bottom: 50px">
        <img src="data:image/png;base64,{logo_base64}" width="150">
    </div>
    """,
    unsafe_allow_html=True
)

hide_streamlit_style = """
    <style>
    /* Hide hamburger menu */
    #MainMenu {visibility: hidden;}
    /* Hide footer */
    footer {visibility: hidden;}
    /* Hide header which contains the deploy/share button */
    [data-testid="stHeader"] {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;  /* Adjust this value as needed */
    }
    .stMetric, .stPlotlyChart, .stIFrame  {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        padding: 10px !important;
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    .stMetric:hover, .stPlotlyChart:hover, .stIFrame:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2) !important;
    }
    [data-testid="stSidebar"] button {
        background-color: transparent !important;  /* Transparent background */
        border: 2px solid #ccc !important;         /* Outline */
        border-radius: 8px !important;             /* Rounded corners */
        color: #444 !important;                    /* Text color */
        margin: 0 auto 10px auto !important;       /* Center horizontally & spacing */
        display: block !important;
        width: 80% !important;                     /* Adjust button width */
        cursor: pointer;
        transition: background-color 0.2s ease, transform 0.2s ease;
    }
    /* Hover effect */
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(0, 0, 0, 0.05) !important;
        transform: scale(1.02);
    }
    </style>
    """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
site1 = "Pflege Dashboard"
site2 = "Wochen Empfehlungen"
site3 = "Bewohner Dashboard"
if "page" not in st.session_state:
    st.session_state.page = site1
# Create navigation buttons underneath the logo
# Each button click updates the session state
if st.sidebar.button(site1, key="btn_home"):
    st.session_state.page = site1
if st.sidebar.button(site2, key="btn_site2"):
    st.session_state.page = site2
if st.sidebar.button(site3, key="btn_site3"):
    st.session_state.page = site3

# Retrieve the current page from session state
selected_page = st.session_state.page

st.sidebar.markdown(f"<div style='text-align: center; margin-top: 40px'>Current Page: <b>{selected_page}</b></div>", unsafe_allow_html=True)

if selected_page == site1:
    # Snowflake Connection
    conn = create_conn()

    st.title(site1)
    st.subheader("Guten Morgen Pfleger*in Alex!")
    st.write("Hier ist deine tägliche persönliche Übersicht.")

    # Split the main page into two columns (50/50)
    left_col, right_col = st.columns([1, 1])

    # ---------------------- LEFT COLUMN ----------------------
    with left_col:

        # Top row: two metrics side by side
        top_row1, top_row2 = st.columns(2)

        if  "count_in_care" not in st.session_state:
            query = "SELECT COUNT(PERSON_ID) FROM PERSON WHERE EMPLOYEE = 'Employee A';"
            df_report = get_context_data(conn, query)
            # safe into session
            st.session_state.count_in_care = df_report.iloc[0].iloc[0]

        count_in_care = st.session_state.count_in_care

        with top_row1:
            st.metric("In Pflege heute", count_in_care)
        
        if "outlier_count" not in st.session_state:
            query = """SELECT 
                        COUNT(PERSON_ID) 
                        FROM OUTLIER_DETECTION od
                        JOIN PERSON p USING(od.person_id)
                        JOIN HISTORICAL_DATA HD  ON HD.PERSON_ID = p.person_id AND HD.MEAL_DATE = od.DATE_
                        JOIN APPOINTMENT A ON HD.MEAL_DATE = A.TIME_STAMP AND  P.PERSON_ID = A.PERSON_ID
                        JOIN MEALPLAN MP USING(HD.MEALPLAN_ID, HD.MEAL_DATE)
                        WHERE 
                        DATE_ = DATEADD(DAY, -1, DATE'2025-03-19')
                        AND MEALTIME != 'breakfast'
                        AND APPEARED = 'No'"""
            df_report = get_context_data(conn, query)
            # safe into session
            st.session_state.outlier_count = df_report.iloc[0].iloc[0]
        
        outlier_count = st.session_state.outlier_count
        
        with top_row2:
            st.metric("Daten Ausreißer gefunden", outlier_count)

        st.write("")  # Spacer

        # save into session chek if it is already there
        if "df_pie_query" not in st.session_state:
            query = """SELECT 
                    MEAL_DATE,
                    APPEARED,
                    COUNT(PERSON_ID) AS COUNT
                    FROM HISTORICAL_DATA
                    WHERE MEAL_DATE = DATEADD(DAY, -1, DATE'2025-03-19')
                    GROUP BY APPEARED, MEAL_DATE;"""
            st.session_state.df_pie_query = get_context_data(conn, query)

        df_pie_query = st.session_state.df_pie_query
        
        # Pie Chart
        df_pie = pd.DataFrame({
            'Status': ['War Anwesend', 'Nicht erschienen'],
            'Count': [df_pie_query[df_pie_query["APPEARED"] == "Yes"]["COUNT"].iloc[0], df_pie_query[df_pie_query["APPEARED"] == "No"]["COUNT"].iloc[0]]
        })
        fig = px.pie(df_pie, values='Count', names='Status', title='In Cafeteria gestern erschienen', hole=0.4)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=454,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---------------------- RIGHT COLUMN ----------------------
    with right_col:
        if "df_report" not in st.session_state:
            query = "SELECT * FROM openai_report"
            st.session_state.df_report = get_context_data(conn, query)
        
        df_report = st.session_state.df_report
        if df_report.empty:
            st.write("No reports found.")
        else:
            outlier_df = df_report[df_report["REPORT_TYPE"] == "outlier"]
            if not outlier_df.empty:
                html_content = outlier_df["REPORT"].iloc[0]
                # Force white background for the HTML content
                components.html(html_content, height=600, scrolling=True)
            else:
                st.write("No outlier report found.")

elif selected_page == site2:
    # Snowflake Connection
    conn = create_conn()

    st.title(site2)
    st.subheader("Guten Morgen Pfleger*in Alex!")
    st.write("Pflege Forecast")

    if "df_report" not in st.session_state:
        query = "SELECT * FROM openai_report"
        st.session_state.df_report = get_context_data(conn, query)
    
    df_report = st.session_state.df_report
    if df_report.empty:
        st.write("No reports found.")
    else:
        outlier_df = df_report[df_report["REPORT_TYPE"] == "forecast"]
        if not outlier_df.empty:
            html_content = outlier_df["REPORT"].iloc[0]
            # Force white background for the HTML content
            components.html(html_content, height=600, scrolling=True)
        else:
            st.write("No outlier report found.")

elif selected_page == site3:
    st.title(site3)
    st.subheader("Herzlich Willkommen, lieber Bewohner!")
    st.write("Hier finden Sie Ihre heutige Übersicht.")

    # ----- Wetter Card -----
    st.subheader("Wetter Heute")
    # Dummy data: replace with actual weather API results if desired
    st.write("Sonnig, 25°C")

    # ----- Row 2: Meal Plan & Calendar -----
    col1, col2 = st.columns(2)

    # Meal Plan Card
    with col1:
        st.subheader("Speiseplan (Woche)")
        # Dummy meal plan data
        meal_plan = {
            "Montag": "Nudeln mit Tomatensauce",
            "Dienstag": "Hähnchen mit Reis",
            "Mittwoch": "Gemüsesuppe",
            "Donnerstag": "Fisch mit Kartoffeln",
            "Freitag": "Pizza",
            "Samstag": "Salat mit Brot",
            "Sonntag": "Braten mit Knödel"
        }
        for day, meal in meal_plan.items():
            st.write(f"**{day}**: {meal}")

    # Calendar/Appointments Card
    with col2:
        st.subheader("Kalender – Zukünftige Termine")
        # Dummy appointments data
        appointments = [
            ("23.03.2025", "Arzttermin"),
            ("25.03.2025", "Besuch vom Enkelkind"),
            ("30.03.2025", "Gemeinsames Kaffeetrinken")
        ]
        st.write("**Bevorstehende Termine:**")
        for date, desc in appointments:
            st.write(f"- **{date}**: {desc}")
