import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Cấu hình giao diện
st.set_page_config(page_title="Hệ thống Quản lý Học tập SOA", layout="wide")

# Địa chỉ các Microservices
SCORE_SERVICE_URL = "http://127.0.0.1:8001/api/v1"
ANALYTICS_SERVICE_URL = "http://127.0.0.1:8002/api/v1"

st.title("🎓 Dashboard Phân tích Kết quả Sinh viên (SOA)")
st.markdown("---")

# --- PHẦN 1: TỔNG QUAN (Từ Analytics Service) ---
st.header("📊 Tổng quan kết quả học tập")

try:
    ov_resp = requests.get(f"{ANALYTICS_SERVICE_URL}/analytics/overview")
    if ov_resp.status_code == 200:
        overview = ov_resp.json()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng số sinh viên", overview['total_students'])
        col2.metric("Số lượng Đậu", overview['passed_count'])
        col3.metric("Số lượng Rớt", overview['failed_count'], delta_color="inverse")
        col4.metric("Tỷ lệ Đậu", f"{overview['pass_rate']}%")
except:
    st.error("Không thể kết nối tới Analytics Service (Port 8002)")

# --- PHẦN 2: BIỂU ĐỒ (Từ Analytics Service) ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Phân phối điểm chữ (A-F)")
    try:
        dist_resp = requests.get(f"{ANALYTICS_SERVICE_URL}/analytics/gpa-distribution")
        if dist_resp.status_code == 200:
            dist_data = dist_resp.json()
            df_dist = pd.DataFrame(list(dist_data.items()), columns=['Grade', 'Count'])
            fig = px.bar(df_dist, x='Grade', y='Count', color='Grade', 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
    except:
        st.write("Đang chờ dữ liệu...")

with col_right:
    st.subheader("Danh sách sinh viên Nguy cơ cao (At-Risk)")
    try:
        risk_resp = requests.get(f"{ANALYTICS_SERVICE_URL}/analytics/at-risk")
        if risk_resp.status_code == 200:
            df_risk = pd.DataFrame(risk_resp.json())
            st.dataframe(df_risk, use_container_width=True)
    except:
        st.write("Đang chờ dữ liệu...")

# --- PHẦN 3: TRA CỨU CHI TIẾT (Từ Score Service) ---
st.markdown("---")
st.header("🔍 Tra cứu điểm chi tiết")

student_id = st.number_input("Nhập MSSV cần tra cứu:", min_value=1, step=1)
if st.button("Truy vấn"):
    try:
        score_resp = requests.get(f"{SCORE_SERVICE_URL}/scores/student/{search_id}")
        if score_resp.status_code == 200:
            data = score_resp.json()
            
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Họ tên:** {data['name']}")
            c2.write(f"**Điểm hệ 10:** {data['grade_10']}")
            
            if data['is_failing']:
                c3.error(f"⚠️ Trạng thái: {data['warning']}")
            else:
                c3.success("✅ Trạng thái: Đạt")
        else:
            st.warning("Không tìm thấy sinh viên này.")
    except:
        st.error("Không thể kết nối tới Score Service (Port 8001)")