
<br/>
<div align="center">

<h3 align="center">Skeletonization Tool</h3>
<p align="center">


<br/>
<br/>
<a href="https://youtu.be/-0nsbsNzMa8">View Demo .</a>  
<a href="mailto:amoseley018@gmail.com?subject=Skeletonization%20Tool%20Bug">Report Bug .</a>

</p>
</div>

## About The Project

This tool allows users to generate skeletons from grayscale images by defining their own parameters, steps, and metadata calculations. Please look at the demo video linked above to learn how to use and modify the tool for your own project.

The project was created with Python and PyQt.

This was created for Dr. Jordan Dowell's biology lab at LSU.
## Getting Started

 
### Prerequisites

You must already have an environment set up to use this project. This is a requirement to install packages using pip. An easy way to set this up is through Anaconda Navigator.
### Installation

1. Clone the repo
   ```sh
   https://github.com/AaronMoseley/SkeletonizationTool.git
   ```
3. Install pip Packages (execute command inside Github repo directory)
   ```sh
   pip install requirements.txt
   ```

### Running the Program

To use the program, make sure you have Python and all the program dependencies installed, then run the following command in your shell/command prompt.

```sh
RunProgram.bat
```

Alternatively, if you need to debug the program, you can open this repo as a folder in VSCode and then run it using the "Main Application" configuration in the "Run and Debug" menu.
   
## Recent Updates

* You can now select lines and line clusters in the Skeleton Viewer and add comments about them on the right side of the screen. These comments are automatically saved in JSON files in the Calculations directory and can be viewed in future sessions.
* In addition to JSON files, CSV files are generated for each input image. A CSV file is generated for the entire image that contains information on the original image, the sample, timestamp, and file paths for the skeletons. CSVs are also generated for each skeleton type that provide the definition of points, line segments, clusters, and metadata. These CSV files are all placed in a directory specific to an individual input image.

## License

Distributed under the MIT License. See [MIT License](https://opensource.org/licenses/MIT) for more information.
## Contact

Aaron Moseley - amoseley018@gmail.com
