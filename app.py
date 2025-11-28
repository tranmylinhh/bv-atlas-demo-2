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

# --- 2. CSS GIAO DIỆN (BẮT BUỘC LIGHT MODE - CHỮ ĐEN) ---
st.markdown("""
<style>
    /* 1. Ép Nền Trắng toàn bộ App */
    .stApp { background-color: #FFFFFF; color: #000000; }
    
    /* 2. Ép Thanh Sidebar màu xám sáng */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E0E0E0;
    }
    
    /* 3. Ép Ô Nhập liệu (Chat Input) thành Nền Trắng - Chữ Đen */
    .stChatInput textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }

    /* === 4. CẤU HÌNH BONG BÓNG CHAT === */
    
    /* CHUNG: Tất cả chữ trong khung chat phải là MÀU ĐEN */
    .stChatMessage p, .stChatMessage li, .stChatMessage div {
        color: #000000 !important;
    }

    /* BOT (Nói trước -> Số Lẻ): Nền Xám Nhạt (#F0F2F6) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F0F2F6 !important;
        border: none;
        border-radius: 20px 20px 20px 0px;
        padding: 15px;
    }

    /* USER (Nói sau -> Số Chẵn): Nền Trắng (#FFFFFF) + Viền Xám */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 20px 20px 0px 20px;
        padding: 15px;
        flex-direction: row-reverse; /* Đảo avatar sang phải */
        text-align: right;
    }
    
    /* Chỉnh lề cho User khi đảo chiều */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) > div:first-child {
        margin-left: 10px; margin-right: 0;
    }

    /* 5. LINK MÀU XANH (Blue) */
    .stChatMessage a {
        color: #0068C9 !important;
        font-weight: bold;
        text-decoration: none;
    }
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

# --- 5. SYSTEM PROMPT (UPDATE LOGIC CSKH NỘI BỘ) ---
current_date = datetime.now().strftime("%d/%m/%Y")

SYSTEM_PROMPT = f"""
VAI TRÒ:
Bạn là BV-Atlas, trợ lý AI chuyên nghiệp của Ban Marketing Bảo hiểm Bảo Việt.
Avatar: Logo Bảo Việt.
THÔNG TIN THỜI GIAN: Hôm nay là {current_date}.

QUY TẮC TRẢ LỜI (BẮT BUỘC TUÂN THỦ):

1. KIỂM TRA HẠN KHUYẾN MÃI: Chỉ liệt kê CTKM còn hạn (Kết thúc >= {current_date}).
2. ĐÚNG SẢN PHẨM: Hỏi sản phẩm nào trả lời sản phẩm đó.
3. PHÂN BIỆT DỊCH VỤ: Bảo lãnh/Bồi thường là DỊCH VỤ, không phải CTKM.
4. GIAO TIẾP: Thân thiện, ngắn gọn.

5. XỬ LÝ KHI KHÔNG TÌM THẤY THÔNG TIN (QUAN TRỌNG):
   - Nếu trong dữ liệu không có câu trả lời, TUYỆT ĐỐI KHÔNG tự bịa ra hotline 1800 hay hướng dẫn liên hệ quản lý khu vực.
   - Hãy trả lời chuẩn mẫu sau:
     "Dạ hiện tại trong kho dữ liệu của BV-Atlas chưa cập nhật thông tin này. Để được hỗ trợ chính xác nhất, bạn vui lòng liên hệ đầu mối Ban Marketing nhé:
     👉 **Ms. TRẦN MỸ LINH - tran.my.linh@baoviet.com.vn**"

6. XỬ LÝ KHI USER KHÓ CHỊU / PHÀN NÀN (Emotional Handling):
   - Nếu user tỏ thái độ không hài lòng, giận dữ hoặc thất vọng vì không tìm thấy tin.
   - Hãy xoa dịu khéo léo:
     "Thành thật xin lỗi bạn vì sự bất tiện này 😔. Ban Marketing đang nỗ lực thu thập thêm dữ liệu để cập nhật lên hệ thống sớm nhất.
     Nếu bạn đang cần gấp, vui lòng nhắn trực tiếp cho **Ms. Linh (tran.my.linh@baoviet.com.vn)** để được hỗ trợ ngay lập tức nhé!"
"""

# --- 6. GIAO DIỆN CHÍNH ---

with st.sidebar:
    st.image(BOT_AVATAR, width=150)
    st.markdown("---")
    st.markdown("### 📸 Tra cứu Ảnh")
    uploaded_img = st.file_uploader("Upload ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)

st.title("🛡️ BV-Atlas: Marketing Assistant")

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file dữ liệu.")

# Khởi tạo lịch sử (Bot nói trước -> Luôn là số lẻ 1)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Xin chào! 👋 Mình là BV-Atlas. Bạn cần tìm tài liệu hay check khuyến mãi gì hôm nay?"}
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
                history_text = ""
                for msg in st.session_state.messages[-5:]:
                    role_name = "User" if msg["role"] == "user" else "BV-Atlas"
                    history_text += f"{role_name}: {msg['content']}\n"

                final_prompt = [
                    f"{SYSTEM_PROMPT}\n",
                    f"=== DỮ LIỆU NỘI BỘ ===\n{KNOWLEDGE_TEXT}\n",
                    f"=== LỊCH SỬ CHAT ===\n{history_text}\n",
                    f"CÂU HỎI USER: {prompt}"
                ]
                
                if img_data:
                    final_prompt.append("User gửi ảnh. Hãy phân tích.")
                    final_prompt.append(img_data)
                
                response = model.generate_content(final_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
