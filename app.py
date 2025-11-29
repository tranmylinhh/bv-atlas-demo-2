import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os
import uuid  # <--- ĐÃ THÊM DÒNG QUAN TRỌNG NÀY
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas", page_icon="img/favicon.png", layout="centered")

# --- CẤU HÌNH AVATAR ---
BOT_AVATAR = "logo.jpg"

# --- 2. CSS GIAO DIỆN (FIX MÀU CHỮ ĐEN 100%) ---
st.markdown("""
<style>
    /* Nền tổng thể: Xanh băng nhạt */
    .stApp { background-color: #F0F4F8; color: #000000; }
    
    /* === BẮT BUỘC MỌI CHỮ TRONG KHUNG CHAT LÀ MÀU ĐEN === */
    .stChatMessage p, .stChatMessage div, .stChatMessage li, .stChatMessage span {
        color: #000000 !important;
        font-size: 16px;
    }

    /* === 1. BONG BÓNG CHAT BOT (BÊN TRÁI - DÒNG LẺ) === */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #FFFFFF; /* Nền Trắng */
        border: 1px solid #E0E0E0;
        border-radius: 20px 20px 20px 5px;
        padding: 15px;
        flex-direction: row;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* === 2. BONG BÓNG CHAT USER (BÊN PHẢI - DÒNG CHẴN) === */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #D1EAFF; /* Xanh dương nhạt (Dễ đọc chữ đen) */
        border: 1px solid #B3D7FF;
        border-radius: 20px 20px 5px 20px;
        padding: 15px;
        flex-direction: row-reverse;
        text-align: right;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) > div:first-child { 
        margin-left: 10px; margin-right: 0; align-items: flex-end;
    }

    /* === 3. HEADER ĐẸP === */
    .header-box {
        text-align: center;
        padding: 20px;
        margin-bottom: 20px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .header-title { color: #005792; font-size: 26px; font-weight: 800; margin: 0; }
    .header-subtitle { color: #555; font-size: 14px; margin-top: 5px; }

    /* === 4. KHUNG NHẬP LIỆU NỔI === */
    .stChatInput { padding-bottom: 30px; }
    .stChatInput textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #005792 !important;
        border-radius: 30px !important;
        box-shadow: 0 4px 10px rgba(0,87,146,0.1);
    }
    
    /* Link */
    .stChatMessage a { color: #005792 !important; font-weight: bold; }
    
    /* Nút Ghim */
    button[kind="secondary"] { color: #005792; border: none; background: white; border-radius: 50%; width: 40px; height: 40px; }

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

# Khởi tạo key cho uploader (để reset sau khi gửi)
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

# 2. HIỂN THỊ LỊCH SỬ CHAT
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

# 3. THANH CÔNG CỤ ĐÍNH KÈM
col_attach, col_space = st.columns([0.5, 9.5])

with col_attach:
    with st.popover("📎", help="Đính kèm ảnh"):
        st.markdown("##### Chọn ảnh")
        # Dùng key động để reset
        uploaded_file = st.file_uploader("Upload", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed", key=st.session_state.uploader_key)
        
        current_img_data = None
        if uploaded_file:
            current_img_data = Image.open(uploaded_file)
            st.image(current_img_data, width=150)
            st.success("Đã chọn!")

with col_space:
    if current_img_data:
        st.caption(f"✅ Đã đính kèm 1 ảnh. Nhập câu hỏi để gửi.")

# 4. Ô NHẬP LIỆU
if prompt := st.chat_input("Nhập câu hỏi..."):
    # Xử lý gửi ảnh
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
                
                # --- RESET NÚT UPLOAD ---
                st.session_state.uploader_key = str(uuid.uuid4())
                st.rerun()
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
