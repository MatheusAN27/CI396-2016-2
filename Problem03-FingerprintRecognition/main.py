import math
import numpy as np
from matplotlib import pyplot as plt
import cv2
import copy
from sklearn.preprocessing import normalize
from rindex28_loader import Rindex28Loader


# cv2.imshow('', np.concatenate((sobelX, sobelY), axis=1))
# cv2.waitKey(0)


def image_enhancement(image):
    mean = np.mean(image)
    std = np.std(image)
    image_enhanced = 150 + 95 * ((image - mean) / float(std))
    image_enhanced[image_enhanced > 255] = 255
    image_enhanced[image_enhanced < 0] = 0
    return np.array(image_enhanced, dtype=np.uint8)


def orientation_computation(image):
    sobelX = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    sobelY = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    orientations = np.array([])
    averages_x = np.array([])
    averages_y = np.array([])
    for i in xrange(30):
        tmpX = sobelX[i * 10:(i + 1) * 10]
        tmpY = sobelY[i * 10:(i + 1) * 10]
        for j in xrange(30):
            Gx = tmpX[:, j * 10:(j + 1) * 10]
            Gy = tmpY[:, j * 10:(j + 1) * 10]
            average_x = np.sum(np.square(Gx) - np.square(Gy)) / float(100)
            average_y = np.sum(2 * Gx * Gy) / float(100)
            angle = math.atan2(average_y, average_x)/float(2)
            averages_x = np.append(averages_x, average_x)
            averages_y = np.append(averages_y, average_y)
            orientations = np.append(orientations, angle)
    orientations = np.reshape(orientations, (30, 30)) * -1
    averages_x = np.reshape(averages_x, (30, 30))
    averages_y = np.reshape(averages_y, (30, 30))
    return orientations, averages_x, averages_y


def show_orientation_lines(image_org, orientations):
    image = copy.deepcopy(image_org)
    lin_block = 0
    for lin in xrange(5, 300, 10):
        col_block = 0
        for col in xrange(5, 300, 10):
            angle = orientations[lin_block][col_block]
            n = np.tan(angle)
            if(np.abs(n) > 1):
                # varia y + 4 e y - 4
                # calcula x = ((y - y0)/n) + x0
                s_point = (col - 4, int((col - 4 - col)/n + lin))
                f_point = (col + 4, int((col + 4 - col)/n + lin))
            else:
                # varia x + 4 e x - 4
                # calcula y = n(x-x0) + y0
                s_point = (int(n*(lin - 4 - lin) + col), lin - 4)
                f_point = (int(n*(lin + 4 - lin) + col), lin + 4)
            cv2.line(image, s_point, f_point, (0, 0, 0))
            col_block += 1
        lin_block += 1
    plt.imshow(image, cmap='Greys_r')
    plt.show()


def show_interesting_blocks(image_original, interesting_blocks):
    image = copy.deepcopy(image_original)
    lin_block = 0
    for lin in xrange(5, 300, 10):
        col_block = 0
        for col in xrange(5, 300, 10):
            if interesting_blocks[lin_block][col_block]:
                cv2.circle(image, (col, lin), 2, (0, 0, 0), -1)
            col_block += 1
        lin_block += 1
    plt.imshow(image, cmap='Greys_r')
    plt.show()


def regions_of_interest(image):
    interesting_blocks = np.zeros((30, 30), dtype=np.bool)
    max_distance = 150 * np.sqrt(2)
    for i in xrange(30):
        tmpImg = image[i * 10:(i + 1) * 10]
        for j in xrange(30):
            block = tmpImg[:, j * 10:(j + 1) * 10]
            curret_distance = np.linalg.norm([150 - i, 150 - j])
            distance_ratio = (max_distance - curret_distance)/float(max_distance)
            mean = np.mean(block)/float(255)
            standard_deviation = np.std(block)/float(255)
            v = 0.5 * (1-mean) + 0.5 * standard_deviation + distance_ratio
            if v > 0.35:
                interesting_blocks[i][j] = True
    return interesting_blocks


def smooth_block(block):
    filter = np.array([[1, 1, 1], [1, 2, 1], [1, 1, 1]])
    return np.sum(np.multiply(block, filter))


def smooth_orientations(averages_x, averages_y, interesting_blocks):
    orientations = np.zeros((30, 30))
    for lin in xrange(1, 29):
        for col in xrange(1, 29):
            if interesting_blocks[lin, col]:
                a = smooth_block(averages_x[lin - 1:lin + 2, col - 1:col + 2])
                b = smooth_block(averages_y[lin - 1:lin + 2, col - 1:col + 2])
                orientations[lin][col] = math.atan2(b, a)/float(2)
    return orientations * -1


def delta(value):
    if abs(value) < np.pi/float(2):
        return value
    if value <= -np.pi/float(2):
        return np.pi + value
    return np.pi - value


def poincare(block):
    sum1 = delta(block[0][0] - block[1][0]) + delta(block[1][0] - block[2][0]) + delta(block[2][0] - block[2][1])
    sum2 = delta(block[2][1] - block[2][2]) + delta(block[2][2] - block[1][2]) + delta(block[1][2] - block[0][2])
    sum3 = delta(block[0][2] - block[0][1]) + delta(block[0][1] - block[0][0]) 
    return (sum1 + sum2 + sum3)/float(np.pi*2)


def singular_points_detection(orientations, interesting_blocks):
    singular_points = np.zeros((30, 30))
    for lin in xrange(1, 29):
        for col in xrange(1, 29):
            block = interesting_blocks[lin - 1:lin + 2, col - 1:col + 2]
            if np.all(block == True):
                sum = poincare(orientations[lin - 1:lin + 2, col - 1:col + 2])
                singular_points[lin][col] = sum
    return singular_points


def show_singular_points(image_original, singular_points):
    image = copy.deepcopy(image_original)
    error_lim = 0.2
    lin_block = 0
    for lin in xrange(5, 300, 10):
        col_block = 0
        for col in xrange(5, 300, 10):
            if 0.5 - error_lim <= singular_points[lin_block][col_block] <= 0.5 + error_lim:
                cv2.circle(image, (col, lin), 4, (0, 0, 0), -1)
            if -0.5 - error_lim <= singular_points[lin_block][col_block] <= -0.5 + error_lim :
                cv2.rectangle(image, (col, lin), (col+4, lin+4), (0,0,0))
            col_block += 1
        lin_block += 1
    plt.imshow(image, cmap='Greys_r')
    plt.show()


def zero_neighborhood(matrix, lin, col, size=5):
    middle = size/2
    upper_left_line = lin - middle
    upper_left_column = col - middle
    filter = np.zeros((size, size))
    filter[middle][middle] = 1.0
    for i in xrange(size):
        for j in xrange(size):
            matrix[upper_left_line + i][upper_left_column + j] *= filter[i][j]

def normalize_singular_points(singular_points):
    error_lim = 0.2
    normalized_singular_points = copy.deepcopy(singular_points)
    for lin in xrange(1, 29):
        for col in xrange(1, 29):
            if 0.5 - error_lim <= np.abs(normalized_singular_points[lin][col]) <= 0.5 + error_lim:
                zero_neighborhood(normalized_singular_points, lin, col)
            else:
                normalized_singular_points[lin][col] = 0.0
    return normalized_singular_points


rindex28 = Rindex28Loader('./databases/rindex28')
for image in rindex28.images:
    image_enhanced = image_enhancement(image)
    blurred_image = cv2.medianBlur(image_enhanced, 5)

    orientations, averages_x, averages_y = orientation_computation(blurred_image)
    # show_orientation_lines(image, orientations)

    interesting_blocks = regions_of_interest(image_enhanced)
    # show_interesting_blocks(image, interesting_blocks)

    smoothed_orientations = smooth_orientations(averages_x, averages_y, interesting_blocks)
    # show_orientation_lines(image, smoothed_orientations)

    singular_points = singular_points_detection(smoothed_orientations, interesting_blocks)
    # show_singular_points(image, singular_points)

    normalized_singular_points = normalize_singular_points(singular_points)
    show_singular_points(image, normalized_singular_points)
