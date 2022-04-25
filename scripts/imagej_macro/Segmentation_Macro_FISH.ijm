#@ File (label = "Input directory", style = "directory") input
#@ File (label = "Output directory", style = "directory") output
#@ String (label = "File suffix", value = ".tiff") suffix

processFolder(input);

// function to scan folders/subfolders/files to find files with correct suffix
function processFolder(input) {
    list = getFileList(input);
    list = Array.sort(list);
    for (i = 0; i < list.length; i++) {
        if(File.isDirectory(input + File.separator + list[i]))
            processFolder(input + File.separator + list[i]);
        if(endsWith(list[i], suffix))
            processFile(input, output, list[i]);
    }
}


function processFile(input, output, image) {

    // open image using Bio-Formats
    run("Bio-Formats", "open=["+ input + File.separator + image +"] autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT");

    // get original image's title
    imageTitle = getTitle();

    // set threshold based on entire stack histogram
    setAutoThreshold("RenyiEntropy dark no-reset stack");

    // create & save a binary mask
    run("Make Binary", "method=RenyiEntropy background=Default create");
    save(output + File.separator + imageTitle + "-BinaryStack");    

    // Using 3D Objects Counter - calculate centroid positions and integrated intensity (i.e. integrated density) for all objects using the binary mask
    run("3D Objects Counter", "threshold=128 slice=40 min.=4 max.=19602000 exclude_objects_on_edges surfaces statistics summary");

    // save surface map
    selectWindow("Surface map of MASK_" + imageTitle);
    save(output + File.separator + imageTitle + "-SurfaceMap");

    // Create a results table as per instructions: X,Y,Z of centroid followed by integrated intensity
    selectWindow("Statistics for MASK_" + imageTitle);
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

    //saves results as a .csv file
    saveAs("Results", output + File.separator + imageTitle + "-Results.csv"); 

    // close all open windows and results tables
    run("Close All");
    close("Statistics for MASK_" + imageTitle);
    close(imageTitle + "-Results.csv");
}