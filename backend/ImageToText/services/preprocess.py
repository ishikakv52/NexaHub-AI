import cv2
import numpy as np
from PIL import Image
import io


def _deskew(image):
    """Handwritten images aksar tilted hoti hain - seedha karo"""
    coords = np.column_stack(np.where(image < 127))
    if len(coords) < 10:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Zyada rotation mat karo - sirf minor corrections
    if abs(angle) > 15:
        return image

    (h, w) = image.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def _connect_strokes(image):
    """Broken handwriting strokes ko connect karo"""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    connected = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    return connected


def _add_border(image, pad=40):
    """Edge pe likhe characters crop hone se bachao"""
    return cv2.copyMakeBorder(
        image, pad, pad, pad, pad,
        cv2.BORDER_CONSTANT,
        value=255  # White border
    )
def _isolate_ink_color(img_bgr):
    """
    Blue/dark ink ko white background se alag karo.
    Blue pen handwriting ke liye best result deta hai.
    """
    b, g, r = cv2.split(img_bgr)

    # Blue ink: Blue channel HIGH, Red+Green LOW
    # Inverted: ink = dark (0), background = white (255)
    ink_mask = cv2.subtract(b, r)  # Blue dominance
    _, isolated = cv2.threshold(
        ink_mask, 20, 255, cv2.THRESH_BINARY
    )
    # Invert: ink black, background white (OCR standard)
    isolated = cv2.bitwise_not(isolated)
    return isolated
def preprocess_image(image_bytes, is_handwritten=False):
    versions = {}

    pil_image = Image.open(
        io.BytesIO(image_bytes)
    ).convert("RGB")

    img_array = np.array(pil_image)
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    ink_isolated = _isolate_ink_color(img_bgr)
    versions['ink_isolated'] = ink_isolated
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    

    # ---------- DENOISE ----------
    # Handwriting ke liye gentler filter - fine strokes preserve karo
    if is_handwritten:
        gray = cv2.GaussianBlur(gray, (3, 3), 0)  # Light blur only
    else:
        gray = cv2.bilateralFilter(gray, 11, 17, 17)

    versions['gray'] = gray

    # ---------- DESKEW (handwriting ke liye) ----------
    if is_handwritten:
        gray = _deskew(gray)

    # ---------- OTSU ----------
    _, otsu = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    versions['otsu'] = otsu

    # ---------- ADAPTIVE (better for uneven lighting in handwriting) ----------
    adaptive = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  # MEAN → GAUSSIAN: smoother result
        cv2.THRESH_BINARY,               # Double inversion hataya
        21,                              # Larger block size for handwriting
        10
    )
    versions['adaptive'] = adaptive

    # ---------- CLAHE ----------
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    clahe_img = clahe.apply(gray)
    versions['clahe'] = clahe_img

    # ---------- SHARPEN ----------
    kernel = np.array([
        [0, -1,  0],
        [-1, 5, -1],
        [0, -1,  0]
    ])
    sharpened = cv2.filter2D(gray, -1, kernel)
    versions['sharpened'] = sharpened

    # ---------- UPSCALE WITH ADAPTIVE THRESH ----------
    h, w = gray.shape
    upscaled = cv2.resize(
        gray, (w * 3, h * 3),          # 4x → 3x: 4x is overkill, slows EasyOCR
        interpolation=cv2.INTER_CUBIC
    )
    ink_up = cv2.resize(
    ink_isolated,
    (w * 3, h * 3),
    interpolation=cv2.INTER_CUBIC
    )

    versions['ink_isolated_upscaled'] = _add_border(ink_up, pad=40)

    # Hardcoded 150 threshold hataya - Otsu use karo
    _, up_thresh = cv2.threshold(
        upscaled, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    versions['upscaled_text'] = up_thresh
    versions['upscaled_padded'] = _add_border(up_thresh, pad=40)

    # ---------- CLAHE + UPSCALE (EasyOCR ke liye best combo) ----------
    clahe_up = cv2.resize(
        clahe_img, (w * 3, h * 3),
        interpolation=cv2.INTER_CUBIC
    )
    versions['clahe_upscaled'] = clahe_up
    versions['clahe_upscaled_padded'] = _add_border(clahe_up, pad=40)

    # ---------- STROKE CONNECTION (handwriting only) ----------
    if is_handwritten:
        connected = _connect_strokes(otsu)
        versions['stroke_connected'] = connected

        # Upscaled + stroke connected - best for cursive
        up_connected = cv2.resize(
            connected, (w * 3, h * 3),
            interpolation=cv2.INTER_CUBIC
        )
        versions['upscaled_thresh'] = up_connected

    return versions, pil_image