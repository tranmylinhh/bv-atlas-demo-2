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

# --- 2. CSS GIAO DIỆN ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #005792; border-radius: 15px 15px 0px 15px; padding: 15px;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #262730; border-radius: 15px 15px 15px 0px; padding: 15px; border: 1px solid #444;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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

# --- 5. SYSTEM PROMPT (THẮT CHẶT QUY TẮC SẢN PHẨM) ---
current_date = datetime.now().strftime("%d/%m/%Y")

SYSTEM_PROMPT = f"""
VAI TRÒ:
Bạn là BV-Atlas, trợ lý AI của Ban Marketing Bảo Việt.
THÔNG TIN THỜI GIAN: Hôm nay là {current_date}.

QUY TẮC NGHIỆP VỤ (BẮT BUỘC TUÂN THỦ TUYỆT ĐỐI):

1. KIỂM TRA HẠN:
   - Chỉ liệt kê các CTKM mà: Ngày kết thúc >= {current_date}.
   - Các CTKM đã quá hạn: Coi như KHÔNG TỒN TẠI trong danh sách đang chạy.

2. ĐÚNG ĐỐI TƯỢNG SẢN PHẨM (QUAN TRỌNG NHẤT):
   - Nếu User hỏi CTKM của sản phẩm A (VD: An Gia), CHỈ tìm CTKM áp dụng cho sản phẩm A.
   - Nếu sản phẩm A không có CTKM nào đang chạy -> Trả lời thẳng thắn: "Hiện tại sản phẩm [Tên SP] chưa có chương trình khuyến mãi nào đang diễn ra."
   - TUYỆT ĐỐI KHÔNG lấy CTKM của sản phẩm B (VD: Flexi) để trả lời cho sản phẩm A. (Flexi là Du lịch, An Gia là Sức khỏe -> Không liên quan).

3. PHÂN BIỆT DỊCH VỤ vs KHUYẾN MÃI:
   - "Bảo lãnh viện phí", "Bồi thường" là DỊCH VỤ. Không được liệt kê vào danh sách Khuyến mãi.

4. PHONG CÁCH:
   - Thân thiện, dùng emoji 😊.
   - Nếu không có CTKM, hãy gợi ý user xem quyền lợi hoặc biểu phí của sản phẩm đó thay thế.
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

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"Chào bạn! 👋 Mình là BV-Atlas. Hôm nay ({current_date}), bạn cần tra cứu thông tin gì?"}]

for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        with st.chat_message(msg["role"], avatar=BOT_AVATAR): st.markdown(msg["content"])
    else:
        with st.chat_message(msg["role"], avatar="👤"): st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"): st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Đang tra cứu..."):
            try:
                history_text = ""
                for msg in st.session_state.messages[-5:]:
                    role_name = "User" if msg["role"] == "user" else "BV-Atlas"
                    history_text += f"{role_name}: {msg['content']}\n"

                final_prompt = [
                    f"{SYSTEM_PROMPT}\n",
                    f"=== DỮ LIỆU ===\n{KNOWLEDGE_TEXT}\n",
                    f"=== LỊCH SỬ CHAT ===\n{history_text}\n",
                    f"CÂU HỎI USER: {prompt}"
                ]
                
                if img_data:
                    final_prompt.append("User gửi ảnh. Hãy phân tích ảnh này.")
                    final_prompt.append(img_data)
                
                response = model.generate_content(final_prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
