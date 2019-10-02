from cv2 import cv2
from ctypes import *
import numpy as np
import random
import math
import time
import os

from anti_deform import from_label_deform

def get_random_vs(rows, cols, _):
    vertex = (random.randint(int(rows / 4), int((rows / 4) * 3)), random.randint(int(cols / 4), int((cols / 4) * 3)))
    avg = (rows + cols) / 2
    v = (random.uniform(0, 2 * math.pi), random.uniform(avg / 10, avg / 9))
    k = math.tan(v[0])

    return vertex, v, k, avg

def distance(k, vertex, point):
    c, b, a = k * vertex[0] - vertex[1], -1 * k, 1
    return abs(a * point[0] + b * point[1] + c) / math.sqrt(a**2 + b**2)


def deform(src_shape, label_x, label_y, type):
    '''
    type:
        0 - fold
        1 - curve
    '''

    # dst_img = np.ones(src_shape) * 255

    # call C 
    c_utils = np.ctypeslib.load_library('util', 'c_src')
    c_deform = c_utils.deform
    c_deform.restype = None
    c_deform.argtypes = [
        np.ctypeslib.ndpointer(dtype=np.float32, ndim=2),
        np.ctypeslib.ndpointer(dtype=np.float32, ndim=2),
        np.ctypeslib.ndpointer(dtype=np.int, ndim=1),
        np.ctypeslib.ndpointer(dtype=np.int, ndim=1),
        np.ctypeslib.ndpointer(dtype=np.float32, ndim=1),
        c_int,
    ]



    rows, cols, _ = src_shape
    vertex, v, k, avg = get_random_vs(*src_shape)

    # prepare data
    label_x = label_x.astype(np.float32)
    label_y = label_y.astype(np.float32)
    shape = np.array([rows, cols])
    vertex = np.array(vertex)
    v = np.array(v).astype(np.float32)


    # defrom
    c_deform(label_x, label_y, shape, vertex, v, type)

    return label_x, label_y

    
    # # distance_array_2d = np.array([distance(k, vertex, (x, y)) for x in range(rows) for y in range(cols)]).reshape((rows, cols))
    # distance_array_2d = np.array([c_distance(c_float(k), vertex[0], vertex[1], x, y) for x in range(rows) for y in range(cols)]).reshape((rows, cols))

    # #debug
    # # np.savetxt('data_gen/color_test_distance.csv', distance_array_2d, fmt='%f')

    # for x in range(rows):
    #     for y in range(cols):
    #         alpha = (avg / 3) if type == 0 else 2
    #         w = (alpha / (distance_array_2d[x][y] + alpha)) if type == 0 else (1 - (distance_array_2d[x][y] / (rows / 2))**alpha)
    #         # w = c_w(c_float(alpha), c_float(distance_array_2d[x][y]), rows, type)
    #         offset_x, offset_y = v[1] * math.cos(v[0]) * w, v[1] * math.sin(v[0]) * w
    #         # src_x, src_y = x - offset_x, y - offset_y

    #         label[x][y][0] += offset_x
    #         label[x][y][1] += offset_y

    # return label

def gen_deform_label(img_path, data_path, operation : list):
    assert os.path.exists(img_path) and os.path.exists(data_path), 'image path or data path not exists'

    print(f'img: {os.path.abspath(img_path)}')
    filename = os.path.basename(img_path)
    img = cv2.imread(img_path, cv2.IMREAD_COLOR)
    img_shape = img.shape
    label_x, label_y =  np.zeros((img.shape[0], img.shape[1])), np.zeros((img.shape[0], img.shape[1]))
    total_start = time.time()

    for i, type_ in enumerate(operation):
        start = time.time()
        print(f'round {i}, type:{"fold" if type_ == 0 else "curve"}')
        start = time.time()
        label_x, label_y = deform(img_shape, label_x, label_y, type_)
        print(f'round {i} finished, time:{time.time() - start}s')

    label_path = os.path.join(data_path, 'labels')

    if not os.path.exists(label_path):
        print(f'path {label_path} not exists, mkdir')
        os.mkdir(label_path)
    
    np.save(os.path.join(label_path, filename[: filename.index('.')] + '_x'), label_x)
    np.save(os.path.join(label_path, filename[: filename.index('.')] + '_y'), label_y)
    # cv2.imwrite(os.path.join(img_path, filename), img)
    print(f'img: {os.path.abspath(img_path)} finished, time:{time.time() - total_start}s')
    return label_x, label_y



if __name__ == '__main__':
    img_path = '/home/wulei/DocUNet/data_gen/scan/dtd_1.jpg'
    operation = [1]
    data_path = '/home/wulei/DocUNet/data_gen'
    filename = os.path.basename(img_path)

    label_x, label_y = gen_deform_label(img_path, data_path, operation)
    print(f'start deformation...')
    start = time.time()
    img = from_label_deform(label_x, label_y, img_path)
    cv2.imwrite(os.path.join(data_path, 'img', filename), img)
    print(f'deformation finished. time: {time.time() - start}')