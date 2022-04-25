import os
import imagej
import scyjava as sj
from typing import List

# initialize ImageJ
ij = imagej.init('sc.fiji:fiji', mode='interactive')
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


def segment():
    # get input and output path
    input_path = get_path('input')
    output_path = get_path('output')
    file_list = os.listdir(path=input_path)
    results_table_macro = """#@ String imageTitle
    selectWindow("Statistics for " + imageTitle);
    X = Table.getColumn("X");
    Y = Table.getColumn("Y");
    Z = Table.getColumn("Z");
    IntDen = Table.getColumn("IntDen");
    Table.create("3D-Segmentation-Results");
    Table.setColumn("X", X);
    Table.setColumn("Y", Y);
    Table.setColumn("Z", Z);
    Table.setColumn("IntDen", IntDen);
    selectWindow("3D-Segmentation-Results");
    """

    for i in range(len(file_list)):
        # arguments for the results_table_macro
        args = {
            'imageTitle': file_list[i]
            }

        # open image data
        dataset_src = ij.io().open(input_path + file_list[i])

        # apply renyiEntropy threshold and convert to ImagePlus for the
        # 3D objects counter plugin
        img_thres = ij.op().threshold().renyiEntropy(dataset_src)
        imp_thres = img_to_imageplus(img_thres)
        imp_thres.show()

        # the re-order the ImagePlus dimensions
        IJ.run("Re-order Hyperstack ...", "channels=[Slices (z)] slices=[Channels (c)] frames=[Frames (t)]")

        # get re-ordered ImagePlus, set the title and save output
        imp_thres = ij.WindowManager.getCurrentImage()
        imp_thres.setTitle(file_list[i])
        IJ.save(imp_thres, output_path + file_list[i] + "-BinaryStack.tif")

        # run the 3D Objects Counter plugin
        IJ.run(imp_thres, "3D Objects Counter", "threshold=128 slice=40 min.=4 max.=19602000 exclude_objects_on_edges surfaces statistics summary")

        # get surface map output and save
        imp_surf_map = ij.WindowManager.getImage(f"Surface map of MASK_{file_list[i]}")
        IJ.save(imp_surf_map, output_path + file_list[i] + "-SurfaceMap.tif")

        # run the ResultsTable macro and save
        ij.py.run_macro(results_table_macro, args)
        results_table = ij.ResultsTable.getResultsTable("3D-Segmentation-Results")
        results_table.saveAs(output_path + file_list[i] + "-Results.csv")
        IJ.run("Close All")

segment()