import numpy as np
import os
from PIL import Image
from scipy.ndimage import label
from skimage.morphology import skeletonize
from scipy.ndimage import gaussian_filter
from skimage.filters import threshold_otsu
from collections import OrderedDict

skeletonKey = "skeleton"
originalImageKey = "originalImage"

def change_contrast(img:Image, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))
    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)

import numpy as np

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

def generate_skeletonized_images(directory:str) -> OrderedDict:
    result = OrderedDict()

    fileNames = os.listdir(directory)
    for fileName in fileNames:
        if not fileName.endswith(".tif") and not fileName.endswith(".png"):
            continue
        
        filePath = os.path.join(directory, fileName)
        img = Image.open(filePath)

        originalImageArray = np.asarray(img, dtype=np.float64)

        img = change_contrast(img, 100)
        imgArray = np.asarray(img, dtype=np.float64)

        maxValue = np.max(imgArray)
        minValue = np.min(imgArray)
        imgArray -= minValue
        maxValue -= minValue
        imgArray /= maxValue

        originalImageArray -= minValue
        originalImageArray /= maxValue

        thresholds = radial_interpolation_array(imgArray.shape[1], imgArray.shape[0], 0.5, 0.1)

        imgArray = np.asarray(imgArray < thresholds, dtype=np.float64)

        imgArray = remove_small_white_islands(imgArray, 300)
        imgArray = smooth_binary_array(imgArray, sigma=1.1)
        imgArray = skeletonize(imgArray)

        currResult = {}
        currResult[skeletonKey] = np.asarray(imgArray, dtype=np.float64)
        currResult[originalImageKey] = np.asarray(originalImageArray, dtype=np.float64)

        currResult["tempCalc1"] = 0.0
        currResult["tempCalc2"] = 0.0

        result[fileName] = currResult

    return result

if __name__ == "__main__":
    directory = "C:\\Users\\Aaron\\Downloads\\JennaProject\\Images"

    images = generate_skeletonized_images(directory)
    Image.fromarray(np.asarray(images[list(images.keys())[0]] * 255, dtype=np.uint8), mode="L").show()