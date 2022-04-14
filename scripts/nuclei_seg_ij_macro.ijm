run("Subtract...", "value=310 stack");
setAutoThreshold("RenyiEntropy dark");
setOption("BlackBackground", false);
run("Convert to Mask", "method=RenyiEntropy background=Dark calculate create");