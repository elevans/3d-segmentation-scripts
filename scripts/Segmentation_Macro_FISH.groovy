#@ DatasetIOService ds
#@ UIService ui
#@ File (label = "Input directory", style = "directory") srcFile
#@ File (label = "Output directory", style = "directory") dstFile
#@ String (label = "File extension", value = ".tif") ext
#@ String (label = "File name contains", value = "") containString

import ij.ij

// load the data
dataset = ds.open(file.getAbsolutePath())

// display the dataset
ui.show(dataset)