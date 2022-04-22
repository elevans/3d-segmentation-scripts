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
    
    // duplicate original image
    run("Duplicate...", "title=duplicate duplicate");
	
	// process duplicated image: mean filter, radius 5
	run("Mean...", "radius=5 stack");
	
	// multiply original and mean-filtered image
	imageCalculator("Multiply create 32-bit stack", imageTitle, "duplicate");
	selectWindow("Result of " + imageTitle);
	
	// convolve resulting image, apply gaussian blur, generate binary mask
	run("Convolve...", "text1=[0 0 0 0 0\n0 0 -1 0 0\n0 -1 5 -1 0\n0 0 -1 0 0\n0 0 0 0 0\n] normalize stack");
	run("Gaussian Blur...", "sigma=1 stack");
	//run("Brightness/Contrast...");
	run("Enhance Contrast", "saturated=0.35");
	setAutoThreshold("Default dark");
	//run("Threshold...");
	setAutoThreshold("Default dark stack");
	run("Make Binary", "method=Default background=Dark black create");
	setOption("BlackBackground", true);
	run("Erode", "stack");

	// use 3D watershed to separate touching nuclei
    run("Distance Transform Watershed 3D", "distances=[Borgefors (3,4,5)] output=[32 bits] normalize dynamic=2 connectivity=6");
	rename("watershed-image");
	selectWindow("watershed-image");

	// binarize the labeled image
	setAutoThreshold("Default dark stack");
	setThreshold(0.01, 255);
	setOption("BlackBackground", true);
	run("Convert to Mask", "method=Default background=Dark black create");
	run("Erode", "stack");
	// save binary mask
	save(output + File.separator + imageTitle + "-BinaryStack");    

	// Using 3D Objects Counter - calculate centroid positions, integrated intensity (i.e. integrated density), and volume for all objects using the binary mask
	selectWindow("MASK_watershed-image");
	run("3D Objects Counter", "threshold=128 slice=50 min.=10 max.=6656400 exclude_objects_on_edges surfaces statistics summary");
 	
 	// save surface map
    selectWindow("Surface map of MASK_watershed-image");
    save(output + File.separator + imageTitle + "-SurfaceMap");

    // Create a results table as per instructions: X,Y,Z of centroid followed by integrated intensity
    selectWindow("Statistics for MASK_watershed-image");
    X = Table.getColumn("X");
    Y = Table.getColumn("Y");
    Z = Table.getColumn("Z");
    IntDen = Table.getColumn("IntDen"); 
    Volume = Table.getColumn("Volume (micron^3)");   
		
    Table.create("3D-Segmentation-Results");
    Table.setColumn("X", X);
    Table.setColumn("Y", Y);
    Table.setColumn("Z", Z);
    Table.setColumn("IntDen", IntDen);
    Table.setColumn("Volume (micron^3)", Volume);
    selectWindow("3D-Segmentation-Results");

    //saves results as a .csv file
    saveAs("Results", output + File.separator + imageTitle + "-Results.csv"); 

    // close all open windows and results tables
    run("Close All");
    close("Statistics for MASK_watershed-image");
    close(imageTitle + "-Results.csv");
}