
import math
import statistics
import os
import numpy as np
import cv2
from datetime import datetime
import psutil
import time
from LocalStreamReciever import LocalStreamReciever
import random
import asyncio
from database_add_entry import send_entry_main, send_entry_secondary,  get_last_id
# class names
class_names = ["rock", "balon", "metall"]
width = 640
height = 640

"""
TO-DO: replace print with logger
"""
def calculate_trashold_table(trashold=100, crop_y0=300):
    """
    Used square approximation.
    1325 - length between roll.
    """
    # trashold = 100  # mm
    height_table = [
        (-0.0002833331 * i ** 2 + 1.7578584372 * i + 94.3323068379) for i in range(1080)
    ]
    trashold_table = [x / 1325 * trashold for x in height_table]
    trashold_table = trashold_table[crop_y0:]

    return trashold_table


def apply_trashold(pred, trashold_table):
    maxs = []
    for det in pred:
        max_storona = max(det[2] - det[0], det[3] - det[1])
        #dioganal = (det[2] - det[0]) ** 2 + (det[3] - det[1]) ** 2
        #dioganal = math.sqrt(dioganal)
        #max_val = max(max_storona, dioganal)
        #print("max_storona=", max_val)
        #print("mean_trashold=", statistics.mean(trashold_table[int(det[1]) : int(det[3])]))
        maxs.append(max_storona)
    pred_trashold = [
        pred[i]
        for i in range(len(maxs))
        if maxs[i] > statistics.mean(trashold_table[int(pred[i][1]) : int(pred[i][3])])
    ]
    return pred_trashold


def apply_trashold2(pred, trashold_table):
    maxs = []
    for det in pred:
        max_storona = max(det[2] - det[0], det[3] - det[1])
        dioganal = (det[2] - det[0]) ** 2 + (det[3] - det[1]) ** 2
        dioganal = math.sqrt(dioganal)
        max_val = max(max_storona, dioganal)
        maxs.append(max_val)

    trashold_table = np.array(trashold_table[300:])
    size_maxs = len(maxs)
    index_trash = np.stack([pred[:size_maxs, 1], pred[:size_maxs, 3]], -1)
    means = np.array(
        [
            trashold_table[index_trash[i, 0] : index_trash[i, 1]].mean()
            for i in range(size_maxs)
        ]
    )
    pred1 = pred[maxs > means]
    return pred1


def detect_onnx(image_src=None):
    num_classes = 3
    """
    something is being handled here

    return:
        batch_detections 
    """
    random.seed(version=2)
    count = random.randint(0, 10)
    batch_detections = []
    for i in range(count):
        x0 = random.randint(0, width - 2)
        y0 = random.randint(0, height - 2)
        x1 = random.randint(x0 + 1, width)
        y1 = random.randint(y0 + 1, height)
        class_object = class_names[random.randint(0, 2)]
        score = random.random()
        batch_detections.append([x0, y0, x1, y1, score, class_object])
    return batch_detections

def return_coords(pred, resize_shape, crop):
    result = []
    crop_x0, crop_y0, crop_x1, crop_y1 = crop
    image_h, image_w = resize_shape
    image_h_crop = crop_y1 - crop_y0
    image_w_crop = crop_x1 - crop_x0
    k_x = image_w_crop / image_w
    k_y = image_h_crop / image_h
    for x in pred:
        x[0] = x[0] * k_x + crop_x0 # top left x
        x[1] = x[1] * k_y + crop_y0 # top left y
        x[2] = x[2] * k_x + crop_x0 # bottom right x
        x[3] = x[3] * k_y + crop_y0 # bottom right y
        result.append(x)
    return result

def crop(original_image, crop):
    backup = original_image.copy()
    if crop is not None:
        img0 = original_image[crop[1]:crop[3], crop[0]:crop[2]]

    return img0

def xyxy2xywh_custom(box, original_shape):
    height, width, chanell = original_shape
    box[0] = box[0] if box[0] >= 0 else 0
    box[1] = box[1] if box[1] >= 0 else 0
    box[2] = box[2] if box[2] <= width else width - 1
    box[3] = box[3] if box[3] <= height else height - 1
    x = (box[0] + box[2]) / 2  # x center
    y = (box[1] + box[3]) / 2  # y center
    w = box[2] - box[0]  # width
    h = box[3] - box[1]  # height
    return [x,y,w,h]

def absolute_coord_to_relative(det, original_shape):
    height, width, chanell = original_shape
    abs_coord = [det[0] / width, det[1] / height, det[2] / width, det[3] / height]
    return [det[0] / width, det[1] / height, det[2] / width, det[3] / height]

def save_detection_in_yolo_format(det, txt_path, image_shape):
    for *xyxy, cls, score in reversed(det):
        xywh = xyxy2xywh_custom(xyxy, image_shape)
        xywh_to_write = absolute_coord_to_relative(xywh, image_shape)
        line = (cls, *xywh_to_write)  # label format
        with open(txt_path, 'a') as f:
            f.write(('%g ' * len(line)).rstrip() % line + '\n')

def checkfreespace2(disk="C:"):
    free = psutil.disk_usage(disk).free/(1024*1024*1024)
    #print(f"{free:.4} gb free on disk {disk}")    
    return free

async def send_to_database(index, name_image, detection, count_det):
    send_entry_main(index, name_image)
    tasks = [asyncio.ensure_future(send_entry_secondary(count_det + i, index, d)) for i, d in enumerate(detection, 1)]
    await asyncio.wait(tasks)


if __name__ == '__main__':
    URL_CAMERA_RTSP_H264 = "rtsp://root:admin@192.168.1.71/axis-media/media.amp?videocodec=h264"
    trashold_table =  calculate_trashold_table(600, 0)
    index, count_det = get_last_id()
    source = LocalStreamReciever(URL_CAMERA_RTSP_H264)

    crop_shape = [570, 300, 1350, 1080]
    folder = "detected"
    original_shape = (1080, 1920, 3)
    source.cv_start_streaming()
    timeout = 5
    try:
        while True:    
            image_src = source.cv_get_frame_raw(timeout)
            #ret, image_src = source.read()
            if image_src is None:
                source.stop_streaming()
                time.sleep(1)
                source = LocalStreamReciever(URL_CAMERA_RTSP_H264)
                source.cv_start_streaming()
                print("start restream")
                continue


            filename = datetime.today().strftime('%Y-%m-%d_%H-%M-%S.%f')[:-3]
            #abs_path = os.path.abspath(folder)
            #name_image = os.path.join(abs_path, filename + ".png")
            #name_txt = os.path.join(abs_path, filename + ".txt")
            
            img_src_crop = crop(image_src, crop_shape)
            batch_detections = detect_onnx(img_src_crop)
            if len(batch_detections):
                cr_det = return_coords(batch_detections, (640, 640), crop_shape)
                res_det = apply_trashold(cr_det, trashold_table)
                print("get ", len(res_det), "detection on ", len(batch_detections), "prediction")
                
                if len(res_det) > 0:
                    #cv2.imwrite(name_image, image_src)
                    asyncio.run(send_to_database(index, filename, res_det, count_det))
                    index += 1
                    count_det += len(res_det)
                    #save_detection_in_yolo_format(res_det, name_txt, original_shape)
            freeSpace = checkfreespace2()
            if freeSpace < 10:
                print("[Warning] No free space found on disk -C-")
                break
    except KeyboardInterrupt:
        print("Exit from programm..")
        pass
    finally:
        source.stop_streaming()
