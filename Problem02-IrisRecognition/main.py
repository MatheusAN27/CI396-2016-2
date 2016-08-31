# Filtro de canny (python canny)
# ler todas as images da base
# preprocessar as imagens
# aplicar o filtro de canny em cada uma delas
# aplicar a transformada circular hough (tentar implementar ela)
# com isso eu detectei a pupila
# dado o centro da pupila conseguimos detectar a iris
# http://stackoverflow.com/questions/9860667/writing-robust-color-and-size-invariant-circle-detection-with-opencv-based-on
# http://stackoverflow.com/questions/10716464/what-are-the-correct-usage-parameter-values-for-houghcircles-in-opencv-for-iris
import cv2
from casia_iris_image_loader import ImageLoaderCASIAIris
import numpy as np
from PIL import Image
from operator import itemgetter
from matplotlib import pyplot as plt


def show_img(imgs):
    cv2.imshow("output", np.hstack(imgs))
    cv2.waitKey(0)


def find_pupil(image):
    accumulator_threshold = 150
    circles = None
    while circles is None:
        circles = cv2.HoughCircles(image, cv2.cv.CV_HOUGH_GRADIENT,
                                   1, 1, param2=accumulator_threshold)
        accumulator_threshold = accumulator_threshold - 1
    circles = np.uint16(np.around(circles[0, :]))
    return circles[0]


def mean(points, image):
    values = []
    for point in points:
        values.append(image[point])
    return np.average(np.array(values))


def get_points_near_circle_perimeter(x, y, r, img, nearness=5):
    points_inside_circle = []
    img_row_size, img_column_size = img.shape
    for i in xrange(img_row_size):
        for j in xrange(img_column_size):
            point_distance = (x-i)**2 + (y-j)**2
            if (r-nearness <= point_distance and point_distance <= r):
                points_inside_circle.append((i, j))
    return points_inside_circle


def find_iris(x_pupil, y_pupil, r_pupil, img, value=4):
    max_r = min(img.shape)
    image = img.copy()
    x, y, r_b = x_pupil, y_pupil, r_pupil
    r_b += 15
    r_a = r_b + 20
    while r_a < max_r:
        print r_a, max_r
        cv2.circle(image, (x, y), r_a, (0, 255, 0), 1)
        cv2.circle(image, (x, y), 2, (0, 0, 255), 3)
        show_img([image])
        points_before = get_points_near_circle_perimeter(x, y, r_b, img)
        points_after = get_points_near_circle_perimeter(x, y, r_a, img)
        mean_after = mean(points_after, img)
        mean_before = mean(points_before, img)
        print abs(mean_after - mean_before)
        if abs(mean_after - mean_before) > value:
            break
        else:
            r_b = r_a
            r_a += 10
    return x, y, r_a


def pre_process_img(image):
    # Threshold.
    # Set values equal to or above 35 to 255.
    # Set values below 35 to 0.

    img = image
    img_with_blur = cv2.medianBlur(img, 25)
    th, im_th = cv2.threshold(img_with_blur, 25, 255, cv2.THRESH_BINARY)

    # Copy the thresholded image.
    im_floodfill = im_th.copy()

    # Mask used to flood filling.
    # Notice the size needs to be 2 pixels than the image.
    h, w = im_th.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)

    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (w/2, h - 1), 0)

    # Invert floodfilled image
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)

    # Combine the two images to get the foreground.
    im_out = im_th & im_floodfill_inv
    # cv2.imshow("Original Image", image)
    # cv2.imshow("Thresholded Image", im_th)
    # cv2.imshow("Floodfilled Image", im_floodfill)
    # cv2.imshow("Inverted Floodfilled Image", im_floodfill_inv)
    # cv2.imshow("Foreground", im_out)
    # cv2.waitKey(0)
    canny = cv2.Canny(im_out, 50, 200)
    return canny


casia = ImageLoaderCASIAIris('./databases/CASIA-Iris-Lamp-100')
for index, image in enumerate(casia.images):
    print casia.subjects[index]
    processed_img = pre_process_img(image)
    x_pupil, y_pupil, r_pupil = find_pupil(processed_img)
    cv2.circle(image, (x_pupil, y_pupil), r_pupil, (0, 255, 0), 1)
    cv2.circle(image, (x_pupil, y_pupil), 2, (0, 0, 255), 3)
    image = cv2.equalizeHist(image)
    x_iris, y_iris, r_iris = find_iris(x_pupil, y_pupil, r_pupil, image)
    cv2.circle(image, (x_iris, y_iris), r_iris, (0, 255, 0), 1)
    cv2.circle(image, (x_iris, y_iris), 2, (0, 0, 255), 3)
    show_img([processed_img, image])
# image = Image.open(
#     './databases/CASIA-Iris-Lamp-100/097/L/S2097L03.jpg').convert('L')
# image = np.array(image, 'uint8')
# processed_img = pre_process_img(image)
# x_pupil, y_pupil, r_pupil = find_pupil(processed_img)
# cv2.circle(image, (x_pupil, y_pupil), r_pupil, (0, 255, 0), 1)
# cv2.circle(image, (x_pupil, y_pupil), 2, (0, 0, 255), 3)
# x_iris, y_iris, r_iris = find_iris(x_pupil, y_pupil, r_pupil, image)
# cv2.circle(image, (x_iris, y_iris), r_iris, (0, 255, 0), 1)
# cv2.circle(image, (x_iris, y_iris), 2, (0, 0, 255), 3)
# show_img([processed_img, image])
