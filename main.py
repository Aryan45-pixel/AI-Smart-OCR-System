import easyocr
import cv2

reader = easyocr.Reader(['en'])

image = cv2.imread('test.jpg')
results = reader.readtext(image)

for (bbox, text, prob) in results:
    print(f"Text: {text}, Confidence: {prob}")