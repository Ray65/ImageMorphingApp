#! /usr/bin/env python3.4
import numpy as np
from scipy.interpolate import RectBivariateSpline
import imageio as img
from PIL import Image, ImageDraw
from scipy.spatial import Delaunay
import time
import os
import subprocess
#import sys
#import getopt
#import load_save

#Helper functions
def _loadImage(filename):
    img = Image.open(filename)
    img.load()
    data = np.asarray(img, dtype='uint8')
    return data

def _saveImage(numpydata, outfile):
    img = Image.fromarray(numpydata)
    img.save(outfile)

def _saveRGB(data, outfile):
    outimg = Image.fromarray(data, "RGB")
    outimg.save(outfile)

def _loadPoints(filename):
    return np.loadtxt(filename)

def _getMask(data, triangle_vertices):
    (height, width) = data.shape
    #print("height = "+str(data.shape[0]))
    #print("width = "+str(data.shape[1]))
    img = Image.new('L', (width,height), 0)
    x1, y1, x2, y2, x3, y3 = triangle_vertices.flatten()
    vertices = [(x1,y1), (x2,y2), (x3,y3)]
    ImageDraw.Draw(img).polygon(vertices, outline=255, fill=255)
    return np.array(img)

def _getMaskRGB(data, triangle_vertices):
    #img = Image.new('RGB', (800,600), 0)
    height, width = data.shape[0], data.shape[1]
    img = Image.new('RGB', (width,height), 0)
    x1, y1, x2, y2, x3, y3 = triangle_vertices.flatten()
    vertices = [(x1,y1), (x2,y2), (x3,y3)]
    ImageDraw.Draw(img).polygon(vertices, outline=255, fill=255)
    return np.array(img)


#ColorAffine
class ColorAffine():

    def __init__(self, source, destination):
        if((not(source.dtype == np.float64)) or (not(destination.dtype == np.float64)) or (not(source.shape == (3,2))) or (not(destination.shape == (3,2)))):
            raise ValueError("Not of valid type or dimension.")

        self.source = source
        self.destination = destination


        #Source Matrix
        source_mat = [
            [source[0,0], source[0,1], 1, 0, 0, 0],
            [0, 0, 0, source[0,0], source[0,1], 1],
            [source[1,0], source[1,1], 1, 0, 0, 0],
            [0, 0, 0, source[1,0], source[1,1], 1],
            [source[2,0], source[2,1], 1, 0, 0, 0],
            [0, 0, 0, source[2,0], source[2,1], 1]
        ]

        #Target Matrix
        target_mat = [[destination[0,0]],[destination[0,1]],[destination[1,0]],[destination[1,1]],[destination[2,0]],[destination[2,1]]]

        h_vect = np.linalg.solve(source_mat, target_mat)

        #Transform matrix
        self.matrix = [
            [h_vect[0,0], h_vect[1,0], h_vect[2,0]],
            [h_vect[3,0], h_vect[4,0], h_vect[5,0]],
            [0, 0, 1]
        ]

        #Inverse Transform function
        self.h_inv_mat = np.linalg.inv(self.matrix)
        self.matrix = np.asarray(self.matrix,dtype=np.uint8)

    def transform(self, sourceImage, destinationImage):
        if((not(isinstance(sourceImage, np.ndarray))) or (not(isinstance(destinationImage, np.ndarray)))):
            raise TypeError("Image must be of type numpy array.")

        #canvas = load_save.getMaskRGB(sourceImage, self.destination)
        canvas = _getMaskRGB(sourceImage, self.destination)
        w, h = sourceImage.shape[0], sourceImage.shape[1]
        sourceImage_r = [[0 for x in range(h)] for y in range(w)]
        sourceImage_g = [[0 for x in range(h)] for y in range(w)]
        sourceImage_b = [[0 for x in range(h)] for y in range(w)]

        sourceImage_r = np.array(sourceImage_r)
        sourceImage_g = np.array(sourceImage_g)
        sourceImage_b = np.array(sourceImage_b)

        non_zero_tuple = canvas.nonzero()
        non_zero_yarr = non_zero_tuple[0]
        non_zero_xarr = non_zero_tuple[1]
        non_zero_colour = non_zero_tuple[2]

        for y in range(sourceImage.shape[1]):
            for x in range(sourceImage.shape[0]):
                sourceImage_r[x,y] = sourceImage[x,y,0]
                sourceImage_g[x,y] = sourceImage[x,y,1]
                sourceImage_b[x,y] = sourceImage[x,y,2]

        #interpolation
        smoothLine_r = RectBivariateSpline(np.arange(sourceImage.shape[0]), np.arange(sourceImage.shape[1]), z = sourceImage_r, kx = 1, ky = 1)
        smoothLine_g = RectBivariateSpline(np.arange(sourceImage.shape[0]), np.arange(sourceImage.shape[1]), z = sourceImage_g, kx = 1, ky = 1)
        smoothLine_b = RectBivariateSpline(np.arange(sourceImage.shape[0]), np.arange(sourceImage.shape[1]), z = sourceImage_b, kx = 1, ky = 1)

        for x, y in zip(non_zero_xarr, non_zero_yarr):
            transformed_matrix = np.dot(self.h_inv_mat, [[x], [y], [1]])
            destinationImage[y,x,0] = smoothLine_r.ev(transformed_matrix[1], transformed_matrix[0])
            destinationImage[y,x,1] = smoothLine_g.ev(transformed_matrix[1], transformed_matrix[0])
            destinationImage[y,x,2] = smoothLine_b.ev(transformed_matrix[1], transformed_matrix[0])


#Affine
class Affine():
    def __init__(self, source, destination):
        if((not(source.dtype == np.float64)) or (not(destination.dtype == np.float64)) or (not(source.shape == (3,2))) or (not(destination.shape == (3,2)))):
            raise ValueError("Not of valid type or dimension.")

        self.source = source
        self.destination = destination


        #Source Matrix
        source_mat = [
            [source[0,0], source[0,1], 1, 0, 0, 0],
            [0, 0, 0, source[0,0], source[0,1], 1],
            [source[1,0], source[1,1], 1, 0, 0, 0],
            [0, 0, 0, source[1,0], source[1,1], 1],
            [source[2,0], source[2,1], 1, 0, 0, 0],
            [0, 0, 0, source[2,0], source[2,1], 1]
        ]

        #Target Matrix
        target_mat = [[destination[0,0]],[destination[0,1]],[destination[1,0]],[destination[1,1]],[destination[2,0]],[destination[2,1]]]

        h_vect = np.linalg.solve(source_mat, target_mat)

        #Transform matrix
        self.matrix = [
            [h_vect[0,0], h_vect[1,0], h_vect[2,0]],
            [h_vect[3,0], h_vect[4,0], h_vect[5,0]],
            [0, 0, 1]
        ]


        #Inverse Transform function
        self.h_inv_mat = np.linalg.inv(self.matrix)
        self.matrix = np.asarray(self.matrix,dtype=np.uint8)

    def transform(self, sourceImage, destinationImage):
        if((not(isinstance(sourceImage, np.ndarray))) or (not(isinstance(destinationImage, np.ndarray)))):
            raise TypeError("Image must be of type numpy array.")

        #canvas = load_save.getMask(sourceImage, self.destination)
        canvas = _getMask(sourceImage, self.destination)

        non_zero_tuple = canvas.nonzero()


        #FML 2
        non_zero_yarr = non_zero_tuple[0]
        non_zero_xarr = non_zero_tuple[1]


        #interpolation
        smoothLine = RectBivariateSpline(np.arange(sourceImage.shape[0]), np.arange(sourceImage.shape[1]), z = sourceImage, kx = 1, ky = 1)

        #FML 1
        for x, y in zip(non_zero_xarr, non_zero_yarr):
            transformed_matrix = np.dot(self.h_inv_mat, [[x], [y], [1]])
            destinationImage[y,x] = smoothLine.ev(transformed_matrix[1], transformed_matrix[0])



class Blender():
    def __init__(self, startImage, startPoints, endImage, endPoints):
        if((not(isinstance(startImage, np.ndarray))) or (not(isinstance(startPoints, np.ndarray))) or (not(isinstance(endImage, np.ndarray))) or (not(isinstance(endPoints, np.ndarray)))):
            raise TypeError("Data points are not of type numpy array.")

        self.startPoints = startPoints
        self.endPoints = endPoints
        self.startImage = startImage
        self.endImage = endImage
        self.start_tri = Delaunay(self.startPoints)

        self.includeReversed = True
       
    def getBlendedImage(self, alpha):

        #New canvas
        #canvas_start = Image.new('L',(800,600),0)
        canvas_start = Image.new('L',(self.startImage.shape[1],self.startImage.shape[0]),0)
        canvas_start_array = np.array(canvas_start)

        #canvas_end = Image.new('L',(800,600),0)
        canvas_end = Image.new('L',(self.endImage.shape[1],self.endImage.shape[0]),0)
        canvas_end_array = np.array(canvas_end)


        if((alpha > 1) or (alpha < 0)):
            raise ValueError("Alpha value must be between 0 & 1.")
        start_tri_list = []
        all_blended_tris = []
        for triangle in (self.start_tri.simplices):
            start_tri_list.append(triangle)
        start_tri_list = np.array(start_tri_list)
        #start_tri_list = self.start_tri.simplices
        #print(start_tri_list)
        for tri in start_tri_list:
            blended_tri = []
            for i in range(3):
                blended_pix = []
                start_coods = self.startPoints[tri[i]]
                end_coods = self.endPoints[tri[i]]
                blend_x = ((1-alpha)*start_coods[0]) + (alpha*end_coods[0])
                blended_pix.append(blend_x)
                blend_y = ((1-alpha)*start_coods[1]) + (alpha*end_coods[1])
                blended_pix.append(blend_y)
                blended_pix = tuple(blended_pix)
                blended_tri.append(blended_pix)
            all_blended_tris.append(blended_tri)


        all_blended_tris = np.array(all_blended_tris)

        #For start img... Need to do for end img
        for src_tri, aff_tri in zip(start_tri_list, all_blended_tris):
            #start_point_int_arr = np.asarray(self.startPoints[src_tri])
            #end_point_int_arr = np.asarray(self.endPoints[src_tri])
            aff_start_obj = Affine(self.startPoints[src_tri] ,aff_tri)
            aff_end_obj = Affine(self.endPoints[src_tri], aff_tri)

            start_img_int =  self.startImage.astype(np.uint8)
            end_img_int =  self.endImage.astype(np.uint8)

            aff_start_obj.transform(start_img_int, canvas_start_array)
            aff_end_obj.transform(end_img_int, canvas_end_array)


        #new_broken_img = Image.new('L',(800,600),0)http://www.bogotobogo.com/python/OpenCV_Python/python_opencv3_basic_image_operations_pixel_access_image_load.php
        new_broken_img = Image.new('L',(self.startImage.shape[1],self.startImage.shape[0]),0)
        new_broken_img_array = np.array(new_broken_img)
        for h in np.arange(self.startImage.shape[1]):
            for w in np.arange(self.startImage.shape[0]):
                new_broken_img_array[w,h] = ((1-alpha)*canvas_start_array[w,h])+((alpha)*canvas_end_array[w,h])


        new_broken_img_array_int = new_broken_img_array.astype(np.uint8)
        return new_broken_img_array_int


    def generateMorphVideo(self, targetFolderPath, sequenceLength, includeReversed):
        self.includeReversed = includeReversed
        if not os.path.exists(targetFolderPath):
            os.makedirs(targetFolderPath)

        #REMEMBER TO UNCOMMENT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # if (sequenceLength < 10):
        #     raise ValueError("Please enter a sequence length greater than or equal to 10.")

        diff = 1/sequenceLength
        alpha_vid = 0
        output_fname = "morph.mp4"

        output_vid_dir = ''.join([targetFolderPath,'/',output_fname])
        for i in range(sequenceLength):
            morph_frame_img_arr = self.getBlendedImage(alpha_vid)
            alpha_vid = alpha_vid + diff
            frame_name = "frame{:03d}".format(i)
            fname = frame_name+".jpg"
            temp_vid_name = 'temp_vid{:03d}'.format(i)
            temp_vid = temp_vid_name+".mp4"
            temp_vid_dir = ''.join([targetFolderPath,'/',temp_vid])
            temp_frame_dir = ''.join([targetFolderPath,'/',fname])
            _saveImage(morph_frame_img_arr, temp_frame_dir)

            ###subprocess.call(['wget', fname, '-o', temp_frame_dir])
            #subprocess.call(['ffmpeg -v verbose -f image2 -pattern_type sequence -start_number 0 -r 5 -i'+temp_frame_dir+'-s 800x600'+temp_vid_dir], shell = True)
            subprocess.call(['ffmpeg -v verbose -f image2 -r 5 -i '+temp_frame_dir+'  -s 800x600 '+temp_vid_dir], shell = True)
            #subprocess.call(['cd ' + targetFolderPath + ' | ffmpeg -v verbose -i "concat:' + output_fname + '|' + fname + '" -c copy ' + temp_vid],shell=True)
            #subprocess.call(['cd ' + targetFolderPath + ' | ffmpeg -v verbose -i "concat:' + output_vid_dir + '|' + temp_frame_dir + '" -c copy ' + temp_vid_dir],shell=True)
            subprocess.call(['cd ' + targetFolderPath + ' | ffmpeg -v verbose -i "concat:' + output_vid_dir + '|' + temp_frame_dir + '" -c copy ' + temp_vid_dir],shell=True)

        os.rename(temp_vid_dir, output_vid_dir)



class ColorBlender():
    def __init__(self, startImage, startPoints, endImage, endPoints):
        if((not(isinstance(startImage, np.ndarray))) or (not(isinstance(startPoints, np.ndarray))) or (not(isinstance(endImage, np.ndarray))) or (not(isinstance(endPoints, np.ndarray)))):
            raise TypeError("Data points are not of type numpy array.")

        self.startPoints = startPoints
        self.endPoints = endPoints
        self.startImage = startImage
        self.endImage = endImage
        self.start_tri = Delaunay(self.startPoints)

    def getBlendedImage(self, alpha):

        #New canvas
        #canvas_start = Image.new('L',(800,600),0)
        canvas_start = Image.new('RGB',(self.startImage.shape[1],self.startImage.shape[0]),0)
        canvas_start_array = np.array(canvas_start)

        canvas_end = Image.new('RGB',(self.endImage.shape[1],self.endImage.shape[0]),0)
        canvas_end_array = np.array(canvas_end)

        if((alpha > 1) or (alpha < 0)):
            raise ValueError("Alpha value must be between 0 & 1.")

        start_tri_list = []
        all_blended_tris = []
        for triangle in (self.start_tri.simplices):
            start_tri_list.append(triangle)
        start_tri_list = np.array(start_tri_list)

        for tri in start_tri_list:
            blended_tri = []
            for i in range(3):
                blended_pix = []
                start_coods = self.startPoints[tri[i]]
                end_coods = self.endPoints[tri[i]]
                blend_x = ((1-alpha)*start_coods[0]) + (alpha*end_coods[0])
                blended_pix.append(blend_x)
                blend_y = ((1-alpha)*start_coods[1]) + (alpha*end_coods[1])
                blended_pix.append(blend_y)
                blended_pix = tuple(blended_pix)
                blended_tri.append(blended_pix)
            all_blended_tris.append(blended_tri)


        all_blended_tris = np.array(all_blended_tris)

        for src_tri, aff_tri in zip(start_tri_list, all_blended_tris):
            aff_start_obj = ColorAffine(self.startPoints[src_tri] ,aff_tri)
            aff_end_obj = ColorAffine(self.endPoints[src_tri], aff_tri)

            start_img_int =  self.startImage.astype(np.uint8)
            end_img_int =  self.endImage.astype(np.uint8)

            aff_start_obj.transform(start_img_int, canvas_start_array)
            aff_end_obj.transform(end_img_int, canvas_end_array)

            #aff_start_obj.test(self.startImage)
        new_broken_img = Image.new('RGB',(self.startImage.shape[1],self.startImage.shape[0]),0)
        new_broken_img_array = np.array(new_broken_img)
        for h in np.arange(self.startImage.shape[1]):
            for w in np.arange(self.startImage.shape[0]):
                new_broken_img_array[w,h,0] = ((1-alpha)*canvas_start_array[w,h,0])+((alpha)*canvas_end_array[w,h,0])
                new_broken_img_array[w,h,1] = ((1-alpha)*canvas_start_array[w,h,1])+((alpha)*canvas_end_array[w,h,1])
                new_broken_img_array[w,h,2] = ((1-alpha)*canvas_start_array[w,h,2])+((alpha)*canvas_end_array[w,h,2])



        new_broken_img_array_int = new_broken_img_array.astype(np.uint8)
        return new_broken_img_array_int






if __name__=="__main__":

    start_img = _loadImage('WolfGray.jpg')
    end_img = _loadImage('Tiger2Gray.jpg')
    start_pts = _loadPoints('wolf.jpg.txt')
    end_pts = _loadPoints('tiger2.jpg.txt')

    #Colour
    start_rgb_img = _loadImage('WolfColor.jpg')
    end_rgb_img = _loadImage('Tiger2Color.jpg')
    start_rgb_pts = _loadPoints('wolf.jpg.txt')
    end_rgb_pts = _loadPoints('tiger2.jpg.txt')


    start_time = time.time()
    #blended_img_array = Blender(start_img,start_pts,end_img,end_pts).getBlendedImage(0.5)
    #_saveImage(blended_img_array, 'New_Broken2.jpg')

    #Final Testing - Grayscale
    #_saveImage(blended_img_array, 'Thank_you_Alex.jpg')
    #print(time.time() - start_time, "seconds")

    coBlend = ColorBlender(start_rgb_img,start_rgb_pts,end_rgb_img,end_rgb_pts).getBlendedImage(0.3)
    _saveRGB(coBlend, "Colour_Blend_Test2.jpg")
    print(time.time() - start_time, "seconds")

    #print(coBlend)

    #print(start_rgb_img[0])
    #print(start_img[0])

    #Movie
    #Blender(start_img,start_pts,end_img,end_pts).generateMorphVideo('Movie', 3, False)

