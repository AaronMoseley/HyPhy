
<br/>
<div align="center">

<h3 align="center">SkelPy</h3>
<p align="center">


<br/>
<br/>
<a href="https://youtu.be/fFXoH72r6VE">View Demo .</a>  
<a href="mailto:amoseley018@gmail.com?subject=Skeletonization%20Tool%20Bug">Report Bug .</a>

</p>
</div>

## About The Project

This is a free, open-source, modular tool meant to help biology researchers create skeletons of structures, like fungi, from images. This is accomplished through modular pipelines with individual steps that each transform the image in some way. After a pipeline is complete, the skeleton is saved as an image, then vectorized into a list of lines and points. Metadata is also calculated about the skeleton to give you more information about it. The completed skeletons and their metadata can be viewed and any pipelines modified through an intuitive GUI interface. As discussed later in the documentation, this tool should also be easy to modify and add content to if you have experience with Python.

This project was created for Dr. Jordan Dowell's biology lab at LSU.

By default, two example skeletonization pipelines with steps and parameters are provided. These worked with example data but are intended as a starting point for users to make their own. You can modify these pipelines, create your own, and add your own custom steps with Python. You can also add your own metadata and comparison functions that will appear in the program. Please refer to the demo video, the ["Adding Your Own Content"](#adding-your-own-content) section, or the documentation in the directory source/UserContent/ for more information on how to do this.

The project was created with Python and PyQt.

## Getting Started

If you use Windows or Mac, navigate to the release section of this repo and download your corresponding version. This is the easiest way to run SkelPy as it doesn't require you to download the code or manually install any packages. If you would like to download the code or run SkelPy more manually, continue with the instructions below. Otherwise, you can skip them.
 
### Prerequisites

You must already have a Python environment set up to use this project. This is a requirement to install packages using pip. An easy way to set this up is through [Anaconda Navigator](https://www.anaconda.com/products/navigator).
### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/AaronMoseley/SkelPy.git
   ```
3. Install pip Packages (execute command inside Github repo directory)
   ```sh
   pip install -r requirements.txt
   ```

### Running the Program

To use the program from the source code, make sure you have Python and all the program dependencies installed, then run the following command in your shell/command prompt while inside the SkelPy directory.

```sh
RunProgram.bat
```

Alternatively, if you need to debug the program, you can open this repo as a folder in VSCode and then run it using the "Main Application" configuration in the "Run and Debug" menu.



## How to Use

Below is shown a basic flowchart for using SkelPy with the two provided skeletonization pipelines as an example. The user provides SkelPy with a series of images (anything that can be opened by the PIL package in Python), it uses a series of parameters and the skeletonization pipelines to detect features, and then calculates metadata and a vectorized version of the skeletons and stores them in .csv and .json files.

![SkelPy Use Flowchart](./SkelPyExample.png)

### Main Window

In the main window, you can look at different images, edit pipelines, edit parameters, and navigate to other windows. Upon starting up the program, use the "Input Directory" and "Output Directory" textboxes to set the directory where your original images are located and where you would like the output images and data to be placed.
Click "Generate All Skeletons" once these are set and wait for it to complete.

If your files are of the format {main file name}_{numeric index}.{extension}, the numeric index will be treated as a timestamp and everything preceding that will be treated as a sample name. Otherwise, your files will each be treated as their own sample with a timestamp of 0.
You can select which sample to view using the dropdown box and the timestamp with the arrows below the input image.

Below the image selection, you can see information about the skeletons and their pipelines. Each pipeline has its own section with its own steps, parameters, and results.

- Click on a skeletonized image to enter the [skeleton viewer](#skeleton-viewer)
- Click ["Preview Steps"](#preview-steps) to view the effect of each step on the image in the preview viewer
- Click "Toggle Overlay On Original" to view the skeleton overlayed onto the input image
- Click ["Compare to External Skeleton"](#external-comparison) to enter the comparison viewer

In this section, you can edit the names of any skeletonization pipeline with the header textbox. You can also delete a pipeline with the X button beside the name. To replace a step with another, use the dropdown with the step name. Some steps have parameters that you can modify with sliders. This is necessary as not all parameter values will work with all images. If you are having trouble getting a pipeline to generate usable output for an image, try modifying the values in the sliders and click "Preview Steps" for a more detailed view.

Clicking "Add Step" will add a new step to that pipeline. Each pipeline ends with the skeletonization step by default and that cannot be changed in the GUI. All changes to pipelines, steps, and parameters are saved automatically and will persist if you close the application.

If you would like to create a skeletonization pipeline from scratch, click "Add Skeletonization Pipeline" at the bottom and it will create a new one for you. This pipeline will only include the skeletonization step, so you would need to provide everything else.

### File Outputs

After your set of skeletonization pipelines has completed, SkelPy will generate a skeletonized image of each input file, per each pipeline. 
For each input image, it will also generate a JSON file with any relevant data for that image.
This includes any metadata calculated about the image for each pipeline and the vectorized versions of the skeletons, represented as points (tuples of XY coordinates in the range 0-1), lines (lists of indices into the list of points), and connected clusters of lines (lists of indices into the list of lines).
SkelPy also generates a set of CSV files representing the same information for each input image. These are placed in a separate directory for each input file. The CSV files are never referenced in the program and are provided to the user solely for convenience. 

Below is the directory tree of example input and output files for a single input image. This example uses the two default skeletonizations pipelines that are included in SkelPy: Sclerotia Primordia and Fungal Network. The Images directory is used as the input directory, while the Skeletons directory is the output.

```
├───Images  
│       ExampleImage_01.tif  
│  
├───Skeletons  
│   │   ExampleImage_01_network.tif  
│   │   ExampleImage_01_sclerotiaPrimordia.tif  
│   │  
│   └───Calculations  
│       │   ExampleImage_01_calculations.json  
│       │  
│       ├───ExampleImage_01_skeleton_csvs  
│       │       fileInfo.csv  
│       │       network_clusters.csv  
│       │       network_lines.csv  
│       │       network_metadata.csv  
│       │       network_points.csv  
│       │       sclerotiaPrimordia_clusters.csv  
│       │       sclerotiaPrimordia_lines.csv  
│       │       sclerotiaPrimordia_metadata.csv  
│       │       sclerotiaPrimordia_points.csv  
```

### Skeleton Viewer

In the skeleton viewer, you can browse the skeletonized version of your image. Clicking on a polyline will select it in purple and the cluster it belongs to in red. On the right side of the screen, you can see any metadata calculated about the skeleton, some of which is specific to the selected line and line cluster. At the top, you can view the length of the selected line and the sum of the lengths of all the lines in the cluster.

Below the metadata, you can add comments referring to a specific line or its cluster. These are saved automatically and will persist if you close the application.

Above the metadata, you can set the units for the image and its width and height. Any relevant metadata will scale with edits you make.

### Preview Steps

In the preview window, you can view how each step in a pipeline affects the input image. On the right side of the screen, you can see the original image at the top along with the current step name and any of its parameters. Below is the current version of the image after the step you are currently viewing finishes processing.

On the left, you can view the list of steps for the current pipeline and their parameters. Editing a parameter value will not automatically regenerate the current image on the right side, so click "Refresh Step" if you want to view the effect of your changes. Changes to parameter values are saved and carry over into the main window, or if you close and reopen the application.

### External Comparison

If you would like to compare a generated skeleton to an externally-created one, you can do this in the comparison viewer. On the far left is the original image, in the middle is the skeleton generated by the program, and on the right is the skeleton you can upload. This begins as black but will update if you click "Upload File" and select the skeleton image.

An uploaded skeleton image is converted to grayscale, normalized, and skeletonized automatically. 
For best results, ensure that the image you provide is already skeletonized (1-pixel wide lines) and is binary (white and black only, nothing in between).
By clicking "Toggle Generated Skeleton Overlay", you can view the skeleton generated by the program drawn overtop the one you have uploaded. 
To the right of the uploaded skeleton is any data used for comparing the two skeletons.
By default, this includes the average and maximum distance from a point on one skeleton to the closest point on the other.

Using this window, you can also compare two skeletons that were both generated by this program. Simply select a skeleton image generated by this program when clicking "Upload File".

### Adding Your Own Content

As mentioned above, SkelPy is intended to be a platform where you can easily add content specific to your own use-case. This includes custom metadata functions, comparison functions, and steps for skeletonization pipelines. 
Most, if not all, of the modifications you will want to perform are located in the source/UserContent/ directory. Please use the functions already located in those files as example to inform how you write your own code.

You can add your own pipeline steps in source/UserContent/SkeletonPipelineSteps.py, your own comparison functions in source/UserContent/ComparisonFunctions.py, and your own metadata functions in source/UserContent/MetricFunctions.py. 

Each function type has its own specific format, both with the parameters it must take and the output it must return. Please reference the functions that are already present, as well as example functions for each format in the three files mentioned above.
You must also make your function visible to the program. In source/UserContent/FunctionMaps.py, you can add a new function to PIPELINE_STEP_FUNCTION_MAP, METADATA_FUNCTION_MAP, or COMPARISON_FUNCTION_MAP. 
Example comments are written in each map to show how to correctly perform this with the example functions in the three files mentioned above. 
For metadata and comparison functions, the key in the map related to this function will be converted from camelCase to capitalized words with spaces when displaying its name. Please keep this in mind.

When adding steps for a pipeline, you must also perform an additional step. First, add the step to the file configs/PipelineSteps.json. 
You must provide a key that will be used as the step's display name, a list of parameters that it uses, and the key to its function. This key must be the key related to the step's function in PIPELINE_STEP_FUNCTION_MAP.
If your step requires a new user-modifiable parameter, you can add it as a new entry in configs/StepParameters.json. You must provide the same key as in the parameters list for the step in PipelineSteps.json, a display name for the parameter, the number of decimals to use, the minimum value for the slider, the maximum value for the slider, and its default value.

All other parts of the code, including the GUI, are fully modifiable, but they are not intended for that purpose and thus are not documented as thoroughly.

## License

Distributed under the MIT License. See [MIT License](https://opensource.org/licenses/MIT) for more information.
## Contact

Aaron Moseley - amoseley018@gmail.com
