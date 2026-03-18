
My First Project - v2 2026-03-18 11:53am
==============================

This dataset was exported via roboflow.com on March 18, 2026 at 10:56 AM GMT

Roboflow is an end-to-end computer vision platform that helps you
* collaborate with your team on computer vision projects
* collect & organize images
* understand and search unstructured image data
* annotate, and create datasets
* export, train, and deploy computer vision models
* use active learning to improve your dataset over time

For state of the art Computer Vision training notebooks you can use with this dataset,
visit https://github.com/roboflow/notebooks

To find over 100k other datasets and pre-trained models, visit https://universe.roboflow.com

The dataset includes 340 images.
Objects are annotated in PNG Masks For Semantic Segmentation format.

The following pre-processing was applied to each image:
* Auto-orientation of pixel data (with EXIF-orientation stripping)
* Resize to 432x432 (Stretch)
* Auto-contrast via histogram equalization

The following augmentation was applied to create 3 versions of each source image:
* Random rotation of between -27 and +27 degrees
* Random shear of between -45° to +45° horizontally and -0° to +0° vertically
* Random Gaussian blur of between 0 and 2.5 pixels
* Salt and pepper noise was applied to 1.13 percent of pixels


