import os
import imagej
import scyjava as sj
import numpy as np
from typing import List

# initialize ImageJ
ij = imagej.init("sc.fiji:fiji", mode='interactive')
print(f"ImageJ version: {ij.getVersion()}")

# get additional ImageJ2 resources
IJ = sj.jimport('ij.IJ')
ImagePlus = sj.jimport('ij.ImagePlus')
Dataset = sj.jimport('net.imagej.Dataset')
HyperSphereShape = sj.jimport('net.imglib2.algorithm.neighborhood.HyperSphereShape')
Views = sj.jimport('net.imglib2.view.Views')

def get_path(direction: str):
    if direction == "input":
        return input("Enter input directory:")
    if direction == "output":
        return input("Enter output directory:")


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
    # get input and output path
    input_path = get_path('input')
    output_path = get_path('output')
    file_list = os.listdir(path=input_path)

    # setup additonal imglib2 resources
    mean_radius = HyperSphereShape(5)
    erode_shape = HyperSphereShape(4)
    sharpen_kernel = np.array([
            [0, 0, 0, 0, 0],
            [0, 0, -1, 0, 0],
            [0, -1, 5, -1, 0],
            [0, 0, -1, 0, 0],
            [0, 0, 0, 0, 0]])
    results_table_macro = """
    selectWindow("Statistics for MASK_dist-watershed");
    X = Table.getColumn("X");
    Y = Table.getColumn("Y");
    Z = Table.getColumn("Z");
    IntDen = Table.getColumn("IntDen");
    Volume = Table.getColumn("Volume (pixel^3)");
    Table.create("3D-Segmentation-Results");
    Table.setColumn("X", X);
    Table.setColumn("Y", Y);
    Table.setColumn("Z", Z);
    Table.setColumn("IntDen", IntDen);
    Table.setColumn("Volume (pixel^3)", Volume);
    """

    for i in range(len(file_list)):
        # open image data and convert to 32-bit
        dataset_src = ij.io().open(input_path + file_list[i])
        dataset_src = ij.op().convert().int32(dataset_src)

        # make a copy to unlink from original object and create output dataset
        dataset_mean = dataset_src.copy() 
        dataset_mean_out = ij.dataset().create(dataset_mean)

        # apply mean filter
        ij.op().filter().mean(dataset_mean_out, dataset_mean, mean_radius)

        # multiply mean image with input
        img_mul = dataset_src * dataset_mean_out

        # convolve stack with 5x5 sharpen kernel, blur, threshold (default) and erode
        img_conv = convolve_stack(sharpen_kernel, img_mul)
        img_blur = ij.op().filter().gauss(img_conv, 1.0)
        img_thres = ij.op().threshold().ij1(img_blur)
        img_erode = ij.op().morphology().erode(img_thres, erode_shape)

        # Distance Transform Watershed 3D requires original ImageJ ImagePlus type
        # convert data to ImagePlus
        imp_erode = img_to_imageplus(img_erode)
        imp_erode.show()

        # re-order the ImagePlus dimensions
        IJ.run("Re-order Hyperstack ...", "channels=[Frames (t)] slices=[Slices (z)] frames=[Channels (c)]")
        IJ.run("Distance Transform Watershed 3D", "distances=[Borgefors (3,4,5)] output=[32 bits] normalize dynamic=2 connectivity=6")
        
        # get re-orded ImagePlus, threshold and create mask
        imp_watershed = ij.WindowManager.getImage("dist-watershed")
        IJ.setAutoThreshold(imp_watershed, "Default dark stack")
        IJ.setThreshold(imp_watershed, 0.01, 255)
        IJ.run("Convert to Mask", "method=Default background=Dark black create")

        # get ImagePlus mask and erode
        imp_mask = ij.WindowManager.getImage("MASK_dist-watershed")
        IJ.run(imp_mask, "Options...", "iterations=1 count=1 black edm=8-bit do=Erode stack")
        
        # save binary mask
        IJ.save(imp_mask, output_path + file_list[i] + "-BinaryStack.tif")
        IJ.run(imp_mask, "3D Objects Counter", "threshold=128 slice=50 min.=10 max.=6656400 exclude_objects_on_edges surfaces statistics summary")
        
        # get surface map output and save
        imp_surf_map = ij.WindowManager.getImage("Surface map of MASK_dist-watershed")
        IJ.save(imp_surf_map, output_path + file_list[i] + "-SurfaceMap.tif")
        
        # run the ResultsTable macro and save
        ij.py.run_macro(results_table_macro)
        results_table = ij.ResultsTable.getResultsTable("3D-Segmentation-Results")
        results_table.saveAs(output_path + file_list[i] + "-Results.csv")
        IJ.run("Close All")


segment()