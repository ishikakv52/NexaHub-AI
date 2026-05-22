import cv2
import tempfile


# def preprocess_image(image_path):

#     img = cv2.imread(image_path)

#     gray = cv2.cvtColor(
#         img,
#         cv2.COLOR_BGR2GRAY
#     )

#     # upscale
#     gray = cv2.resize(
#         gray,
#         None,
#         fx=3,
#         fy=3,
#         interpolation=cv2.INTER_CUBIC
#     )

#     # sharpen
#     kernel = cv2.getStructuringElement(
#         cv2.MORPH_RECT,
#         (1, 1)
#     )

#     gray = cv2.dilate(gray, kernel)

#     # threshold
#     processed = cv2.adaptiveThreshold(
#         gray,
#         255,
#         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY,
#         11,
#         2
#     )

#     temp = tempfile.NamedTemporaryFile(
#         delete=False,
#         suffix=".jpg"
#     )

#     path = temp.name

#     temp.close()

#     cv2.imwrite(path, processed)

#     return path
def preprocess_image(image_path):
    return image_path