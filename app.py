import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os
import uuid  # Thư viện tạo ID ngẫu nhiên để reset nút upload
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
# Dùng layout "wide" để Sidebar rộng rãi hơn
st.set_page_config(page_title="BV-Atlas Marketing", page_icon="img/favicon.png", layout="wide")

# --- CẤU HÌNH AVATAR ---
BOT_AVATAR = "logo.jpg"

# --- 2. CSS GIAO DIỆN (LIGHT MODE - CHỮ ĐEN - LINK XANH) ---
st.markdown("""
<style>
    /* 1. Nền Trắng */
    .stApp { background-color: #FFFFFF; color: #000000; }
    
    /* 2. Bong bóng chat */
    .stChatMessage { 
        padding: 12px 18px; 
        border-radius: 18px; 
        margin-bottom: 10px; 
        display: flex; 
        color: #000000 !important;
        font-size: 16px;
    }
    
    /* Bot (Trái) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F2F4F6; /* Xám nhạt */
        border: none;
        flex-direction: row;
    }
    
    /* User (Phải) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #E3F2FD; /* Xanh rất nhạt */
        border: 1px solid #BBDEFB;
        flex-direction: row-reverse;
        text-align: right;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) > div:first-child { 
        margin-left: 10px; margin-right: 0; align-items: flex-end; 
    }

    /* Ép màu chữ đen */
    .stChatMessage p, .stChatMessage li, .stChatMessage div { color: #000000 !important; }
    
    /* Link */
    .stChatMessage a { color: #0068C9 !important; font-weight: bold; text-decoration: none; }
    .stChatMessage a:hover { text-decoration: underline; }

    /* 3. HEADER CENTER */
    .header-container {
        text-align: center;
        padding-bottom: 10px;
        margin-bottom: 20px;
        border-bottom: 2px solid #F0F0F0; /* Đường gạch ngang */
    }
    .header-title {
        color: #005792;
        font-size: 28px;
        font-weight: 800;
        margin-top: 10px;
    }
    
    /* 4. SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA;
        border-right: 1px solid #E0E0E0;
    }
    
    /* 5. INPUT */
    .stChatInput textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #005792 !important;
        border-radius: 30px;
    }

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

# --- 5. SYSTEM PROMPT (UPDATE QUY TẮC KHÔNG SPAM LINK) ---
current_date = datetime.now().strftime("%d/%m/%Y")

SYSTEM_PROMPT = f"""
VAI TRÒ:
Bạn là BV-Atlas, trợ lý AI của Ban Marketing Bảo hiểm Bảo Việt.
Avatar: Logo Bảo Việt.
THỜI GIAN: {current_date}.

QUY TẮC ỨNG XỬ (ƯU TIÊN CAO NHẤT):

1. KHÔNG LIỆT KÊ HÀNG LOẠT (ANTI-SPAM):
   - Nếu User hỏi chung chung (Ví dụ: "Tìm tài liệu", "Gửi link sản phẩm", "Có những gì?"):
     -> TUYỆT ĐỐI KHÔNG liệt kê danh sách link ra ngay.
     -> HÃY HỎI NGƯỢC LẠI để làm rõ nhu cầu: "Chào bạn! Kho tài liệu của mình có đầy đủ thông tin về An Gia, Tâm Bình, K-Care, Intercare... Bạn đang cần tìm cụ thể cho sản phẩm nào ạ?"
   - CHỈ đưa link khi User đã nhắc đến TÊN SẢN PHẨM cụ thể (Ví dụ: "Tài liệu An Gia").
   - TUYỆT ĐỐI KHÔNG GỢI Ý những tài liệu mà bạn KHÔNG CÓ trong tay. (Ví dụ: Đừng hỏi "Bạn có muốn xem biểu phí không?" nếu bạn biết chắc chắn trong kho không có link biểu phí của sản phẩm đó).
   - Chỉ giới thiệu các tài liệu của các sản phẩm có sẵn trong kho dữ liệu cho user.

2. LOGIC TRẢ LỜI:
   - Bước 1: Xác nhận yêu cầu.
   - Bước 2: Cung cấp đúng thông tin/link của sản phẩm đó (Không kèm sản phẩm khác).
   - Bước 3: Gợi ý mở rộng liên quan đến chính sản phẩm đó.

3. KIỂM TRA HẠN KHUYẾN MÃI:
   - Chỉ liệt kê CTKM có (Ngày kết thúc >= {current_date}).
   - Nếu user hỏi CTKM đã hết hạn, báo rõ là đã hết hạn.

4. XỬ LÝ KHI THIẾU THÔNG TIN / USER KHÓ CHỊU:
   - Nếu không tìm thấy hoặc bị user bắt lỗi:
     "Thành thật xin lỗi bạn vì sự bất tiện này 😔. Ban Marketing đang cập nhật thêm dữ liệu. Nếu cần gấp, bạn vui lòng nhắn trực tiếp Ms. TRẦN MỸ LINH (tran.my.linh@baoviet.com.vn) để được hỗ trợ ngay nhé!"

5. PHONG CÁCH:
   - Thân thiện, ngắn gọn. Xưng "Mình" - "Bạn".
"""
# --- KHỞI TẠO SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "type": "text", "content": f"Chào bạn! 👋 Mình là BV-Atlas. Bạn cần tìm tài liệu hay check khuyến mãi gì hôm nay?"}
    ]

# Khởi tạo ID cho nút upload (Chìa khóa để fix lỗi đỏ)
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

# --- 6. GIAO DIỆN CHÍNH ---

# === SIDEBAR (UPLOAD ẢNH) ===
with st.sidebar:
    st.image(BOT_AVATAR, width=120)
    st.markdown("### 📸 Tra cứu bằng Ảnh")
    st.info(
        "**Hướng dẫn:**\n"
        "1. Tải ảnh Poster/Banner/Sản phẩm lên đây.\n"
        "2. Nhập câu hỏi bên khung chat (VD: 'Poster này là chương trình gì?').\n"
        "3. BV-Atlas sẽ phân tích ảnh và trả lời."
    )
    
    # Nút upload sử dụng key động
    uploaded_file = st.file_uploader(
        "Chọn ảnh từ máy...", 
        type=['jpg', 'png', 'jpeg'], 
        key=st.session_state.uploader_key
    )
    
    current_img_data = None
    if uploaded_file:
        current_img_data = Image.open(uploaded_file)
        st.image(current_img_data, caption="✅ Ảnh đã sẵn sàng gửi", use_container_width=True)

# === MAIN COLUMN (CHAT) ===

# HEADER CENTER
st.markdown(f"""
    <div class="header-container">
        <img src="{BOT_AVATAR}" width="60" style="vertical-align: middle;">
        <div class="header-title">BV-Atlas Marketing</div>
    </div>
""", unsafe_allow_html=True)

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file dữ liệu trên GitHub.")

# 1. HIỂN THỊ LỊCH SỬ CHAT
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=BOT_AVATAR):
            st.markdown(msg["content"])
    else:
        with st.chat_message(msg["role"], avatar="👤"):
            if msg.get("type") == "image":
                st.image(msg["content"], width=200)
            else:
                st.markdown(msg["content"])

# 2. XỬ LÝ KHI USER GỬI TIN
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    
    # Bước 1: Xử lý Ảnh (Nếu có bên Sidebar)
    if current_img_data:
        st.session_state.messages.append({"role": "user", "type": "image", "content": current_img_data})
        with st.chat_message("user", avatar="👤"):
            st.image(current_img_data, width=200)
    
    # Bước 2: Xử lý Text
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Bước 3: Bot trả lời
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Đang tra cứu..."):
            try:
                # Ghép Prompt
                history_text = ""
                for msg in st.session_state.messages[-5:]:
                    if msg.get("type") == "text":
                        role_name = "User" if msg["role"] == "user" else "BV-Atlas"
                        history_text += f"{role_name}: {msg['content']}\n"

                final_prompt = [
                    f"{SYSTEM_PROMPT}\n",
                    f"=== DỮ LIỆU NỘI BỘ ===\n{KNOWLEDGE_TEXT}\n",
                    f"=== LỊCH SỬ CHAT ===\n{history_text}\n",
                    f"CÂU HỎI USER: {prompt}"
                ]
                
                # Nếu có ảnh, gửi kèm cho Bot
                if current_img_data:
                    final_prompt.append("LƯU Ý: User gửi kèm ảnh. Hãy phân tích.")
                    final_prompt.append(current_img_data)
                
                response = model.generate_content(final_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": response.text})
                
                # --- RESET NÚT UPLOAD (FIX LỖI ĐỎ) ---
                # Tạo key mới -> Streamlit sẽ xóa nút cũ và tạo nút mới trống trơn
                st.session_state.uploader_key = str(uuid.uuid4())
                st.rerun()
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
