import cv2
import numpy as np
from PIL import Image
import io


def _stroke_irregularity(gray):
    """
    Handwriting ka sabse strong signal:
    Printed text = uniform stroke width
    Handwritten = irregular, varying stroke width
    """
    _, binary = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Skeleton nikalo - stroke width measure karne ke liye
    dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    nonzero = dist[dist > 0]

    if len(nonzero) < 50:
        return 0.0

    # Coefficient of variation = std/mean
    # High CoV = irregular strokes = handwritten
    cov = float(np.std(nonzero) / (np.mean(nonzero) + 1e-6))
    return cov


def _line_straightness(gray):
    """
    Printed text lines are perfectly straight.
    Handwritten lines wobble.
    Returns wobble score: higher = more handwritten.
    """
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180,
        threshold=80,
        minLineLength=50,
        maxLineGap=10
    )

    if lines is None or len(lines) < 3:
        return 0.5  # Not enough lines - neutral score

    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        # Sirf near-horizontal lines lo (text lines)
        if angle < 20 or angle > 160:
            angles.append(angle)

    if len(angles) < 3:
        return 0.5

    # Low std = straight lines = printed
    # High std = wobbly lines = handwritten
    wobble = float(np.std(angles))
    return min(wobble / 10.0, 1.0)  # Normalize 0-1


def _white_background_score(gray):
    """
    Handwritten notes aksar white/light background pe hote hain.
    Returns 0-1: 1 = very white background
    """
    corners = [
        gray[0:30, 0:30],   gray[0:30, -30:],
        gray[-30:, 0:30],   gray[-30:, -30:]
    ]
    bg_mean = float(np.mean([np.mean(c) for c in corners]))
    # 200+ = light background
    return min(bg_mean / 255.0, 1.0)


def classify_image_content(image_bytes):
    """
    Pure math se image type detect karo.
    Handwriting detection ke liye stroke irregularity + line wobble use karo.
    """
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(pil_image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # --- Feature extraction ---
    variance = float(np.var(gray))

    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0) / edges.size)

    small = cv2.resize(img_bgr, (100, 100))
    unique_colors = len(np.unique(small.reshape(-1, 3), axis=0))

    corners = [
        gray[0:20, 0:20], gray[0:20, -20:],
        gray[-20:, 0:20], gray[-20:, -20:]
    ]
    bg_var = float(np.mean([np.var(c) for c in corners]))

    # --- New strong signals ---
    stroke_irr   = _stroke_irregularity(gray)   # High = handwritten
    line_wobble  = _line_straightness(gray)      # High = handwritten
    white_bg     = _white_background_score(gray) # High = light background

    # --- Scoring system (0-100) ---
    handwritten_score = 0

    # Stroke irregularity: strongest signal (40 pts)
    if stroke_irr > 0.6:
        handwritten_score += 40
    elif stroke_irr > 0.4:
        handwritten_score += 25
    elif stroke_irr > 0.2:
        handwritten_score += 10

    # Line wobble (25 pts)
    if line_wobble > 0.6:
        handwritten_score += 25
    elif line_wobble > 0.3:
        handwritten_score += 15

    # White/light background (15 pts)
    if white_bg > 0.75:
        handwritten_score += 15
    elif white_bg > 0.5:
        handwritten_score += 8

    # Moderate variance - not too uniform (screenshot), not too chaotic (photo)
    if 3000 < variance < 15000:
        handwritten_score += 10

    # Edge density in typical handwriting range
    if 0.02 < edge_density < 0.15:
        handwritten_score += 10

    screenshot_score = 0

    # Screenshots have very few unique colors
    if unique_colors < 300:
        screenshot_score += 40
    elif unique_colors < 500:
        screenshot_score += 25

    # Very uniform background
    if bg_var < 50:
        screenshot_score += 30
    elif bg_var < 100:
        screenshot_score += 15

    # Low variance overall
    if variance < 4000:
        screenshot_score += 20
    elif variance < 6000:
        screenshot_score += 10

    # Low stroke irregularity (printed UI text)
    if stroke_irr < 0.2:
        screenshot_score += 10

    # --- Final classification ---
    is_handwritten = handwritten_score >= 50
    is_screenshot = screenshot_score >= 60 and not is_handwritten

    if is_screenshot:
        img_type = 'screenshot'
        ocr_mode = 'screenshot'
        confidence = min(55 + screenshot_score // 3, 97)

    elif is_handwritten:
        img_type = 'handwritten'
        ocr_mode = 'handwritten'
        confidence = min(50 + handwritten_score // 2, 97)

    elif unique_colors > 5000 and variance > 8000:
        img_type = 'photo'
        ocr_mode = 'mixed'
        confidence = 72

    else:
        img_type = 'mixed'
        ocr_mode = 'mixed'
        confidence = 60

    return {
        'type': img_type,
        'ocr_mode': ocr_mode,
        'confidence': confidence,
        'is_handwritten': is_handwritten,   # ← preprocess_image() ko pass karo
        'stats': {
            'variance': round(variance, 2),
            'edge_density': round(edge_density, 4),
            'unique_colors': unique_colors,
            'stroke_irregularity': round(stroke_irr, 3),
            'line_wobble': round(line_wobble, 3),
            'white_bg_score': round(white_bg, 3),
            'handwritten_score': handwritten_score,
            'screenshot_score': screenshot_score,
        }
    }