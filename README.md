# BOM radar image ripper

Python script for scraping the Australian BOM for rain radar images. The script processes these from .png images into an intensity array with a cropped aspect ratio of 16:9. The intensity array is then downsampled to a 16x9 array before being exported as a text file. 

This script is utilised on an AWS ec2 [server][http://http://34.222.32.30/] along with an apache web server. There the text files are to be retrieved by a microcontroller and displayed on a charliplexed 16x9 [led display][https://www.adafruit.com/product/2973] from adafruit 