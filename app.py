import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx
import os

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="🛡️", layout="wide")

# --- 2. CSS GIAO DIỆN (Chat App Chuẩn) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    
    /* User Message - Xanh đậm */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #005792; 
        border-radius: 15px 15px 0px 15px;
        padding: 15px;
        border: none;
    }
    /* Bot Message - Xám tối */
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
    model = genai.GenerativeModel('gemini-1.5-flash')
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

# --- 5. SYSTEM PROMPT (NÂNG CẤP LOGIC GỢI Ý) ---
SYSTEM_PROMPT = """
VAI TRÒ:
Bạn là BV-Atlas, trợ lý AI chuyên nghiệp của Ban Marketing Bảo Việt.

PHONG CÁCH:
- Thân thiện, ngắn gọn, đi thẳng vào vấn đề.
- Luôn chủ động GỢI Ý thông tin liên quan (Proactive Suggestion).

QUY TẮC TRẢ LỜI (NGHIÊM NGẶT):
1. TRẢ LỜI TRƯỚC - GỢI Ý SAU:
   - Bước 1: Cung cấp ngay thông tin/link user cần.
   - Bước 2: Tóm tắt nhanh 1 dòng về nội dung file đó (nếu là link).
   - Bước 3: Gợi ý các thông tin liên quan mà User có thể cần tiếp theo.
   
   *Ví dụ:* "Dưới đây là tờ rơi An Gia: [Link]. Tài liệu này có đủ bảng quyền lợi và phí. 👉 Bạn có muốn xem thêm **Danh sách bệnh viện bảo lãnh** hay **Thủ tục bồi thường** không?"

2. KHÔNG LẶP LẠI CÂU HỎI: Tuyệt đối không hỏi lại kiểu "Bạn muốn tìm tờ rơi An Gia đúng không?". Hãy đưa tờ rơi luôn.

3. HIỂU NGỮ CẢNH (CONTEXT):
   - Nếu user nói "ừ", "ok", "cảm ơn" -> Hãy đáp lại thân thiện và gợi ý chủ đề khác.
   - Nếu user nói "còn cái kia thì sao" -> Hãy hiểu user đang hỏi về sản phẩm/vấn đề vừa nhắc đến trước đó.

4. NẾU KHÔNG BIẾT: Hướng dẫn liên hệ Ms. Linh (Ban Marketing).
"""

# --- 6. GIAO DIỆN CHÍNH ---

# === SIDEBAR (Upload Ảnh) ===
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Bao_Viet_Holdings_Logo.svg/1200px-Bao_Viet_Holdings_Logo.svg.png", width=180)
    st.markdown("---")
    st.markdown("### 📸 Tra cứu Ảnh")
    uploaded_img = st.file_uploader("Upload poster/banner...", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")
    
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)

# === MAIN (CHATBOT) ===
st.title("🛡️ BV-Atlas: Marketing Assistant")

if KNOWLEDGE_TEXT is None:
    st.warning("⚠️ Chưa tìm thấy file `Du_lieu_BV_Atlas.docx` trên GitHub.")

# 1. Khởi tạo lịch sử chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Chào bạn! 👋 Mình là BV-Atlas. Hôm nay bạn cần tìm tài liệu sản phẩm, check khuyến mãi hay tìm file thiết kế nào?"}
    ]

# 2. Hiển thị lịch sử (Tin nhắn cũ nằm trên)
for msg in st.session_state.messages:
    avatar = "🛡️" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# 3. Ô Nhập liệu & Xử lý Logic
if prompt := st.chat_input("Nhập câu hỏi..."):
    # Hiện câu hỏi user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Xử lý trả lời
    with st.chat_message("assistant", avatar="🛡️"):
        with st.spinner("Đang tra cứu..."):
            try:
                # --- PHẦN QUAN TRỌNG: TẠO BỘ NHỚ (MEMORY) ---
                # Gom lại 5 tin nhắn gần nhất để Bot nhớ ngữ cảnh
                history_text = ""
                for msg in st.session_state.messages[-5:]: 
                    role_name = "User" if msg["role"] == "user" else "BV-Atlas"
                    history_text += f"{role_name}: {msg['content']}\n"

                # Ghép Prompt hoàn chỉnh
                final_prompt = [
                    f"{SYSTEM_PROMPT}\n",
                    f"=== DỮ LIỆU KIẾN THỨC ===\n{KNOWLEDGE_TEXT}\n",
                    f"=== LỊCH SỬ CHAT ===\n{history_text}\n",
                    f"CÂU HỎI MỚI NHẤT CỦA USER: {prompt}"
                ]
                
                # Nếu có ảnh
                if img_data:
                    final_prompt.append("User gửi kèm ảnh. Hãy phân tích ảnh này dựa trên Dữ liệu.")
                    final_prompt.append(img_data)
                
                # Gọi Gemini
                response = model.generate_content(final_prompt)
                
                # Hiện kết quả
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Lỗi: {e}")
