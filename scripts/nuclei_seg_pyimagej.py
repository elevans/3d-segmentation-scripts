import imagej
import scyjava as sj
import os
import code # TODO: remove after debugging
from typing import List

# initialize ImageJ
ij = imagej.init(mode='interactive')
print(f"ImageJ version: {ij.getVersion()}")

# get additional ImageJ2 resources
HyperSphereShape = sj.jimport('net.imglib2.algorithm.neighborhood.HyperSphereShape')

def get_path():
    return input("Enter directory:")

def segment():
    path = get_path()
    file_list = os.listdir(path=path)
    mean_radius = HyperSphereShape(5)

    for i in range(len(file_list)):
        dataset_src = ij.io().open(path + file_list[i])
        dataset_src = ij.op().convert().int32(dataset_src) # convert to 32-bit
        dataset_mean = dataset_src.copy()
        dataset_mean_out = ij.dataset().create(dataset_mean) # create an output dataset
        ij.op().filter().mean(dataset_mean_out, dataset_mean, mean_radius)
        img_mul = dataset_src * dataset_mean_out # multiply mean image with input (returns PlanarImg)
        img_thres = ij.op().threshold().moments(img_mul)
        ij.ui().show(f'input_{file_list[i]}', dataset_src)
        #ij.ui().show(f'mean_{file_list[i]}', dataset_mean_out)
        #ij.ui().show(f'mul_{file_list[i]}', img_mul)
        ij.ui().show(f'thres_{file_list[i]}', img_thres)

segment()

# TODO: remove after debugging
code.interact(local=locals())