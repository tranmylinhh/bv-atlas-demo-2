import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="img/favicon.png", layout="wide")

# --- CẤU HÌNH AVATAR (Dùng Link Online để đảm bảo hiện ảnh 100%) ---
BOT_AVATAR = "logo.jpg"

# --- 2. CSS GIAO DIỆN (LIGHT MODE - CHUẨN ĐẸP) ---
st.markdown("""
<style>
    /* Nền Trắng */
    .stApp { background-color: #FFFFFF; color: #000000; }
    
    /* Bong bóng chat USER (Đen - Chữ Trắng) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #000000; 
        color: #FFFFFF !important;
        border-radius: 20px 20px 0px 20px;
        padding: 15px;
        border: none;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) p { color: #FFFFFF !important; }
    
    /* Bong bóng chat BOT (Xám Nhạt - Chữ Đen) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #F2F4F6;
        color: #000000 !important;
        border-radius: 20px 20px 20px 0px;
        padding: 15px;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) p { color: #000000 !important; }

    /* Link Xanh */
    .stChatMessage a { color: #0068C9 !important; font-weight: 600; text-decoration: none; }
    .stChatMessage a:hover { text-decoration: underline; }

    /* Ẩn Header */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI API KEY ---
if 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    st.error("⚠️ Chưa nhập API Key.")
    st.stop()

# --- 4. HÀM ĐỌC DỮ LIỆU TỪ GITHUB ---
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

# --- 5. SYSTEM PROMPT (FIX LỖI CHÀO LẶP + PHONG CÁCH CHUYÊN NGHIỆP) ---
current_date = datetime.now().strftime("%d/%m/%Y")

SYSTEM_PROMPT = f"""
VAI TRÒ:
Bạn là BV-Atlas, trợ lý AI chuyên nghiệp của Ban Marketing Bảo hiểm Bảo Việt.
Đối tượng phục vụ: Cán bộ nhân viên nội bộ (đã am hiểu cơ bản về sản phẩm).
Nhiệm vụ: Hỗ trợ tra cứu nhanh tài liệu, thông số, quy định. KHÔNG tư vấn bán hàng sáo rỗng.

THÔNG TIN THỜI GIAN: Hôm nay là {current_date}.

QUY TẮC TRẢ LỜI:
1. KHÔNG LẶP LẠI LỜI CHÀO:
   - Kiểm tra lịch sử chat. Nếu đã chào rồi thì đi thẳng vào câu trả lời.
   - Không dùng các câu thừa thãi như "Cảm ơn bạn đã hỏi", "Câu hỏi rất hay".

2. TRA CỨU CHÍNH XÁC:
   - User hỏi tài liệu -> Gửi Link ngay.
   - User hỏi thông tin -> Trích xuất dữ liệu từ file Word (Quyền lợi, Phí, Thời hạn...).
   - Nếu không có thông tin -> Hướng dẫn liên hệ Ms. Linh (Ban Marketing).

3. XỬ LÝ KHUYẾN MÃI:
   - Chỉ liệt kê CTKM còn hạn (Kết thúc >= {current_date}).
   - Phân biệt rõ: Bảo lãnh/Bồi thường là DỊCH VỤ, không phải Khuyến mãi.

4. PHONG CÁCH:
   - Ngắn gọn, súc tích, chuyên nghiệp.
   - Xưng hô: "Mình" - "Bạn".
"""

# --- 6. GIAO DIỆN CHÍNH ---

# === SIDEBAR ===
with st.sidebar:
    st.image(BOT_AVATAR, width=150)
    st.markdown("---")
    st.markdown("### 📸 Tra cứu Ảnh")
    uploaded_img = st.file_uploader("Upload ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)

# === MAIN ===
st.title("🛡️ BV-Atlas: Marketing Assistant")

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file `Du_lieu_BV_Atlas.docx` trên GitHub.")

# Khởi tạo lịch sử
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Chào bạn! 👋 Mình là BV-Atlas. Bạn cần tra cứu tài liệu hay thông tin gì hôm nay?"}
    ]

# Hiển thị lịch sử
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=BOT_AVATAR):
            st.markdown(msg["content"])
    else:
        with st.chat_message(msg["role"], avatar="👤"):
            st.markdown(msg["content"])

# Ô Nhập liệu
if prompt := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("..."):
            try:
                # Lấy lịch sử để tránh chào lại
                history_text = ""
                for msg in st.session_state.messages:
                    role_name = "User" if msg["role"] == "user" else "BV-Atlas"
                    history_text += f"{role_name}: {msg['content']}\n"

                final_prompt = [
                    f"{SYSTEM_PROMPT}\n",
                    f"=== DỮ LIỆU NỘI BỘ ===\n{KNOWLEDGE_TEXT}\n",
                    f"=== LỊCH SỬ CHAT ===\n{history_text}\n",
                    f"CÂU HỎI MỚI NHẤT: {prompt}"
                ]
                
                if img_data:
                    final_prompt.append("User gửi ảnh. Hãy phân tích.")
                    final_prompt.append(img_data)
                
                response = model.generate_content(final_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
