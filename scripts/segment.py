import imagej
import scyjava as sj
import numpy as np
import tooled as t
import code

# initialize ImageJ
ij = imagej.init(mode='interactive')
print(f"ImageJ version: {ij.getVersion()}")
ij.ui().showUI()

# get resources
IJ = sj.jimport('ij.IJ')
ImagePlus = sj.jimport('ij.ImagePlus')

# get data
src_dataset = ij.io().open('nuclei/nuclei_data.tif')
ij.ui().show('original', src_dataset)

# subtract w/ ops
ops_dataset = src_dataset.copy()
img_arr = ops_dataset.getImgPlus().getImg()
img_sub = ij.op().math().subtract(img_arr, 310.0)
ij.ui().show('ops_sub', img_sub)

# subtract w/ imagej
imagej_dataset = src_dataset.copy()
imp = ij.convert().convert(imagej_dataset, ImagePlus)
IJ.run(imp, "Subtract...", "value=310 stack")
imp.getProcessor().resetMinAndMax()
imp.show()

# return REPL
code.interact(local=locals())