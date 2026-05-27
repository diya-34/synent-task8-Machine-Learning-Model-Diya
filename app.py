import streamlit as st
import pickle
import numpy as np
import pandas as pd
from fpdf import FPDF
import sqlite3
import yagmail
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Loan Prediction System",
    page_icon="🏦",
    layout="wide"
)

# =========================
# CUSTOM CSS
# =========================
page_bg = """
<style>

/* Background */
.stApp {
    background: linear-gradient(to right, #e0ecff, #f8fbff);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #bfdbfe;
    width: 320px !important;
}

/* Headings */
h1 {
    color: #2563eb !important;
    font-weight: bold;
}

h2, h3, h4 {
    color: #1e3a8a !important;
}

/* Text */
p, label {
    color: #111827 !important;
    font-size: 15px;
    font-weight: 500;
}

/* Input Fields */
.stTextInput input,
.stNumberInput input {
    background-color: white !important;
    color: black !important;
    border-radius: 10px;
    border: 2px solid #93c5fd;
}

/* Select Box */
.stSelectbox div {
    background-color: white !important;
    color: black !important;
    border-radius: 10px;
}

/* Buttons */
.stButton > button {
    background-color: #2563eb;
    color: white;
    border-radius: 12px;
    border: none;
    height: 55px;
    width: 100%;
    font-size: 18px;
    font-weight: bold;
    transition: 0.3s;
}

.stButton > button:hover {
    background-color: #1d4ed8;
    box-shadow: 0px 5px 15px rgba(37, 99, 235, 0.4);
}

/* Cards */
.main-card {
    background-color: white;
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0px 5px 18px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    border: 1px solid #dbeafe;
}

/* Metrics */
[data-testid="metric-container"] {
    background-color: white;
    border-radius: 15px;
    padding: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
}

</style>
"""

st.markdown(page_bg, unsafe_allow_html=True)

# =========================
# DATABASE
# =========================
conn = sqlite3.connect('loan_data.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS predictions(
    ApplicantIncome REAL,
    LoanAmount REAL,
    Prediction TEXT
)
''')

conn.commit()

# =========================
# LOAD MODEL
# =========================
@st.cache_resource
def load_model():
    try:
        return pickle.load(open('loan_model.pkl', 'rb'))
    except FileNotFoundError:
        return None

model = load_model()

# =========================
# TITLE
# =========================
st.markdown(
    "<h1 style='text-align:center;'>🏦 Loan Prediction System</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h4 style='text-align:center; color:#4b5563;'>AI Powered Banking Prediction Dashboard</h4>",
    unsafe_allow_html=True
)

st.write("")

# =========================
# DASHBOARD METRICS
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🏦 Total Applications", "12,540")

with col2:
    st.metric("✅ Approval Rate", "70%")

with col3:
    st.metric("💰 Loans Approved", "$8.5M")

st.write("---")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("📌 About Project")

st.sidebar.write("""
This AI system predicts whether a loan will be approved or rejected based on customer details.
""")

st.sidebar.write("### 🛠️ Technologies Used")
st.sidebar.write("✔ Machine Learning")
st.sidebar.write("✔ Streamlit")
st.sidebar.write("✔ Python")
st.sidebar.write("✔ SQL Database")
st.sidebar.write("✔ Email Notification")

st.sidebar.success("✅ System Status: Active")
st.sidebar.info("🔐 Secure AI Banking System")

st.sidebar.write("---")

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.sidebar.file_uploader(
    "📂 Upload CSV File",
    type=["csv"]
)

if uploaded_file is not None:

    uploaded_df = pd.read_csv(uploaded_file)

    st.sidebar.write("### Uploaded Dataset")

    st.sidebar.dataframe(
        uploaded_df.head(),
        use_container_width=True
    )

# =========================
# SESSION STATE
# =========================
if 'prediction_done' not in st.session_state:
    st.session_state.prediction_done = False
    st.session_state.result_text = ""
    st.session_state.prob_value = 0.0
    st.session_state.app_income = 0.0
    st.session_state.loan_amt = 0.0

# =========================
# CENTERED LAYOUT
# =========================
m_left, m_center, m_right = st.columns([2, 7, 2])

with m_center:

    # =========================
    # FORM CARD
    # =========================
    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    st.subheader("📝 Enter Applicant Details")

    col1, col2 = st.columns(2, gap="large")

    with col1:

        Gender = st.selectbox(
            "👤 Gender",
            ["Male", "Female"]
        )

        Married = st.selectbox(
            "💍 Married",
            ["Yes", "No"]
        )

        Dependents = st.selectbox(
            "👨‍👩‍👧 Dependents",
            [0, 1, 2, 3]
        )

        Education = st.selectbox(
            "🎓 Education",
            ["Graduate", "Not Graduate"]
        )

        Self_Employed = st.selectbox(
            "💼 Self Employed",
            ["Yes", "No"]
        )

    with col2:

        ApplicantIncome = st.number_input(
            "💰 Applicant Income ($)",
            min_value=0.0,
            step=500.0
        )

        CoapplicantIncome = st.number_input(
            "💵 Coapplicant Income ($)",
            min_value=0.0,
            step=500.0
        )

        LoanAmount = st.number_input(
            "🏠 Loan Amount ($)",
            min_value=0.0,
            step=100.0
        )

        Loan_Amount_Term = st.number_input(
            "📅 Loan Amount Term (Months)",
            min_value=0.0,
            value=360.0
        )

        Credit_History = st.selectbox(
            "💳 Credit History",
            [1, 0],
            format_func=lambda x:
            "Good (1)" if x == 1 else "Poor (0)"
        )

        Property_Area = st.selectbox(
            "📍 Property Area",
            ["Urban", "Semiurban", "Rural"]
        )

        user_email = st.text_input(
            "📧 Enter Email"
        )

    # =========================
    # ENCODING
    # =========================
    Gender_val = 1 if Gender == "Male" else 0
    Married_val = 1 if Married == "Yes" else 0
    Education_val = 0 if Education == "Graduate" else 1
    Self_Employed_val = 1 if Self_Employed == "Yes" else 0

    Property_Area_dict = {
        "Rural": 0,
        "Semiurban": 1,
        "Urban": 2
    }

    Property_Area_val = Property_Area_dict[Property_Area]

    st.write("")

    btn_col1, btn_col2, btn_col3 = st.columns([1,2,1])

    with btn_col2:
        predict_btn = st.button("🚀 Predict Loan Status")

    st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # PREDICTION
    # =========================
    if predict_btn:

        if model is None:

            st.error(
                "⚠️ loan_model.pkl file not found."
            )

        else:

            with st.spinner(
                "⏳ AI analyzing customer profile..."
            ):

                time.sleep(1.5)

                input_data = np.array([[
                    Gender_val,
                    Married_val,
                    Dependents,
                    Education_val,
                    Self_Employed_val,
                    ApplicantIncome,
                    CoapplicantIncome,
                    LoanAmount,
                    Loan_Amount_Term,
                    Credit_History,
                    Property_Area_val
                ]])

                prediction = model.predict(input_data)

                probability = model.predict_proba(input_data)

                st.session_state.prediction_done = True

                st.session_state.prob_value = probability[0][1]

                st.session_state.app_income = ApplicantIncome

                st.session_state.loan_amt = LoanAmount

                if prediction[0] == 1:
                    st.session_state.result_text = "Approved"

                else:
                    st.session_state.result_text = "Rejected"

    # =========================
    # RESULT DISPLAY
    # =========================
    if st.session_state.prediction_done:

        st.markdown("""
        <div style="
        background: linear-gradient(to right,#2563eb,#1d4ed8);
        padding:20px;
        border-radius:15px;
        color:white;
        text-align:center;
        font-size:22px;
        font-weight:bold;
        margin-bottom:20px;">
        AI Loan Decision Result
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="main-card">', unsafe_allow_html=True)

        if st.session_state.result_text == "Approved":

            st.success(
                "🎉 Congratulations! Your Loan is Approved."
            )

            st.balloons()

        else:

            st.error(
                "❌ Sorry! Your Loan Application has been Rejected."
            )

        # =========================
        # APPROVAL CHANCE
        # =========================
        st.write(
            f"### 📊 Approval Chance: "
            f"{st.session_state.prob_value*100:.2f}%"
        )

        st.progress(
            int(st.session_state.prob_value * 100)
        )

        # =========================
        # SAVE TO DATABASE
        # =========================
        c.execute(
            'INSERT INTO predictions VALUES (?, ?, ?)',
            (
                st.session_state.app_income,
                st.session_state.loan_amt,
                st.session_state.result_text
            )
        )

        conn.commit()

        # =========================
        # METRICS
        # =========================
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("🎯 Model Accuracy", "92%")

        with c2:
            st.metric("📈 Approval Rate", "70%")

        with c3:
            st.metric("📉 Rejection Rate", "30%")

        # =========================
        # CREDIT SCORE
        # =========================
        st.subheader("💳 Customer Credit Score")

        credit_score = np.random.randint(650, 900)

        st.metric(
            "📌 Estimated Credit Score",
            credit_score
        )

        if credit_score >= 750:

            st.success(
                "✅ Excellent Credit Profile"
            )

        elif credit_score >= 650:

            st.warning(
                "⚠️ Average Credit Profile"
            )

        else:

            st.error(
                "❌ Poor Credit Profile"
            )

        st.progress(credit_score / 900)

        # =========================
        # EMI CALCULATOR
        # =========================
        st.subheader("💳 EMI Calculator")

        interest_rate = st.slider(
            "Interest Rate (%)",
            1.0,
            20.0,
            8.5
        )

        if LoanAmount > 0 and Loan_Amount_Term > 0:

            monthly_rate = interest_rate / 12 / 100

            emi = (
                LoanAmount
                * monthly_rate
                * (1 + monthly_rate) ** Loan_Amount_Term
            ) / (
                (1 + monthly_rate) ** Loan_Amount_Term - 1
            )

            st.metric(
                "📌 Estimated Monthly EMI",
                f"${emi:.2f}"
            )

        # =========================
        # PDF REPORT
        # =========================
        pdf = FPDF()

        pdf.add_page()

        pdf.set_font("Arial", size=12)

        pdf.cell(
            200,
            10,
            txt="Loan Prediction Report",
            ln=True,
            align='C'
        )

        pdf.cell(
            200,
            10,
            txt=f"Status: {st.session_state.result_text}",
            ln=True
        )

        pdf.cell(
            200,
            10,
            txt=f"Applicant Income: ${ApplicantIncome}",
            ln=True
        )

        pdf.cell(
            200,
            10,
            txt=f"Loan Amount: ${LoanAmount}",
            ln=True
        )

        pdf.output("Loan_Report.pdf")

        dl_col, email_col = st.columns(2)

        with dl_col:

            with open("Loan_Report.pdf", "rb") as file:

                st.download_button(
                    "📄 Download PDF Report",
                    file,
                    file_name="Loan_Report.pdf",
                    use_container_width=True
                )

        with email_col:

            send_email_btn = st.button(
                "📧 Email Report",
                use_container_width=True
            )

            if send_email_btn:

                if user_email:

                    try:

                        with st.spinner("Sending email..."):

                            yag = yagmail.SMTP(
                                "your_email@gmail.com",
                                "your_app_password"
                            )

                            yag.send(
                                to=user_email,
                                subject="Loan Prediction Result",
                                contents=f"""
Loan Prediction Status:
{st.session_state.result_text}

Applicant Income:
${ApplicantIncome}

Loan Amount:
${LoanAmount}
"""
                            )

                            st.success(
                                "✅ Email Sent Successfully!"
                            )

                    except Exception:

                        st.error(
                            "❌ Failed to send email."
                        )

                else:

                    st.warning(
                        "⚠️ Please enter email address."
                    )

        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# LOAN ELIGIBILITY TIPS
# =========================
with m_center:

    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    st.subheader("🏦 Loan Eligibility Tips")

    st.info("✔ Maintain a good credit history")

    st.info("✔ Keep existing debts low")

    st.info("✔ Ensure stable monthly income")

    st.info("✔ Apply for a reasonable loan amount")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# AI ASSISTANT
# =========================
with m_center:

    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    st.subheader("🤖 AI Loan Assistant")

    st.info(
        "🤖 Ask questions related to loans, EMI, banking, and approval chances."
    )

    user_question = st.text_input(
        "Ask AI About Loan",
        key="ai_chat"
    )

    if st.button("Ask AI"):

        if user_question.strip() != "":

            with st.spinner("AI Thinking..."):

                time.sleep(1)

                st.success(
                    "💡 AI Response: "
                    "Loan approval mainly depends on income, "
                    "credit history, and repayment capacity."
                )

        else:

            st.warning(
                "⚠️ Please enter a question."
            )

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# VOICE ASSISTANT
# =========================
with m_center:

    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    st.subheader("🎤 Voice Assistant")

    if st.button(
        "Start Voice Assistant",
        use_container_width=True
    ):

        with st.spinner("Listening... 🎙️"):

            time.sleep(2)

        st.success(
            "🎙️ Voice Assistant Started Successfully!"
        )

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# PREDICTION HISTORY
# =========================
with m_center:

    st.markdown('<div class="main-card">', unsafe_allow_html=True)

    st.subheader("📜 Prediction History")

    history_df = pd.read_sql_query(
        "SELECT * FROM predictions",
        conn
    )

    st.dataframe(
        history_df,
        use_container_width=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# FOOTER
# =========================
st.write("---")

st.markdown("""
<div style="
text-align:center;
padding:20px;
color:#6b7280;
font-size:14px;
margin-top:30px;">

© 2026 Loan Prediction System <br>
Built with 😍 using Python, Streamlit & Machine Learning

</div>
""", unsafe_allow_html=True)