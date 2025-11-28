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

# --- 2. CSS GIAO DIỆN (TRẮNG TINH KHÔI & TỐI GIẢN) ---
st.markdown("""
<style>
    /* Nền trắng toàn bộ */
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
        background-color: #E5F3FF; /* Màu xanh nhạt dễ chịu */
        border: 1px solid #CDE8FF;
        flex-direction: row-reverse;
        text-align: right;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) > div:first-child { margin-left: 10px; margin-right: 0; }

    /* Link */
    .stChatMessage a { color: #0068C9 !important; font-weight: bold; text-decoration: none; }
    
    /* === THANH NHẬP LIỆU & NÚT ĐÍNH KÈM === */
    /* Làm đẹp nút Popover (Cái ghim) */
    button[kind="secondary"] {
        border: none;
        background-color: transparent;
        color: #555;
        font-size: 20px;
        padding: 0px;
    }
    button[kind="secondary"]:hover {
        color: #0068C9;
        background-color: transparent;
    }
    
    /* Ô nhập liệu */
    .stTextInput input { background-color: #FFFFFF !important; color: #000000 !important; border-radius: 20px; border: 1px solid #ddd; }
    
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

# Tiêu đề tối giản
col1, col2 = st.columns([1, 8])
with col1: st.image(BOT_AVATAR, width=50)
with col2: st.subheader("BV-Atlas Marketing")

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file dữ liệu.")

# 1. KHỞI TẠO LỊCH SỬ (Thêm trường 'type' để phân loại tin nhắn)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "type": "text", "content": f"Chào bạn! 👋 Mình là BV-Atlas. Hôm nay bạn cần tìm tài liệu hay check khuyến mãi gì?"}
    ]

# 2. HIỂN THỊ LỊCH SỬ CHAT (CẬP NHẬT LOGIC HIỂN THỊ ẢNH)
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=BOT_AVATAR):
            st.markdown(msg["content"])
            # Nút Feedback
            if i > 0 and msg.get("type") == "text":
                c1, c2, c3 = st.columns([0.5, 0.5, 8])
                with c1: 
                    if st.button("👍", key=f"up_{i}"): st.toast("Đã thích!")
                with c2: 
                    if st.button("👎", key=f"down_{i}"): st.toast("Đã ghi nhận!")
    else:
        # Tin nhắn User
        with st.chat_message(msg["role"], avatar="👤"):
            # Kiểm tra loại tin nhắn
            if msg.get("type") == "image":
                # Nếu là ảnh thì hiển thị ảnh
                st.image(msg["content"], width=200)
            else:
                # Nếu là text thì hiển thị text
                st.markdown(msg["content"])

# 3. KHU VỰC NHẬP LIỆU & ĐÍNH KÈM
col_attach, col_space = st.columns([1, 5])
with col_attach:
    with st.popover("📎", help="Đính kèm ảnh"):
        st.markdown("### Chọn ảnh")
        uploaded_file = st.file_uploader("Upload", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed", key="uploader")
        
        # Xử lý ảnh upload ngay tại đây để dùng cho phần gửi bên dưới
        current_img_data = None
        if uploaded_file:
            current_img_data = Image.open(uploaded_file)
            st.image(current_img_data, width=150)
            st.success("Đã chọn! Hãy nhập câu hỏi và nhấn Enter.")

# 4. XỬ LÝ KHI USER GỬI TIN NHẮN (QUAN TRỌNG NHẤT)
if prompt := st.chat_input("Nhập câu hỏi... (VD: Tải tờ rơi An Gia)"):
    
    # BƯỚC 1: Kiểm tra xem có ảnh đang chờ gửi không
    if current_img_data:
        # Nếu có, thêm ảnh vào lịch sử trước
        st.session_state.messages.append({"role": "user", "type": "image", "content": current_img_data})
        # Hiển thị ngay lập tức
        with st.chat_message("user", avatar="👤"):
            st.image(current_img_data, width=200)
            
    # BƯỚC 2: Thêm tin nhắn chữ vào lịch sử
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # BƯỚC 3: Gửi cho Bot xử lý
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("..."):
            try:
                # Lấy lịch sử (chỉ lấy phần text để đưa vào prompt)
                history_text = ""
                for msg in st.session_state.messages[-5:]:
                    if msg.get("type") == "text":
                        role_name = "User" if msg["role"] == "user" else "BV-Atlas"
                        history_text += f"{role_name}: {msg['content']}\n"

                final_prompt = [
                    f"{SYSTEM_PROMPT}\n",
                    f"=== DỮ LIỆU ===\n{KNOWLEDGE_TEXT}\n",
                    f"=== LỊCH SỬ CHAT ===\n{history_text}\n",
                    f"CÂU HỎI USER: {prompt}"
                ]
                
                # Nếu vừa gửi kèm ảnh thì đưa ảnh vào prompt cho Bot nhìn
                if current_img_data:
                    final_prompt.append("LƯU Ý: User vừa gửi một bức ảnh (đã hiển thị trong lịch sử). Hãy phân tích ảnh đó.")
                    final_prompt.append(current_img_data)
                
                response = model.generate_content(final_prompt)
                
                # Hiển thị câu trả lời của Bot
                st.markdown(response.text)
                # Lưu câu trả lời vào lịch sử
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": response.text})
                
                # Rerun để cập nhật giao diện và reset uploader nếu cần
                st.rerun()
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
