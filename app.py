"""
🌸 Mandala & Character Art Generator
A Streamlit app that generates printable Mandala art (and animal characters)
using OpenAI's latest gpt-image-1 model.

HOW TO RUN:
1. Install requirements: pip install streamlit openai pillow requests fpdf2
2. Run: streamlit run mandala_app.py
3. Enter your OpenAI API key in the sidebar
4. Type one word and click Generate!
"""

import streamlit as st
import openai
import base64
import io
import requests
from PIL import Image

# ─────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="🌸 Mandala Art Generator",
    page_icon="🌸",
    layout="centered",
)

# ─────────────────────────────────────────────
# Custom CSS – warm, artistic, print-friendly look
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Lato:wght@300;400&display=swap');

    html, body, [class*="css"] {
        font-family: 'Lato', sans-serif;
    }
    .main { background: #fdf8f2; }
    h1, h2, h3 { font-family: 'Cinzel', serif; color: #3a2d1e; }

    .hero-title {
        font-family: 'Cinzel', serif;
        font-size: 2.6rem;
        color: #3a2d1e;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        text-align: center;
        color: #7a6652;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #c9853a, #e8a95b);
        color: white;
        border: none;
        border-radius: 30px;
        padding: 0.65rem 2.2rem;
        font-size: 1.05rem;
        font-family: 'Cinzel', serif;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #a06428, #c9853a);
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    }
    .info-box {
        background: #fff8ee;
        border-left: 4px solid #c9853a;
        padding: 1rem 1.2rem;
        border-radius: 6px;
        margin: 1rem 0;
        color: #3a2d1e;
        font-size: 0.95rem;
    }
    .tip-box {
        background: #eef8f0;
        border-left: 4px solid #4caf7d;
        padding: 0.9rem 1.2rem;
        border-radius: 6px;
        margin: 1rem 0;
        color: #1e3a2d;
        font-size: 0.9rem;
    }
    .footer {
        text-align: center;
        color: #aaa;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar – API Key & Settings
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    api_key = st.text_input(
        "🔑 OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Your key stays in your browser session only – never stored.",
    )
    st.markdown("---")

    art_mode = st.selectbox(
        "🎨 Art Mode",
        ["Mandala (Coloring)", "Animal Character (Coloring)"],
        help="Mandala = circular geometric patterns. Animal = cute character outline."
    )

    quality = st.selectbox(
        "🖼️ Image Quality",
        ["low", "medium", "high"],
        index=1,
        help="Higher quality = more detail but costs slightly more API credits."
    )

    image_size = st.selectbox(
        "📐 Image Size",
        ["1024x1024", "1024x1536 (Portrait)", "1536x1024 (Landscape)"],
        index=0
    )
    size_map = {
        "1024x1024": "1024x1024",
        "1024x1536 (Portrait)": "1024x1536",
        "1536x1024 (Landscape)": "1536x1024",
    }
    chosen_size = size_map[image_size]

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.82rem; color:#7a6652;">
    <b>💡 Beginner Tips</b><br>
    • Get your API key at <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a><br>
    • Low quality is fastest & cheapest<br>
    • High quality = best for printing<br>
    • Use <b>1024×1024</b> for standard paper
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Hero Header
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">🌸 Mandala Art Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Type one word · Generate art · Print & Color 🖍️</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# How-to guide (collapsible)
# ─────────────────────────────────────────────
with st.expander("📖 How to use this app (Beginner's Guide)", expanded=False):
    st.markdown("""
    ### Step-by-Step Guide

    **Step 1 – Get an OpenAI API Key**
    - Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
    - Sign up or log in, then click **"Create new secret key"**
    - Copy the key (starts with `sk-`)
    - Paste it in the sidebar on the left

    **Step 2 – Choose your Art Mode**
    - **Mandala** → Beautiful circular geometric coloring pattern
    - **Animal Character** → Cute animal outline you can color in

    **Step 3 – Type ONE Word of Inspiration**
    - For Mandala: try words like *ocean*, *forest*, *love*, *fire*, *peace*
    - For Animal: type an animal name like *elephant*, *fox*, *peacock*, *lion*

    **Step 4 – Click "Generate Art"**
    - Wait 15–30 seconds for the image to be created
    - The art will appear on screen

    **Step 5 – Download & Print**
    - Click **"⬇️ Download PNG"** to save the image
    - Open the file and print on **A4 / Letter** paper
    - Use a black marker, colored pencils, or crayons to color!

    ---
    **⚠️ Important Notes:**
    - You need an OpenAI account with credits (costs ~$0.02–$0.19 per image)
    - Never share your API key with anyone
    - The sidebar key field is password-protected and session-only
    """)


# ─────────────────────────────────────────────
# Main Input
# ─────────────────────────────────────────────
st.markdown("### ✏️ Enter Your Inspiration Word")

col1, col2 = st.columns([3, 1])
with col1:
    word = st.text_input(
        "",
        placeholder="e.g.  ocean  /  elephant  /  peace  /  lotus",
        label_visibility="collapsed",
        max_chars=40,
    )
with col2:
    generate_btn = st.button("🎨 Generate")


# ─────────────────────────────────────────────
# Prompt builder
# ─────────────────────────────────────────────
def build_prompt(word: str, mode: str) -> str:
    word = word.strip().lower()
    if "Animal" in mode:
        return (
            f"A cute {word} animal character in a thick black outline coloring book style. "
            f"The character should be playful, child-friendly, symmetrical, centered on a pure white background. "
            f"Use only black lines on white, NO gray fill, NO color, NO shading, NO gradients. "
            f"Add small decorative floral and geometric patterns inside the body outline for coloring. "
            f"The line art must be crisp, bold, and suitable for printing and hand-coloring."
        )
    else:
        return (
            f"A highly intricate, symmetrical mandala inspired by the concept of '{word}'. "
            f"The mandala should be perfectly circular with multiple concentric rings filled with "
            f"elaborate geometric patterns, petals, stars, paisleys, and fine line work. "
            f"Pure black line art on a completely white background. "
            f"NO gray, NO shading, NO color fill whatsoever — only black strokes on white. "
            f"Suitable for adult coloring books, high print quality, centered composition, "
            f"ornate and meditative in style. The motifs should subtly reflect '{word}'."
        )


# ─────────────────────────────────────────────
# Generation logic
# ─────────────────────────────────────────────
def generate_image(prompt: str, api_key: str, quality: str, size: str):
    """
    Uses the latest OpenAI gpt-image-1 model via the Images API.
    Returns raw image bytes.
    """
    client = openai.OpenAI(api_key=api_key)

    response = client.images.generate(
        model="gpt-image-1",          # Latest model (April 2026)
        prompt=prompt,
        n=1,
        size=size,
        quality=quality,              # "low" | "medium" | "high"
        output_format="png",
    )

    # gpt-image-1 always returns base64
    image_b64 = response.data[0].b64_json
    image_bytes = base64.b64decode(image_b64)
    return image_bytes


# ─────────────────────────────────────────────
# On Generate button click
# ─────────────────────────────────────────────
if generate_btn:
    if not api_key:
        st.error("🔑 Please enter your OpenAI API key in the sidebar first.")
    elif not word.strip():
        st.error("✏️ Please enter an inspiration word.")
    else:
        prompt = build_prompt(word, art_mode)

        with st.spinner(f"✨ Creating your {'mandala' if 'Mandala' in art_mode else 'character'} art for **'{word}'**… this takes 20–40 seconds…"):
            try:
                img_bytes = generate_image(prompt, api_key, quality, chosen_size)

                # Store in session so it persists
                st.session_state["img_bytes"] = img_bytes
                st.session_state["word"] = word
                st.session_state["mode"] = art_mode
                st.session_state["prompt_used"] = prompt

            except openai.AuthenticationError:
                st.error("❌ Invalid API key. Please check and re-enter in the sidebar.")
            except openai.RateLimitError:
                st.error("⚠️ Rate limit reached. Please wait a moment and try again.")
            except openai.BadRequestError as e:
                st.error(f"⚠️ Request rejected by OpenAI: {e}\n\nTry a different word.")
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")


# ─────────────────────────────────────────────
# Display result
# ─────────────────────────────────────────────
if "img_bytes" in st.session_state:
    img_bytes = st.session_state["img_bytes"]
    word_used = st.session_state.get("word", "art")
    mode_used = st.session_state.get("mode", "")

    st.markdown("---")
    label = "🌸 Your Mandala" if "Mandala" in mode_used else "🐾 Your Animal Character"
    st.markdown(f"### {label} — *'{word_used}'*")

    # Show image
    img = Image.open(io.BytesIO(img_bytes))
    st.image(img, use_container_width=True, caption=f"Inspired by: {word_used}")

    # Printing tip
    st.markdown("""
    <div class="tip-box">
    🖨️ <b>Printing Tip:</b> Download the PNG below and print on A4 / Letter paper.
    Set your printer to <b>Fit to page</b> and use <b>Black & White / Grayscale</b> mode
    for best ink-saving results. Works great with a laser or inkjet printer!
    </div>
    """, unsafe_allow_html=True)

    # Download PNG
    st.download_button(
        label="⬇️ Download PNG (for printing)",
        data=img_bytes,
        file_name=f"mandala_{word_used.replace(' ', '_')}.png",
        mime="image/png",
        use_container_width=True,
    )

    # Show prompt used (collapsible)
    with st.expander("🔍 See the prompt sent to AI", expanded=False):
        st.code(st.session_state.get("prompt_used", ""), language=None)

    # Regenerate hint
    st.markdown("""
    <div class="info-box">
    💡 <b>Want a different design?</b> Just click <b>Generate</b> again with the same or a new word —
    each generation creates a unique piece of art!
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Example words showcase
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💡 Inspiration Word Ideas")

col_m, col_a = st.columns(2)
with col_m:
    st.markdown("""
    **🌸 For Mandala:**
    `ocean` · `fire` · `peace` · `lotus` · `moon`
    `forest` · `love` · `star` · `breath` · `mandala`
    `cosmos` · `bloom` · `zen` · `infinity` · `storm`
    """)
with col_a:
    st.markdown("""
    **🐾 For Animal Character:**
    `elephant` · `fox` · `peacock` · `lion` · `owl`
    `butterfly` · `tiger` · `deer` · `parrot` · `turtle`
    `whale` · `koala` · `wolf` · `cat` · `dragon`
    """)


# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Built with ❤️ using Streamlit + OpenAI gpt-image-1 · 
    Images generated are for personal use · 
    Happy coloring! 🖍️
</div>
""", unsafe_allow_html=True)
