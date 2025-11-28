import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="🛡️", layout="wide")

# --- 2. CSS GIAO DIỆN (Dark Mode & Professional) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    /* Bong bóng chat */
    .stChatMessage { background-color: #262730; border-radius: 10px; padding: 10px; margin-bottom: 10px;}
    /* Ẩn icon github mặc định */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI API KEY ---
if 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ Lỗi: Chưa kết nối API Key. Vui lòng báo Admin.")
    st.stop()

# --- 4. HÀM ĐỌC DỮ LIỆU TỪ HỆ THỐNG (GITHUB) ---
@st.cache_resource # Giúp load 1 lần dùng mãi mãi, không load lại gây chậm
def load_knowledge_base():
    file_path = "Du_lieu_BV_Atlas.docx" # Tên file bạn đã up lên GitHub
    
    if not os.path.exists(file_path):
        return None # Không tìm thấy file
        
    try:
        doc = docx.Document(file_path)
        full_text = []
        # Đọc văn bản
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        # Đọc bảng biểu (Table)
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text for cell in row.cells]
                full_text.append(" | ".join(row_text))
        return '\n'.join(full_text)
    except Exception as e:
        return f"Lỗi đọc file: {e}"

# Tự động nạp dữ liệu ngay khi mở App
KNOWLEDGE_TEXT = load_knowledge_base()

# --- 5. SYSTEM PROMPT ---
SYSTEM_PROMPT = """
VAI TRÒ: Bạn là BV-Atlas, trợ lý AI chuyên nghiệp của Ban Marketing Bảo Việt.
NHIỆM VỤ: Trả lời câu hỏi dựa trên DỮ LIỆU ĐƯỢC CUNG CẤP bên dưới.

QUY TẮC:
1. Nếu User hỏi tài liệu/link: Lấy link chính xác trong dữ liệu gửi cho họ.
2. Nếu User hỏi Khuyến mãi: Tóm tắt Thời gian, Đối tượng, Quà tặng.
3. Nếu không có thông tin trong dữ liệu: Trả lời "Hiện tại mình chưa có thông tin này, vui lòng liên hệ Ms. Linh (Ban Marketing)."
4. Thái độ: Thân thiện, xưng hô "Mình" - "Bạn".
"""

# --- 6. GIAO DIỆN NGƯỜI DÙNG (USER UI) ---

# SIDEBAR: Chỉ để User upload ảnh (Visual Search)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Bao_Viet_Holdings_Logo.svg/1200px-Bao_Viet_Holdings_Logo.svg.png", width=180)
    st.markdown("---")
    st.markdown("### 📸 Tìm kiếm bằng Ảnh")
    st.info("Upload Poster/Banner CTKM để hỏi chi tiết.")
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'])
    
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh bạn vừa tải lên", use_container_width=True)

# MAIN SCREEN: Chatbot
st.title("🛡️ BV-Atlas: Marketing Assistant")

# Kiểm tra dữ liệu nạp thành công chưa
if KNOWLEDGE_TEXT is None:
    st.error("🚨 CẢNH BÁO ADMIN: Chưa tìm thấy file `Du_lieu_BV_Atlas.docx` trên hệ thống. Vui lòng upload lên GitHub.")
elif "Lỗi đọc file" in KNOWLEDGE_TEXT:
    st.error(f"🚨 CẢNH BÁO ADMIN: {KNOWLEDGE_TEXT}")
else:
    # Nếu dữ liệu OK thì hiện Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Mình là BV-Atlas. Mình đã học xong các tài liệu về An Gia, Tâm Bình và CTKM mới nhất. Bạn cần hỗ trợ gì không?"}]

    # Hiện lịch sử chat
    for msg in st.session_state.messages:
        avatar = "🛡️" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Xử lý câu hỏi
    if prompt := st.chat_input("Nhập câu hỏi... (VD: Gửi link tờ rơi An Gia)"):
        # 1. Hiện câu hỏi user
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # 2. Xử lý trả lời
        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("Đang tra cứu dữ liệu nội bộ..."):
                try:
                    # Ghép Prompt
                    final_prompt = [f"{SYSTEM_PROMPT}\n\n=== DỮ LIỆU NỘI BỘ ===\n{KNOWLEDGE_TEXT}\n"]
                    
                    if img_data:
                        final_prompt.append("User gửi kèm ảnh. Hãy phân tích ảnh này dựa trên Dữ liệu nội bộ.")
                        final_prompt.append(img_data)
                    
                    final_prompt.append(f"\nCÂU HỎI USER: {prompt}")
                    
                    # Gọi Gemini
                    response = model.generate_content(final_prompt)
                    
                    # Hiện kết quả
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")
