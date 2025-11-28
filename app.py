import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os

st.set_page_config(page_title="BV-Atlas Debug", page_icon="🔧", layout="wide")

# --- CSS ---
st.markdown("""<style>.stApp { background-color: #0E1117; color: #FAFAFA; }</style>""", unsafe_allow_html=True)

# --- SIDEBAR: KHU VỰC TEST MODEL ---
with st.sidebar:
    st.title("🔧 BẢNG ĐIỀU KHIỂN")
    
    # 1. Nhập Key
    if 'GOOGLE_API_KEY' in st.secrets:
        api_key = st.secrets['GOOGLE_API_KEY']
        st.success("✅ Đã nhận API Key")
    else:
        api_key = st.text_input("Nhập API Key:", type="password")

    st.divider()
    
    # 2. MENU CHỌN MODEL ĐỂ TEST
    st.markdown("### 🧪 Test Model")
    selected_model = st.selectbox(
        "Chọn model muốn thử:",
        [
            "gemini-pro",           # Bản 1.0 ổn định nhất
            "gemini-1.5-flash",     # Bản mới nhanh nhất
            "gemini-1.5-pro",       # Bản mới thông minh nhất
            "gemini-1.0-pro"        # Bản cũ dự phòng
        ]
    )
    
    # Nút bấm kiểm tra
    if st.button("🔴 BẤM ĐỂ KIỂM TRA KẾT NỐI"):
        if not api_key:
            st.error("Chưa có Key!")
        else:
            try:
                genai.configure(api_key=api_key)
                test_model = genai.GenerativeModel(selected_model)
                response = test_model.generate_content("Xin chào, bạn có hoạt động không?")
                st.success(f"✅ THÀNH CÔNG! Model {selected_model} hoạt động tốt.")
                st.info(f"Trả lời: {response.text}")
            except Exception as e:
                st.error(f"❌ THẤT BẠI: {e}")

# --- PHẦN CHÍNH: CHATBOT (Sử dụng model đã chọn bên trái) ---
st.title(f"🛡️ BV-Atlas (Đang chạy: {selected_model})")

# Logic đọc file (Giữ nguyên)
@st.cache_resource
def load_knowledge_base():
    file_path = "Du_lieu_BV_Atlas.docx"
    if not os.path.exists(file_path): return None
    try:
        doc = docx.Document(file_path)
        text = []
        for para in doc.paragraphs: text.append(para.text)
        return '\n'.join(text)
    except: return None

KNOWLEDGE = load_knowledge_base()

# Logic Chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Mình là BV-Atlas. Hãy chọn Model bên trái để test thử nhé!"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # CẤU HÌNH THEO LỰA CHỌN CỦA BẠN
            genai.configure(api_key=api_key)
            active_model = genai.GenerativeModel(selected_model)
            
            # Gửi tin nhắn
            if KNOWLEDGE:
                full_prompt = f"Dữ liệu:\n{KNOWLEDGE}\n\nCâu hỏi: {prompt}"
            else:
                full_prompt = prompt
                
            response = active_model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Lỗi: {e}")
