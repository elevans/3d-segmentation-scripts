import imagej
import scyjava as sj
import numpy as np
import os
import code # TODO: remove after debugging
from typing import List

# initialize ImageJ
ij = imagej.init("/home/edward/Documents/software/fiji/", mode='interactive')
print(f"ImageJ version: {ij.getVersion()}")

# get additional ImageJ2 resources
IJ = sj.jimport('ij.IJ')
ImagePlus = sj.jimport('ij.ImagePlus')
HyperSphereShape = sj.jimport('net.imglib2.algorithm.neighborhood.HyperSphereShape')
Views = sj.jimport('net.imglib2.view.Views')

def get_path():
    #return input("Enter directory:")
    return "/home/edward/Documents/workspaces/scratch/3d_seg_challange/nuclei/"


def img_to_imageplus(img):
    return ij.convert().convert(ij.dataset().create(img), ImagePlus)

def convolve_stack(kernel: np.ndarray, image):
    # convolve each slice, append list, concatenate slices into new stack
    conv_results = []
    for i in range(int(image.shape[2])):
        input_slice = image[:, :, i]
        conv_slice = ij.op().filter().convolve(input_slice, ij.py.to_java(kernel))
        conv_slice = Views.addDimension(conv_slice, 1, 1)
        conv_results.append(conv_slice)

    conv_stack = Views.concatenate(2, conv_results)
    return ij.op().convert().int32(conv_stack) # convert float back to int32 to match input images


def segment():
    path = get_path()
    file_list = os.listdir(path=path)
    mean_radius = HyperSphereShape(5)
    erode_shape = HyperSphereShape(4)
    sharpen_kernel = np.array([
            [0, 0, 0, 0, 0],
            [0, 0, -1, 0, 0],
            [0, -1, 5, -1, 0],
            [0, 0, -1, 0, 0],
            [0, 0, 0, 0, 0]])

    for i in range(len(file_list)):
        dataset_src = ij.io().open(path + file_list[i])
        dataset_src = ij.op().convert().int32(dataset_src) # convert to 32-bit
        dataset_mean = dataset_src.copy()
        dataset_mean_out = ij.dataset().create(dataset_mean) # create an output dataset
        ij.op().filter().mean(dataset_mean_out, dataset_mean, mean_radius)
        img_mul = dataset_src * dataset_mean_out # multiply mean image with input (returns PlanarImg)
        img_conv = convolve_stack(sharpen_kernel, img_mul)
        img_blur = ij.op().filter().gauss(img_conv, 1.0)
        img_thres = ij.op().threshold().ij1(img_blur)
        img_erode = ij.op().morphology().erode(img_thres, erode_shape)
        # Distance Transform Watershed 3D requires original ImageJ ImagePlus type
        # Original ImageJ going forward
        imp_erode = img_to_imageplus(img_erode)
        imp_erode.show()
        IJ.run("Re-order Hyperstack ...", "channels=[Frames (t)] slices=[Slices (z)] frames=[Channels (c)]")
        IJ.run("Distance Transform Watershed 3D", "distances=[Borgefors (3,4,5)] output=[32 bits] normalize dynamic=2 connectivity=6")
        ij.ui().showUI()
        breakpoint()

segment()

# TODO: remove after debugging
code.interact(local=locals())