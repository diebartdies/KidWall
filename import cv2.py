import cv2
import numpy as np

# Load image
img = cv2.imread('input.jpg')

# Convert to HSV and use the Value channel
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
v = hsv[:,:,2]

# Adaptive threshold
thresh = cv2.adaptiveThreshold(v, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)

# Save thresholded image for debugging
cv2.imwrite('thresh_debug.jpg', thresh)

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Draw contours
img_contour = img.copy()
cv2.drawContours(img_contour, contours, -1, (0, 0, 0), 1)

# Save result
cv2.imwrite('output.jpg', img_contour)

print("Done! Check output.jpg and thresh_debug.jpg for results.")