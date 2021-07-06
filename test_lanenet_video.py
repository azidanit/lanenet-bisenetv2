#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 18-5-23 上午11:33
# @Author  : MaybeShewill-CV
# @Site    : https://github.com/MaybeShewill-CV/lanenet-lane-detection
# @File    : test_lanenet.py
# @IDE: PyCharm Community Edition
"""
test LaneNet model on single image
"""
import argparse
import os.path as ops
import time
import socket

import cv2
import matplotlib.pyplot as plt
import numpy as np
# import tensorflow as tf

import tensorflow.compat.v1 as tf
tf.disable_v2_behavior() 

from lanenet_model import lanenet
from lanenet_model import lanenet_postprocess
from local_utils.config_utils import parse_config_utils
from local_utils.log_util import init_logger

CFG = parse_config_utils.lanenet_cfg
LOG = init_logger.get_logger(log_file_name_prefix='lanenet_test')


def init_args():
    """

    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_path', type=str, help='The image path or the src image save dir')
    parser.add_argument('--weights_path', type=str, help='The model weights path')

    return parser.parse_args()


def args_str2bool(arg_value):
    """

    :param arg_value:
    :return:
    """
    if arg_value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True

    elif arg_value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Unsupported value encountered.')


def minmax_scale(input_arr):
    """
    :param input_arr:
    :return:
    """
    min_val = np.min(input_arr)
    max_val = np.max(input_arr)

    output_arr = (input_arr - min_val) * 255.0 / (max_val - min_val)

    return output_arr

#ui actions..

control_x = 0
mouse_x = 0
control_y = 0
mouse_y = 0
kb_input = 0
moving_average_size = 100
moving_average_vector = np.array([])
moving_window_size = 8
def mouse_events(event, x, y, flags, param):
    global mouse_x, mouse_y, kb_input, control_x, control_y
        
    if event == cv2.EVENT_LBUTTONDOWN:
        if kb_input == ord('x'):
            mouse_x = x
        elif kb_input == ord('y'):
            mouse_y = y
        elif kb_input == ord(' '):
            kb_input = 0
            

def test_lanenet(video_path, weights_path):
    """

    :param image_path:
    :param weights_path:
    :return:
    """
    global sess, mouse_x, mouse_y, kb_input, control_x, control_y, moving_average_size, moving_average_vector

    assert ops.exists(video_path), '{:s} not exist'.format(video_path)

    # LOG.info('Start reading image and preprocessing')
    t_start = time.time()

    # LOG.info('Image load complete, cost time: {:.5f}s'.format(time.time() - t_start))

    input_tensor = tf.placeholder(dtype=tf.float32, shape=[1, 256, 512, 3], name='input_tensor')

    net = lanenet.LaneNet(phase='test', cfg=CFG)
    binary_seg_ret, instance_seg_ret = net.inference(input_tensor=input_tensor, name='LaneNet')

    postprocessor = lanenet_postprocess.LaneNetPostProcessor(cfg=CFG)

    # Set sess configuration
    sess_config = tf.ConfigProto()
    sess_config.gpu_options.per_process_gpu_memory_fraction = CFG.GPU.GPU_MEMORY_FRACTION
    sess_config.gpu_options.allow_growth = CFG.GPU.TF_ALLOW_GROWTH
    sess_config.gpu_options.allocator_type = 'BFC'

    sess = tf.Session(config=sess_config)

    # define moving average version of the learned variables for eval
    with tf.variable_scope(name_or_scope='moving_avg'):
        variable_averages = tf.train.ExponentialMovingAverage(
            CFG.SOLVER.MOVING_AVE_DECAY)
        variables_to_restore = variable_averages.variables_to_restore()

    # define saver
    saver = tf.train.Saver(variables_to_restore)

    # mask_image = np.zeros((512, 256,3))
    # image_vis = np.zeros((512,256))
    # embedding_image = np.zeros((512,256))
    # binary_image = np.zeros((512,256))

    # plt.figure('mask_image')
    # window_mask = plt.imshow(mask_image[:, :, (2, 1, 0)])
    # plt.figure('src_image')
    # window_src = plt.imshow(image_vis[:, :, (2, 1, 0)])
    # plt.figure('instance_image')
    # window_instance = plt.imshow(embedding_image[:, :, (2, 1, 0)])
    # plt.figure('binary_image')
    # window_binary = plt.imshow(binary_image * 255, cmap='gray')

    cap = cv2.VideoCapture(video_path)
    cap.set(5,30)
    frame_counter = 0
    plt.ion()

    #set mouse stuffs
    cv2.imshow('MainWindow', np.zeros((360,480)))
    cv2.setMouseCallback('MainWindow',mouse_events)
    back_error = 0


    udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    udp_socket.bind(("127.0.0.1",5000)) #client 42069
    with sess.as_default():
        saver.restore(sess=sess, save_path=weights_path)
        while (cap.isOpened()):
            ret, image = cap.read()
            # image = cv2.imread('data/cvt/6.png')
            # image = cv2.resize(image, (640,480))
            # image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if not (ret):
                LOG.info('Error ret...\n')
                break

            t_start = time.time()

            image_vis = image
            image = cv2.resize(image, (512, 256), interpolation=cv2.INTER_LINEAR)
            image = image / 127.5 - 1.0
            frame_counter += 1

            # loop_times = 500
            # for i in range(loop_times):
            #     binary_seg_image, instance_seg_image = sess.run(
            #         [binary_seg_ret, instance_seg_ret],
            #         feed_dict={input_tensor: [image]}
            #     ) test:
            #     print('WHYYY')
            # LOG.info('Single imgae inference cost time: {:.5f}s'.format(t_cost))
            binary_seg_image, instance_seg_image = sess.run(
                    [binary_seg_ret, instance_seg_ret],
                    feed_dict={input_tensor: [image]}
                )

            # postprocess_result = postprocessor.postprocess(
            #     binary_seg_result=binary_seg_image[0],
            #     instance_seg_result=instance_seg_image[0],
            #     source_image=image_vis
            # )
            # mask_image = postprocess_result['mask_image']
#  test:
            #     print('WHYYY')
            for i in range(CFG.MODEL.EMBEDDING_FEATS_DIMS):
                instance_seg_image[0][:, :, i] = minmax_scale(instance_seg_image[0][:, :, i])
            embedding_image = np.array(instance_seg_image[0], np.uint8)
            # plt.figure('mask_image')
            # plt.imshow(mask_image[:, :, (2, 1, 0)])
            # plt.figure('src_image')
            # plt.imshow(image_vis[:, :, (2, 1, 0)])
            # plt.figure('instance_image')
            # plt.imshow(embedding_image[:, :, (2, 1, 0)])
            # plt.figure('binary_image')
            # plt.show()
            # window_mask.set_data(mask_image[:, :, (2, 1, 0)])
            # plt.show()
            # window_src.set_data(image_vis[:, :, (2, 1, 0)])
            # window_instance.set_data(embedding_image[:, :, (2, 1, 0)])
            # window_binary.set_data(binary_seg_image[0] * 255)
            # binseggray = cv2.applyColorMap(binary_seg_image[0]*255,cv2.COLORMAP_JET)
            # print(mask_image)
            bin_out_mask = np.array(binary_seg_image[0]*255).astype('uint8')
            bin_out_mask_resized = cv2.resize(bin_out_mask, (640, 480))
            bin_out_mask_resized = cv2.cvtColor(bin_out_mask_resized, cv2.COLOR_GRAY2RGB)
            cv2.imshow("binnary seg image",np.array(binary_seg_image[0]*255).astype('uint8'))
            cv2.imshow("emebedding image",embedding_image)
            cv2.imshow("binnary image res",bin_out_mask_resized)


            print(type(image_vis))
            print(type(embedding_image))
            print(bin_out_mask.shape)
            print(embedding_image[:,:,:-1].shape)

            embedding_image = cv2.bitwise_and(embedding_image[:,:,:-1],embedding_image[:,:,:-1],mask=bin_out_mask)


            out_img = cv2.addWeighted(image_vis, 1, bin_out_mask_resized, 0.4, 0)
            # cv2.imshow("mask image",mask_image)
            cv2.imshow("out img bin", out_img)
            cv2.imshow("out img ins", cv2.addWeighted(image_vis, 1, cv2.resize(embedding_image, (640,480)), 0.75, 0))
            cv2.imshow("src_image",image_vis)

            
            res_wk = cv2.waitKey(30)

            LOG.info('frame {frame_c}, FPS: {fps}'.format(frame_c=frame_counter,fps=-1/(t_start-time.time())))


            if res_wk == ord('q'):
                break

            
            if res_wk == ord('x'):
                kb_input = res_wk
            if res_wk == ord('y'):
                kb_input = res_wk
            if res_wk == ord(' '):
                kb_input = res_wk
                control_x = mouse_x
                control_y = mouse_y

            # drawing on mainwindow + detecting control point
            control_point_y = -1
            _tmp = 0
            test = False
            bin_mask = np.array(binary_seg_image[0])
            for i in reversed(range(256)):
                # pixsum = np.sum(bin_mask[   max(0,i-moving_window_size//2)         : min(255,i+moving_window_size//2),
                #                             max(0,control_x-moving_window_size//2) : min(255,control_x+moving_window_size//2)])
                pixsum = 0
                for ii in range(moving_window_size//2):
                    for jj in range(moving_window_size//2):
                        if 0<ii+i<256 and 0<jj+control_x<513:
                            pixsum += bin_mask[ii+i][jj+control_x]
                # print(pixsum)
                if pixsum > _tmp:
                    _tmp = pixsum
                    control_point_y = i
                    test = True
            # if test:
            #     print('WHYYY')
            cv2.circle(image, (control_x,control_point_y), 5, 255, 3)

            cv2.line(  image, (control_x, 0), (control_x,255), (0,0,255), 2)
            cv2.line(  image, (0, control_y), (513,control_y), (0,0,255), 2)

            cv2.line(  image, (mouse_x, 0),   (mouse_x, 255),  (50,50,200), 2)
            cv2.line(  image, (0, mouse_y),   (513,mouse_y),   (50,50,200), 2)

            cv2.imshow("MainWindow",image)

            distance_error = control_y - control_point_y
            moving_average_vector = np.append(moving_average_vector, distance_error)
            # print("asdf",moving_average_vector.shape)
                # print("HAHAHAH")
            if len(moving_average_vector) > moving_average_size:
                moving_average_vector = moving_average_vector[1:]

            moving_average = int(np.sum(moving_average_vector)/len(moving_average_vector) )
            print(distance_error," ",moving_average)

            # to_send = bytes(str(distance_error)+","+str(moving_average),'utf-8')
            # udp_socket.sendto(to_send,("127.0.0.1",5005))
            
            # print("DISTAN CE ERROR: ", distance_error)
            
            # if cv2.waitKey(30) & 0xFF == ord('q'):
            #     break
            
    cv2.destroyAllWindows()

    sess.close()

    return


if __name__ == '__main__':
    """
    test code
    """
    # init args
    args = init_args()

    test_lanenet('data/jalanits/cam2_1.avi', 'model/tusimple4_3/bisenetv2_lanenet/tusimple_train_miou=0.7279.ckpt-896')