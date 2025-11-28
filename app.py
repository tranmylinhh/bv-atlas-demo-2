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

# --- 2. CSS GIAO DIỆN (STYLE GIỐNG ẢNH MẪU 99%) ---
st.markdown("""
<style>
    /* Nền trắng sạch sẽ */
    .stApp { background-color: #FFFFFF; color: #000000; }
    
    /* === BONG BÓNG CHAT === */
    .stChatMessage { padding: 15px; border-radius: 15px; margin-bottom: 5px; display: flex; color: #000000 !important; }
    .stChatMessage p, .stChatMessage li { color: #000000 !important; font-size: 16px; line-height: 1.5; }

    /* BOT (Trái - Xám Nhạt) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F2F4F6; /* Xám nhạt */
        border: none;
        flex-direction: row;
    }
    
    /* USER (Phải - Xanh Nhạt - Không viền hoặc viền rất mờ) */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #EBF7FF; /* Xanh nhạt giống ảnh */
        border: none;
        flex-direction: row-reverse;
        text-align: right;
    }
    /* Chỉnh lề nội dung User */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) > div:first-child { margin-left: 10px; margin-right: 0; }

    /* Link màu Xanh đậm */
    .stChatMessage a { color: #0068C9 !important; font-weight: 600; text-decoration: none; }
    .stChatMessage a:hover { text-decoration: underline; }

    /* === THANH NHẬP LIỆU (Input) === */
    /* Bo tròn như viên thuốc, nền xám */
    .stChatInput textarea {
        background-color: #F0F2F5 !important; /* Xám nhạt */
        color: #000000 !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 25px !important; /* Bo tròn */
        padding: 10px 15px;
    }
    
    /* Ẩn các thành phần thừa */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Chỉnh nút Feedback nhỏ lại */
    .stButton button {
        border: none;
        background: transparent;
        color: #555;
        padding: 0px 10px;
        font-size: 14px;
    }
    .stButton button:hover {
        color: #0068C9;
        background: transparent;
    }
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
# --- 6. GIAO DIỆN CHÍNH (LAYOUT 1 CỘT) ---

# Tiêu đề & Logo
col1, col2 = st.columns([1, 6])
with col1: st.image(BOT_AVATAR, width=70)
with col2:
    st.subheader("BV-Atlas: Marketing Assistant")
    st.caption("Trợ lý tra cứu Tài liệu & Hình ảnh")

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Admin chưa upload file `Du_lieu_BV_Atlas.docx`.")

# 1. KHỞI TẠO LỊCH SỬ
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Xin chào! 👋 Mình là BV-Atlas. Bạn cần tìm tài liệu hay check khuyến mãi gì hôm nay?"}
    ]

# 2. HIỂN THỊ LỊCH SỬ CHAT
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "assistant":
        # Tin nhắn Bot
        with st.chat_message(msg["role"], avatar=BOT_AVATAR):
            st.markdown(msg["content"])
            
            # --- TÍNH NĂNG FEEDBACK (CHỈ HIỆN CHO CÂU TRẢ LỜI CỦA BOT) ---
            if i > 0: # Không hiện cho câu chào đầu tiên
                col_fb1, col_fb2, col_fb3 = st.columns([4, 1, 1])
                with col_fb1: st.caption("Bạn thấy kết quả này thế nào?")
                with col_fb2: 
                    if st.button("👍", key=f"like_{i}"): st.toast("Cảm ơn bạn đã đánh giá!")
                with col_fb3: 
                    if st.button("👎", key=f"dislike_{i}"): st.toast("Ban Marketing sẽ cải thiện thêm!")
    else:
        # Tin nhắn User
        with st.chat_message(msg["role"], avatar="👤"):
            st.markdown(msg["content"])

# 3. KHU VỰC UPLOAD (Nằm ngay trên ô nhập liệu)
with st.expander("📎 Đính kèm ảnh/Poster (Nhấn để mở)", expanded=False):
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Đã đính kèm", width=200)
        st.success("Ảnh đã sẵn sàng!")

# 4. Ô NHẬP LIỆU (Placeholder có gợi ý)
if prompt := st.chat_input("Nhập câu hỏi... (VD: Tải tờ rơi An Gia, Poster CTKM này là gì?)"):
    # User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Bot
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
                
                # Feedback hiện ngay sau khi trả lời xong
                st.rerun() # Load lại trang để hiện nút like/dislike
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
