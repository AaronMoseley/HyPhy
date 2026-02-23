from .ComparisonFunctions import *
from .MetricFunctions import *
from .SkeletonPipelineSteps import *

from ..Helpers.HelperFunctions import functionKey, functionTypeKey, imageTypeKey, lineTypeKey, clusterTypeKey

PIPELINE_STEP_FUNCTION_MAP = {
    #below is an example entry into this map that should be the basis for including your own functions
    #more information about the function is included in source/UserContent/SkeletonPipelineSteps.py

    #"exampleFunction": ExamplePipelineFunction,
    "normalizeImage": NormalizeImage,
    "convertToGrayScale": ConvertToGrayScale,
    "radialThreshold": RadialThreshold,
    "removeSmallWhiteIslands": CallRemoveSmallWhiteIslands,
    "removeStructurallyNoisyIslands": CallRemoveStructurallyNoisyIslands,
    "smoothBinaryArray": CallSmoothBinaryArray,
    "skeletonize": CallSkeletonize,
    "adjustContrast": CallAdjustContrast,
    "edgeDetection": CallEdgeDetection,
    "segmentCenterArea": SegmentAreasAroundCenter,
    "rgbToHSV": RGBToHSV,
    "reduceToSingleChannel": ReduceToSingleChannel,
    "binaryEdgeDetection": BinaryEdgeDetection
}

#calculates metadata about each skeleton
METADATA_FUNCTION_MAP = {
    #below are example entries into this map that should be the basis for including your own functions
    #more information about the function is included in source/UserContent/MetricFunctions.py

    #"randomNumberPerImage": {
    #   functionKey: RandomNumberPerImage,
    #   functionTypeKey: imageTypeKey,
    #   "inImageSpace": False
    #},
    #"randomNumberPerCluster": {
    #   functionKey: RandomNumberPerCluster,
    #   functionTypeKey: clusterTypeKey,
    #   "inImageSpace": False
    #},
    #"randomNumberPerLine": {
    #   functionKey: RandomNumberPerLine,
    #   functionTypeKey: lineTypeKey,
    #   "inImageSpace": False
    #},
    "fractalDimension": {
        functionKey: FractalDimension,
        functionTypeKey: imageTypeKey,
        "inImageSpace": False
    },
    "linesInImage": {
        functionKey: LineCountInImage,
        functionTypeKey: imageTypeKey,
        "inImageSpace": False
    },
    "clustersInImage": {
        functionKey: ClusterCountInImage,
        functionTypeKey: imageTypeKey,
        "inImageSpace": False
    },
    "linesInCluster": {
        functionKey: LineCountInCluster,
        functionTypeKey: clusterTypeKey,
        "inImageSpace": False
    },
    "averageLineLength": {
        functionKey: AverageLineLengthInCluster,
        functionTypeKey: clusterTypeKey,
        "inImageSpace": True
    },
    "sinuosity": {
        functionKey: Sinuosity,
        functionTypeKey: lineTypeKey,
        "inImageSpace": False
    },
    "centerLineWidth": {
        functionKey:CalculateWidthAtLineCenter,
        functionTypeKey: lineTypeKey,
        "inImageSpace": True
    }
}

#compares generated skeletons to uploaded skeletons
COMPARISON_FUNCTION_MAP = {
    #below is an example entry into this map that should be the basis for including your own functions
    #more information about the function is included in source/UserContent/ComparisonFunctions.py

    #"exampleFunction": ExampleComparisonFunction,
    "averageDistanceToClosestPoint": AvgDistanceToClosestPoint,
    "maxDistanceToClosestPoint": MaxDistanceToClosestPoint
}