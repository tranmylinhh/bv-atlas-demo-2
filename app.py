import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý thông tin Marketing", page_icon="img/favicon.png", layout="wide")

# --- CẤU HÌNH AVATAR ---
BOT_AVATAR = "logo.jpg"

import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="img/favicon.png", layout="wide")

# --- CẤU HÌNH AVATAR ---
BOT_AVATAR = "logo.jpg"

# --- 2. CSS GIAO DIỆN (LIGHT MODE - CHUẨN YÊU CẦU) ---
st.markdown("""
<style>
    /* 1. Cấu hình Nền & Chữ chung */
    .stApp { 
        background-color: #FFFFFF; 
        color: #000000; 
    }
    
    /* 2. Bong bóng chat USER (Trắng + Viền Xám + Chữ Đen) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #FFFFFF; 
        border: 1px solid #E0E0E0; /* Viền xám nhẹ */
        border-radius: 20px 20px 0px 20px;
        padding: 15px;
        color: #000000 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); /* Đổ bóng nhẹ cho nổi */
    }
    
    /* 3. Bong bóng chat BOT (Xám Nhạt + Chữ Đen) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #F2F4F6; /* Xám nhạt chuẩn chat app */
        border: none;
        border-radius: 20px 20px 20px 0px;
        padding: 15px;
        color: #000000 !important;
    }

    /* 4. Ép màu chữ trong bong bóng chat thành ĐEN tuyệt đối */
    .stChatMessage p, .stChatMessage li, .stChatMessage h1, .stChatMessage h2, .stChatMessage h3 {
        color: #000000 !important;
    }

    /* 5. Link màu Xanh (Blue) chuẩn Marketing */
    .stChatMessage a {
        color: #0068C9 !important;
        font-weight: 600;
        text-decoration: none;
    }
    .stChatMessage a:hover {
        text-decoration: underline;
    }

    /* 6. Tinh chỉnh Sidebar và Input cho đồng bộ */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E0E0E0;
    }
    .stTextInput input {
        background-color: #FFFFFF;
        color: #000000;
        border: 1px solid #E0E0E0;
        border-radius: 20px;
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
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    st.error("⚠️ Chưa nhập API Key.")
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

# --- 5. SYSTEM PROMPT (TINH CHỈNH GIAO TIẾP TỰ NHIÊN) ---
current_date = datetime.now().strftime("%d/%m/%Y")

SYSTEM_PROMPT = f"""
VAI TRÒ:
Bạn là BV-Atlas, đại diện ảo của Ban Marketing - Bảo hiểm Bảo Việt.
Avatar của bạn là Logo Bảo Việt.
Thời gian hiện tại: {current_date}.

QUY TẮC TRẢ LỜI (TUÂN THỦ TUYỆT ĐỐI):

1. KHÔNG LẶP LẠI LỜI CHÀO:
   - Kiểm tra lịch sử chat. Nếu trước đó đã chào hỏi rồi, thì ở câu trả lời tiếp theo hãy ĐI THẲNG VÀO VẤN ĐỀ.
   - Không nói lại câu: "Chào bạn, mình là BV-Atlas..." hay "BV-Atlas đây!" một lần nữa.

2. CẤU TRÚC TỰ NHIÊN (KHÔNG HIỆN "BƯỚC 1, BƯỚC 2"):
   - Tuyệt đối KHÔNG viết các từ khóa như "Bước 1:", "Bước 2:", "Phần 1:", "Trả lời:".
   - Hãy trả lời tự nhiên như một đoạn hội thoại liền mạch.
   - Ví dụ SAI: "Bước 1: Link tải..."
   - Ví dụ ĐÚNG: "Gửi bạn bộ tài liệu An Gia nhé: [Link]. Tài liệu này bao gồm..."

3. QUY TẮC NGHIỆP VỤ:
   - Đúng sản phẩm: Hỏi An Gia trả lời An Gia.
   - Đúng khuyến mãi: Chỉ liệt kê CTKM còn hạn (Ngày kết thúc >= Hôm nay).
   - Phân biệt dịch vụ: "Bảo lãnh", "Bồi thường" là dịch vụ, không phải khuyến mãi.

4. GỢI Ý MỞ RỘNG (TINH TẾ):
   - Cuối câu trả lời, hãy gợi ý thêm 1-2 ý liên quan bằng câu hỏi nhẹ nhàng.
   - Ví dụ: "Bạn có cần thêm danh sách bệnh viện bảo lãnh cho gói này không?"
"""

# --- 6. GIAO DIỆN CHÍNH ---

with st.sidebar:
    st.image(BOT_AVATAR, width=150)
    st.markdown("---")
    st.markdown("### 📸 Tra cứu Ảnh")
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)

st.title("🛡️ BV-Atlas: Marketing Assistant")

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Admin chưa upload file `Du_lieu_BV_Atlas.docx` lên GitHub.")

# Khởi tạo lịch sử
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Chào bạn! 👋 Mình là BV-Atlas (Ban Marketing). Hôm nay {current_date}, bạn cần tra cứu thông tin gì?"}
    ]

for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=BOT_AVATAR): st.markdown(msg["content"])
    else:
        with st.chat_message(msg["role"], avatar="👤"): st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("..."):
            try:
                # Lấy lịch sử chat để Bot biết mình đã chào hay chưa
                history_text = ""
                for msg in st.session_state.messages:
                    role_name = "User" if msg["role"] == "user" else "BV-Atlas"
                    history_text += f"{role_name}: {msg['content']}\n"

                final_prompt = [
                    f"{SYSTEM_PROMPT}\n",
                    f"=== DỮ LIỆU ===\n{KNOWLEDGE_TEXT}\n",
                    f"=== LỊCH SỬ CHAT (ĐỂ TRÁNH LẶP TỪ) ===\n{history_text}\n",
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
