import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import docx
from PIL import Image

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="BV-Atlas Pro", page_icon="🛡️", layout="wide")

# 2. CSS GIAO DIỆN DARK MODE & CARD
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #262730; padding: 20px; border-radius: 10px;
    }
    h1 { color: #4F8BF9 !important; }
</style>
""", unsafe_allow_html=True)

# 3. KẾT NỐI API
if 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
else:
    st.error("⚠️ Chưa nhập API Key trong Secrets!")
    st.stop()

# 4. HÀM XỬ LÝ FILE
def get_files_text(uploaded_files):
    text = ""
    for file in uploaded_files:
        ext = file.name.split(".")[-1].lower()
        try:
            if ext == "pdf":
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages: text += page.extract_text() or ""
            elif ext == "docx":
                doc = docx.Document(file)
                for para in doc.paragraphs: text += para.text + "\n"
            elif ext == "txt":
                text += file.read().decode("utf-8") + "\n"
        exceptException: pass
    return text

# 5. GIAO DIỆN CHÍNH
st.title("🛡️ BV-Atlas: Marketing Assistant")
st.markdown("---")

col_chat, col_img = st.columns([1.5, 1])

# --- CỘT TRÁI: CHATBOT ---
with col_chat:
    st.subheader("💬 Chat & Tra cứu")
    
    # Nạp kiến thức
    with st.expander("📂 Nạp tài liệu (Word/PDF) cho Bot"):
        uploaded_docs = st.file_uploader("Upload tài liệu:", accept_multiple_files=True, type=['pdf', 'docx', 'txt'])
        knowledge_text = ""
        if uploaded_docs:
            with st.spinner("Đang đọc..."):
                knowledge_text = get_files_text(uploaded_docs)
                st.success(f"Đã học {len(uploaded_docs)} tài liệu!")

    # Chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Xin chào! Mình là BV-Atlas. Bạn cần tìm thông tin gì?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🛡️" if msg["role"]=="assistant" else "👤"):
            st.markdown(msg["content"])

# --- CỘT PHẢI: VISUAL SEARCH ---
with col_img:
    st.subheader("🖼️ Phân tích Ảnh")
    uploaded_img = st.file_uploader("Upload Poster/Banner:", type=['jpg', 'png', 'jpeg'])
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)

# --- XỬ LÝ LOGIC ---
if prompt := st.chat_input("Nhập câu hỏi..."):
    # Hien cau hoi
    st.session_state.messages.append({"role": "user", "content": prompt})
    with col_chat:
        with st.chat_message("user", avatar="👤"): st.markdown(prompt)

    # Xu ly tra loi
    with col_chat:
        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("Đang suy nghĩ..."):
                try:
                    # Model Flash (Bản ổn định nhất)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Ghep Prompt
                    parts = []
                    if knowledge_text:
                        parts.append(f"DỰA VÀO TÀI LIỆU SAU ĐỂ TRẢ LỜI:\n{knowledge_text}\n\n")
                    
                    if img_data:
                        parts.append("Hãy phân tích hình ảnh này.")
                        parts.append(img_data)
                    
                    parts.append(f"Câu hỏi: {prompt}")
                    
                    response = model.generate_content(parts)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Lỗi: {e}")
