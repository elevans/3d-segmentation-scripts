import imagej
import scyjava as sj
import code # TODO: remove after debugging

# initialize ImageJ
ij = imagej.init(mode='interactive')
print(f"ImageJ version: {ij.getVersion()}")

# get additional ImageJ2 resources
HyperSphereShape = sj.jimport('net.imglib2.algorithm.neighborhood.HyperSphereShape')

# load data
path = '/home/edward/Documents/workspaces/scratch/3d_seg_challange/nuclei/nuclei_3.tif'
dataset_src = ij.io().open(path)
dataset_mean = dataset_src.copy() # create a working copy...images are linked

# mean filter the data
mean_radius = HyperSphereShape(5)
dataset_mean_out = ij.dataset().create(dataset_mean) # create an output dataset
ij.op().filter().mean(dataset_mean_out, dataset_mean, mean_radius)

# multiply mean image with input (returns PlanarImg)
img_mul = dataset_src * dataset_mean_out

# threshold image
img_thres = ij.op().threshold().moments(img_mul)

# show images
ij.ui().show('input', dataset_src)
ij.ui().show('mean', dataset_mean_out)
ij.ui().show('mul', img_mul)
ij.ui().show('thres', img_thres)

# TODO: remove after debugging
code.interact(local=locals())