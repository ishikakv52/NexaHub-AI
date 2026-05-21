import cv2


def preprocess_image(image_path):

    image = cv2.imread(image_path)

    # grayscale
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # noise removal
    blur = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    # threshold
    processed = cv2.threshold(
        blur,
        0,
        255,
        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )[1]

    processed_path = (
        image_path +
        "_processed.jpg"
    )

    cv2.imwrite(
        processed_path,
        processed
    )

    return processed_path