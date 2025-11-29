import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os
import uuid
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas Marketing", page_icon="img/favicon.png", layout="wide")

# --- CẤU HÌNH AVATAR ---
BOT_AVATAR = "logo.jpg"

# --- 2. CSS GIAO DIỆN (TỐI ƯU UI/UX) ---
st.markdown("""
<style>
    /* 1. Nền tổng thể: Trắng */
    .stApp { background-color: #FFFFFF; color: #000000; }
    
    /* 2. Sidebar: Màu xám nhẹ, Logo to */
    section[data-testid="stSidebar"] {
        background-color: #F7F9FB; /* Xám rất nhạt */
        border-right: 1px solid #EAEAEA;
    }
    /* Chỉnh Logo Sidebar căn giữa và to */
    section[data-testid="stSidebar"] img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        margin-bottom: 20px;
    }

    /* 3. Header Chính (Giữa màn hình) */
    .header-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 40px;
        padding-top: 20px;
    }
    .header-title {
        color: #005792;
        font-size: 28px;
        font-weight: 800;
        margin-top: 15px;
    }
    
    /* 4. Bong bóng Chat */
    .stChatMessage { 
        padding: 12px 18px; border-radius: 18px; margin-bottom: 10px; display: flex; color: #000000 !important;
    }
    .stChatMessage p { color: #000000 !important; }

    /* Bot (Trái): Xám Nhạt */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F0F2F5; 
        border: none;
        flex-direction: row;
    }
    
    /* User (Phải): Xanh Nhạt */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #E3F2FD; 
        border: none;
        flex-direction: row-reverse;
        text-align: right;
    }
    

    /* 5. ÉP MÀU LINK XANH (QUAN TRỌNG - ĐÈ LÊN MÀU ĐEN Ở TRÊN) */
    /* Chỉ áp dụng cho thẻ 'a' (đường dẫn) */
    .stChatMessage a { 
        color: #005792 !important; /* Xanh Bảo Việt đậm đà */
        font-weight: 700;          /* In đậm cho dễ thấy */
        text-decoration: none;     /* Bỏ gạch chân cho đẹp */
    }
    .stChatMessage a:hover { 
        text-decoration: underline; /* Di chuột vào mới hiện gạch chân */
        color: #003366 !important; /* Di chuột vào thì xanh tối hơn chút */
    }
    /* Áp dụng cho đoạn văn, danh sách, tiêu đề... */
    .stChatMessage p, 
    .stChatMessage div, 
    .stChatMessage span, 
    .stChatMessage li,
    .stChatMessage h1, .stChatMessage h2, .stChatMessage h3,
    .stChatMessage table, .stChatMessage td, .stChatMessage th {
        color: #000000 !important; 
    }

    /* 6. KHUNG NHẬP LIỆU (FIX LỖI CHỒNG KHUNG) */
    
    /* Ẩn khung chứa mặc định của Streamlit (Cái gây ra viền chồng) */
    .stChatInput {
        background-color: transparent !important;
        border: none !important;
    }
    div[data-testid="stChatInput"] > div {
        background-color: transparent !important;
        border-color: transparent !important;
    }

    /* Tạo kiểu cho ô nhập liệu thật sự (Textarea) */
    .stChatInput textarea {
        background-color: #F0F2F5 !important; /* Xám nhạt giống Messenger */
        color: #000000 !important;             /* Chữ đen */
        border: 1px solid #DDDDDD !important;  /* Viền mỏng */
        border-radius: 25px !important;        /* Bo tròn */
        padding: 12px 20px;
    }
    /* Khi bấm vào thì viền xanh */
    .stChatInput textarea:focus {
        border: 1px solid #005792 !important;
        box-shadow: none !important;
    }
    
    /* Nút Gửi */
    .stChatInput button {
        color: #005792 !important;
    }

    /* 7. Box Upload (Sidebar) */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 1px dashed #CCC;
        border-radius: 10px;
        padding: 10px;
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
Bạn là BV-Atlas, trợ lý ảo chuyên trách của Ban Marketing - Bảo hiểm Bảo Việt.
Đối tượng giao tiếp: Cán bộ nhân viên (Đồng nghiệp) trong công ty.
Mục tiêu: Hỗ trợ đồng nghiệp tìm kiếm tài liệu, thông tin CTKM nhanh nhất để phục vụ kinh doanh.
Avatar: Logo Bảo Việt.

DỮ LIỆU THỜI GIAN: Hôm nay là {current_date}.

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

3. KHI TRAO ĐỔI VỀ CHƯƠNG TRÌNH KHUYẾN MÃI, (QUAN TRỌNG) CẦN KIỂM TRA THỜI HẠN KHUYẾN MÃI:
   - Chỉ liệt kê CTKM có (Ngày kết thúc >= {current_date}).
   - Nếu user hỏi CTKM có (Ngày kết thúc < Hôm nay) -> ĐÃ HẾT HẠN. -> TUYỆT ĐỐI KHÔNG giới thiệu là "đang chạy"/ "Đang diễn ra".
   - Nếu sản phẩm không có CTKM nào đang chạy -> Trả lời thẳng: "Hiện tại sản phẩm này chưa có CTKM mới, bạn có muốn tìm kiếm chương trình khuyến mãi đang chạy không?"

4. XỬ LÝ KHI BỊ BẮT LỖI (Quan trọng):
   - Nếu User phản hồi "Sai rồi", "Hết hạn rồi", "Sao lại giới thiệu cái cũ", "Thông tin này không đúng":
   - HÃY NHẬN LỖI CHÂN THÀNH & TỰ NHIÊN.
   - Ví dụ: "Ôi mình xin lỗi, mình check sót ngày kết thúc. Cảm ơn bạn đã nhắc nhé! Đúng là chương trình này đã hết hạn từ ngày [Ngày] rồi."
   - Đừng vội lôi "văn mẫu" liên hệ Ms. Linh ra ngay, trừ khi Bot thực sự không có dữ liệu để trả lời tiếp.

5. XỬ LÝ KHI THIẾU THÔNG TIN / USER KHÓ CHỊU:
   - Nếu không tìm thấy mà không thể thay thế bằng một thông tin khác:
     "Thành thật xin lỗi bạn vì sự bất tiện này 😔. Kho dữ liệu của mình chưa có tài liệu này rồi, Ban Marketing vẫn đang cập nhật thêm dữ liệu. Nếu cần gấp, bạn vui lòng nhắn trực tiếp đầu mối Ban Marketing là Ms. TRẦN MỸ LINH (tran.my.linh@baoviet.com.vn) để được hỗ trợ ngay nhé!"

6. PHONG CÁCH, THÁI ĐỘ "ĐỒNG NGHIỆP" (Human Touch):
   - Không trả lời như người máy vô cảm. Hãy dùng ngôn ngữ văn phòng, lịch sự nhưng gần gũi, thân thiện.
   - Xưng hô: "Mình" - "Bạn".
   - Dùng emoji 😊, ☺️, 🥹 để giảm căng thẳng.
"""
# --- KHỞI TẠO SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "type": "text", "content": f"Chào bạn! 👋 Mình là BV-Atlas đây. Bạn cần tìm tài liệu hay check thông tin chương trình khuyến mãi hôm nay?"}
    ]

# Khởi tạo ID cho nút upload (Chìa khóa để fix lỗi đỏ)
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = str(uuid.uuid4())

# --- 6. GIAO DIỆN CHÍNH ---

# === SIDEBAR (LOGO TO & UPLOAD) ===
with st.sidebar:
    # Logo to, tự động căn giữa theo CSS
    st.image(BOT_AVATAR, use_container_width=True) 
    
    st.markdown("### 📸 Tra cứu Ảnh")
    # Box thông tin màu xanh nhạt
    st.info("Upload ảnh Poster/Banner để hỏi thông tin.")
    
    # Nút upload
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed", key=f"uploader_{st.session_state.get('uploader_key', 'init')}")
    
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)

# === MAIN HEADER (LOGO & TÊN Ở GIỮA) ===
# Dùng HTML thuần để đảm bảo hiển thị ảnh không bị lỗi
st.markdown(f"""
    <div class="header-container">
        <img src="{BOT_AVATAR}" width="80" style="border-radius: 10px;">
        <div class="header-title">BV-Atlas Marketing</div>
        <div style="color: #666; margin-top: 5px;">Trợ lý thông tin Ban Marketing</div>
    </div>
""", unsafe_allow_html=True)

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file dữ liệu.")

# 1. KHỞI TẠO LỊCH SỬ
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "type": "text", "content": f"Chào bạn! 👋 Mình là BV-Atlas đây. Bạn cần tìm tài liệu hay check thông tin chương trình khuyến mãi hôm nay?"}
    ]
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

# 3. Ô NHẬP LIỆU (FIX LỖI GIAO DIỆN)
if prompt := st.chat_input("Nhập câu hỏi..."):
    # Xử lý gửi ảnh (Từ Sidebar)
    if img_data:
        st.session_state.messages.append({"role": "user", "type": "image", "content": img_data})
        with st.chat_message("user", avatar="👤"):
            st.image(img_data, width=200)
            
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
                
                if img_data:
                    final_prompt.append("LƯU Ý: User gửi ảnh bên Sidebar. Hãy phân tích.")
                    final_prompt.append(img_data)
                
                response = model.generate_content(final_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": response.text})
                
                # Reset Sidebar Uploader
                st.session_state.uploader_key = str(uuid.uuid4())
                st.rerun()
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
