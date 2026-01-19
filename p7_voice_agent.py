import streamlit as st
import asyncio
import edge_tts
from openai import OpenAI

# --- 1. 配置 Groq (Key 已填好) ---
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=st.secrets["GROQ_API_KEY"],
)

# --- 2. 核心函数：文字转语音 (TTS) ---
async def generate_audio(text, output_file="output.mp3"):
    """
    使用 Edge TTS 将文字转换为语音文件
    Voice 列表推荐：
    - zh-CN-XiaoxiaoNeural (女声，温柔)
    - zh-CN-YunxiNeural (男声，稳重)
    """
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(output_file)

def play_audio(text):
    """
    包装函数：运行异步生成，并在 Streamlit 播放
    """
    output_file = "response_audio.mp3"
    
    # 运行异步任务
    asyncio.run(generate_audio(text, output_file))
    
    # 在网页上显示音频播放器
    st.audio(output_file, format="audio/mp3", start_time=0)

# --- 3. 页面设置 ---
st.set_page_config(page_title="语音 AI", page_icon="🎙️")
st.title("🎙️ 会说话的 AI 助手 (Edge TTS)")
st.caption("基于 Groq (Llama 3) + Edge TTS (免费语音)")

# 初始化记忆
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "你好！我现在不仅能打字，还能说话了。快来试试吧！"}
    ]

# 显示历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 4. 交互逻辑 ---
if user_input := st.chat_input("输入问题，我会读出答案..."):
    # 显示用户输入
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI 回答
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 调用 Groq
        try:
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=st.session_state.messages,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # --- 关键步骤：说完话后，生成音频 ---
            # 为了防止太长的字读半天，我们限制只读前 200 个字，或者你可以去掉这个限制
            if full_response:
                with st.spinner("正在生成语音..."):
                    play_audio(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"发生错误: {e}")
