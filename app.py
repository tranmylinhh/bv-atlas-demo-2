import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="🛡️", layout="wide")

# --- 2. CSS GIAO DIỆN (Tinh chỉnh cho giống Chat App thật) ---
st.markdown("""
<style>
    /* Nền tối sang trọng */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    /* Bong bóng chat User */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #262730; 
        border-radius: 15px;
        padding: 15px;
    }
    /* Bong bóng chat Bot */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1E1E2E; 
        border-radius: 15px; 
        padding: 15px;
        border: 1px solid #363945;
    }
    /* Ẩn menu mặc định */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI API KEY ---
if 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    # Dùng model ổn định nhất
    model = genai.GenerativeModel('gemini-1.5-flash')
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

# --- 5. SYSTEM PROMPT (NHÂN CÁCH HÓA) ---
SYSTEM_PROMPT = """
VAI TRÒ:
Bạn là BV-Atlas, một trợ lý AI trẻ trung, nhiệt tình và chuyên nghiệp của Ban Marketing Bảo Việt.
Bạn đang nói chuyện với đồng nghiệp trong công ty.

PHONG CÁCH GIAO TIẾP (QUAN TRỌNG):
- Xưng hô: "Mình" (hoặc BV-Atlas) và "Bạn" (hoặc Anh/Chị nếu người dùng xưng hô trước).
- Giọng điệu: Tự nhiên, cởi mở, như người thật. Dùng các từ đệm nhẹ nhàng (nhé, ạ, đây ạ...).
- Cảm xúc: Sử dụng Emoji 😊, 🛡️, 📎 một cách tinh tế để cuộc hội thoại sinh động hơn.

QUY TẮC TRẢ LỜI:
1. KHI CHÀO HỎI: Đừng liệt kê tài liệu ngay. Hãy chào thân thiện: "Chào bạn! 👋 Mình là BV-Atlas. Hôm nay bạn cần tìm thông tin gì về An Gia, Tâm Bình hay các chương trình khuyến mãi mới không?"
2. KHI HỎI LINK TẢI: "Gửi bạn link tải brochure An Gia nhé: [Link] 📎" (Đi thẳng vào vấn đề).
3. KHI HỎI KHUYẾN MẠI: Tóm tắt ngắn gọn 3 ý chính (Thời gian, Đối tượng, Quà) rồi hỏi lại: "Bạn có cần thêm thể lệ chi tiết không?"
4. NẾU KHÔNG BIẾT: "Ui, thông tin này hiện tại chưa được cập nhật trong hệ thống của mình rồi 😅. Bạn vui lòng liên hệ trực tiếp Ms. Linh (Ban Marketing) để được hỗ trợ nhanh nhất nhé!"
"""

# --- 6. GIAO DIỆN NGƯỜI DÙNG ---

# === SIDEBAR (CỘT TRÁI - Dành cho Visual Search) ===
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Bao_Viet_Holdings_Logo.svg/1200px-Bao_Viet_Holdings_Logo.svg.png", width=180)
    st.markdown("### 📸 Tra cứu bằng Ảnh")
    st.caption("Upload poster/banner để hỏi thông tin.")
    
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh bạn vừa tải lên", use_container_width=True)
        st.success("Ảnh đã sẵn sàng! Hãy đặt câu hỏi bên khung chat.")

# === MAIN SCREEN (KHUNG CHAT CHÍNH) ===
st.title("🛡️ BV-Atlas: Marketing Assistant")

# Kiểm tra dữ liệu
if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file `Du_lieu_BV_Atlas.docx` trên GitHub.")

# Khởi tạo chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! 👋 Mình là BV-Atlas đây. Hôm nay mình có thể giúp gì cho bạn nè? (Tìm tài liệu, check khuyến mãi, hay tìm ảnh?)"}]

# Hiện lịch sử chat
for msg in st.session_state.messages:
    avatar = "🛡️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# === Ô NHẬP LIỆU (TỰ ĐỘNG DÍNH DƯỚI ĐÁY) ===
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # 1. Hiện câu hỏi user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 2. Xử lý trả lời
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
