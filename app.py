import streamlit as st
import math
import json
import io
import random
from PIL import Image, ImageDraw
from openai import OpenAI
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mandala Art Generator",
    page_icon="🌸",
    layout="centered",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&display=swap');
h1 { font-family: 'Cinzel', serif; letter-spacing: 3px; text-align: center; }
.subtitle { text-align: center; color: #888; font-size: 0.85rem;
            letter-spacing: 2px; text-transform: uppercase; margin-top: -1rem; }
.stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("🌸 Mandala Generator")
st.markdown('<p class="subtitle">One word · Infinite geometry · Ready to colour</p>',
            unsafe_allow_html=True)
st.markdown("---")

# ── Sidebar – API key ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔑 OpenAI API Key")
    api_key = st.text_input(
        "Paste your key here",
        type="password",
        placeholder="sk-...",
        help="Your key is never stored. It lives only in this session.",
    )
    st.caption("Get a key at [platform.openai.com](https://platform.openai.com)")
    st.markdown("---")
    st.subheader("🎨 Drawing options")
    canvas_size = st.slider("Canvas size (px)", 600, 1400, 900, 100)
    line_width   = st.slider("Line thickness", 1, 5, 2)
    st.markdown("---")
    st.info("**How to use**\n1. Enter your OpenAI key\n2. Type an inspiration word\n3. Click Generate\n4. Download PNG or PDF")


# ── Helper: ask OpenAI for mandala parameters ─────────────────────────────────
def get_word_params(word: str, key: str) -> dict:
    client = OpenAI(api_key=key)
    system = """You are a generative-art assistant.
Given one English word, return ONLY a valid JSON object with these keys:
- petals: integer 6-16  (rotational symmetry, reflects the word's energy)
- rings: integer 4-9    (concentric ring layers, reflects depth/complexity)
- complexity: float 0.3-1.0  (intricacy level)
- style: one of floral | geometric | classic | angular | organic
No markdown, no extra text, just the raw JSON."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": word},
        ],
        max_tokens=120,
        temperature=0.7,
    )
    return json.loads(response.choices[0].message.content.strip())


# ── Helper: deterministic RNG seeded from the word ────────────────────────────
def make_rng(seed_str: str):
    s = sum(ord(c) * (i + 1) for i, c in enumerate(seed_str)) % (2**32)
    rng = random.Random(s)
    return rng


# ── Core drawing function (pure PIL) ─────────────────────────────────────────
def draw_mandala(params: dict, word: str, size: int, lw: int) -> Image.Image:
    petals     = int(params.get("petals", 8))
    rings      = int(params.get("rings", 5))
    complexity = float(params.get("complexity", 0.6))
    style      = params.get("style", "classic")

    img  = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    rng  = make_rng(word + str(petals) + str(rings))

    cx = cy = size // 2
    max_r = int(size * 0.42)
    lw_thin = max(1, lw - 1)

    # ── Outer border rings ────────────────────────────────────────────────────
    for offset in (8, 16):
        r = max_r + int(size * offset / 900)
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            outline="black", width=max(1, lw - 1),
        )

    # ── Concentric ring circles ───────────────────────────────────────────────
    for ring in range(1, rings + 1):
        r = int((ring / rings) * max_r)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline="black", width=lw_thin)

    # ── Per-ring petal / motif drawing ────────────────────────────────────────
    for ring in range(1, rings + 1):
        r_out  = (ring / rings) * max_r
        r_in   = ((ring - 1) / rings) * max_r
        r_mid  = (r_out + r_in) / 2
        band_h = r_out - r_in

        for i in range(petals):
            angle  = (i / petals) * 2 * math.pi
            n_angle = ((i + 1) / petals) * 2 * math.pi
            m_angle = (angle + n_angle) / 2

            # Radial spoke
            x0 = cx + r_in  * math.cos(angle)
            y0 = cy + r_in  * math.sin(angle)
            x1 = cx + r_out * math.cos(angle)
            y1 = cy + r_out * math.sin(angle)
            draw.line([(x0, y0), (x1, y1)], fill="black", width=lw_thin)

            # ── Style-specific petal motif ────────────────────────────────────
            if style in ("floral", "organic"):
                # Leaf / teardrop petal
                pw = band_h * 0.35 * (0.5 + complexity * 0.5)
                points = []
                steps  = 20
                for k in range(steps + 1):
                    t = k / steps
                    pr = r_in + band_h * t
                    offset_ang = pw / max(pr, 1) * math.sin(math.pi * t)
                    points.append((
                        cx + pr * math.cos(m_angle + offset_ang),
                        cy + pr * math.sin(m_angle + offset_ang),
                    ))
                for k in range(steps, -1, -1):
                    t = k / steps
                    pr = r_in + band_h * t
                    offset_ang = pw / max(pr, 1) * math.sin(math.pi * t)
                    points.append((
                        cx + pr * math.cos(m_angle - offset_ang),
                        cy + pr * math.sin(m_angle - offset_ang),
                    ))
                if len(points) > 2:
                    draw.polygon(points, outline="black", fill=None)

            elif style in ("geometric", "angular"):
                hw = math.sin(math.pi / petals) * r_mid * (0.5 + complexity * 0.3)
                p1 = (cx + r_in  * math.cos(m_angle), cy + r_in  * math.sin(m_angle))
                p2 = (cx + r_out * math.cos(m_angle - hw / r_out),
                      cy + r_out * math.sin(m_angle - hw / r_out))
                p3 = (cx + r_out * math.cos(m_angle + hw / r_out),
                      cy + r_out * math.sin(m_angle + hw / r_out))
                draw.polygon([p1, p2, p3], outline="black", fill=None)

            else:  # classic / default diamond
                hw = math.sin(math.pi / petals) * r_mid * 0.45
                tip_in  = (cx + r_in  * math.cos(m_angle), cy + r_in  * math.sin(m_angle))
                tip_out = (cx + r_out * math.cos(m_angle), cy + r_out * math.sin(m_angle))
                side1   = (cx + r_mid * math.cos(m_angle - hw / r_mid),
                           cy + r_mid * math.sin(m_angle - hw / r_mid))
                side2   = (cx + r_mid * math.cos(m_angle + hw / r_mid),
                           cy + r_mid * math.sin(m_angle + hw / r_mid))
                draw.polygon([tip_in, side1, tip_out, side2],
                             outline="black", fill=None)

            # ── Dot accents ───────────────────────────────────────────────────
            if complexity > 0.5 and ring % 2 == 0:
                dx = cx + r_mid * math.cos(m_angle)
                dy = cy + r_mid * math.sin(m_angle)
                dot = int(size * 2 / 900)
                draw.ellipse([dx - dot, dy - dot, dx + dot, dy + dot],
                             fill="black")

            # ── Inner arc decoration ──────────────────────────────────────────
            if ring > 1 and complexity > 0.4:
                arc_r  = int(r_in + band_h * 0.25)
                span   = math.pi / petals * 0.7
                a_start = math.degrees(m_angle - span)
                a_end   = math.degrees(m_angle + span)
                bbox    = [cx - arc_r, cy - arc_r, cx + arc_r, cy + arc_r]
                draw.arc(bbox, start=a_start, end=a_end,
                         fill="black", width=lw_thin)

        # ── Dot ring between bands ────────────────────────────────────────────
        if ring < rings and complexity > 0.55:
            dot_n = petals * 2
            for j in range(dot_n):
                a  = (j / dot_n) * 2 * math.pi + (0.5 / petals) * 2 * math.pi
                dr = r_out + int(size * 3 / 900)
                dx = cx + dr * math.cos(a)
                dy = cy + dr * math.sin(a)
                dot = int(size * 1.5 / 900)
                draw.ellipse([dx - dot, dy - dot, dx + dot, dy + dot],
                             fill="black")

    # ── Centre dot ────────────────────────────────────────────────────────────
    cd = int(size * 5 / 900)
    draw.ellipse([cx - cd, cy - cd, cx + cd, cy + cd], fill="black")

    # ── Word label ────────────────────────────────────────────────────────────
    label = f"~ {word.upper()} ~"
    label_y = cy + max_r + int(size * 28 / 900)
    draw.text((cx, label_y), label, fill="#444444", anchor="mm")

    return img


# ── PDF export ────────────────────────────────────────────────────────────────
def img_to_pdf(img: Image.Image, word: str) -> bytes:
    buf = io.BytesIO()
    w_pt, h_pt = A4          # 595 × 842 points
    c = rl_canvas.Canvas(buf, pagesize=A4)

    # Title
    c.setFont("Helvetica-Oblique", 14)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawCentredString(w_pt / 2, h_pt - 36, f"Mandala  —  {word}")

    # Image (centred, 90% of page width)
    img_w = w_pt * 0.90
    img_h = img_w  # square mandala
    x = (w_pt - img_w) / 2
    y = (h_pt - img_h) / 2 - 10

    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), x, y, width=img_w, height=img_h,
                preserveAspectRatio=True)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawCentredString(w_pt / 2, 20, "Print & colour at your own pace.")
    c.save()
    buf.seek(0)
    return buf.read()


# ── Main UI ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    word = st.text_input(
        "✨ Inspiration word",
        placeholder="e.g. ocean, lotus, fire, serenity…",
        max_chars=40,
    )
    generate_btn = st.button("🌸 Generate Mandala", use_container_width=True)

if generate_btn:
    if not api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif not word.strip():
        st.warning("Please enter an inspiration word.")
    else:
        word = word.strip().lower()
        with st.spinner(f'The oracle is meditating on "{word}"…'):
            try:
                params = get_word_params(word, api_key)
                st.session_state["params"] = params
                st.session_state["word"]   = word
            except Exception as e:
                st.error(f"OpenAI error: {e}")
                st.stop()

        with st.spinner("Weaving sacred geometry…"):
            img = draw_mandala(params, word, canvas_size, line_width)
            st.session_state["img"] = img

# ── Show result if available ──────────────────────────────────────────────────
if "img" in st.session_state:
    img    = st.session_state["img"]
    word   = st.session_state["word"]
    params = st.session_state["params"]

    st.markdown(f"<h4 style='text-align:center;letter-spacing:2px;'>✦ Inspired by: <em>{word}</em> ✦</h4>",
                unsafe_allow_html=True)

    with st.expander("🔍 Geometry parameters used"):
        st.json(params)

    st.image(img, use_container_width=True)

    # ── Download section ──────────────────────────────────────────────────────
    st.markdown("#### ⬇️ Download Your Mandala")

    col_sel, col_btn = st.columns([2, 1])

    with col_sel:
        file_type = st.selectbox(
            "Select file format",
            options=["PNG — High-resolution image (best for digital use)",
                     "PDF — A4 print-ready document (best for printing)",
                     "JPEG — Compressed image (smaller file size)"],
            index=0,
            label_visibility="collapsed",
        )

    fmt = file_type.split("—")[0].strip()   # "PNG", "PDF", or "JPEG"

    # Prepare the correct bytes based on selection
    if fmt == "PNG":
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        download_data  = buf.getvalue()
        download_name  = f"mandala-{word}.png"
        download_mime  = "image/png"
        download_label = "⬇️ Download PNG"

    elif fmt == "PDF":
        download_data  = img_to_pdf(img, word)
        download_name  = f"mandala-{word}.pdf"
        download_mime  = "application/pdf"
        download_label = "⬇️ Download PDF"

    else:  # JPEG
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=95)
        download_data  = buf.getvalue()
        download_name  = f"mandala-{word}.jpg"
        download_mime  = "image/jpeg"
        download_label = "⬇️ Download JPEG"

    with col_btn:
        st.download_button(
            label=download_label,
            data=download_data,
            file_name=download_name,
            mime=download_mime,
            use_container_width=True,
        )

    # Format-specific tips
    tips = {
        "PNG":  "💡 PNG is lossless and ideal for large prints. Recommended for home printing.",
        "PDF":  "💡 PDF is formatted for A4 paper. Just open and print — no resizing needed.",
        "JPEG": "💡 JPEG is smaller in size. Good for sharing digitally, slightly less sharp when printed.",
    }
    st.caption(tips[fmt])
    st.success("✅ Your mandala is ready! Print on white cardstock for the best colouring experience.")
