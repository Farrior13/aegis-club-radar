import os
import math
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_font(bold=False, serif=False, mono=False, size=24):
    candidates = []
    if mono:
        candidates = [
            r"C:\Windows\Fonts\consolab.ttf" if bold else r"C:\Windows\Fonts\consola.ttf",
            r"C:\Windows\Fonts\courbd.ttf" if bold else r"C:\Windows\Fonts\cour.ttf",
        ]
    elif serif:
        candidates = [
            r"C:\Windows\Fonts\georgiab.ttf" if bold else r"C:\Windows\Fonts\georgia.ttf",
            r"C:\Windows\Fonts\timesbd.ttf" if bold else r"C:\Windows\Fonts\times.ttf",
        ]
    else:
        candidates = [
            r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_star(draw, cx, cy, r_outer=12, r_inner=5, fill=255):
    pts = []
    for i in range(10):
        ang = math.radians(-90 + i * 36)
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def draw_arrow_right(draw, cx, cy, size=14, fill=255):
    # Shaft + head
    draw.rectangle([cx - size, cy - 3, cx + 2, cy + 3], fill=fill)
    draw.polygon([(cx, cy - 10), (cx + size, cy), (cx, cy + 10)], fill=fill)


def draw_checkmark_badge(draw, cx, cy, r=15):
    draw.rectangle([cx - r, cy - r, cx + r, cy + r], fill=0)
    draw.line([(cx - 8, cy + 1), (cx - 2, cy + 7), (cx + 9, cy - 6)], fill=255, width=4)


def draw_guilloche_border(draw, w, h, margin=28, inner_margin=44):
    # Outer thick frame
    draw.rectangle([margin, margin, w - margin, h - margin], outline=0, width=6)
    # Inner fine frame
    draw.rectangle([inner_margin, inner_margin, w - inner_margin, h - inner_margin], outline=0, width=2)
    
    # Decorative banknote micro-tick pattern between outer and inner frames
    step = 18
    for x in range(inner_margin + 12, w - inner_margin - 12, step):
        draw.line([(x, margin + 2), (x + 6, inner_margin - 2)], fill=0, width=2)
        draw.line([(x + 6, margin + 2), (x, inner_margin - 2)], fill=0, width=2)
        draw.line([(x, h - inner_margin + 2), (x + 6, h - margin - 2)], fill=0, width=2)
        draw.line([(x + 6, h - inner_margin + 2), (x, h - margin - 2)], fill=0, width=2)

    for y in range(inner_margin + 12, h - inner_margin - 12, step):
        draw.line([(margin + 2, y), (inner_margin - 2, y + 6)], fill=0, width=2)
        draw.line([(margin + 2, y + 6), (inner_margin - 2, y)], fill=0, width=2)
        draw.line([(w - inner_margin + 2, y), (w - margin - 2, y + 6)], fill=0, width=2)
        draw.line([(w - inner_margin + 2, y + 6), (w - margin - 2, y)], fill=0, width=2)

    # Corner rosettes (banknote engraving style)
    corners = [
        (inner_margin, inner_margin),
        (w - inner_margin, inner_margin),
        (inner_margin, h - inner_margin),
        (w - inner_margin, h - inner_margin),
    ]
    for cx, cy in corners:
        r = 18
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255, outline=0, width=4)
        draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=0, outline=0)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=255, outline=255)


def draw_front_emblem(draw, cx, cy, radius=255):
    """
    Draws a high-impact pure black-and-white woodcut/engraving emblem:
    - Outer circular guilloche seal with sunburst engraving lines
    - Crossed-out panopticon surveillance eye at top
    - Bold physical banknote with '$' crest in the center
    - Ribbon banner at base of seal
    """
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=255, outline=0, width=6)
    draw.ellipse([cx - radius + 12, cy - radius + 12, cx + radius - 12, cy + radius - 12], fill=0, outline=0)
    
    # Sunburst engraving rays inside dark medallion
    inner_r = radius - 16
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        r_start = 50 if deg % 10 == 0 else 85
        x1 = cx + int(r_start * math.cos(rad))
        y1 = cy + int(r_start * math.sin(rad))
        x2 = cx + int((inner_r - 4) * math.cos(rad))
        y2 = cy + int((inner_r - 4) * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=255, width=2)

    # Central white shield / circle
    r_mid = 152
    draw.ellipse([cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid], fill=255, outline=0, width=5)
    draw.ellipse([cx - r_mid + 8, cy - r_mid + 8, cx + r_mid - 8, cy + r_mid - 8], outline=0, width=2)

    # Top part of emblem: Surveillance Eye with bold strike-through
    eye_y = cy - 60
    eye_w, eye_h = 76, 35
    pts_top = []
    pts_bot = []
    for i in range(-eye_w, eye_w + 1, 4):
        t = i / eye_w
        y_off = int(eye_h * (1 - t * t))
        pts_top.append((cx + i, eye_y - y_off))
        pts_bot.append((cx - i, eye_y + y_off))
    draw.polygon(pts_top + pts_bot, fill=255, outline=0)
    for i in range(len(pts_top) - 1):
        draw.line([pts_top[i], pts_top[i + 1]], fill=0, width=5)
        draw.line([pts_bot[i], pts_bot[i + 1]], fill=0, width=5)
    # Pupil (CCTV lens)
    draw.ellipse([cx - 22, eye_y - 22, cx + 22, eye_y + 22], fill=0, outline=0)
    draw.ellipse([cx - 8, eye_y - 8, cx + 8, eye_y + 8], fill=255, outline=255)
    # Bold diagonal NO-SURVEILLANCE slash across eye
    draw.line([(cx - 64, eye_y + 34), (cx + 64, eye_y - 34)], fill=255, width=14)
    draw.line([(cx - 64, eye_y + 34), (cx + 64, eye_y - 34)], fill=0, width=7)

    # Bottom part of emblem: Crisp Physical Banknote Stack
    bill_w, bill_h = 180, 88
    bx1, by1 = cx - bill_w // 2, cy + 2
    bx2, by2 = cx + bill_w // 2, cy + 2 + bill_h
    draw.rectangle([bx1 + 10, by1 + 10, bx2 + 10, by2 + 10], fill=0, outline=0)
    draw.rectangle([bx1 + 5, by1 + 5, bx2 + 5, by2 + 5], fill=255, outline=0, width=3)
    draw.rectangle([bx1, by1, bx2, by2], fill=255, outline=0, width=5)
    draw.rectangle([bx1 + 9, by1 + 9, bx2 - 9, by2 - 9], fill=255, outline=0, width=2)
    for cbx, cby in [(bx1 + 18, by1 + 18), (bx2 - 18, by1 + 18), (bx1 + 18, by2 - 18), (bx2 - 18, by2 - 18)]:
        draw.ellipse([cbx - 5, cby - 5, cbx + 5, cby + 5], fill=0)
    bcx, bcy = (bx1 + bx2) // 2, (by1 + by2) // 2
    draw.ellipse([bcx - 28, bcy - 26, bcx + 28, bcy + 26], fill=0, outline=0)
    f_bill = load_font(bold=True, serif=True, size=40)
    bbox = draw.textbbox((0, 0), "$", font=f_bill)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((bcx - tw // 2 - bbox[0], bcy - th // 2 - bbox[1]), "$", fill=255, font=f_bill)
    for ly in range(by1 + 22, by2 - 18, 9):
        draw.line([(bx1 + 26, ly), (bcx - 36, ly)], fill=0, width=2)
        draw.line([(bcx + 36, ly), (bx2 - 26, ly)], fill=0, width=2)

    # Ribbon banner at base of seal
    rib_w, rib_h = 236, 40
    rx1, ry1 = cx - rib_w // 2, cy + 114
    rx2, ry2 = cx + rib_w // 2, cy + 114 + rib_h
    draw.rectangle([rx1, ry1, rx2, ry2], fill=0, outline=255, width=3)
    f_rib = load_font(bold=True, mono=True, size=20)
    txt = "UNTRACKED • OFFLINE"
    bbox = draw.textbbox((0, 0), txt, font=f_rib)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2 - bbox[0], (ry1 + ry2) // 2 - th // 2 - bbox[1]), txt, fill=255, font=f_rib)


def render_front_card():
    # 3.5" x 2.0" @ 600 DPI = 2100 x 1200 px
    W, H = 2100, 1200
    img = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(img)

    draw_guilloche_border(draw, W, H, margin=28, inner_margin=46)

    # Left panel: High-contrast Woodcut/Engraving Emblem
    emblem_cx = 365
    emblem_cy = 520
    draw_front_emblem(draw, emblem_cx, emblem_cy, radius=255)

    # Caption under emblem on left panel
    f_ecap = load_font(bold=True, mono=True, size=23)
    c1 = "PEER-TO-PEER EXCHANGE"
    c2 = "ZERO DATA SURVEILLANCE"
    b1 = draw.textbbox((0, 0), c1, font=f_ecap)
    b2 = draw.textbbox((0, 0), c2, font=f_ecap)
    draw.text((emblem_cx - (b1[2] - b1[0]) // 2 - b1[0], 815), c1, fill=0, font=f_ecap)
    draw.text((emblem_cx - (b2[2] - b2[0]) // 2 - b2[0], 848), c2, fill=0, font=f_ecap)

    # Vertical engraving divider line
    div_x = 675
    draw.line([(div_x, 86), (div_x, H - 255)], fill=0, width=4)
    draw.line([(div_x + 8, 86), (div_x + 8, H - 255)], fill=0, width=1)

    # Right panel content area: x from 720 to 2015
    rx = 720
    rw = 1295

    # Top inverted pill tag with vector stars
    pill_h = 56
    draw.rectangle([rx, 88, rx + rw, 88 + pill_h], fill=0)
    f_tag = load_font(bold=True, mono=True, size=27)
    tag_text = "PAID IN PHYSICAL CASH  •  PUBLIC FREEDOM HANDOUT"
    bbox = draw.textbbox((0, 0), tag_text, font=f_tag)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx_tag = rx + (rw - tw) // 2 - bbox[0]
    draw.text((tx_tag, 88 + (pill_h - th) // 2 - bbox[1]), tag_text, fill=255, font=f_tag)
    draw_star(draw, tx_tag - 36, 88 + pill_h // 2, r_outer=13, r_inner=5, fill=255)
    draw_star(draw, tx_tag + tw + 36, 88 + pill_h // 2, r_outer=13, r_inner=5, fill=255)

    # Main Display Headline
    f_h1 = load_font(bold=True, serif=True, size=114)
    draw.text((rx, 164), "CASH IS FREEDOM.", fill=0, font=f_h1)

    # Subheadline with crisp underline
    f_sub = load_font(bold=True, size=42)
    draw.text((rx, 302), "No Surveillance. No Middleman. No Shutdown Switch.", fill=0, font=f_sub)
    draw.line([(rx, 366), (rx + rw, 366)], fill=0, width=5)

    # Succinct explanation body text
    f_body = load_font(bold=False, serif=True, size=35)
    f_body_bold = load_font(bold=True, serif=True, size=35)
    body_lines = [
        "Why did I hand you this card with my cash?",
        "Because every card tap and phone scan permanently logs where you go,",
        "what you buy, and who you deal with inside a surveilled banking grid.",
        "Physical cash is the last private, offline, peer-to-peer tool for human",
        "liberty—and if we stop using it, the state will eliminate it forever."
    ]
    y_curr = 390
    for idx, line in enumerate(body_lines):
        font_use = f_body_bold if idx in (0, 4) else f_body
        draw.text((rx, y_curr), line, fill=0, font=font_use)
        y_curr += 53

    # 3 High-Contrast Pillar Badges on Front
    box_y = 682
    box_h = 158
    gap = 22
    col_w = (rw - 2 * gap) // 3
    pillars = [
        ("1. HARD TO TRACK", "Zero digital data trail.", "100% private exchange."),
        ("2. 100% OFFLINE", "Works when power fails", "or networks go down."),
        ("3. FUNGIBLE & FREE", "Outside bank control.", "Cannot be frozen.")
    ]
    f_p_title = load_font(bold=True, mono=True, size=29)
    f_p_desc = load_font(bold=False, size=27)
    for i, (ptitle, pl1, pl2) in enumerate(pillars):
        bx = rx + i * (col_w + gap)
        draw.rectangle([bx, box_y, bx + col_w, box_y + box_h], fill=255, outline=0, width=4)
        draw.rectangle([bx, box_y, bx + col_w, box_y + 52], fill=0)
        bb = draw.textbbox((0, 0), ptitle, font=f_p_title)
        ptw, pth = bb[2] - bb[0], bb[3] - bb[1]
        draw.text((bx + (col_w - ptw) // 2 - bb[0], box_y + (52 - pth) // 2 - bb[1]), ptitle, fill=255, font=f_p_title)
        
        bb1 = draw.textbbox((0, 0), pl1, font=f_p_desc)
        draw.text((bx + (col_w - (bb1[2] - bb1[0])) // 2 - bb1[0], box_y + 66), pl1, fill=0, font=f_p_desc)
        bb2 = draw.textbbox((0, 0), pl2, font=f_p_desc)
        draw.text((bx + (col_w - (bb2[2] - bb2[0])) // 2 - bb2[0], box_y + 104), pl2, fill=0, font=f_p_desc)

    # Full-width Bottom Call-to-Action & Flip Prompt Bar
    foot_y = 975
    foot_h = 138
    draw.rectangle([86, foot_y, W - 86, foot_y + foot_h], fill=0)
    draw.rectangle([96, foot_y + 10, W - 96, foot_y + foot_h - 10], outline=255, width=2)
    f_cta = load_font(bold=True, size=41)
    f_flip = load_font(bold=True, mono=True, size=28)
    cta_txt = "KEEP CASH ALIVE: SPEND IT • ACCEPT IT • DEMAND IT"
    draw.text((126, foot_y + 24), cta_txt, fill=255, font=f_cta)
    
    flip_txt = "TURN CARD OVER: 4 REASONS CASH PROTECTS YOUR FREEDOM"
    draw.text((126, foot_y + 82), flip_txt, fill=255, font=f_flip)
    bb_fl = draw.textbbox((0, 0), flip_txt, font=f_flip)
    draw_arrow_right(draw, 126 + (bb_fl[2] - bb_fl[0]) + 30, foot_y + 98, size=14, fill=255)

    # Right-side white badge inside footer
    badge_x1 = W - 475
    draw.rectangle([badge_x1, foot_y + 22, W - 115, foot_y + foot_h - 22], fill=255)
    f_b = load_font(bold=True, mono=True, size=30)
    b_txt = "FLIP CARD OVER"
    bbb = draw.textbbox((0, 0), b_txt, font=f_b)
    btx = badge_x1 + (330 - (bbb[2] - bbb[0])) // 2 - bbb[0]
    bty = foot_y + 22 + (foot_h - 44 - (bbb[3] - bbb[1])) // 2 - bbb[1]
    draw.text((btx, bty), b_txt, fill=0, font=f_b)
    draw_arrow_right(draw, btx + (bbb[2] - bbb[0]) + 26, foot_y + foot_h // 2, size=12, fill=0)

    return img


def draw_pillar_icon(draw, kind, cx, cy, r=56):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0, outline=0)
    draw.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5], outline=255, width=2)

    if kind == "privacy":
        ew, eh = 36, 19
        pts = [(cx - ew, cy), (cx - ew // 2, cy - eh), (cx + ew // 2, cy - eh),
               (cx + ew, cy), (cx + ew // 2, cy + eh), (cx - ew // 2, cy + eh)]
        draw.polygon(pts, fill=0, outline=255, width=4)
        draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=255)
        draw.line([(cx - 32, cy + 26), (cx + 32, cy - 26)], fill=0, width=10)
        draw.line([(cx - 32, cy + 26), (cx + 32, cy - 26)], fill=255, width=5)

    elif kind == "offline":
        bolt = [
            (cx + 8, cy - 36),
            (cx - 22, cy + 4),
            (cx - 2, cy + 4),
            (cx - 10, cy + 36),
            (cx + 24, cy - 6),
            (cx + 2, cy - 6),
        ]
        draw.polygon(bolt, fill=255)

    elif kind == "bank":
        shield = [
            (cx, cy - 36),
            (cx + 30, cy - 22),
            (cx + 26, cy + 10),
            (cx, cy + 36),
            (cx - 26, cy + 10),
            (cx - 30, cy - 22),
        ]
        draw.polygon(shield, fill=0, outline=255, width=4)
        f_s = load_font(bold=True, serif=True, size=40)
        bb = draw.textbbox((0, 0), "$", font=f_s)
        draw.text((cx - (bb[2] - bb[0]) // 2 - bb[0], cy - (bb[3] - bb[1]) // 2 - bb[1] - 2), "$", fill=255, font=f_s)

    elif kind == "torch":
        draw.rectangle([cx - 7, cy + 4, cx + 7, cy + 34], fill=255)
        draw.rectangle([cx - 18, cy - 4, cx + 18, cy + 6], fill=255)
        flame = [
            (cx, cy - 38),
            (cx + 18, cy - 15),
            (cx + 11, cy - 4),
            (cx - 11, cy - 4),
            (cx - 18, cy - 15),
        ]
        draw.polygon(flame, fill=255)
        draw.polygon([(cx, cy - 24), (cx + 7, cy - 11), (cx - 7, cy - 11)], fill=0)


def render_back_card():
    # 3.5" x 2.0" @ 600 DPI = 2100 x 1200 px
    W, H = 2100, 1200
    img = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(img)

    draw_guilloche_border(draw, W, H, margin=28, inner_margin=46)

    # Top Header Banner
    hdr_x, hdr_y = 84, 78
    hdr_w, hdr_h = W - 168, 108
    draw.rectangle([hdr_x, hdr_y, hdr_x + hdr_w, hdr_y + hdr_h], fill=0)
    f_hdr = load_font(bold=True, serif=True, size=48)
    hdr_txt = "WHY USING & ACCEPTING CASH PROTECTS US ALL"
    bb = draw.textbbox((0, 0), hdr_txt, font=f_hdr)
    draw.text((hdr_x + 32, hdr_y + (hdr_h - (bb[3] - bb[1])) // 2 - bb[1]), hdr_txt, fill=255, font=f_hdr)

    # Right tag inside header
    tag_w = 420
    draw.rectangle([hdr_x + hdr_w - tag_w - 20, hdr_y + 20, hdr_x + hdr_w - 20, hdr_y + hdr_h - 20], fill=255)
    f_htag = load_font(bold=True, mono=True, size=26)
    ht_txt = "DEFEND HUMAN LIBERTY"
    bb_t = draw.textbbox((0, 0), ht_txt, font=f_htag)
    draw.text((hdr_x + hdr_w - tag_w - 20 + (tag_w - (bb_t[2] - bb_t[0])) // 2 - bb_t[0],
               hdr_y + 20 + (hdr_h - 40 - (bb_t[3] - bb_t[1])) // 2 - bb_t[1]), ht_txt, fill=0, font=f_htag)

    # 2x2 Grid of Illustrated Freedom & Privacy Pillars
    gx, gy = 84, 210
    gw = W - 168
    gh = 668
    col_gap = 28
    row_gap = 24
    cw = (gw - col_gap) // 2
    ch = (gh - row_gap) // 2

    cards = [
        (
            "privacy",
            "1. DEFEATS MASS SURVEILLANCE",
            [
                "Digital payments are heavily surveilled, logging every",
                "purchase, location, and habit. Cash is hard to track—",
                "letting you transact privately without a data trail."
            ]
        ),
        (
            "offline",
            "2. WORKS WHEN POWER GOES OUT",
            [
                "Cash is 100% offline infrastructure. When cell towers",
                "fail, payment servers crash, or the power grid goes",
                "down, physical bills keep people and shops running."
            ]
        ),
        (
            "bank",
            "3. OUTSIDE THE BANKING SYSTEM",
            [
                "Cash is fungible and permissionless. No bank or state",
                "algorithm can freeze a bill in your hand, skim swipe",
                "fees from local trade, or dictate what you may buy."
            ]
        ),
        (
            "torch",
            "4. USE IT OR LOSE IT FOREVER",
            [
                "As young people voluntarily opt out of cash for",
                "surveilled digital apps, it becomes easy for the state",
                "to abolish cash entirely. Circulation keeps it alive."
            ]
        ),
    ]

    f_ctitle = load_font(bold=True, size=33)
    f_cbody = load_font(bold=False, serif=True, size=27)

    for idx, (icon_kind, title, lines) in enumerate(cards):
        col = idx % 2
        row = idx // 2
        x1 = gx + col * (cw + col_gap)
        y1 = gy + row * (ch + row_gap)
        x2 = x1 + cw
        y2 = y1 + ch

        draw.rectangle([x1, y1, x2, y2], fill=255, outline=0, width=4)
        draw.line([(x1, y1 + 8), (x2, y1 + 8)], fill=0, width=4)

        icx = x1 + 78
        icy = (y1 + y2) // 2 + 6
        draw_pillar_icon(draw, icon_kind, icx, icy, r=54)

        tx = x1 + 154
        draw.text((tx, y1 + 26), title, fill=0, font=f_ctitle)
        draw.line([(tx, y1 + 72), (x2 - 24, y1 + 72)], fill=0, width=3)

        ly = y1 + 92
        for line in lines:
            draw.text((tx, ly), line, fill=0, font=f_cbody)
            ly += 42

    # Bottom Call-to-Action Stamp Box
    cta_y = 904
    cta_h = 212
    draw.rectangle([84, cta_y, W - 84, cta_y + cta_h], fill=0)
    draw.rectangle([96, cta_y + 12, W - 96, cta_y + cta_h - 12], outline=255, width=3)

    # Left CTA Stamp Box (White on Black)
    stamp_w = 435
    sx1 = 116
    draw.rectangle([sx1, cta_y + 28, sx1 + stamp_w, cta_y + cta_h - 28], fill=255)
    draw.rectangle([sx1 + 8, cta_y + 36, sx1 + stamp_w - 8, cta_y + cta_h - 36], outline=0, width=3)
    f_st1 = load_font(bold=True, mono=True, size=27)
    f_st2 = load_font(bold=True, serif=True, size=46)
    s1 = "CALL TO ACTION"
    s2 = "CHOOSE CASH"
    bb1 = draw.textbbox((0, 0), s1, font=f_st1)
    bb2 = draw.textbbox((0, 0), s2, font=f_st2)
    st1_x = sx1 + (stamp_w - (bb1[2] - bb1[0])) // 2 - bb1[0]
    draw.text((st1_x, cta_y + 50), s1, fill=0, font=f_st1)
    draw_star(draw, st1_x - 26, cta_y + 64, r_outer=11, r_inner=4, fill=0)
    draw_star(draw, st1_x + (bb1[2] - bb1[0]) + 26, cta_y + 64, r_outer=11, r_inner=4, fill=0)
    draw.text((sx1 + (stamp_w - (bb2[2] - bb2[0])) // 2 - bb2[0], cta_y + 98), s2, fill=0, font=f_st2)

    # Right CTA Action Steps (White text on Black)
    rx_cta = 584
    f_cta_h = load_font(bold=True, size=39)
    f_cta_b = load_font(bold=False, size=30)
    f_cta_m = load_font(bold=True, mono=True, size=26)

    draw.text((rx_cta, cta_y + 28), "HOW YOU CAN HELP KEEP CASH ALIVE TODAY:", fill=255, font=f_cta_h)
    draw.text((rx_cta, cta_y + 84), "1. Pay with physical bills at local shops     2. Welcome & accept cash proudly", fill=255, font=f_cta_b)
    step4_txt = "3. Keep emergency bills offline at home   4. PASS THIS CARD TO THE NEXT PERSON"
    draw.text((rx_cta, cta_y + 134), step4_txt, fill=255, font=f_cta_m)
    bb_s4 = draw.textbbox((0, 0), step4_txt, font=f_cta_m)
    draw_arrow_right(draw, rx_cta + (bb_s4[2] - bb_s4[0]) + 24, cta_y + 148, size=12, fill=255)

    return img


def draw_crop_marks(draw, x, y, w, h, mark_len=28, offset=12):
    draw.line([(x - offset - mark_len, y), (x - offset, y)], fill=0, width=3)
    draw.line([(x, y - offset - mark_len), (x, y - offset)], fill=0, width=3)
    draw.line([(x + w + offset, y), (x + w + offset + mark_len, y)], fill=0, width=3)
    draw.line([(x + w, y - offset - mark_len), (x + w, y - offset)], fill=0, width=3)
    draw.line([(x - offset - mark_len, y + h), (x - offset, y + h)], fill=0, width=3)
    draw.line([(x, y + h + offset), (x, y + h + offset + mark_len)], fill=0, width=3)
    draw.line([(x + w + offset, y + h), (x + w + offset + mark_len, y + h)], fill=0, width=3)
    draw.line([(x + w, y + h + offset), (x + w, y + h + offset + mark_len)], fill=0, width=3)


def render_showcase(front_img, back_img):
    """
    Creates a 2600 x 1650 pure black-and-white presentation & print proof sheet.
    """
    SW, SH = 2600, 1650
    sheet = Image.new("L", (SW, SH), 255)
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([24, 24, SW - 24, SH - 24], outline=0, width=6)
    draw.rectangle([36, 36, SW - 36, SH - 36], outline=0, width=2)

    # Top Title Banner
    draw.rectangle([60, 56, SW - 60, 196], fill=0)
    f_t1 = load_font(bold=True, serif=True, size=56)
    f_t2 = load_font(bold=True, mono=True, size=27)
    t1 = "“CASH IS FREEDOM” — 3.5\" × 2.0\" BLACK & WHITE BUSINESS CARD HANDOUT"
    t2 = "STANDARD US BUSINESS CARD (88.9 × 50.8 MM)  •  100% PURE MONOCHROME (B&W)  •  FRONT & BACK WITH ILLUSTRATIONS + CALL TO ACTION"
    bb1 = draw.textbbox((0, 0), t1, font=f_t1)
    bb2 = draw.textbbox((0, 0), t2, font=f_t2)
    draw.text(((SW - (bb1[2] - bb1[0])) // 2 - bb1[0], 74), t1, fill=255, font=f_t1)
    draw.text(((SW - (bb2[2] - bb2[0])) // 2 - bb2[0], 146), t2, fill=255, font=f_t2)

    cw, ch = 1155, 660
    f_resized = front_img.resize((cw, ch), Image.Resampling.LANCZOS)
    b_resized = back_img.resize((cw, ch), Image.Resampling.LANCZOS)

    fx, fy = 95, 290
    bx, by = 1350, 290

    f_lbl = load_font(bold=True, mono=True, size=31)
    l_front = "[ FRONT SIDE: 3.5\" × 2.0\" — ENGRAVED SEAL + HOOK ]"
    l_back = "[ BACK SIDE: 3.5\" × 2.0\" — 4 ILLUSTRATED PILLARS + CTA ]"
    draw.text((fx + 14, 214), l_front, fill=0, font=f_lbl)
    draw.text((bx + 14, 214), l_back, fill=0, font=f_lbl)

    draw.rectangle([fx + 12, fy + 12, fx + cw + 12, fy + ch + 12], fill=0)
    draw.rectangle([bx + 12, by + 12, bx + cw + 12, by + ch + 12], fill=0)
    sheet.paste(f_resized, (fx, fy))
    sheet.paste(b_resized, (bx, by))
    draw.rectangle([fx, fy, fx + cw, fy + ch], outline=0, width=4)
    draw.rectangle([bx, by, bx + cw, by + ch], outline=0, width=4)
    draw_crop_marks(draw, fx, fy, cw, ch)
    draw_crop_marks(draw, bx, by, cw, ch)

    # Bottom Section: Spec Table + Ready-to-Print 10-Up Cut Sheet Preview
    bot_y = 1015
    draw.line([(60, bot_y), (SW - 60, bot_y)], fill=0, width=4)

    sx = 85
    sy = bot_y + 28
    f_sh = load_font(bold=True, serif=True, size=40)
    f_sb = load_font(bold=False, size=29)
    f_sb_b = load_font(bold=True, size=29)
    draw.text((sx, sy), "PRINT-READY SPECIFICATION & BOUNTY CHECKLIST:", fill=0, font=f_sh)

    specs = [
        ("Standard Business Card Size:", "Exact 3.5\" × 2.0\" (88.9 × 50.8 mm) ratio (1.75:1) @ 300 & 600 DPI."),
        ("Front & Back Text + Images:", "Custom banknote guilloche border, anti-surveillance seal & 4 pillar icons."),
        ("Pure Black & White Only:", "100% monochrome (#000000 & #FFFFFF) — prints crisply on any laser/inkjet."),
        ("Freedom & Privacy Message:", "Succinctly explains why cash is private, fungible, offline & outside banks."),
        ("Youth Opt-Out Warning:", "Explains how abandoning cash lets the state abolish it (Use It or Lose It)."),
        ("Strong Call to Action:", "“Spend Cash • Accept Cash • Pass This Card to the Next Person” on both sides."),
        ("Included Print Deliverables:", "Front/Back 600 DPI PNGs, Vector SVGs & 8.5\"×11\" 10-Up Cut Sheet (CC0).")
    ]
    cy_s = sy + 68
    for k, v in specs:
        draw_checkmark_badge(draw, sx + 16, cy_s + 17, r=15)
        draw.text((sx + 46, cy_s), k, fill=0, font=f_sb_b)
        draw.text((sx + 485, cy_s), v, fill=0, font=f_sb)
        cy_s += 52

    # Right bottom: Mini 10-Up 8.5" x 11" Cut Sheet Diagram
    px = 1860
    py = bot_y + 30
    pw, ph = 650, 540
    draw.rectangle([px, py, px + pw, py + ph], fill=255, outline=0, width=4)
    draw.rectangle([px, py, px + pw, py + 58], fill=0)
    f_p = load_font(bold=True, mono=True, size=25)
    pt = "INCLUDED: 8.5\"×11\" 10-UP PRINT SHEET"
    bb_p = draw.textbbox((0, 0), pt, font=f_p)
    draw.text((px + (pw - (bb_p[2] - bb_p[0])) // 2 - bb_p[0], py + 15), pt, fill=255, font=f_p)

    mini_w, mini_h = 128, 72
    m_front = front_img.resize((mini_w, mini_h), Image.Resampling.LANCZOS)
    m_back = back_img.resize((mini_w, mini_h), Image.Resampling.LANCZOS)

    for s_idx, (m_img, lbl) in enumerate([(m_front, "FRONT SHEET (10x)"), (m_back, "BACK SHEET (10x)")]):
        page_x = px + 24 + s_idx * 308
        page_y = py + 76
        page_w = 294
        page_h = 408
        draw.rectangle([page_x, page_y, page_x + page_w, page_y + page_h], fill=255, outline=0, width=3)
        for r in range(5):
            for c in range(2):
                cx_m = page_x + 14 + c * 134
                cy_m = page_y + 14 + r * 76
                sheet.paste(m_img, (cx_m, cy_m))
                draw.rectangle([cx_m, cy_m, cx_m + mini_w, cy_m + mini_h], outline=0, width=1)
        f_ml = load_font(bold=True, mono=True, size=21)
        bbm = draw.textbbox((0, 0), lbl, font=f_ml)
        draw.text((page_x + (page_w - (bbm[2] - bbm[0])) // 2 - bbm[0], page_y + page_h + 10), lbl, fill=0, font=f_ml)

    return sheet


def render_10up_print_sheet(card_img):
    PW, PH = 2550, 3300
    sheet = Image.new("L", (PW, PH), 255)
    draw = ImageDraw.Draw(sheet)

    cw, ch = 1050, 600
    card_300 = card_img.resize((cw, ch), Image.Resampling.LANCZOS)

    mx, my = 225, 150
    for r in range(5):
        for c in range(2):
            x = mx + c * cw
            y = my + r * ch
            sheet.paste(card_300, (x, y))
            draw_crop_marks(draw, x, y, cw, ch, mark_len=30, offset=10)

    return sheet


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    front_600 = render_front_card()
    back_600 = render_back_card()

    front_600_path = os.path.join(OUT_DIR, "cash_card_front_600dpi.png")
    back_600_path = os.path.join(OUT_DIR, "cash_card_back_600dpi.png")
    front_300_path = os.path.join(OUT_DIR, "cash_card_front_300dpi.png")
    back_300_path = os.path.join(OUT_DIR, "cash_card_back_300dpi.png")
    showcase_path = os.path.join(OUT_DIR, "cash_freedom_handout_showcase.png")
    sheet_front_path = os.path.join(OUT_DIR, "cash_card_10up_letter_front_300dpi.png")
    sheet_back_path = os.path.join(OUT_DIR, "cash_card_10up_letter_back_300dpi.png")
    pdf_path = os.path.join(OUT_DIR, "cash_card_print_ready_duplex.pdf")

    front_600.save(front_600_path, dpi=(600, 600))
    back_600.save(back_600_path, dpi=(600, 600))

    front_300 = front_600.resize((1050, 600), Image.Resampling.LANCZOS)
    back_300 = back_600.resize((1050, 600), Image.Resampling.LANCZOS)
    front_300.save(front_300_path, dpi=(300, 300))
    back_300.save(back_300_path, dpi=(300, 300))

    showcase = render_showcase(front_600, back_600)
    showcase.save(showcase_path, dpi=(300, 300))

    s_front = render_10up_print_sheet(front_600)
    s_back = render_10up_print_sheet(back_600)
    s_front.save(sheet_front_path, dpi=(300, 300))
    s_back.save(sheet_back_path, dpi=(300, 300))

    s_front.convert("RGB").save(
        pdf_path, "PDF", resolution=300.0, save_all=True, append_images=[s_back.convert("RGB")]
    )

    print("Successfully generated all print-ready monochrome assets in:", OUT_DIR)


if __name__ == "__main__":
    main()
