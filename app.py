"""
🌸 Mandala & Character Art Generator
A Streamlit app that generates printable Mandala art (and animal characters)
using OpenAI's latest gpt-image-1 model.

HOW TO RUN LOCALLY:
1. pip install -r requirements.txt
2. Create a file called .streamlit/secrets.toml and add:
      OPENAI_API_KEY = "sk-your-key-here"
   OR just paste the key in the sidebar when the app opens.
3. streamlit run mandala_app.py

HOW TO DEPLOY (Streamlit Community Cloud):
1. Push both files to GitHub
2. Deploy on share.streamlit.io
3. Go to App Settings → Secrets → paste:
      OPENAI_API_KEY = "sk-your-key-here"
4. The app will never ask for your key again!
"""

import streamlit as st
import openai
import base64
import io
import os
from PIL import Image

# ─────────────────────────────────────────────
# Auto-load API key from Streamlit Secrets or env
# ─────────────────────────────────────────────
def get_api_key():
    """
    Priority order:
    1. Streamlit Secrets (cloud deployment / local secrets.toml)
    2. Environment variable OPENAI_API_KEY
    3. Manual entry in the sidebar (fallback)
    """
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return key, True   # (key, is_pre_configured)
    except Exception:
        pass
    env_key = os.environ.get("OPENAI_API_KEY", "")
    if env_key:
        return env_key, True
    return "", False

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
# Resolve API key (secrets → env → sidebar input)
# ─────────────────────────────────────────────
auto_key, key_is_set = get_api_key()

# ─────────────────────────────────────────────
# Sidebar – Settings
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    if key_is_set:
        # Key loaded automatically — show a green confirmation, no input box
        st.success("🔑 API key loaded automatically!", icon="✅")
        api_key = auto_key
    else:
        # Fallback: let the user paste their key manually
        st.warning("No API key found in Secrets.", icon="⚠️")
        api_key = st.text_input(
            "🔑 Paste your OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help=(
                "To avoid entering this every time, add your key to "
                "Streamlit Secrets (Settings → Secrets) as:\n\n"
                "OPENAI_API_KEY = \"sk-...\""
            ),
        )
        st.caption(
            "💡 **Fix this permanently:** "
            "Go to your app on share.streamlit.io → "
            "⋮ menu → Settings → Secrets → paste your key there."
        )
    st.markdown("---")

    art_mode = st.selectbox(
        "🎨 Art Mode",
        [
            "Mandala – Black & White (Coloring)",
            "Mandala – Dot Art / Painted (Colored)",
            "Mandala – Mehndi / Henna Style",
            "Mandala – Geometric Sacred",
            "Mandala – Watercolor Splash",
            "Animal Character (Coloring)",
        ],
        help=(
            "Black & White = printable coloring sheet\n"
            "Dot Art = teal & gold painted mandala style (like the image!)\n"
            "Mehndi = intricate henna-inspired patterns\n"
            "Geometric Sacred = sharp, mathematical patterns\n"
            "Watercolor = soft painted look with color washes\n"
            "Animal = cute character outline for coloring"
        )
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
    • Use <b>1024×1024</b> for standard paper<br>
    • <b>Dot Art</b> style = teal &amp; gold painted look<br>
    • <b>Mehndi</b> = henna-inspired brown on cream<br>
    • <b>Watercolor</b> = soft, colorful painted style
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

    elif "Dot Art" in mode:
        return (
            f"A stunning dot-art painted mandala inspired by '{word}'. "
            f"Rich teal and turquoise background with intricate gold and metallic dot patterns. "
            f"Multiple concentric rings of petals, leaves, and eye motifs filled with tiny raised dots. "
            f"Pointillism technique — every detail formed by dots of metallic gold, deep teal, and brown. "
            f"Painted on a textured canvas surface. Ornate, jewel-like, deeply colorful and three-dimensional. "
            f"Centered composition, perfectly symmetrical, highly detailed mandala art. "
            f"Style: Indian dot mandala painting, similar to Pebble art or rock painting mandalas."
        )

    elif "Mehndi" in mode:
        return (
            f"An intricate mehndi / henna-style mandala inspired by '{word}'. "
            f"Deep brown henna tones on a warm cream/ivory background. "
            f"Extremely fine line work with paisleys, lotus petals, leafy vines, teardrops, and dots. "
            f"Traditional Indian bridal henna patterns arranged in perfect circular symmetry. "
            f"Multiple decorative rings radiating outward, filled with micro-detail floral motifs. "
            f"Authentic henna art style, elegant and feminine, high contrast, print quality."
        )

    elif "Geometric Sacred" in mode:
        return (
            f"A sacred geometry mandala inspired by '{word}'. "
            f"Perfect mathematical precision — Flower of Life, Sri Yantra, and Metatron's Cube elements. "
            f"Sharp, clean vector-like black lines on pure white background. "
            f"Interlocking triangles, hexagons, circles, and star polygons in exact geometric harmony. "
            f"No organic curves — only straight lines and perfect arcs. "
            f"Minimalist yet deeply intricate, suitable for high-res printing and coloring."
        )

    elif "Watercolor" in mode:
        return (
            f"A beautiful watercolor mandala inspired by '{word}'. "
            f"Soft, flowing washes of color — purples, pinks, teals, and golds bleeding into each other. "
            f"Delicate black ink outlines with loose, painterly watercolor fills. "
            f"The center radiates lighter tones, deepening to rich saturated hues at the edges. "
            f"Artistic, dreamy, and ethereal. Painted on white watercolor paper texture. "
            f"Professional watercolor illustration style, intricate floral mandala with color washes."
        )

    else:  # Default Black & White coloring
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
    🖨️ <b>Printing Tip:</b> Choose your download format below.
    For best print quality use <b>PDF (A4)</b> — it fits perfectly on paper.
    Set your printer to <b>Black & White / Grayscale</b> to save ink!
    </div>
    """, unsafe_allow_html=True)

    # ── Download format selector ──────────────────────────────
    st.markdown("#### ⬇️ Download Your Art")

    fmt = st.radio(
        "Choose file format:",
        options=["PNG  🖼️", "JPG  📷", "PDF – A4 Print Ready  📄", "PDF – Letter Print Ready  📃"],
        horizontal=True,
        help=(
            "PNG = best quality, transparent background support\n"
            "JPG = smaller file size, solid white background\n"
            "PDF A4 = perfect for A4 paper printing (Europe/Asia)\n"
            "PDF Letter = perfect for US Letter paper printing"
        ),
    )

    # ── Convert image to the chosen format ────────────────────
    img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    fname_base = f"mandala_{word_used.replace(' ', '_')}"

    if fmt.startswith("PNG"):
        # PNG – lossless, best quality
        buf = io.BytesIO()
        img_pil.save(buf, format="PNG", optimize=True)
        dl_bytes = buf.getvalue()
        dl_name  = f"{fname_base}.png"
        dl_mime  = "image/png"

    elif fmt.startswith("JPG"):
        # JPG – smaller file, white background
        buf = io.BytesIO()
        img_pil.save(buf, format="JPEG", quality=95, optimize=True)
        dl_bytes = buf.getvalue()
        dl_name  = f"{fname_base}.jpg"
        dl_mime  = "image/jpeg"

    else:
        # PDF – embed image centred on the chosen paper size
        from fpdf import FPDF

        # Paper dimensions in mm
        if "A4" in fmt:
            pw, ph = 210, 297          # A4 portrait
            paper_label = "A4"
        else:
            pw, ph = 215.9, 279.4      # US Letter portrait
            paper_label = "Letter"

        # Save PIL image to a temp PNG buffer for fpdf
        tmp = io.BytesIO()
        img_pil.save(tmp, format="PNG")
        tmp.seek(0)

        # Write temp PNG to a temp file path (fpdf needs a path)
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tf.write(tmp.read())
            tmp_path = tf.name

        try:
            pdf = FPDF(orientation="P", unit="mm", format=(pw, ph))
            pdf.set_margins(10, 10, 10)
            pdf.add_page()

            # Centre image on page with 10 mm margins
            usable_w = pw - 20
            usable_h = ph - 20
            img_w_px, img_h_px = img_pil.size
            ratio = min(usable_w / img_w_px * 96,   # 96 dpi approx
                        usable_h / img_h_px * 96)
            img_w_mm = img_w_px * ratio / 96 * 25.4
            img_h_mm = img_h_px * ratio / 96 * 25.4

            # Clamp to usable area
            if img_w_mm > usable_w:
                scale = usable_w / img_w_mm
                img_w_mm *= scale
                img_h_mm *= scale
            if img_h_mm > usable_h:
                scale = usable_h / img_h_mm
                img_w_mm *= scale
                img_h_mm *= scale

            x_off = (pw - img_w_mm) / 2
            y_off = (ph - img_h_mm) / 2
            pdf.image(tmp_path, x=x_off, y=y_off, w=img_w_mm, h=img_h_mm)

            # Tiny footer
            pdf.set_y(ph - 8)
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(180, 180, 180)
            pdf.cell(0, 4, f"Mandala Art — '{word_used}' | Generated by Mandala Art Generator", align="C")

            dl_bytes = bytes(pdf.output())
        finally:
            os.unlink(tmp_path)

        dl_name = f"{fname_base}_{paper_label}.pdf"
        dl_mime = "application/pdf"

    # ── Download button ───────────────────────────────────────
    st.download_button(
        label=f"⬇️ Download  {dl_name}",
        data=dl_bytes,
        file_name=dl_name,
        mime=dl_mime,
        use_container_width=True,
        type="primary",
    )

    # Format guide
    with st.expander("📋 Which format should I choose?", expanded=False):
        st.markdown("""
        | Format | Best For | File Size | Quality |
        |--------|----------|-----------|---------|
        | **PNG** | Digital sharing, high-res printing | Medium | ⭐⭐⭐⭐⭐ Lossless |
        | **JPG** | Email, WhatsApp, social media | Small | ⭐⭐⭐⭐ Great |
        | **PDF A4** | Printing in India, Europe, Asia | Medium | ⭐⭐⭐⭐⭐ Print perfect |
        | **PDF Letter** | Printing in USA, Canada | Medium | ⭐⭐⭐⭐⭐ Print perfect |

        💡 **Tip for best coloring results:** Print PDF at **100% scale** (no "fit to page") 
        on **thick paper (120–160 gsm)** so markers don't bleed through.
        """)

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
    **🌸 For Any Mandala Style:**
    `ocean` · `fire` · `peace` · `lotus` · `moon`
    `forest` · `love` · `star` · `cosmos` · `storm`
    `bloom` · `zen` · `infinity` · `divine` · `soul`
    """)
with col_a:
    st.markdown("""
    **🐾 For Animal Character:**
    `elephant` · `fox` · `peacock` · `lion` · `owl`
    `butterfly` · `tiger` · `deer` · `parrot` · `turtle`
    `whale` · `koala` · `wolf` · `cat` · `dragon`
    """)

st.markdown("### 🎨 Style Guide")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    **🔵 Dot Art / Painted**
    Teal & gold, jewel-like,
    raised dot patterns.
    Best words: `ocean` `peacock`
    `emerald` `cosmos` `teal`
    """)
with c2:
    st.markdown("""
    **🟤 Mehndi / Henna**
    Brown on cream, fine
    paisleys & floral vines.
    Best words: `love` `bride`
    `lotus` `jasmine` `faith`
    """)
with c3:
    st.markdown("""
    **💜 Watercolor Splash**
    Soft dreamy color washes,
    painterly & ethereal.
    Best words: `dream` `bloom`
    `sky` `aurora` `dusk`
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
