import streamlit as st
import google.generativeai as genai
from PIL import Image
import docx

# --- 1. CẤU HÌNH TRANG ---
st.set_page_config(page_title="BV-Atlas: Trợ lý Marketing", page_icon="🛡️", layout="wide")

# --- 2. CSS GIAO DIỆN (Dark Mode & Card Style) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #262730; padding: 20px; border-radius: 10px;
        border: 1px solid #363945;
    }
    h1 { color: #4F8BF9 !important; }
    .stButton>button { width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 3. KẾT NỐI API KEY ---
if 'GOOGLE_API_KEY' in st.secrets:
    api_key = st.secrets['GOOGLE_API_KEY']
    genai.configure(api_key=api_key)
    # Dùng model chuẩn, ổn định
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ Chưa nhập API Key trong Secrets!")
    st.stop()

# --- 4. HỆ THỐNG NHẮC VIỆC (SYSTEM INSTRUCTION) ---
# Đây là phần "Tính cách" và "Luật lệ" bạn đã quy định
SYSTEM_PROMPT = """
Bạn là BV-Atlas, trợ lý AI nội bộ thân thiện và chuyên nghiệp của Ban Marketing - Bảo hiểm Bảo Việt.
Nhiệm vụ của bạn là hỗ trợ đồng nghiệp tra cứu thông tin Sản phẩm và Chương trình Khuyến mại (CTKM).

PHONG CÁCH TRÒ CHUYỆN (TONE & VOICE):
- Thân thiện, cởi mở, sử dụng ngôn ngữ tự nhiên (Ví dụ: "Chào bạn", "Để mình tìm giúp bạn nhé", "Dưới đây là thông tin bạn cần...").
- Tránh trả lời cộc lốc hoặc quá máy móc.
- Xưng hô: "Mình" (hoặc "BV-Atlas") và "Bạn".

NGUYÊN TẮC ỨNG XỬ (BẮT BUỘC):
1. KHI CHÀO HỎI / HỎI CHUNG CHUNG:
   - Tuyệt đối KHÔNG liệt kê danh sách toàn bộ tài liệu ngay từ đầu.
   - Hãy hỏi ngược lại để làm rõ nhu cầu.
   - Ví dụ: "Chào bạn! Kho tài liệu của mình có rất nhiều thông tin về An Gia, Tâm Bình và các CTKM mới. Bạn đang cần tìm cụ thể cho sản phẩm nào không?"

2. KHI HỎI VỀ TÀI LIỆU/LINK TẢI:
   - CHỈ cung cấp link tải của ĐÚNG sản phẩm mà người dùng hỏi.
   - Luôn kèm theo một câu dẫn dắt. (Ví dụ: "Đây là brochure An Gia bản mới nhất cho bạn nhé: [Link]").

3. KHI HỎI VỀ CHƯƠNG TRÌNH KHUYẾN MẠI (PROMOTION):
   - Dựa vào tài liệu đã học, hãy tóm tắt rõ 3 ý chính:
     + Thời gian diễn ra.
     + Đối tượng áp dụng.
     + Quà tặng/Ưu đãi cụ thể.
   - Nếu có file Thể lệ chi tiết, hãy gửi link tải ở cuối câu.

4. KHI TÌM HÌNH ẢNH / VISUAL SEARCH:
   - Nếu người dùng mô tả ảnh: Hãy tìm trong dữ liệu xem có mô tả nào khớp không và trả về Link file thiết kế gốc.
   - Nếu người dùng UPLOAD ẢNH:
     + Bước 1: Phân tích nội dung bức ảnh vừa upload (chữ trên ảnh, hình ảnh).
     + Bước 2: Dùng thông tin đó đối chiếu với Kho kiến thức để tìm ra tên chương trình hoặc Link tải file gốc tương ứng.

5. XỬ LÝ KHI KHÔNG CÓ THÔNG TIN:
   - Nếu không tìm thấy thông tin trong Knowledge Base, hãy trả lời khéo léo và hướng dẫn liên hệ:
   "Xin lỗi bạn, hiện tại mình chưa tìm thấy thông tin này trong kho dữ liệu. Bạn vui lòng liên hệ trực tiếp Ban Marketing để được hỗ trợ nhé.
   Đầu mối hỗ trợ từ ban Marketing:
   TRẦN MỸ LINH - tran.my.linh@baoviet.com.vn
   Ban Marketing - Tầng 6 - Số 8 Lê Thái Tổ - Hoàn Kiếm - HN."
"""

# --- 5. HÀM ĐỌC FILE WORD ---
def read_docx(file):
    doc = docx.Document(file)
    full_text = []
    # Đọc văn bản thường
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    # Đọc bảng biểu (Table) - Rất quan trọng cho bảo hiểm
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text for cell in row.cells]
            full_text.append(" | ".join(row_text))
    return '\n'.join(full_text)

# --- 6. GIAO DIỆN CHÍNH ---
st.title("🛡️ BV-Atlas: Marketing Assistant")
st.caption("Trợ lý tra cứu Tài liệu, Sản phẩm & Khuyến mãi")
st.markdown("---")

col_chat, col_upload = st.columns([2, 1])

# --- CỘT PHẢI: KHU VỰC NẠP DỮ LIỆU ---
with col_upload:
    st.subheader("📂 Nạp Kiến Thức")
    st.info("💡 Upload file Word chứa thông tin Sản phẩm & CTKM để Bot học.")
    
    # Upload File Knowledge
    uploaded_file = st.file_uploader("Chọn file dữ liệu (.docx)", type=['docx'])
    knowledge_text = ""
    
    if uploaded_file:
        with st.spinner("Đang học tài liệu..."):
            try:
                knowledge_text = read_docx(uploaded_file)
                st.success(f"✅ Đã học xong: {uploaded_file.name}")
                with st.expander("Xem nội dung đã học"):
                    st.text(knowledge_text[:1000] + "...") 
            except Exception as e:
                st.error(f"Lỗi đọc file: {e}")

    st.markdown("---")
    st.subheader("🖼️ Visual Search")
    st.info("Upload Poster/Banner để hỏi thông tin.")
    uploaded_img = st.file_uploader("Chọn ảnh (.jpg, .png)", type=['jpg', 'png', 'jpeg'])
    img_data = None
    if uploaded_img:
        img_data = Image.open(uploaded_img)
        st.image(img_data, caption="Ảnh xem trước", use_container_width=True)

# --- CỘT TRÁI: KHUNG CHAT ---
with col_chat:
    # Khởi tạo lịch sử chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Mình là BV-Atlas. Bạn cần tìm thông tin gì về An Gia, Tâm Bình hay các CTKM mới không?"}]

    # Hiển thị tin nhắn cũ
    for msg in st.session_state.messages:
        avatar = "🛡️" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Xử lý nhập liệu
    if prompt := st.chat_input("Nhập câu hỏi... (VD: Tải tờ rơi An Gia, Khuyến mãi tháng này)"):
        # 1. Hiện câu hỏi User
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # 2. Xử lý Trả lời
        # Kiểm tra xem đã có dữ liệu chưa
        if not knowledge_text and not img_data:
            response_text = "⚠️ **Bạn chưa upload file dữ liệu (Word) bên cột phải.**\nHãy upload file `Du_lieu_BV_Atlas.docx` để mình có kiến thức trả lời nhé!"
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            with st.chat_message("assistant", avatar="🛡️"):
                st.markdown(response_text)
        else:
            # Gọi Google Gemini
            with st.chat_message("assistant", avatar="🛡️"):
                with st.spinner("Đang tra cứu..."):
                    try:
                        # Ghép Prompt gửi cho Gemini
                        final_prompt = [f"{SYSTEM_PROMPT}\n\n=== DỮ LIỆU KIẾN THỨC NỀN TẢNG ===\n{knowledge_text}\n=================================="]
                        
                        if img_data:
                            final_prompt.append("Người dùng gửi kèm ảnh. Hãy phân tích ảnh này dựa trên Kiến thức nền tảng.")
                            final_prompt.append(img_data)
                        
                        final_prompt.append(f"\nCÂU HỎI CỦA NGƯỜI DÙNG: {prompt}")
                        
                        # Gọi API
                        response = model.generate_content(final_prompt)
                        
                        # Hiện kết quả
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                        
                        # Nút Feedback (Giả lập)
                        c1, c2 = st.columns([1,10])
                        with c1: st.button("👍")
                        with c2: st.button("👎")
                        
                    except Exception as e:
                        st.error(f"Có lỗi xảy ra: {e}")
