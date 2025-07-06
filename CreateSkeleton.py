import numpy as np
import os
from PIL import Image
from scipy.ndimage import label
from skimage.morphology import skeletonize
from skimage.measure import regionprops
from scipy.ndimage import gaussian_filter, uniform_filter
from skimage.filters import threshold_otsu
from skimage import morphology
from skimage import feature

from VectorizeSkeleton import VectorizeSkeleton

from HelperFunctions import skeletonKey, statFunctionMap, vectorKey, pointsKey, linesKey, clusterKey, functionKey

def top_hat(image:np.ndarray) -> np.ndarray:
    footprint = morphology.disk(1)
    res = morphology.white_tophat(image, footprint)

    return res

def remove_noisy_islands(binary_array, max_perimeter_area_ratio=0.5):
    # Label connected components
    labeled_array, num_features = label(binary_array)
    
    # Output image
    cleaned = np.zeros_like(binary_array)

    # Analyze each region
    for region in regionprops(labeled_array):
        area = region.area
        perimeter = region.perimeter
        if area == 0:
            continue

        ratio = perimeter / area
        if ratio <= max_perimeter_area_ratio:
            # Keep only coherent regions
            cleaned[labeled_array == region.label] = 1

    return cleaned

def count_black_neighbors(binary_array, x, y):
    neighbors = binary_array[x-1:x+2, y-1:y+2]
    return 8 - np.sum(neighbors, dtype=np.int64)  # count black (0) pixels

def remove_structurally_noisy_islands(binary_array, max_avg_black_neighbors=4.0):
    # Label connected white regions
    labeled_array, num_features = label(binary_array)

    # Pad array to handle edges safely
    padded_array = np.pad(binary_array, 1)
    padded_labels = np.pad(labeled_array, 1)

    output = np.zeros_like(binary_array)

    for label_id in range(1, num_features + 1):
        coords = np.argwhere(padded_labels == label_id)
        black_neighbor_counts = []

        for x, y in coords:
            black_neighbors = count_black_neighbors(padded_array, x, y)
            black_neighbor_counts.append(black_neighbors)

        avg_black_neighbors = np.mean(black_neighbor_counts)

        if avg_black_neighbors <= max_avg_black_neighbors:
            # Keep coherent island
            for x, y in coords:
                output[x - 1, y - 1] = 1  # remove padding offset

    return output

def remove_small_white_islands(binary_array:np.ndarray, min_size):
    """
    Remove white islands (connected components of 1s) with fewer than `min_size` pixels.
    
    Parameters:
        binary_array (np.ndarray): 2D binary NumPy array (0s and 1s).
        min_size (int): Minimum number of pixels a white island must have to be kept.
        
    Returns:
        np.ndarray: A new binary array with small white islands removed.
    """
    # Label connected components
    labeled_array, num_features = label(binary_array)
    
    # Count the number of pixels in each component (ignore label 0 which is background)
    component_sizes = np.bincount(labeled_array.ravel())
    
    # Create a mask of components to keep
    keep_labels = np.where(component_sizes >= min_size)[0]
    
    # Remove background (label 0) from the keep list
    keep_labels = keep_labels[keep_labels != 0]
    
    # Build a mask of all pixels to keep
    cleaned_array = np.isin(labeled_array, keep_labels).astype(np.uint8)
    
    return cleaned_array

def radial_interpolation_array(width, height, center_value, edge_value):
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
    result = center_value + (edge_value - center_value) * norm_distances
    
    return result

def smooth_binary_array(binary_array, sigma=1.0):
    """
    Smooths white structures in a binary numpy array to have smoother edges.

    Parameters:
    - binary_array: np.ndarray, binary input array (0s and 1s)
    - sigma: float, standard deviation for Gaussian blur
    - morph_radius: int, radius for morphological operations

    Returns:
    - smoothed_binary: np.ndarray, binary array with smoothed edges
    """
    # Ensure the array is binary
    binary_array = (binary_array > 0).astype(np.uint8)

    # Apply Gaussian filter to blur the edges
    blurred = gaussian_filter(binary_array.astype(float), sigma=sigma)

    # Threshold to convert back to binary
    threshold = threshold_otsu(blurred)
    smoothed_binary = (blurred > threshold).astype(np.uint8)

    return smoothed_binary


def adjust_contrast(image: np.ndarray, contrast: float) -> np.ndarray:
    """
    Adjust the contrast of a normalized 2D grayscale image.
    
    Parameters:
        image (np.ndarray): 2D numpy array with values in [0, 1].
        contrast (float): Contrast adjustment factor.
                          1.0 = no change,
                          >1.0 = increase contrast,
                          <1.0 = decrease contrast.
                          
    Returns:
        np.ndarray: Contrast-adjusted image, still in [0, 1].
    """
    if not (0 <= image.min() and image.max() <= 1):
        raise ValueError("Input image must be normalized to range [0, 1].")
    
    # Adjust contrast: scale pixel values away from or toward the midpoint (0.5)
    adjusted = 0.5 + contrast * (image - 0.5)
    
    # Clip values to ensure they're still in [0, 1]
    return np.clip(adjusted, 0, 1)

def threshold_and_proximity(image, edgeDetection, maxThreshold, minThreshold, distance, ratioThreshold):
    """
    Returns a binary array where each element is 1 if:
    - the corresponding element in array1 is less than the threshold, and
    - there is at least one element equal to 1 in array2 within the specified distance.

    Parameters:
    - array1: 2D numpy array
    - array2: 2D numpy array of the same shape as array1
    - threshold: numeric value
    - distance: int, neighborhood radius to consider

    Returns:
    - result: 2D numpy array of 0s and 1s
    """

    if image.shape != edgeDetection.shape:
        raise ValueError("Input arrays must have the same shape.")


    smoothedImage = uniform_filter(image, size=10, mode="constant")
    condition1 = np.logical_and(image < smoothedImage * maxThreshold, image > smoothedImage * minThreshold)

    # Condition 1: array1 < threshold
    #condition1 = np.logical_and(image < maxThreshold, image > minThreshold)

    size = 2 * distance + 1
    edgeDetection = np.asarray(edgeDetection, dtype=np.float64)
    local_ratio = uniform_filter(edgeDetection, size=size, mode='constant')

    # Condition 2: ratio of 1s in neighborhood >= ratio_threshold
    condition2 = local_ratio >= ratioThreshold

    # Final result: element-wise AND of both conditions
    result = np.logical_and(condition1, condition2).astype(np.float64)

    return result

def GenerateSkeleton(directory:str, fileName:str, parameters:dict, steps:list) -> dict:
    if not fileName.endswith(".tif") and not fileName.endswith(".png"):
        return None
    
    filePath = os.path.join(directory, fileName)
    img = Image.open(filePath)

    originalImageArray = np.asarray(img, dtype=np.float64)

    imgArray = np.asarray(img, dtype=np.float64)

    maxValue = np.max(imgArray)
    minValue = np.min(imgArray)
    imgArray -= minValue
    maxValue -= minValue
    imgArray /= maxValue

    originalImageArray -= minValue
    originalImageArray /= maxValue

    #call all the functions
    for step in steps:
        imgArray = stepFunctionMap[step["function"]](imgArray, parameters)

    result = {}
    result[skeletonKey] = np.asarray(imgArray, dtype=np.float64)

    lines, points, clusters = VectorizeSkeleton(imgArray)

    vectors = {
        linesKey: lines,
        pointsKey: points,
        clusterKey: clusters
    }

    result[vectorKey] = vectors

    for key in statFunctionMap:
        result[key] = statFunctionMap[key][functionKey](imgArray, lines, points, clusters)
        
    print(f"Created skeleton for {fileName}")

    return result

def RadialThreshold(imgArray:np.ndarray, parameters:dict) -> np.ndarray:
    thresholds = radial_interpolation_array(imgArray.shape[1], imgArray.shape[0], parameters["centerThreshold"], parameters["edgeThreshold"])

    imgArray = np.asarray(imgArray < thresholds, dtype=np.float64)

    return imgArray

def CallRemoveSmallWhiteIslands(imgArray:np.ndarray, parameters:dict) -> np.ndarray:
    imgArray = remove_small_white_islands(imgArray, parameters["minWhiteIslandSize"])

    return imgArray

def CallRemoveStructurallyNoisyIslands(imgArray:np.ndarray, parameters:dict) -> np.ndarray:
    imgArray = remove_structurally_noisy_islands(imgArray, max_avg_black_neighbors=parameters["noiseTolerance"])
    return imgArray

def CallSmoothBinaryArray(imgArray:np.ndarray, parameters:dict) -> np.ndarray:
    imgArray = smooth_binary_array(imgArray, sigma=parameters["gaussianBlurSigma"])
    return imgArray

def CallSkeletonize(imgArray:np.ndarray, parameters:dict) -> np.ndarray:
    imgArray = skeletonize(imgArray)
    return imgArray

def CallAdjustContrast(imgArray:np.ndarray, parameters:dict) -> np.ndarray:
    imgAdjustedContrast = adjust_contrast(imgArray, parameters["contrastAdjustment"])
    return imgAdjustedContrast

def CallEdgeDetection(imgArray:np.ndarray, parameters:dict) -> np.ndarray:
    edges = feature.canny(imgArray, sigma=parameters["gaussianBlurSigma"])
    
    imgArray = threshold_and_proximity(imgArray, edges, parameters["maxThreshold"], parameters["minThreshold"], 5, parameters["edgeNeighborRatio"])
    return imgArray

stepFunctionMap = {
    "radialThreshold": RadialThreshold,
    "removeSmallWhiteIslands": CallRemoveSmallWhiteIslands,
    "removeStructurallyNoisyIslands": CallRemoveStructurallyNoisyIslands,
    "smoothBinaryArray": CallSmoothBinaryArray,
    "skeletonize": CallSkeletonize,
    "adjustContrast": CallAdjustContrast,
    "edgeDetection": CallEdgeDetection
}