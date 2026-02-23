import numpy as np
from scipy.ndimage import label
from skimage.morphology import skeletonize
from scipy.ndimage import gaussian_filter, uniform_filter
from skimage.filters import threshold_otsu, sobel
from skimage import feature
from collections import deque

"""
The function below is an example that can be used in a skeleton pipeline
Functions also need to be defined in configs/PipelineSteps.json with a key string and list of any necessary parameters
For a full list of all possible parameters, look at configs/StepParameters.json.
If you are creating a new step and require additional parameters, add a new entry in StepParameters.json in the same format
Once the function is complete, you must add the function (using the key string) to the STEP_FUNCTION_MAP in source/UserContent/FunctionMaps.py as shown there
"""

def ExamplePipelineFunction(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    This is an example function for performing a step in a skeleton pipeline. This should perform an operation on the input image and return a modified version.

    All pipeline functions should have the same structure as this.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function.
        parameters (dict): The parameters related to this step in the pipeline. Each step has its own set of parameters that can be set with sliders in the main window. As mentioned in the documentation above, the parameters required for each step are set in configs/PipelineSteps.json and the full list of possible parameters is established in configs/StepParameters.json. You can reference any related parameters to a step in its function with the keys in StepParameters.json.
        
    Returns:
        np.ndarray: The modified version of the image. If this is the last step in the skeletonization pipeline, it should return an array compatible with skimage.morphology.skeletonize.
        Specifically, the shape of the image should be (H, W) and all non-zero values will be treated as a white pixel when performing skeletonization.
    """

    #perform some processing on imageArray

    return imageArray

def ConvertToGrayScale(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    Converts the image to grayscale by taking the mean of all its channels if the image is not already grayscale.
    The input array should be of the shape (H, W, C) or (H, W).

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function.
        parameters (dict): This will be empty.
        
    Returns:
        np.ndarray: The grayscale image in the shape (H, W).
    """

    if imageArray.ndim > 2:
        if imageArray.shape[-1] == 4:
            imageArray = imageArray[:, :, :3]

        imageArray = np.mean(imageArray, axis=-1)

    return imageArray

def NormalizeImage(imageArray:np.ndarray, parameters) -> np.ndarray:
    """
    Normalizes the image by subtracting its minimum value and dividing by the maximum of the modified array.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function.
        parameters (dict): This will be empty.
        
    Returns:
        np.ndarray: The normalized image.
    """
    
    maxValue = np.max(imageArray)
    minValue = np.min(imageArray)
    imageArray -= minValue
    maxValue -= minValue
    imageArray /= maxValue
    return imageArray

def RadialThreshold(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    Thresholds the image based on a radial array.
    Given the parameters "centerThreshold" and "edgeThreshold", a circle is drawn on an array that fades from one value at the center to another at the edge.
    This is then used as a per-pixel threshold.
    This is useful when the input images are darker or lighter at the center and require a different threshold value than objects at the edge.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a grayscale image of shape (H, W).
        parameters (dict): Contains "centerThreshold" and "edgeThreshold" which are used as the values in the radial mask at the center and edge respectively.
        
    Returns:
        np.ndarray: The thresholded image array.
    """
    
    thresholds = CreateRadialMask(imageArray.shape[1], imageArray.shape[0], parameters["centerThreshold"], parameters["edgeThreshold"])

    imageArray = np.asarray(imageArray < thresholds, dtype=np.float64)

    return imageArray

def CallRemoveSmallWhiteIslands(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    A wrapper function that removes any "white islands", or groups of ones, in the binary image that are too small.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a binary image of shape (H, W).
        parameters (dict): Contains "minWhiteIslandSize" which is the number of pixels that must be in each group of ones for the group to be kept. All smaller groups will be set to 0.
        
    Returns:
        np.ndarray: The image array with reduced islands.
    """

    imageArray = RemoveSmallWhiteIslands(imageArray, parameters["minWhiteIslandSize"])

    return imageArray

def CallRemoveStructurallyNoisyIslands(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    A wrapper function that removes groups of ones that are too noisy. Noise is measured as the average number of black neighbors white pixels. Higher counts mean that the group is noisier.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a binary image of shape (H, W).
        parameters (dict): Contains "noiseTolerance" which is the maximum allowed number of black neighbors, on average, for each group of white pixels. All groups with a higher value will be removed. Setting this to 8 will remove all white pixels and any higher values will cause issues.
        
    Returns:
        np.ndarray: The image array with reduced islands.
    """
    
    imageArray = RemoveStructurallyNoisyIslands(imageArray, maxAverageBlackNeighbors=parameters["noiseTolerance"])
    return imageArray

def CallSmoothBinaryArray(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    A wrapper function that performs Gaussian Blur (https://en.wikipedia.org/wiki/Gaussian_blur) on the binary image. This smooths out the image and can make connections between lines that would become disconnected otherwise.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a binary image of shape (H, W).
        parameters (dict): Contains "gaussianBlurSigma" which is given to skimage.ndimage.gaussian_filter. Please refer to their documentation for further explanation.
        
    Returns:
        np.ndarray: The image array with reduced islands.
    """
    
    imageArray = GaussianBlur(imageArray, sigma=parameters["gaussianBlurSigma"])
    return imageArray

def CallSkeletonize(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    A wrapper function that skeletonizes the input image using the Zhang-Suen algorithm (https://rosettacode.org/wiki/Zhang-Suen_thinning_algorithm). 
    This calls the function skimage.morphology.skeletonize. Please refer to their documentation for further information.
    This is automatically called at the end of every pipeline.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a binary image of shape (H, W).
        parameters (dict): This will be empty.
        
    Returns:
        np.ndarray: The skeletonized binary image.
    """
    
    imageArray = skeletonize(imageArray)
    return imageArray

def SegmentAreasAroundCenter(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    Perform BFS on a 2D numpy array starting from the center.
    Only visits cells with values strictly less than threshold.
    
    Parameters:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a binary image of shape (H, W).
        parameters (dict): Contains "threshold" which is used as the threshold used when visiting neigjbor pixels
        
    Returns:
        np.ndarray: Binary array of same shape with 1 where visited, 0 otherwise
    """

    if imageArray.ndim != 2:
        raise ValueError("Input array must be 2D")
    
    rows, cols = imageArray.shape
    visited = np.zeros((rows, cols), dtype=np.uint8)
    
    # Find center index
    start_row = rows // 2
    start_col = cols // 2
    
    # If center does not satisfy threshold, return empty mask
    if imageArray[start_row, start_col] >= parameters["searchThreshold"]:
        return visited
    
    # BFS setup
    queue = deque()
    queue.append((start_row, start_col))
    visited[start_row, start_col] = 1
    
    # 4-directional neighbors (up, down, left, right)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    while queue:
        r, c = queue.popleft()
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            
            # Check bounds
            if 0 <= nr < rows and 0 <= nc < cols:
                # Check threshold and not yet visited
                if visited[nr, nc] == 0 and imageArray[nr, nc] < parameters["searchThreshold"]:
                    visited[nr, nc] = 1
                    queue.append((nr, nc))
    
    return visited

def RGBToHSV(imageArray: np.ndarray, parameters:dict) -> np.ndarray:
    """
    Convert an RGB image (H, W, 3) to HSV.
    
    Parameters:
        imageArray (np.ndarray): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a binary image of shape (H, W).
        parameters (dict): This will be empty
    
    Returns:
        np.ndarray: Array representing HSV image
    """

    if imageArray.ndim != 3 or imageArray.shape[2] != 3:
        raise ValueError("Input must be an RGB image with shape (H, W, 3)")
    
    img = imageArray.astype(np.float64)
    
    # Normalize if uint8
    if img.max() > 1.0:
        img /= 255.0
    
    r = img[..., 0]
    g = img[..., 1]
    b = img[..., 2]
    
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin
    
    # Initialize HSV channels
    h = np.zeros_like(cmax)
    s = np.zeros_like(cmax)
    v = cmax
    
    # Saturation
    s[cmax != 0] = delta[cmax != 0] / cmax[cmax != 0]
    
    # Hue calculation
    mask = delta != 0
    
    # Red is max
    idx = (cmax == r) & mask
    h[idx] = ((g[idx] - b[idx]) / delta[idx]) % 6
    
    # Green is max
    idx = (cmax == g) & mask
    h[idx] = ((b[idx] - r[idx]) / delta[idx]) + 2
    
    # Blue is max
    idx = (cmax == b) & mask
    h[idx] = ((r[idx] - g[idx]) / delta[idx]) + 4
    
    h /= 6.0  # Normalize to [0, 1]
    
    hsv = np.stack((h, s, v), axis=-1)
    return hsv

def ReduceToSingleChannel(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    Reduces a multi-channel image into a single channel. The channel dimension is assumed to be the third dimensions
    
    Parameters:
        imageArray (np.ndarray): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a binary image of shape (H, W).
        parameters (dict): Contains "singleChannelIndex" which is the index of the channel to keep
    
    Returns:
        np.ndarray: Array representing the single channel image
    """

    channelIndex = int(parameters["singleChannelIndex"])

    result = imageArray[:, :, channelIndex]

    return result

def BinaryEdgeDetection(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    Finds edges in a binary image, keeps all pixels with black neighbors
    
    Parameters:
        imageArray (np.ndarray): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a binary image of shape (H, W).
        parameters (dict): This will be empty
    
    Returns:
        np.ndarray: Array representing the edge-detected image
    """
    
    # Pad with 1s so borders are handled correctly
    padded = np.pad(imageArray, pad_width=1, mode='constant', constant_values=1)

    # Collect 8 neighbors
    neighbors = [
        padded[:-2, :-2], padded[:-2, 1:-1], padded[:-2, 2:],
        padded[1:-1, :-2],                    padded[1:-1, 2:],
        padded[2:, :-2],  padded[2:, 1:-1],  padded[2:, 2:]
    ]

    # Check if any neighbor is zero
    has_zero_neighbor = np.any(np.stack(neighbors, axis=0) == 0, axis=0)

    # Keep pixel only if it is 1 and has at least one 0 neighbor
    return imageArray & has_zero_neighbor

def CallAdjustContrast(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    A wrapper function that modifies the contrast of the input image.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a grayscale image of shape (H, W).
        parameters (dict): Contains "contrastAdjustment" which is used as a contrast scale. Higher values will result in higher contrast in the output image.
        
    Returns:
        np.ndarray: The image array with reduced islands.
    """
    
    imgAdjustedContrast = AdjustContrast(imageArray, parameters["contrastAdjustment"])
    return imgAdjustedContrast

def CallEdgeDetection(imageArray:np.ndarray, parameters:dict) -> np.ndarray:
    """
    A wrapper function that calls an edge detection algorithm based on Canny Edge Detection (https://en.wikipedia.org/wiki/Canny_edge_detector).
    After performing Canny Edge Detection, the algorithm finds pixels that are the correct color (dark but not too dark) and they pass the threshold if close enough
    to an edge detected by the Canny algorithm.

    Args:
        imageArray (np.ndarry): The image produced by all the previous steps in the pipeline. If this is the first step in the pipeline, the image will be read with PIL.Image.open and converted to a float64 numpy array before being given to this function. This should be a grayscale image of shape (H, W).
        parameters (dict): Contains "gaussianBlurSigma", "maxThreshold", "minThreshold", "searchDistance", and "edgeNeighborRatio".\n
            -"gaussianBlurSigma" is used in Canny Edge Detection, please refer to the documentation for skimage.feature.canny for more information\n
            -"maxThreshold" and "minThreshold" are used to determine what value a pixel must be to be kept. The local average for each pixel is calculated in a 10-pixel radius and each pixel must satisfy (minThreshold * localAverage) < pixelValue < (maxThreshold * localAverage)
            -"searchDistance" is the Manhattan Distance from each pixel that is searched for pixels detected by Canny Edge Detection
            -"edgeNeighborRatio" is the ratio of neighbors to each pixel within searchDistance that must have been detected by Canny Edge Detection for it to be kept
        
    Returns:
        np.ndarray: The image array with reduced islands.
    """
    
    edges = feature.canny(imageArray, sigma=parameters["gaussianBlurSigma"])
    
    imageArray = ThresholdAndProximity(imageArray, edges, parameters["maxThreshold"], parameters["minThreshold"], parameters["searchDistance"], parameters["edgeNeighborRatio"])
    return imageArray

def CountZeroNeighbors(binaryArray:np.ndarray, x:int, y:int) -> int:
    """
    Counts the number of pixels equal to zero that neighbor a given point.

    Args:
        binaryArray (np.ndarry): A binary array of shape (H, W).
        x (int): The first index of the given point
        y (int): The second index of the given point
        
    Returns:
        int: The number of neighbors to the given pixel equal to zero.
    """

    neighbors = binaryArray[x-1:x+2, y-1:y+2]
    return 8 - np.sum(neighbors, dtype=np.int64)  # count black (0) pixels

def RemoveStructurallyNoisyIslands(binaryArray:np.ndarray, maxAverageBlackNeighbors:float=4.0) -> np.ndarray:
    """
    Sets any white islands to black when they are too structurally noisy.
    Noise is defined by the average number of black neighbors for each group of white pixels.

    Args:
        binaryArray (np.ndarry): A binary array of shape (H, W).
        maxAverageBlackNeighbors (float): The maximum allowable average number of black neighbors.
        
    Returns:
        np.ndarray: The modified version of binaryArray without noisy islands.
    """
    
    # Label connected white regions
    labeled_array, num_features = label(binaryArray)

    # Pad array to handle edges safely
    padded_array = np.pad(binaryArray, 1)
    padded_labels = np.pad(labeled_array, 1)

    output = np.zeros_like(binaryArray)

    for label_id in range(1, num_features + 1):
        coords = np.argwhere(padded_labels == label_id)
        black_neighbor_counts = []

        for x, y in coords:
            black_neighbors = CountZeroNeighbors(padded_array, x, y)
            black_neighbor_counts.append(black_neighbors)

        avg_black_neighbors = np.mean(black_neighbor_counts)

        if avg_black_neighbors <= maxAverageBlackNeighbors:
            # Keep coherent island
            for x, y in coords:
                output[x - 1, y - 1] = 1  # remove padding offset

    return output

def RemoveSmallWhiteIslands(binaryArray:np.ndarray, minIslandSize:int) -> np.ndarray:
    """
    Removes any white islands from the image that are too small.

    Args:
        binaryArray (np.ndarry): A binary array of shape (H, W).
        minIslandSize (int): The number of pixels that must be included in each white island.
        
    Returns:
        np.ndarray: The modified version of binaryArray without small islands.
    """

    # Label connected components
    labeled_array, _ = label(binaryArray)
    
    # Count the number of pixels in each component (ignore label 0 which is background)
    component_sizes = np.bincount(labeled_array.ravel())
    
    # Create a mask of components to keep
    keep_labels = np.where(component_sizes >= minIslandSize)[0]
    
    # Remove background (label 0) from the keep list
    keep_labels = keep_labels[keep_labels != 0]
    
    # Build a mask of all pixels to keep
    cleaned_array = np.isin(labeled_array, keep_labels).astype(np.uint8)
    
    return cleaned_array

def CreateRadialMask(width:int, height:int, centerValue:float, edgeValue:float) -> np.ndarray:
    """
    Creates a grayscale image of a specified size that has centerValue at the center and fades to edgeValue at the edges.

    Args:
        width (int): The width of the output array.
        height (int): The height of the output array.
        centerValue (float): The value at the center of the output array.
        edgeValue (float): The value at the edge of the output array.
        
    Returns:
        np.ndarray: A radial image fading from one value to another.
    """
    
    # Create a grid of (x, y) coordinates
    y, x = np.indices((height, width))
    
    # Calculate the center of the array
    center_x = (width - 1) / 2
    center_y = (height - 1) / 2
    
    # Compute distance of each point to the center
    distances = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    # Normalize distances to the range [0, 1]
    max_distance = np.sqrt(center_x**2 + center_y**2)
    norm_distances = distances / max_distance
    
    # Linearly interpolate between center_value and edge_value
    result = centerValue + (edgeValue - centerValue) * norm_distances
    
    return result

def GaussianBlur(binaryArray:np.ndarray, sigma:float=1.0) -> np.ndarray:
    """
    Performs Gaussian Blur on a binary array to smooth it. 
    This uses scipy.ndimage.gaussian_filter. Please refer to their documentation for more details.

    Args:
        binaryArray (np.ndarray): The original binary array of shape (H, W).
        sigma (float): The sigma value used in the Gaussian blur operation.
        
    Returns:
        np.ndarray: A smoothed binary image array of the same shape as binaryArray.
    """

    # Ensure the array is binary
    binaryArray = (binaryArray > 0).astype(np.uint8)

    # Apply Gaussian filter to blur the edges
    blurred = gaussian_filter(binaryArray.astype(float), sigma=sigma)

    # Threshold to convert back to binary
    threshold = threshold_otsu(blurred)
    smoothed_binary = (blurred > threshold).astype(np.uint8)

    return smoothed_binary


def AdjustContrast(image: np.ndarray, contrast: float) -> np.ndarray:
    """
    Adjusts the contrast of a grayscale image by scaling values towards the extrema (0, 1) and the middle (0.5).

    Args:
        image (np.ndarray): The original grayscale image array of shape (H, W). This must be in the range 0-1.
        contrast (float): How much the values are scaled towards the 3 target points.
        
    Returns:
        np.ndarray: A modified version of image with different contrast.
    """

    if not (0 <= image.min() and image.max() <= 1):
        raise ValueError("Input image must be normalized to range [0, 1].")
    
    # Adjust contrast: scale pixel values away from or toward the midpoint (0.5)
    adjusted = 0.5 + contrast * (image - 0.5)
    
    # Clip values to ensure they're still in [0, 1]
    return np.clip(adjusted, 0, 1)

def ThresholdAndProximity(image:np.ndarray, cannyResults:np.ndarray, maxThreshold:float, minThreshold:float, edgeSearchDistance:int, edgeNeighborRatioThreshold:float) -> np.ndarray:
    """
    Thresholds an input image given the results of Canny Edge Detection and a desired color.\n

    This algorithm first finds the average value of each pixel in a 10-pixel radius.
    Pixels are only kept white if they are in the range ((minThreshold * localAverage), (maxThreshold * localAverage)).
    This keeps pixels that are darker than some in their locality, but not too dark.\n

    Given the results of Canny Edge Detection, the ratio (Canny-Edge-Detected neighbors) / (total number of neighbors) is calculated for each pixel.
    Pixels are only kept if that ratio is high enough.
    This is performed because Canny Edge Detection will detect an outline around an object, but not its skeleton.

    Args:
        image (np.ndarray): The original grayscale image array of shape (H, W). This must be in the range 0-1.
        cannyResults (np.ndarray): The results from Canny Edge Detection.
        maxThreshold (float): Multiplied by the local average for each pixel to determine if its value is in the correct range.
        minThreshold (float): Multiplied by the local average for each pixel to determine if its value is in the correct range.
        edgeSearchDistance (int): The distance used to calculate the ratio of edge-detected neighbors to total neighbors.
        edgeNeighborRatioThreshold (float): The minimum ratio of edge-detected neighbors to total neighbors for a pixel to be kept white.
        
    Returns:
        np.ndarray: A thresholded version of image based on the Canny Edge Detection results. This is a binary array of shape (H, W).
    """

    if image.shape != cannyResults.shape:
        raise ValueError("Input arrays must have the same shape.")

    #gets the average value with a 10 pixel radius around each pixel
    smoothedImage = uniform_filter(image, size=10, mode="constant")
    #thresholds pixels so they have to be above the (minThreshold * average) and below the (maxThreshold * average) in their local area
    condition1 = np.logical_and(image < smoothedImage * maxThreshold, image > smoothedImage * minThreshold)

    #smooths out the canny edge detection (which outlines the skeleton) so that the pixels around it know they are close to an edge, just not on which side
    size = 2 * edgeSearchDistance + 1
    cannyResults = np.asarray(cannyResults, dtype=np.float64)
    local_ratio = uniform_filter(cannyResults, size=size, mode='constant')

    #finds all pixels that are close to the canny-edge-detected outline
    condition2 = local_ratio >= edgeNeighborRatioThreshold

    #returns all pixels that are dark but not too dark and are close to a canny-edge detected outline
    result = np.logical_and(condition1, condition2).astype(np.float64)

    return result