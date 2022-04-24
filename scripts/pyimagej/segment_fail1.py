from locale import THOUSEP
import imagej
import scyjava as sj
import numpy as np
import code

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


def fill_holes_stack(image):
    fill_results = []
    for i in range(int(image.shape[2])):
        input_slice = image[:, :, i]
        fill_slice = ij.op().morphology().fillHoles(input_slice)
        fill_slice = Views.addDimension(fill_slice, 1, 1)
        fill_results.append(fill_slice)

    fill_stack = Views.concatenate(2, fill_results)
    return fill_stack


def get_kernel(key: str) -> np.ndarray:
    kernels = {
        "emboss" : np.array([
            [-2, -1, 0],
            [-1, 1, 1], 
            [0, 1, 2]
        ]),
        "sharp" : np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]]),
        "ridge" : np.array([
            [-1, -1, -1],
            [-1, 8, -1],
            [-1, -1, -1]]),
        "imagej" : np.array([
            [-1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1],
            [-1, -1, 24, -1, -1], 
            [-1, -1, -1, -1, -1],
            [-1, -1, -1, -1, -1]]),
        "emboss1" : np.array([
            [0, 0, 0, 0, 0],
            [0, -2, -1, 0, 0],
            [0, -1, 1, 1, 0],
            [0, 0, 1, 2, 0],
            [0, 0, 0, 0, 0]
        ]),
        "emboss2" : np.array([
            [0, 0, 0, 0, 0],
            [0, 2, 1, 0, 0],
            [0, 1, -1, -1, 0], 
            [0, 0, -1, -2, 0],
            [0, 0, 0, 0, 0]
        ])
    }

    if key in kernels:
        return kernels[key]
    else:
        raise ValueError(f"Kernel \"{key}\" not found.")

 
# initialize ImageJ
ij = imagej.init('sc.fiji:fiji', mode='interactive')
print(f"ImageJ version: {ij.getVersion()}")

# imagej resources
CreateNamespace = sj.jimport('net.imagej.ops.create.CreateNamespace')
HyperSphereShape = sj.jimport('net.imglib2.algorithm.neighborhood.HyperSphereShape')
Dataset = sj.jimport('net.imagej.Dataset')
Views = sj.jimport('net.imglib2.view.Views')

# start UI
ij.ui().showUI()
dataset = ij.io().open('/home/edward/Documents/workspaces/scratch/3d_seg_challange/nuclei/nuclei_3.tif')
dataset = ij.op().convert().int32(dataset)
dataset_blur = ij.op().filter().gauss(dataset, 5.0)
img_sub = (dataset - dataset_blur)

# get kernels
emboss1 = get_kernel('emboss1')
emboss2 = get_kernel('emboss2')
sharp = get_kernel('sharp')

# convolve stack with a kernel
img_sub_blur = ij.op().filter().gauss(img_sub, 1.5)
img_conv = convolve_stack(sharp, img_sub_blur)
img_conv = convolve_stack(emboss1, img_conv)
img_conv = convolve_stack(emboss2, img_conv)

# add back convolved image to input for enhanced edges
img_enhanced = (dataset * img_conv)

# median filter enhanced image
radius = HyperSphereShape(2) # pixel radius of 2
img_enhanced_median = ij.dataset().create(img_enhanced)
ij.op().filter().median(img_enhanced_median, img_enhanced, radius)

# threshold image
img_thres = ij.op().threshold().minError(img_enhanced_median)

# fill holes
img_fill = fill_holes_stack(img_thres)

# display images
ij.ui().show("input", dataset)
ij.ui().show("gaussian_subtracted" ,img_sub)
ij.ui().show("convolved", img_conv)
ij.ui().show("enhanced median", img_enhanced_median)
ij.ui().show("threshold", img_thres)
ij.ui().show("segmentation", img_fill)

code.interact(local=locals())