import easyocr
import cv2

reader = easyocr.Reader(
    ['en', 'hi'],
    gpu=False
)


def extract_text(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return "Image not readable"

    results = reader.readtext(
        img,
        detail=1
    )

    if not results:
        return "No text detected"

    # SORT RESULTS
    results = sorted(
        results,
        key=lambda x: (
            int(x[0][0][1] / 20),
            x[0][0][0]
        )
    )

    final_lines = []

    current_line = ""

    prev_y = None

    for item in results:

        try:

            bbox = item[0]
            text = item[1]
            confidence = item[2]

            if confidence < 0.20:
                continue

            current_y = bbox[0][1]

            # NEW LINE
            if prev_y is not None and abs(current_y - prev_y) > 18:

                final_lines.append(
                    current_line
                )

                current_line = text

            else:

                if current_line == "":
                    current_line = text
                else:
                    current_line += " " + text

            prev_y = current_y

        except:
            continue

    # LAST LINE
    if current_line:
        final_lines.append(current_line)

    final_text = "\n".join(final_lines)

    return final_text