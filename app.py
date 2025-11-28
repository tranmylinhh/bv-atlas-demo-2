import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="🛡️", layout="wide")

# --- 2. CSS GIAO DIỆN (Chat App Chuẩn Zalo/Mess) ---
st.markdown("""
<style>
    /* Nền tối chuyên nghiệp */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    /* Bong bóng chat - User (Xanh đậm) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #005792; 
        border-radius: 15px 15px 0px 15px; /* Bo góc kiểu chat app */
        padding: 15px;
        margin-bottom: 10px;
    }
    /* Bong bóng chat - Bot (Xám tối) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #262730; 
        border-radius: 15px 15px 15px 0px;
        padding: 15px;
        border: 1px solid #363945;
        margin-bottom: 10px;
    }
    /* Ẩn Header/Footer thừa */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI API KEY ---
if 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    # Dùng model 2.0 Flash (đã kiểm chứng chạy OK)
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    st.error("⚠️ Lỗi hệ thống: Chưa nhập API Key.")
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

# --- 5. SYSTEM PROMPT (Update theo yêu cầu Persona) ---
SYSTEM_PROMPT = """
VAI TRÒ:
Bạn là BV-Atlas, trợ lý ảo của Ban Marketing Bảo hiểm Bảo Việt.
Nhiệm vụ: Hỗ trợ đồng nghiệp tra cứu Tài liệu, Sản phẩm, CTKM và Hình ảnh thiết kế.

PHONG CÁCH:
- Xưng hô: "Mình" (hoặc BV-Atlas) và "Bạn".
- Giọng điệu: Chuyên nghiệp nhưng thân thiện, cởi mở, dùng ngôn ngữ tự nhiên.
- Dùng Emoji 😊, 📎, 🛡️ để cuộc hội thoại sinh động.

QUY TẮC ỨNG XỬ (NGHIÊM NGẶT):
1. KHÔNG SPAM: Khi chào hỏi, tuyệt đối KHÔNG liệt kê danh sách tài liệu. Chỉ chào và hỏi nhu cầu.
2. ĐÚNG TRỌNG TÂM: Chỉ cung cấp đúng link/thông tin user hỏi. Không đưa thừa.
3. TRA CỨU ẢNH: 
   - Nếu user gửi ảnh mờ/mô tả ảnh -> Hãy tìm trong dữ liệu xem có mô tả nào khớp không (ví dụ "Poster cô gái áo xanh").
   - Nếu khớp, hãy gửi Link tải ảnh chất lượng cao (High-res) cho user.
4. KHÔNG BIẾT: Nếu không có trong dữ liệu, hướng dẫn liên hệ Ms. Linh (Ban Marketing).
"""

# --- 6. GIAO DIỆN CHÍNH ---

# === SIDEBAR (Chỉ dành cho Upload Ảnh - Để thanh chat chính rộng rãi) ===
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Bao_Viet_Holdings_Logo.svg/1200px-Bao_Viet_Holdings_Logo.svg.png", width=180)
    st.markdown("---")
    st.markdown("### 📸 Tra cứu Ảnh Gốc")
    st.info("Upload ảnh mờ/banner để tìm file thiết kế gốc.")
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh bạn vừa tải lên", use_container_width=True)
        st.success("Đã nhận ảnh! Hãy qua khung chat hỏi chi tiết.")

# === MAIN (CHATBOT) ===
st.title("🛡️ BV-Atlas: Marketing Assistant")

# Cảnh báo nếu chưa có dữ liệu (Chỉ hiện cho Admin biết, User ko cần quan tâm lắm)
if KNOWLEDGE_TEXT is None:
    st.toast("⚠️ Admin ơi, chưa upload file `Du_lieu_BV_Atlas.docx` lên GitHub nhé!", icon="🚨")

# 1. KHỞI TẠO LỊCH SỬ CHAT
if "messages" not in st.session_state:
    # Lời chào chuẩn Ban Marketing
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! 👋 Mình là BV-Atlas, trợ lý AI của Ban Marketing. Hôm nay bạn cần tìm tài liệu sản phẩm, check chương trình khuyến mãi hay tìm file thiết kế nào không?"}
    ]

# 2. HIỂN THỊ LỊCH SỬ (Vòng lặp này nằm TRƯỚC chat_input -> Tin nhắn cũ sẽ ở trên)
for msg in st.session_state.messages:
    avatar = "🛡️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 3. Ô NHẬP LIỆU (Luôn nằm dưới cùng)
if prompt := st.chat_input("Nhập câu hỏi... (VD: Tải tờ rơi An Gia, Tìm ảnh gốc poster này)"):
    # Hiện câu hỏi user ngay lập tức
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Xử lý trả lời
    with st.chat_message("assistant", avatar="🛡️"):
        with st.spinner("Đang tra cứu dữ liệu..."):
            try:
                # Ghép Prompt
                final_prompt = [f"{SYSTEM_PROMPT}\n\n=== DỮ LIỆU NỘI BỘ (Word) ===\n{KNOWLEDGE_TEXT}\n"]
                
                if img_data:
                    final_prompt.append("User đang gửi kèm một bức ảnh bên Sidebar.")
                    final_prompt.append("Nhiệm vụ: Hãy phân tích ảnh này, so sánh với mô tả trong Dữ liệu nội bộ để tìm ra Link tải ảnh gốc/chất lượng cao.")
                    final_prompt.append(img_data)
                
                final_prompt.append(f"\nCÂU HỎI USER: {prompt}")
                
                # Gọi Gemini
                response = model.generate_content(final_prompt)
                
                # Hiện kết quả
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Có lỗi kết nối: {e}")
