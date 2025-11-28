import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os
from datetime import datetime

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Ban Marketing", page_icon="img/favicon.png", layout="wide")

# --- CẤU HÌNH AVATAR ---
BOT_AVATAR = "logo.jpg"

# --- 2. CSS GIAO DIỆN (GIỮ NGUYÊN STYLE DARK MODE SANG TRỌNG) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #005792; 
        border-radius: 15px 15px 0px 15px;
        padding: 15px;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #262730; 
        border-radius: 15px 15px 15px 0px;
        padding: 15px;
        border: 1px solid #444;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI API KEY ---
if 'GOOGLE_API_KEY' in st.secrets:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    model = genai.GenerativeModel('gemini-2.0-flash')
else:
    st.error("⚠️ Chưa nhập API Key trong Secrets!")
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

# --- 5. SYSTEM PROMPT (TỐI ƯU GIỌNG ĐIỆU MARKETING) ---
current_date = datetime.now().strftime("%d/%m/%Y")

SYSTEM_PROMPT = f"""
VAI TRÒ:
Bạn là BV-Atlas, đại diện ảo của Ban Marketing - Bảo hiểm Bảo Việt.
Sứ mệnh của bạn là hỗ trợ các anh chị em đồng nghiệp kinh doanh và nghiệp vụ tra cứu thông tin nhanh chóng, chính xác.

THÔNG TIN THỜI GIAN: Hôm nay là {current_date}.

PHONG CÁCH GIAO TIẾP (TONE & VOICE):
- Chuyên nghiệp nhưng Thân thiện: Sử dụng ngôn ngữ chuẩn mực của môi trường công sở, nhưng không cứng nhắc.
- Xưng hô: "Mình" (BV-Atlas) và "Bạn" (hoặc Anh/Chị).
- Thái độ: Nhiệt tình, luôn sẵn sàng hỗ trợ. Dùng emoji 😊, 📎, 🛡️ một cách tinh tế.

QUY TẮC NGHIỆP VỤ (BẮT BUỘC):

1. KIỂM TRA HẠN KHUYẾN MÃI:
   - Chỉ liệt kê các CTKM có (Ngày kết thúc >= {current_date}).
   - Nếu chương trình đã hết hạn, hãy thông báo rõ ràng để tránh gây hiểu lầm.

2. ĐÚNG SẢN PHẨM:
   - User hỏi sản phẩm nào -> Trả lời đúng sản phẩm đó.
   - Tuyệt đối KHÔNG lấy CTKM của sản phẩm Du lịch (Flexi) để trả lời cho Sức khỏe (An Gia). Nếu An Gia không có khuyến mãi, hãy nói thẳng là "Hiện chưa có".

3. PHÂN BIỆT DỊCH VỤ:
   - "Bảo lãnh viện phí", "Bồi thường" là Tiện ích dịch vụ, KHÔNG PHẢI là chương trình khuyến mãi.

4. CẤU TRÚC TRẢ LỜI (ĐỂ TỐI ƯU TRẢI NGHIỆM):
   - Bước 1: Đi thẳng vào vấn đề (Cung cấp Link hoặc Thông tin ngay).
   - Bước 2: Tóm tắt ngắn gọn nội dung (nếu là link).
   - Bước 3: Gợi ý mở rộng (Proactive Suggestion).
     *Ví dụ:* "Dưới đây là link tải Brochure An Gia 2025 nhé: [Link]. 👉 Bạn có muốn mình gửi thêm **Danh sách bệnh viện bảo lãnh** hay **Biểu phí chi tiết** không?"

5. XỬ LÝ KHI THIẾU THÔNG TIN:
   - "Dạ, thông tin này hiện chưa có trong kho dữ liệu của BV-Atlas. Bạn vui lòng liên hệ trực tiếp đầu mối Ban Marketing để được hỗ trợ chi tiết nhé:
   TRẦN MỸ LINH - tran.my.linh@baoviet.com.vn"
"""

# --- 6. GIAO DIỆN CHÍNH ---

# === SIDEBAR ===
with st.sidebar:
    st.image(BOT_AVATAR, width=150)
    st.markdown("---")
    st.markdown("### 📸 Tra cứu Ảnh")
    st.info("Upload Poster/Banner để tìm thông tin chiến dịch.")
    uploaded_img = st.file_uploader("Chọn ảnh...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh bạn vừa tải lên", use_container_width=True)

# === MAIN ===
st.title("🛡️ BV-Atlas: Marketing Assistant")

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Cảnh báo Admin: Chưa tìm thấy file `Du_lieu_BV_Atlas.docx` trên GitHub.")

# 1. LỜI CHÀO MỞ ĐẦU (ĐƯỢC VIẾT LẠI THÂN THIỆN HƠN)
if "messages" not in st.session_state:
    welcome_msg = (
        f"Xin chào! 👋 **Mình là BV-Atlas - Trợ lý ảo của Ban Marketing Bảo Việt.**\n\n"
        f"Mình ở đây để hỗ trợ bạn tra cứu nhanh các thông tin:\n"
        f"- 📄 **Tài liệu sản phẩm** (Brochure, Quy tắc, Biểu phí...)\n"
        f"- 🎁 **Chương trình Khuyến mãi** (Đang chạy)\n"
        f"- 🖼️ **Hình ảnh truyền thông & Thương hiệu**\n\n"
        f"Bạn cần mình hỗ trợ thông tin gì cho chiến dịch hôm nay không? 😊"
    )
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]

# 2. HIỂN THỊ LỊCH SỬ CHAT
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=BOT_AVATAR):
            st.markdown(msg["content"])
    else:
        with st.chat_message(msg["role"], avatar="👤"):
            st.markdown(msg["content"])

# 3. XỬ LÝ HỘI THOẠI
if prompt := st.chat_input("Nhập câu hỏi... (VD: Tải tờ rơi An Gia, Khuyến mãi du lịch)"):
    # User
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Bot
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("BV-Atlas đang tra cứu dữ liệu..."):
            try:
                # Tạo bộ nhớ (Context Window)
                history_text = ""
                for msg in st.session_state.messages[-5:]:
                    role_name = "User" if msg["role"] == "user" else "BV-Atlas"
                    history_text += f"{role_name}: {msg['content']}\n"

                final_prompt = [
                    f"{SYSTEM_PROMPT}\n",
                    f"=== DỮ LIỆU NỘI BỘ (Word) ===\n{KNOWLEDGE_TEXT}\n",
                    f"=== LỊCH SỬ HỘI THOẠI ===\n{history_text}\n",
                    f"CÂU HỎI MỚI CỦA USER: {prompt}"
                ]
                
                if img_data:
                    final_prompt.append("User gửi ảnh. Hãy phân tích ảnh này theo dữ liệu Marketing.")
                    final_prompt.append(img_data)
                
                response = model.generate_content(final_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
