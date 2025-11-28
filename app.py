import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="🛡️", layout="wide")

# --- 2. CSS GIAO DIỆN (Chat App Chuẩn) ---
st.markdown("""
<style>
    /* Nền tối */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    /* Bong bóng chat User */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #1E252B; 
        border-radius: 15px;
        border: 1px solid #444;
    }
    /* Bong bóng chat Bot */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #262730; 
        border-radius: 15px;
        border: 1px solid #363945;
    }
    /* Ẩn menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI API KEY ---
if 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    
    # === SỬA LỖI TẠI ĐÂY ===
    # Dùng bản 002 (Bản mới nhất của dòng Flash ổn định)
    # Nó khắc phục được lỗi 404 của bản 001 và lỗi 429 của bản 2.0
    model = genai.GenerativeModel('gemini-1.5-flash-002')
    
else:
    st.error("⚠️ Chưa nhập API Key trong Secrets!")
    st.stop()

# --- 4. HÀM ĐỌC DỮ LIỆU ---
@st.cache_resource
def load_knowledge_base():
    file_path = "Du_lieu_BV_Atlas.docx"
    if not os.path.exists(file_path): return None
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip(): full_text.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text for cell in row.cells]
                full_text.append(" | ".join(row_text))
        return '\n'.join(full_text)
    except Exception as e: return f"Lỗi đọc file: {e}"

KNOWLEDGE_TEXT = load_knowledge_base()

# --- 5. SYSTEM PROMPT (Thân thiện & Human) ---
SYSTEM_PROMPT = """
VAI TRÒ:
Bạn là BV-Atlas, trợ lý AI trẻ trung, nhiệt tình của Ban Marketing Bảo Việt.

PHONG CÁCH:
- Xưng hô: "Mình" (BV-Atlas) và "Bạn".
- Giọng điệu: Tự nhiên, dùng emoji 😊, 🛡️, 📎. Tránh máy móc.

QUY TẮC:
1. KHI CHÀO: "Chào bạn! 👋 Mình là BV-Atlas đây. Hôm nay mình có thể giúp gì cho bạn nè? (Tìm tài liệu, check khuyến mãi, hay tìm ảnh?)"
2. KHI HỎI LINK: "Gửi bạn link tải brochure An Gia nhé: [Link] 📎" (Đi thẳng vào vấn đề).
3. KHI HỎI KHUYẾN MẠI: Tóm tắt 3 ý chính (Thời gian, Đối tượng, Quà) rồi hỏi lại: "Bạn có cần thêm thể lệ chi tiết không?"
4. KHÔNG BIẾT: "Ui, thông tin này mình chưa có rồi 😅. Bạn liên hệ Ms. Linh (Marketing) giúp mình nhé!"
"""

# --- 6. GIAO DIỆN ---

# === SIDEBAR (Visual Search) ===
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Bao_Viet_Holdings_Logo.svg/1200px-Bao_Viet_Holdings_Logo.svg.png", width=180)
    st.markdown("### 📸 Tra cứu Ảnh")
    st.info("Upload poster/banner để hỏi thông tin.")
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)
        st.success("Ảnh đã sẵn sàng!")

# === MAIN (Chatbot) ===
st.title("🛡️ BV-Atlas: Marketing Assistant")

# Kiểm tra dữ liệu
if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file `Du_lieu_BV_Atlas.docx` trên GitHub.")

# Khởi tạo chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! 👋 Mình là BV-Atlas đây. Hôm nay mình có thể giúp gì cho bạn nè?"}]

# Hiện lịch sử chat
for msg in st.session_state.messages:
    avatar = "🛡️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# === INPUT (Xử lý thông minh) ===
if prompt := st.chat_input("Nhập câu hỏi... (VD: Tải tờ rơi An Gia)"):
    # 1. Hiện câu hỏi user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Bot trả lời
    with st.chat_message("assistant", avatar="🛡️"):
        with st.spinner("Đang tra cứu..."):
            try:
                # Ghép Prompt
                final_prompt = [f"{SYSTEM_PROMPT}\n\n=== DỮ LIỆU NỘI BỘ ===\n{KNOWLEDGE_TEXT}\n"]
                
                if img_data:
                    final_prompt.append("User gửi kèm ảnh bên Sidebar. Hãy phân tích ảnh này dựa trên Dữ liệu nội bộ.")
                    final_prompt.append(img_data)
                
                final_prompt.append(f"\nCÂU HỎI USER: {prompt}")
                
                # Gọi Gemini
                response = model.generate_content(final_prompt)
                
                # Hiện kết quả
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Lỗi kết nối: {e}")
