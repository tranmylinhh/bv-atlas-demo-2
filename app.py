import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="🛡️", layout="wide")

# --- 2. CSS GIAO DIỆN ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #262730; padding: 20px; border-radius: 10px;
    }
    h1 { color: #4F8BF9 !important; }
    /* Ẩn menu mặc định */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI API KEY ---
if 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    
    # -----------------------------------------------------------
    # QUAN TRỌNG: DÙNG ĐÚNG TÊN MODEL SỐ 6 TRONG DANH SÁCH CỦA BẠN
    # -----------------------------------------------------------
    model = genai.GenerativeModel('gemini-2.0-flash') 
    
else:
    st.error("⚠️ Chưa nhập API Key trong Secrets!")
    st.stop()

# --- 4. HÀM ĐỌC DỮ LIỆU TỪ GITHUB ---
@st.cache_resource
def load_knowledge_base():
    # Đảm bảo bạn đã upload file này lên GitHub
    file_path = "Du_lieu_BV_Atlas.docx"
    
    if not os.path.exists(file_path):
        return None
        
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

# --- 5. SYSTEM PROMPT ---
SYSTEM_PROMPT = """
VAI TRÒ: Bạn là BV-Atlas, trợ lý AI chuyên nghiệp của Ban Marketing Bảo Việt.
NHIỆM VỤ: Trả lời câu hỏi dựa trên DỮ LIỆU ĐƯỢC CUNG CẤP.

QUY TẮC ỨNG XỬ:
1. Nếu User hỏi tài liệu/link: Lấy link chính xác trong dữ liệu gửi cho họ.
2. Nếu User hỏi Khuyến mãi: Tóm tắt Thời gian, Đối tượng, Quà tặng.
3. Nếu không có thông tin: Trả lời "Hiện tại mình chưa có thông tin này, vui lòng liên hệ Ms. Linh (Ban Marketing)."
4. Thái độ: Thân thiện, xưng hô "Mình" - "Bạn". Dùng emoji 😊.
"""

# --- 6. GIAO DIỆN CHÍNH ---
st.title("🛡️ BV-Atlas: Marketing Assistant")

col_chat, col_img = st.columns([2, 1])

# CỘT PHẢI: VISUAL SEARCH
with col_img:
    st.subheader("🖼️ Phân tích Ảnh")
    st.info("Upload Poster/Banner để hỏi thông tin.")
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'])
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)

# CỘT TRÁI: CHATBOT
with col_chat:
    if KNOWLEDGE_TEXT is None:
        st.warning("⚠️ Chưa tìm thấy file `Du_lieu_BV_Atlas.docx`. Hãy upload lên GitHub!")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Mình là BV-Atlas. Mình đã học xong dữ liệu về An Gia, Tâm Bình và các CTKM. Bạn cần hỗ trợ gì không?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🛡️" if msg["role"]=="assistant" else "👤"):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Nhập câu hỏi..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("Đang tra cứu..."):
                try:
                    final_prompt = [f"{SYSTEM_PROMPT}\n\n=== DỮ LIỆU ===\n{KNOWLEDGE_TEXT}\n\nCÂU HỎI: {prompt}"]
                    
                    if img_data:
                        final_prompt.append("User gửi kèm ảnh. Hãy phân tích ảnh này.")
                        final_prompt.append(img_data)
                    
                    # Gọi Model
                    response = model.generate_content(final_prompt)
                    
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    
                except Exception as e:
                    st.error(f"Lỗi: {e}")
