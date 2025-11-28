import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
# Cũ: layout="wide"
# Mới: layout="centered"
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="img/favicon.png", layout="centered")

# --- CẤU HÌNH AVATAR ---
BOT_AVATAR = "logo.jpg"

# --- 2. CSS GIAO DIỆN (TỐI GIẢN - CLEAN UI) ---
st.markdown("""
<style>
    /* Nền trắng */
    .stApp { background-color: #FFFFFF; color: #000000; }
    
    /* === BONG BÓNG CHAT === */
    .stChatMessage { padding: 10px 15px; border-radius: 18px; margin-bottom: 5px; display: flex; color: #000000 !important; }
    .stChatMessage p, .stChatMessage li { color: #000000 !important; margin-bottom: 0px; }

    /* BOT (Trái) - Xám nhạt */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F2F4F6; border: none; flex-direction: row;
    }
    
    /* USER (Phải) - Xanh Zalo Nhạt */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #E5F3FF;
        border: 1px solid #CDE8FF;
        flex-direction: row-reverse;
        text-align: right;
    }
    
    /* Link */
    .stChatMessage a { color: #0068C9 !important; font-weight: bold; text-decoration: none; }
    
    /* === THANH CÔNG CỤ ĐÍNH KÈM (POPOVER) === */
    /* Biến nút bấm thành icon ghim gọn gàng */
    button[kind="secondary"] {
        border: none; 
        background-color: transparent !important; 
        color: #555; 
        font-size: 24px; 
        padding: 0px 10px;
        margin-bottom: -10px; /* Đẩy sát xuống ô nhập liệu */
    }
    button[kind="secondary"]:hover { color: #0068C9; }
    
    /* Ô nhập liệu */
    .stTextInput input { 
        background-color: #F0F2F5 !important; 
        color: #000000 !important; 
        border-radius: 25px; 
        border: 1px solid #ddd; 
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
# --- 6. GIAO DIỆN CHÍNH ---

# Header
col1, col2 = st.columns([1, 8])
with col1: st.image(BOT_AVATAR, width=50)
with col2: st.subheader("BV-Atlas Marketing")

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file dữ liệu.")

# 1. KHỞI TẠO LỊCH SỬ
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "type": "text", "content": f"Chào bạn! 👋 Mình là BV-Atlas. Bạn cần tìm tài liệu hay check khuyến mãi gì?"}
    ]

# 2. HIỂN THỊ LỊCH SỬ CHAT (Đã bỏ nút Like/Dislike)
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

# 3. THANH CÔNG CỤ ĐÍNH KÈM (Toolbar sát đáy)
# Tạo layout 2 cột: Cột trái là icon Ghim, Cột phải để trống (hoặc để text trạng thái)
col_tool_1, col_tool_2 = st.columns([0.5, 9.5])

with col_tool_1:
    # Nút bấm nhỏ hình cái ghim
    with st.popover("📎", help="Đính kèm ảnh"):
        st.markdown("##### Chọn ảnh")
        uploaded_file = st.file_uploader("Upload", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed", key="uploader")
        
        # Biến tạm để lưu ảnh vừa chọn
        current_img_data = None
        if uploaded_file:
            current_img_data = Image.open(uploaded_file)
            st.image(current_img_data, width=150)
            st.success("Đã chọn!")

# Hiện thông báo nhỏ nếu đã chọn ảnh (ở cột bên cạnh cho gọn)
with col_tool_2:
    if current_img_data:
        st.caption(f"✅ Đã đính kèm 1 ảnh. Nhập câu hỏi bên dưới để gửi.")

# 4. Ô NHẬP LIỆU (Chat Input)
if prompt := st.chat_input("Nhập câu hỏi..."):
    # Xử lý gửi ảnh trước (nếu có)
    if current_img_data:
        st.session_state.messages.append({"role": "user", "type": "image", "content": current_img_data})
        with st.chat_message("user", avatar="👤"):
            st.image(current_img_data, width=200)
            
    # Xử lý gửi chữ
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Bot trả lời
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("..."):
            try:
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
                
                if current_img_data:
                    final_prompt.append("LƯU Ý: User vừa gửi ảnh. Hãy phân tích.")
                    final_prompt.append(current_img_data)
                
                response = model.generate_content(final_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": response.text})
                # Rerun để reset lại trạng thái upload (làm sạch icon ghim cho lần sau)
                st.rerun()
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
