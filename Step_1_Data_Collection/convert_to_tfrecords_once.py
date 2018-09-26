import numpy as np
from skimage import io
from matplotlib import pyplot as plt
import linecache

import tensorflow as tf

NUM_OF_IMAGES = input("Number of images?\r\n")

def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def _float32_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))

tfrecords_filename = 'record.tfrecords'
tfWriter = tf.python_io.TFRecordWriter(tfrecords_filename)

for fileIndex in range(1, int(NUM_OF_IMAGES)+1):
    image = io.imread("./dataset/" + "%0*d" %(6, fileIndex) + ".jpg")
    
    # height, width, depth = image.shape
    imageString = image.tostring()

    direction = int(linecache.getline(r"./dataset/steer_log.txt", fileIndex))

    example = tf.train.Example(features=tf.train.Features(feature={
        'image': _bytes_feature(imageString),
        'label': _int64_feature(direction)
    }))

    print("Writing record " + "%0*d" %(6, fileIndex) + ".jpg " + "with label " + str(direction))
    tfWriter.write(example.SerializeToString())

tfWriter.close()
