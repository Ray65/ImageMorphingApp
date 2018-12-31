import sys
import re
from PySide.QtCore import *
from PySide.QtGui import *
from MorphingGUI import *
import numpy as np
from scipy.interpolate import RectBivariateSpline
import imageio as img
from PIL import Image, ImageDraw
from scipy.spatial import Delaunay
import time
import os
import subprocess
import Morphing

#Helper functions & classes
class _POINT():
    def __init__(self, x, y, ok):
        if(x == None):
            self.x = 0
        else:
            self.x = x

        if(y == None):
            self.y = 0
        else:
            self.y = y

        if(ok == None):
            self.ok = 0
        else:
            self.ok = ok

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
    img = Image.new('L', (width,height), 0)
    x1, y1, x2, y2, x3, y3 = triangle_vertices.flatten()
    vertices = [(x1,y1), (x2,y2), (x3,y3)]
    ImageDraw.Draw(img).polygon(vertices, outline=255, fill=255)
    return np.array(img)

def _getMaskRGB(data, triangle_vertices):
    height, width = data.shape[0], data.shape[1]
    img = Image.new('RGB', (width,height), 0)
    x1, y1, x2, y2, x3, y3 = triangle_vertices.flatten()
    vertices = [(x1,y1), (x2,y2), (x3,y3)]
    ImageDraw.Draw(img).polygon(vertices, outline=255, fill=255)
    return np.array(img)


class MorphingApp(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MorphingApp, self).__init__(parent)
        self.setupUi(self)

        #Flags & Counters
        self.img_flag = 0
        self.DelaunayFlag = 0
        self.start_flag = 0
        self.end_flag = 0
        self.start_bkspcFlag = 0
        self.end_bkspcFlag = 0
        self.start_count = 0
        self.corr_starttext_exists = 0
        self.corr_endtext_exists = 0
        self.also_recorded_flag = 0
        self.mainWindow_flag = 0
        self.do_nothing_flag = 0
        self.final_record_flag = 0
        self.also_final_record_flag = 0
        self.endOK_flag = 0
        self.start_temp_hasChanged = 0
        self.end_temp_hasChanged = 0
        self.persist_PrevPairFlag = 0
        self.endOK_Prev = 0


        #Empty declarations
        self.start_item_list = []
        self.end_item_list = []
        self.recorded_start_item_list = []
        self.recorded_end_item_list = []
        self.start_img_x = None
        self.start_img_y = None
        self.end_img_x = None
        self.end_img_y = None

        self.temp_start_x = None
        self.temp_start_y = None
        self.temp_end_x = None
        self.temp_end_y = None
        self.start_temp_ptobj = _POINT(None, None, 0)
        self.end_temp_ptobj = _POINT(None, None, 0)
        ######################
        self.start_readIn = []
        self.start_persisted = []
        self.end_readIn = []
        self.end_persisted = []
        self.start_readIn_POINTObj = []
        self.end_readIn_POINTObj = []

        #Disabling widgets
        self.sldrAlpha.setEnabled(False)
        self.txtAlphaVal.setEnabled(False)
        self.btnBlend.setEnabled(False)

        #Enabling widgets
        self.btnStart.setEnabled(True)
        self.btnEnd.setEnabled(True)

        self.btnStart.clicked.connect(self.loadStartImage)
        self.btnEnd.clicked.connect(self.loadEndImage)
        self.btnBlend.clicked.connect(self.getBlendedImage)
        self.chkShowTri.stateChanged.connect(self.DrawDelaunayFlag)
        self.sldrAlpha.valueChanged.connect(self.getAlphaValue)

    #Loading Start Image
    def loadStartImage(self):
        #File Explorer
        filePath, _ = QFileDialog.getOpenFileName(self, caption='Open image file ...')

        if not filePath:
            return

        points_fname = filePath+'.txt'

        self.start_filePath = filePath

        #Checking image type
        if(self.is_StartImg_GreyScale() == True):
            print("START IMAGE IS GREY")
        else:
            print("START IMAGE IS RGB")

        # if not points_fname:
        #     self.getStartPoints()

        self.start_points_fname = points_fname
        #Enabling disabled widgets
        self.img_flag = self.img_flag + 1
        self.EnableInitiallyDisabledWidgies()

        #Displaying points
        self.start_scene = QGraphicsScene()
        self.start_pixMap = QPixmap(filePath)

        self.start_img = _loadImage(filePath)
        try:
            self.corr_starttext_exists = 1
            self.start_pts = _loadPoints(points_fname)
            print(self.start_pts)
            # self.Also_getStartPoints()

        except:
            self.getStartPoints()
        else:
            self.start_scene.addPixmap(self.start_pixMap)
            for i in range(len(self.start_pts)):
                brush = QBrush()
                pen = QPen()
                pen.setColor(QColor(255,0,0))
                brush.setColor(QColor(255,0,0))
                brush.setStyle(Qt.SolidPattern)
                self.start_scene.addEllipse(self.start_pts[i, 0]-5 ,self.start_pts[i, 1]-5 , 10 , 10, pen, brush)
                # self.start_scene.addEllipse(self.start_pts[i][0]-3.5 ,self.start_pts[i][1]-3.5 , 10 , 10, pen, brush)
                print("START PTS:")
                print(self.start_pts)
            self.Also_getStartPoints()
            self.graphicStartImg.setScene(self.start_scene)
            self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

    #Loading End Image

    def loadEndImage(self):
        #File Explorer
        filePath, _ = QFileDialog.getOpenFileName(self, caption='Open image file ...')



        if not filePath:
            return

        self.end_filePath = filePath
        points_fname = filePath+'.txt'

        # if not points_fname:
        #     self.getEndPoints()

        self.end_points_fname = points_fname

        #Checking image type
        if(self.is_EndImg_GreyScale() == True):
            print("END IMAGE IS GREY")
        else:
            print("END IMAGE IS RGB")


        #Enabling disabled widgets
        self.img_flag = self.img_flag + 1
        self.EnableInitiallyDisabledWidgies()

        #Displaying points
        self.end_scene = QGraphicsScene()
        self.end_pixMap = QPixmap(filePath)

        self.end_img = _loadImage(filePath)
        try:
            self.corr_endtext_exists = 1
            self.end_pts = _loadPoints(points_fname)
            # self.Also_getEndPoints()

        except:
            self.getEndPoints()
        else:
            self.end_scene.addPixmap(self.end_pixMap)
            for i in range(len(self.end_pts)):
                brush = QBrush()
                pen = QPen()
                pen.setColor(QColor(255,0,0))
                brush.setColor(QColor(255,0,0))
                brush.setStyle(Qt.SolidPattern)
                self.end_scene.addEllipse(self.end_pts[i, 0]-5 ,self.end_pts[i, 1]-5 , 10 , 10, pen, brush)
                # self.end_scene.addEllipse(self.end_pts[i][0]-3.5 ,self.end_pts[i][1]-3.5 , 10 , 10, pen, brush)
            self.Also_getEndPoints()
            self.graphicEndImg.setScene(self.end_scene)
            self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe



    def DrawDelaunayFlag(self):
        self.DelaunayFlag = self.DelaunayFlag + 1
        #Drawing calls
        if(self.DelaunayFlag % 2 == 1):
            # self.DrawDelaunay() #For images with given .txt files
            #For own images
            # if((self.corr_starttext_exists != 1)or(self.corr_endtext_exists != 1)):
            #     self.ResetWidgets()
            #     self.StartEnd_CreateDelaunay()
            #     # self.Start_CreateDelaunay()
            #     # self.End_CreateDelaunay()
            #     self.start_scene.mousePressEvent = self.getStartPos
            #     self.end_scene.mousePressEvent = self.getEndPos
            # else:
            #
            #     self.DrawDelaunay2()
            #     self.start_scene.mousePressEvent = self.getStartPos
            #     self.end_scene.mousePressEvent = self.getEndPos
            self.DrawDelaunay2()
            self.start_scene.mousePressEvent = self.getStartPos
            self.end_scene.mousePressEvent = self.getEndPos

        #Clearing calls
        else:
            # # self.ClearDelaunay()  #For images with given .txt files
            # if((self.corr_starttext_exists != 1)or(self.corr_endtext_exists != 1)):
            #     self.ResetWidgets()
            #     self.Start_ClearDelaunay()
            #     self.End_ClearDelaunay()
            #     self.start_scene.mousePressEvent = self.getStartPos
            #     self.end_scene.mousePressEvent = self.getEndPos
            # else:
            #     self.ClearDelaunay()
            #     self.start_scene.mousePressEvent = self.getStartPos
            #     self.end_scene.mousePressEvent = self.getEndPos
            self.ClearDelaunay()
            self.start_scene.mousePressEvent = self.getStartPos
            self.end_scene.mousePressEvent = self.getEndPos



    def DrawDelaunay2(self):

        print("In Draw Delaunay 2")
        self.start_pts = _loadPoints(self.start_points_fname)
        self.end_pts = _loadPoints(self.end_points_fname)
        self.start_tri = Delaunay(self.start_pts)

        #LIGHT-BLUE --- For drawing lines
        brush_LBlue = QBrush()
        pen_LBlue = QPen()
        pen_LBlue.setColor(QColor(0,191,255))
        brush_LBlue.setColor(QColor(0,191,255))

        #ORANGE --- For errors/suspicious points
        brush_orange = QBrush()
        pen_orange = QPen()
        pen_orange.setColor(QColor(255, 165, 0))
        brush_orange.setColor(QColor(255, 165, 0))
        brush_orange.setStyle(Qt.SolidPattern)

        #VIOLET ---- For newly persisted
        brush_violet = QBrush()
        pen_violet = QPen()
        pen_violet.setColor(QColor(138, 43, 226))
        brush_violet.setColor(QColor(138, 43, 226))
        brush_violet.setStyle(Qt.SolidPattern)

        #RED --- For previously existing
        brush_red = QBrush()
        pen_red = QPen()
        pen_red.setColor(QColor(255,0,0))
        brush_red.setColor(QColor(255,0,0))
        brush_red.setStyle(Qt.SolidPattern)

        #Plotting the points
        if(len(self.start_pts) != 0):
            for i in range(len(self.start_pts)):
                self.start_scene.addEllipse(self.start_pts[i, 0]-5 ,self.start_pts[i, 1]-5 , 10 , 10, pen_red, brush_red)
            self.graphicStartImg.setScene(self.start_scene)
            self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

            #PREVIOUSLY EXISTING POINTS IN FILE
            #Drawing the lines
            for triangle in (self.start_tri.simplices):
                tri_s = QPolygonF()
                tri_e = QPolygonF()
                # print(triangle)
                xs1, ys1 = self.start_pts[triangle[0]].flatten()
                xs2, ys2 = self.start_pts[triangle[1]].flatten()
                xs3, ys3 = self.start_pts[triangle[2]].flatten()

                xe1, ye1 = self.end_pts[triangle[0]].flatten()
                xe2, ye2 = self.end_pts[triangle[1]].flatten()
                xe3, ye3 = self.end_pts[triangle[2]].flatten()

                tri_s.append(QPointF(xs1,ys1))
                tri_s.append(QPointF(xs2,ys2))
                tri_s.append(QPointF(xs3,ys3))

                tri_e.append(QPointF(xe1,ye1))
                tri_e.append(QPointF(xe2,ye2))
                tri_e.append(QPointF(xe3,ye3))

                self.start_scene.addPolygon(tri_s, pen_LBlue, brush_LBlue)
                self.end_scene.addPolygon(tri_e, pen_LBlue, brush_LBlue)

            # self.after_start_green.addPolygon(tri_s, pen, brush)
            # self.after_end_green.addPolygon(tri_e, pen, brush)

        #####################END OF DEALING WITH ALREADY EXISTING################

        #NEWLY PERSISTED POINTS
        if(len(self.start_persisted) != 0):
            self.start_persisted_array = np.array(self.start_persisted)
            self.end_persisted_array = np.array(self.end_persisted)

            print("Start persist array:")
            print(self.start_persisted_array)
            print("End persist array:")
            print(self.end_persisted_array)

            #Plotting the points

            for i in range(len(self.start_persisted_array)):
                self.start_scene.addEllipse(self.start_persisted_array[i, 0]-5 ,self.start_persisted_array[i, 1]-5 , 10 , 10, pen_violet, brush_violet)

            self.graphicStartImg.setScene(self.start_scene)
            self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe


            for i in range(len(self.end_persisted_array)):
                self.end_scene.addEllipse(self.end_persisted_array[i, 0]-5 ,self.end_persisted_array[i, 1]-5 , 10 , 10, pen_violet, brush_violet)

            self.graphicEndImg.setScene(self.end_scene)
            self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

            #Drawing the lines
            try:
                self.start_tri = Delaunay(self.start_persisted_array)

                for triangle in (self.start_tri.simplices):
                    tri_s = QPolygonF()
                    tri_e = QPolygonF()
                    # print(triangle)
                    xs1, ys1 = self.start_persisted_array[triangle[0]].flatten()
                    xs2, ys2 = self.start_persisted_array[triangle[1]].flatten()
                    xs3, ys3 = self.start_persisted_array[triangle[2]].flatten()

                    xe1, ye1 = self.end_persisted_array[triangle[0]].flatten()
                    xe2, ye2 = self.end_persisted_array[triangle[1]].flatten()
                    xe3, ye3 = self.end_persisted_array[triangle[2]].flatten()
                    tri_s.append(QPointF(xs1,ys1))
                    tri_s.append(QPointF(xs2,ys2))
                    tri_s.append(QPointF(xs3,ys3))

                    tri_e.append(QPointF(xe1,ye1))
                    tri_e.append(QPointF(xe2,ye2))
                    tri_e.append(QPointF(xe3,ye3))

                    self.start_scene.addPolygon(tri_s, pen_LBlue, brush_LBlue)
                    self.end_scene.addPolygon(tri_e, pen_LBlue, brush_LBlue)
            except:
                pass

        #####################END OF DEALING WITH PERSISTED################

        #Mouse-press detected
        self.graphicStartImg.setEnabled(True)
        self.start_scene.mousePressEvent = self.getStartPos
        self.end_scene.mousePressEvent = self.getEndPos

        if(len(self.start_readIn) != len(self.end_readIn)):
            if(self.start_count > 1):
                self.Persist_Prev_Pair()
                # del self.start_readIn[-1]
                # print("Do you even, bro?!?!?!?!!")
                # self.start_persisted.append((self.start_readIn[-1][0], self.start_readIn[-1][1]))
                # self.end_persisted.append((self.end_readIn[-1][0], self.end_readIn[-1][1]))
                # self.endOK_flag == 1

        # #READ-IN POINTS
        # if(len(self.start_readIn) != 0):
        #     self.start_readIn_array = np.array(self.start_readIn)
        #     self.end_readIn_array = np.array(self.end_readIn)
        #     print("Start read-in array:")
        #     print(self.start_readIn_array)
        #     print("End read-in array:")
        #     print(self.end_readIn_array)
        #
        #     #Plotting Points
        #     for i in range(len(self.start_readIn)):
        #         self.start_scene.addEllipse(self.start_readIn_array[i, 0]-5 ,self.start_readIn_array[i, 1]-5 , 10 , 10, pen_violet, brush_violet)
        #     # self.start_scene.addEllipse(self.temp_start_x-3.5, self.temp_start_y-3.5, 10, 10, pen2, brush2)     (self.start_readIn[-1][0], self.start_readIn[-1][1])
        #
        #     self.start_scene.addEllipse(self.start_readIn[-1][0]-5, self.start_readIn[-1][1]-5, 10, 10, pen_orange, brush_orange)
        #     self.graphicStartImg.setScene(self.start_scene)
        #     self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
        #
        #
        #     for i in range(len(self.end_readIn_array)):
        #         self.end_scene.addEllipse(self.end_readIn_array[i, 0]-5 ,self.end_readIn_array[i, 1]-5 , 10 , 10, pen_violet, brush_violet)
        #
        #     self.end_scene.addEllipse(self.temp_end_x-5, self.temp_end_y-5, 10, 10, pen_orange, brush_orange)
        #     self.graphicEndImg.setScene(self.end_scene)
        #     self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
        #
        #
        #     #Drawing Lines
        #     try:
        #         self.start_tri = Delaunay(self.start_readIn_array)
        #         # brush = QBrush()
        #         # pen = QPen()
        #         # pen.setColor(QColor(0,191,255))
        #         # brush.setColor(QColor(0,191,255))
        #         for triangle in (self.start_tri.simplices):
        #             tri_s2 = QPolygonF()
        #             tri_e2 = QPolygonF()
        #             # print(triangle)
        #             xs1_2, ys1_2 = self.start_readIn_array[triangle[0]].flatten()
        #             xs2_2, ys2_2 = self.start_readIn_array[triangle[1]].flatten()
        #             xs3_2, ys3_2 = self.start_readIn_array[triangle[2]].flatten()
        #
        #             try:
        #                 xe1_2, ye1_2 = self.end_readIn_array[triangle[0]].flatten()
        #                 xe2_2, ye2_2 = self.end_readIn_array[triangle[1]].flatten()
        #                 xe3_2, ye3_2 = self.end_readIn_array[triangle[2]].flatten()
        #             except:
        #                 pass
        #
        #             finally:
        #                 tri_s2.append(QPointF(xs1_2,ys1_2))
        #                 tri_s2.append(QPointF(xs2_2,ys2_2))
        #                 tri_s2.append(QPointF(xs3_2,ys3_2))
        #
        #                 tri_e2.append(QPointF(xe1_2,ye1_2))
        #                 tri_e2.append(QPointF(xe2_2,ye2_2))
        #                 tri_e2.append(QPointF(xe3_2,ye3_2))
        #
        #                 self.start_scene.addPolygon(tri_s, pen_LBlue, brush_LBlue)
        #                 self.end_scene.addPolygon(tri_e, pen_LBlue, brush_LBlue)
        #     except:
        #         pass
        # #####################END OF DEALING WITH READ-IN################


    def ClearDelaunay(self):

        print("In Clear Delaunay")


        #For Start Image
        self.start_scene = QGraphicsScene()
        self.start_pixMap = QPixmap(self.start_filePath)
        self.start_scene.addPixmap(self.start_pixMap)

        #For Start Image
        self.start_scene = QGraphicsScene()
        self.start_pixMap = QPixmap(self.start_filePath)
        self.start_scene.addPixmap(self.start_pixMap)
        self.start_pts = _loadPoints(self.start_points_fname)

        #GREEN --- For non-okay-ed
        brush_green = QBrush()
        pen_green = QPen()
        pen_green.setColor(QColor(0,255,0))
        brush_green.setColor(QColor(0,255,0))
        brush_green.setStyle(Qt.SolidPattern)

        #VIOLET ---- For newly persisted
        brush_violet = QBrush()
        pen_violet = QPen()
        pen_violet.setColor(QColor(138, 43, 226))
        brush_violet.setColor(QColor(138, 43, 226))
        brush_violet.setStyle(Qt.SolidPattern)

        #ORANGE --- For errors/suspicious points
        brush_orange = QBrush()
        pen_orange = QPen()
        pen_orange.setColor(QColor(255, 165, 0))
        brush_orange.setColor(QColor(255, 165, 0))
        brush_orange.setStyle(Qt.SolidPattern)

        #RED --- For previously existing
        brush = QBrush()
        pen = QPen()
        pen.setColor(QColor(255,0,0))
        brush.setColor(QColor(255,0,0))
        brush.setStyle(Qt.SolidPattern)

        #GREEN --- For selected but NOT persisted points
        brush_green = QBrush()
        pen_green = QPen()
        pen_green.setColor(QColor(0,255,0))
        brush_green.setColor(QColor(0,255,0))
        brush_green.setStyle(Qt.SolidPattern)

        #For previously existing points
        if(len(self.start_pts) != 0):
            for i in range(len(self.start_pts)):
                self.start_scene.addEllipse(self.start_pts[i, 0]-5 ,self.start_pts[i, 1]-5 , 10 , 10, pen, brush)

            self.graphicStartImg.setScene(self.start_scene)
            self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

        # for i in range(len(self.end_pts)):
        #
        #     self.end_scene.addEllipse(self.end_pts[i, 0]-5 ,self.end_pts[i, 1]-5 , 10 , 10, pen, brush)
        # self.graphicEndImg.setScene(self.end_scene)
        # self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe


        #For new points
        if(len(self.start_persisted) != 0) or (len(self.start_readIn) != 0):
            if(self.endOK_flag == 1):
                #Persisted Points
                if(len(self.start_persisted) != 0):
                    self.start_persisted_array = np.array(self.start_persisted)
                    for i in range(len(self.start_persisted_array)):

                        self.start_scene.addEllipse(self.start_persisted_array[i, 0]-5 ,self.start_persisted_array[i, 1]-5 , 10 , 10, pen_violet, brush_violet)
                    self.graphicStartImg.setScene(self.start_scene)
                    self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
                else:
                    pass

            elif(self.endOK_flag == 0):
                #Points in Read-In List
                if(len(self.start_readIn) != 0):
                    self.start_readIn_array = np.array(self.start_readIn)
                    for i in range(len(self.start_readIn_array)):

                        self.start_scene.addEllipse(self.start_readIn_array[i, 0]-5 ,self.start_readIn_array[i, 1]-5 , 10 , 10, pen_violet, brush_violet)
                    # self.start_scene.addEllipse(self.temp_start_x-5, self.temp_start_y-5, 10, 10, pen_green, brush_green)     (self.start_readIn[-1][0], self.start_readIn[-1][1])

                    # self.start_scene.addEllipse(self.start_readIn[-1][0]-5, self.start_readIn[-1][1]-5, 10, 10, pen_orange, brush_orange)  #####################Start Scene is Ok (For now) #########################
                    self.start_scene.addEllipse(self.start_readIn[-1][0]-5, self.start_readIn[-1][1]-5, 10, 10, pen_green, brush_green)

                    self.graphicStartImg.setScene(self.start_scene)
                    self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
                else:
                    pass

            else:
                pass
        else:
            pass


        #For End Image
        self.end_scene = QGraphicsScene()
        self.end_pixMap = QPixmap(self.end_filePath)
        self.end_scene.addPixmap(self.end_pixMap)

        #For End Image
        self.end_scene = QGraphicsScene()
        self.end_pixMap = QPixmap(self.end_filePath)
        self.end_scene.addPixmap(self.end_pixMap)

        self.end_pts = _loadPoints(self.end_points_fname)

        #For already existing points
        if(len(self.end_pts) != 0):
            for i in range(len(self.end_pts)):
                brush = QBrush()
                pen = QPen()
                pen.setColor(QColor(255,0,0))
                brush.setColor(QColor(255,0,0))
                brush.setStyle(Qt.SolidPattern)
                self.end_scene.addEllipse(self.end_pts[i, 0]-5 ,self.end_pts[i, 1]-5 , 10 , 10, pen, brush)
            self.graphicEndImg.setScene(self.end_scene)
            self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

        #For new points
        if(len(self.end_persisted) != 0) or (len(self.end_readIn) != 0):

            if(self.endOK_flag == 1):
                #For persisted points
                if(len(self.end_persisted) != 0):
                    self.end_persisted_array = np.array(self.end_persisted)
                    for i in range(len(self.end_persisted_array)):

                        self.end_scene.addEllipse(self.end_persisted_array[i, 0]-5 ,self.end_persisted_array[i, 1]-5 , 10 , 10, pen_violet, brush_violet)
                    self.graphicEndImg.setScene(self.end_scene)
                    self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
                else:
                    pass

            elif(self.endOK_flag == 0):
                #For points in Read-In List
                if(len(self.end_readIn) != 0):
                    self.end_readIn_array = np.array(self.end_readIn)
                    for i in range(len(self.end_readIn_array)):

                        self.end_scene.addEllipse(self.end_readIn_array[i, 0]-5 ,self.end_readIn_array[i, 1]-5 , 10 , 10, pen_violet, brush_violet)


                    if(len(self.start_readIn) == (len(self.end_readIn))):
                        # self.end_scene.addEllipse(self.temp_end_x-5, self.temp_end_y-5, 10, 10, pen_orange, brush_orange)   ##################Should be okay for endPoint as well###########
                        self.end_scene.addEllipse(self.temp_end_x-5, self.temp_end_y-5, 10, 10, pen_green, brush_green)
                    else:
                        pass

                    print("I am the suspicious one in End Image:")
                    print((self.temp_end_x, self.temp_end_y))
                    self.graphicEndImg.setScene(self.end_scene)
                    self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

                else:
                    pass
        else:
            pass





    def Start_ClearDelaunay(self):
        #For Start Image
        self.start_scene = QGraphicsScene()
        self.start_pixMap = QPixmap(self.start_filePath)
        self.start_scene.addPixmap(self.start_pixMap)
        self.start_pts = _loadPoints(self.start_points_fname)

        brush2 = QBrush()
        pen2 = QPen()
        pen2.setColor(QColor(0,255,0))
        brush2.setColor(QColor(0,255,0))
        brush2.setStyle(Qt.SolidPattern)
        for i in range(len(self.start_pts)):
            brush = QBrush()
            pen = QPen()
            pen.setColor(QColor(255,0,0))
            brush.setColor(QColor(255,0,0))
            brush.setStyle(Qt.SolidPattern)
            self.start_scene.addEllipse(self.start_pts[i, 0]-5 ,self.start_pts[i, 1]-5 , 10 , 10, pen, brush)

        # if(self.also_final_record_flag == 1):
        # if((self.start_img_x != self.start_item_list[-1].x())and(self.start_img_y != self.start_item_list[-1].y())):

        if(len(self.recorded_start_item_list) == 0):
            self.start_scene.addEllipse(self.start_img_x-7 ,self.start_img_y-7 , 14 , 14, pen2, brush2)
            self.graphicStartImg.setScene(self.start_scene)
            self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
        else:
            if((self.start_img_x == self.recorded_start_item_list[-1].x())and(self.start_img_y == self.recorded_start_item_list[-1].y())):
                self.graphicStartImg.setScene(self.start_scene)
                self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

            else:
                self.start_scene.addEllipse(self.start_img_x-7 ,self.start_img_y-7 , 14 , 14, pen2, brush2)
                self.graphicStartImg.setScene(self.start_scene)
                self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe



        # #Displaying points
        # self.start_scene = QGraphicsScene()
        # self.start_pixMap = QPixmap(self.start_filePath)
        #
        # self.start_img = _loadImage(self.start_filePath)
        #
        # self.start_pts = _loadPoints(self.start_points_fname)
        # brush2 = QBrush()
        # pen2 = QPen()
        # pen2.setColor(QColor(0,255,0))
        # brush2.setColor(QColor(0,255,0))
        # brush2.setStyle(Qt.SolidPattern)
        #
        #
        # self.start_scene.addPixmap(self.start_pixMap)
        # for i in range(len(self.start_pts)):
        #     brush = QBrush()
        #     pen = QPen()
        #     pen.setColor(QColor(0,0,255))
        #     brush.setColor(QColor(0,0,255))
        #     brush.setStyle(Qt.SolidPattern)
        #     self.start_scene.addEllipse(self.start_pts[i, 0]-5 ,self.start_pts[i, 1]-5 , 7 , 7, pen, brush)
        #
        # self.start_scene.addEllipse(self.start_img_x-7 ,self.start_img_y-7 , 14 , 14, pen2, brush2)
        # self.graphicStartImg.setScene(self.start_scene)
        # self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
        # print(self.graphicStartImg.isEnabled())
        # # self.ResetWidgets()

        # #Displaying points
        # brush = QBrush()
        # pen = QPen()
        # pen.setColor(QColor(0,255,0))
        # brush.setColor(QColor(0,255,0))
        # brush.setStyle(Qt.SolidPattern)
        # # self.after_start_green.addEllipse(self.start_img_x-7 ,self.start_img_y-7 , 14 , 14, pen, brush)
        # self.after_start_green.addEllipse(self.start_item_list[-1].x()-7 ,self.start_item_list[-1].y()-7 , 14 , 14, pen, brush)
        # self.graphicStartImg.setScene(self.after_start_green)
        # self.graphicStartImg.fitInView(self.after_start_green.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
        # print(self.graphicStartImg.isEnabled())
        # # self.ResetWidgets()


    def End_ClearDelaunay(self):
        brush2 = QBrush()
        pen2 = QPen()
        pen2.setColor(QColor(0,255,0))
        brush2.setColor(QColor(0,255,0))
        brush2.setStyle(Qt.SolidPattern)
        self.end_scene = QGraphicsScene()
        self.end_pixMap = QPixmap(self.end_filePath)
        self.end_scene.addPixmap(self.end_pixMap)
        self.end_pts = _loadPoints(self.end_points_fname)
        for i in range(len(self.start_pts)):
            brush = QBrush()
            pen = QPen()
            pen.setColor(QColor(255,0,0))
            brush.setColor(QColor(255,0,0))
            brush.setStyle(Qt.SolidPattern)
            self.end_scene.addEllipse(self.end_pts[i, 0]-5 ,self.end_pts[i, 1]-5 , 10 , 10, pen, brush)

        # if(self.also_final_record_flag == 1):
        # if((self.end_img_x != self.end_item_list[-1].x())and(self.end_img_y != self.end_item_list[-1].y())):
        if(len(self.recorded_end_item_list) == 0):
            self.end_scene.addEllipse(self.end_img_x-7 ,self.end_img_y-7 , 14 , 14, pen2, brush2)
            self.graphicEndImg.setScene(self.end_scene)
            self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

        else:
            if((self.end_img_x == self.recorded_end_item_list[-1].x())and(self.end_img_y == self.recorded_end_item_list[-1].y())):
                self.graphicEndImg.setScene(self.end_scene)
                self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

            else:
                self.end_scene.addEllipse(self.end_img_x-7 ,self.end_img_y-7 , 14 , 14, pen2, brush2)
                self.graphicEndImg.setScene(self.end_scene)
                self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe



        # #Displaying points
        # self.end_scene = QGraphicsScene()
        # self.end_pixMap = QPixmap(self.end_filePath)
        #
        # self.end_img = _loadImage(self.end_filePath)
        #
        # self.end_pts = _loadPoints(self.end_points_fname)
        # brush2 = QBrush()
        # pen2 = QPen()
        # pen2.setColor(QColor(0,255,0))
        # brush2.setColor(QColor(0,255,0))
        # brush2.setStyle(Qt.SolidPattern)
        #
        # self.end_scene.addPixmap(self.end_pixMap)
        # for i in range(len(self.end_pts)):
        #     brush = QBrush()
        #     pen = QPen()
        #     pen.setColor(QColor(0,0,255))
        #     brush.setColor(QColor(0,0,255))
        #     brush.setStyle(Qt.SolidPattern)
        #     self.end_scene.addEllipse(self.end_pts[i, 0]-5 ,self.end_pts[i, 1]-5 , 7 , 7, pen, brush)
        #
        # self.end_scene.addEllipse(self.end_img_x-7 ,self.end_img_y-7 , 14 , 14, pen2, brush2)
        # self.graphicEndImg.setScene(self.end_scene)
        # self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
        # print(self.graphicEndImg.isEnabled())
        # # self.ResetWidgets()


        # brush = QBrush()
        # pen = QPen()
        # pen.setColor(QColor(0,255,0))
        # brush.setColor(QColor(0,255,0))
        # brush.setStyle(Qt.SolidPattern)
        # # self.after_end_green.addEllipse(self.end_img_x-7 ,self.end_img_y-7 , 14 , 14, pen, brush)
        # self.after_end_green.addEllipse(self.end_item_list[-1].x()-7 ,self.end_item_list[-1].y()-7 , 14 , 14, pen, brush)
        # self.graphicEndImg.setScene(self.after_end_green)
        # self.graphicEndImg.fitInView(self.after_end_green.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
        # print(self.graphicEndImg.isEnabled())


    def EnableInitiallyDisabledWidgies(self):
        if(self.img_flag >= 2):
            self.sldrAlpha.setEnabled(True)
            self.txtAlphaVal.setEnabled(True)
            self.txtAlphaVal.setText(str(self.sldrAlpha.value()))
            self.btnBlend.setEnabled(True)
        else:
            pass

    def getAlphaValue(self):
        num_val = self.sldrAlpha.value()
        self.alpha_val = num_val/100
        self.txtAlphaVal.setText(str(self.alpha_val))


    def getBlendedImage(self):
        blended_img_array = Morphing.Blender(self.start_img,self.start_pts,self.end_img,self.end_pts).getBlendedImage(self.alpha_val)
        alpha_percent = int(self.alpha_val*100)
        temp_img_name = 'Broken{:03d}'.format(alpha_percent)
        temp_img = temp_img_name+".jpg"
        _saveImage(blended_img_array, temp_img)

        self.broken_scene = QGraphicsScene()
        self.broken_pixMap = QPixmap(temp_img)

        self.broken_img = _loadImage(temp_img)
        #self.broken_pts = _loadPoints(points_fname)
        self.broken_scene.addPixmap(self.broken_pixMap)

        self.graphicBlendImg.setScene(self.broken_scene)
        self.graphicBlendImg.fitInView(self.broken_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

    def Also_getStartPoints(self):
        self.start_scene.mousePressEvent = self.getStartPos

    def Also_getEndPoints(self):
        self.graphicEndImg.setEnabled(False)

        self.end_scene.mousePressEvent = self.getEndPos
        #
        # #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        # if((self.do_nothing_flag == 1)and((self.mainWindow_flag != 1)or(self.start_count==0))):
        #     self.do_nothing_flag = 0
        #     del self.start_item_list[-1]
        #     del self.end_item_list[-1]
        #     pass


        self.HL1_2.mousePressEvent = self.SetMainWindowFlag
        self.HL2_2.mousePressEvent = self.SetMainWindowFlag
        self.HL3_2.mousePressEvent = self.SetMainWindowFlag
        self.HL4_2.mousePressEvent = self.SetMainWindowFlag
        self.HL5_2.mousePressEvent = self.SetMainWindowFlag
        self.HL6_2.mousePressEvent = self.SetMainWindowFlag
        self.HL7_2.mousePressEvent = self.SetMainWindowFlag
        self.HL8_2.mousePressEvent = self.SetMainWindowFlag
        self.HL9_2.mousePressEvent = self.SetMainWindowFlag
        self.HL10_2.mousePressEvent = self.SetMainWindowFlag
        self.HL11_2.mousePressEvent = self.SetMainWindowFlag
        self.HL12_2.mousePressEvent = self.SetMainWindowFlag
        self.HL13_2.mousePressEvent = self.SetMainWindowFlag
        self.HL14_2.mousePressEvent = self.SetMainWindowFlag
        self.HL15_2.mousePressEvent = self.SetMainWindowFlag
        self.VL1_2.mousePressEvent = self.SetMainWindowFlag
        self.VL2_2.mousePressEvent = self.SetMainWindowFlag
        self.VL3_2.mousePressEvent = self.SetMainWindowFlag
        self.VL4_2.mousePressEvent = self.SetMainWindowFlag
        self.VL5_2.mousePressEvent = self.SetMainWindowFlag
        self.VL6_2.mousePressEvent = self.SetMainWindowFlag
        self.VL7_2.mousePressEvent = self.SetMainWindowFlag
        self.VL8_2.mousePressEvent = self.SetMainWindowFlag
        self.VL9_2.mousePressEvent = self.SetMainWindowFlag


    def getStartPoints(self):
        self.start_points_fname = self.start_filePath+'.txt'
        self.start_scene = QGraphicsScene()
        print(self.start_filePath)
        self.start_pixMap = QPixmap(self.start_filePath)
        self.start_scene.addPixmap(self.start_pixMap)
        self.start_img = _loadImage(self.start_filePath)
        self.graphicStartImg.setScene(self.start_scene)
        self.graphicStartImg.fitInView(self.start_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe
        self.start_scene.mousePressEvent = self.getStartPos

        # if(self.start_count == 0):
        #     self.start_scene.mousePressEvent = self.getStartPos

        # self.start_scene.mousePressEvent = self.set_inStartWidget


    def SetMainWindowFlag(self, event):
        self.mainWindow_flag = 1
        self.EndPointOK()


    def getEndPoints(self):
        self.end_points_fname = self.end_filePath+'.txt'
        self.end_scene = QGraphicsScene()
        print(self.end_filePath)
        self.end_pixMap = QPixmap(self.end_filePath)
        self.end_scene.addPixmap(self.end_pixMap)
        self.end_img = _loadImage(self.end_filePath)
        self.graphicEndImg.setScene(self.end_scene)
        self.graphicEndImg.fitInView(self.end_scene.itemsBoundingRect(), Qt.KeepAspectRatio) #Maybe

        self.graphicEndImg.setEnabled(False)

        self.end_scene.mousePressEvent = self.getEndPos

        # self.chkShowTri.stateChanged.connect(self.SetDoNothingFlag())
        #
        # #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        # if((self.do_nothing_flag == 1)and((self.mainWindow_flag != 1)or(self.start_count==0))):
        #     self.do_nothing_flag = 0
        #     del self.start_item_list[-1]
        #     del self.end_item_list[-1]
        #     pass


        self.HL1_2.mousePressEvent = self.SetMainWindowFlag
        self.HL2_2.mousePressEvent = self.SetMainWindowFlag
        self.HL3_2.mousePressEvent = self.SetMainWindowFlag
        self.HL4_2.mousePressEvent = self.SetMainWindowFlag
        self.HL5_2.mousePressEvent = self.SetMainWindowFlag
        self.HL6_2.mousePressEvent = self.SetMainWindowFlag
        self.HL7_2.mousePressEvent = self.SetMainWindowFlag
        self.HL8_2.mousePressEvent = self.SetMainWindowFlag
        self.HL9_2.mousePressEvent = self.SetMainWindowFlag
        self.HL10_2.mousePressEvent = self.SetMainWindowFlag
        self.HL11_2.mousePressEvent = self.SetMainWindowFlag
        self.HL12_2.mousePressEvent = self.SetMainWindowFlag
        self.HL13_2.mousePressEvent = self.SetMainWindowFlag
        self.HL14_2.mousePressEvent = self.SetMainWindowFlag
        self.HL15_2.mousePressEvent = self.SetMainWindowFlag
        self.VL1_2.mousePressEvent = self.SetMainWindowFlag
        self.VL2_2.mousePressEvent = self.SetMainWindowFlag
        self.VL3_2.mousePressEvent = self.SetMainWindowFlag
        self.VL4_2.mousePressEvent = self.SetMainWindowFlag
        self.VL5_2.mousePressEvent = self.SetMainWindowFlag
        self.VL6_2.mousePressEvent = self.SetMainWindowFlag
        self.VL7_2.mousePressEvent = self.SetMainWindowFlag
        self.VL8_2.mousePressEvent = self.SetMainWindowFlag
        self.VL9_2.mousePressEvent = self.SetMainWindowFlag

        # self.mousePressEvent = self.checkWidget


    def checkWidget(self, event):
        if(self.end_scene.mousePressEvent()) or (self.start_scene.mousePressEvent()):
            pass
        else:
            self.SetMainWindowFlag()



    def getStartPos(self, event):
        if(self.graphicStartImg.isEnabled() != 'False'):
            print("Hi, Start! I'm here")
            self.start_count = self.start_count + 1
            self.start_flag = 1
            self.start_bkspcFlag = 1
            print("start_count:")
            print(self.start_count)
            position = event.scenePos()
            print(position)
            self.start_item_list.append(position)
            self.final_record_flag = 0
            self.also_final_record_flag = 0
            # print(position.x())
            self.start_img_x = position.x()
            self.start_img_y = position.y()

            self.start_readIn.append((position.x(),position.y()))
            # start_ptobj = _POINT(position.x(), position.y(), 0)
            # self.start_readIn_POINTObj.append(start_ptobj)
            # self.start_currReadIn_ptonj = self.start_readIn_POINTObj[-1]

            self.endOK_flag = 0

            # if(len(self.start_readIn_POINTObj) == 1):
            #     self.start_temp_ptobj = self.start_currReadIn_ptonj
            # else:
            #     self.start_temp_ptobj = self.start_readIn_POINTObj[-2]
            #
            # if((self.start_temp_ptobj.ok == 0) and (self.start_currReadIn_ptonj.ok == 0)):
            #     # del self.start_readIn_POINTObj[-1]
            #     # del self.start_readIn[-1]
            #     self.start_readIn_POINTObj[-1] = self.start_temp_ptobj
            #     self.start_readIn[-1] = (self.start_temp_ptobj.x, self.start_temp_ptobj.y)
            #     self.start_currReadIn_ptonj = self.start_readIn_POINTObj[-1]


            #ALEX'S IDEA:
            self.temp_start_x = position.x()
            self.temp_start_y = position.y()
            # self.start_temp_hasChanged = 1
            # if(self.start_temp_hasChanged == 1):
            #     self.endOK_flag = 0
            # else:
            #     self.endOK_flag = 1

            # if(self.start_count == 1):
            #     self.Start_ColourPosGreen()
            # else:
            #     self.StartPointOK()
            self.Start_ColourPosGreen()

    def Start_ColourPosGreen(self):
        brush = QBrush()
        pen = QPen()
        pen.setColor(QColor(0,255,0))
        brush.setColor(QColor(0,255,0))
        brush.setStyle(Qt.SolidPattern)
        # self.start_scene.addEllipse(self.start_img_x-7 ,self.start_img_y-7 , 14 , 14, pen, brush) #Interchange x & y when writing to txt file????
        # self.start_scene.addEllipse(self.start_currReadIn_ptonj.x-7 ,self.start_currReadIn_ptonj.y-7 , 14 , 14, pen, brush) #Interchange x & y when writing to txt file????
        self.start_scene.addEllipse(self.temp_start_x-7 ,self.temp_start_y-7 , 14 , 14, pen, brush)

        self.after_start_green = self.start_scene #Saving scene after green dots



        self.graphicEndImg.setEnabled(True)
        print("start_count:")
        print(self.start_count)
        self.StartPointOK()


    def EndPointOK_StartPress(self, event):
        brush = QBrush()
        pen = QPen()
        pen.setColor(QColor(0,0,255))
        brush.setColor(QColor(0,0,255))
        brush.setStyle(Qt.SolidPattern)
        if(self.start_flag == 1):
            if(self.end_flag == 1):

                # if(self.chkShowTri.stateChanged.connect(self.DoNothing)):
                #     pass

                #add "else:" ?????????????????????
                if(self.start_count > 0):
                    self.endOK_flag = 1
                    print(self.end_item_list)
                    self.graphicEndImg.setEnabled(False)
                    self.end_bkspcFlag = 0

                    # print(self.end_item_list)
                    # print(self.start_item_list[-1])
                    # print(self.end_item_list[-1])
                    # self.start_scene.addEllipse(self.start_item_list[-1].x()-7 ,self.start_item_list[-1].y()-7 , 14 , 14, pen, brush)
                    # self.end_scene.addEllipse(self.end_item_list[-1].x()-7 ,self.end_item_list[-1].y()-7 , 14 , 14, pen, brush)

                    self.start_scene.addEllipse(self.temp_start_x-7 ,self.temp_start_y-7 , 14 , 14, pen, brush)
                    self.end_scene.addEllipse(self.temp_end_x-7 ,self.temp_end_y-7 , 14 , 14, pen, brush)

                    if((self.corr_starttext_exists == 1) or (self.corr_endtext_exists == 1)):
                        print("I'm being responsible.")
                        print(self.corr_endtext_exists)
                        print(self.corr_starttext_exists)
                        self.Also_Record_Correspondences()
                    else:
                        print("I'm being an idiot.")
                        print(self.corr_endtext_exists)
                        print(self.corr_starttext_exists)
                        self.Record_Correspondences()
                else:
                    pass

    def SetDoNothingFlag(self):
        self.do_nothing_flag = 1


    def EndPointOK(self):
        #BLUE --- Colour of the Persisted
        brush_Blue = QBrush()
        pen_Blue = QPen()
        pen_Blue.setColor(QColor(0,0,255))
        brush_Blue.setColor(QColor(0,0,255))

        brush_Blue.setStyle(Qt.SolidPattern)
        if(self.start_flag == 1):
            if(self.end_flag == 1):
                # if(self.chkShowTri.stateChanged.connect(self.DoNothing)):
                #     pass

                #add "else:" ?????????????????????
                if((self.mainWindow_flag == 1) or (self.start_count > 1)):
                    self.endOK_flag = 1
                    print(self.end_item_list)
                    self.graphicEndImg.setEnabled(False)
                    self.end_bkspcFlag = 0

                    if((self.start_count > 1)and(self.persist_PrevPairFlag == 1)):
                        self.start_scene.addEllipse(self.start_readIn[-2][0]-7 ,self.start_readIn[-2][1]-7 , 14 , 14, pen_Blue, brush_Blue)
                        self.end_scene.addEllipse(self.end_readIn[-1][0]-7 ,self.end_readIn[-1][1]-7 , 14 , 14, pen_Blue, brush_Blue)

                    elif((self.start_count > 1)and(self.mainWindow_flag == 0)):
                        self.start_scene.addEllipse(self.start_readIn[-2][0]-7 ,self.start_readIn[-2][1]-7 , 14 , 14, pen_Blue, brush_Blue)
                        # self.end_scene.addEllipse(self.end_readIn[-2][0]-7 ,self.end_readIn[-2][1]-7 , 14 , 14, pen_Blue, brush_Blue)
                        self.end_scene.addEllipse(self.end_readIn[-1][0]-7 ,self.end_readIn[-1][1]-7 , 14 , 14, pen_Blue, brush_Blue)

                    else:
                        self.start_scene.addEllipse(self.temp_start_x-7 ,self.temp_start_y-7 , 14 , 14, pen_Blue, brush_Blue)
                        self.end_scene.addEllipse(self.temp_end_x-7 ,self.temp_end_y-7 , 14 , 14, pen_Blue, brush_Blue)

                    if((self.corr_starttext_exists == 1) or (self.corr_endtext_exists == 1)):
                        print("I'm being responsible.")
                        print(self.corr_endtext_exists)
                        print(self.corr_starttext_exists)
                        self.Also_Record_Correspondences()
                    else:
                        print("I'm being an idiot.")
                        print(self.corr_endtext_exists)
                        print(self.corr_starttext_exists)
                        self.Record_Correspondences()
                else:
                    pass

    def StartPointOK(self):


            if((self.start_flag == 1)):
                if(self.start_count <= 1):
                    if(self.end_flag != 1):
                        print(self.start_item_list)
                        self.graphicStartImg.setEnabled(False)
                        # self.start_bkspcFlag = 0
                        # self.start_bkspcFlag = 1
                        print(self.graphicStartImg.isEnabled())
                        print("set enabled off")
                    else:
                        self.start_bkspcFlag = 0
                        #disabling end graphicview
                        self.graphicEndImg.setEnabled(False)
                        #MIGHT HAVE TO REMOVE THE FOLL!!!! :   (NO, I'M GOOD! :D)
                        if(self.start_count > 0):
                            self.graphicStartImg.setEnabled(True)
                            # if(self.start_count > 1):
                            #     self.EndPointOK()
                            # else:
                            #     self.start_scene.mousePressEvent = self.EndPointOK_StartPress
                elif(self.start_count > 1):
                    if(self.end_flag == 1):
                        self.graphicStartImg.setEnabled(False)
                        self.graphicEndImg.setEnabled(True)
                        self.start_bkspcFlag = 1
                        self.Persist_Prev_Pair()
                    else:
                        pass
                else:
                    pass

            else:
                # self.start_bkspcFlag = 1
                self.start_bkspcFlag = 0

    def Persist_Prev_Pair(self):
        self.persist_PrevPairFlag = 1
        self.EndPointOK()
        # self.Start_ColourPosGreen()



    def StartPointNotOK(self):
        self.ResetWidgets()

    def getEndPos(self, event):
        print("Hi, End! I'm here")

        position = event.scenePos()
        print(position)
        self.end_item_list.append(position)
        self.final_record_flag = 0
        self.also_final_record_flag = 0

        # self.chkShowTri.stateChanged.connect(self.SetDoNothingFlag)
        #
        # #AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
        # if((self.do_nothing_flag == 1)and((self.mainWindow_flag != 1)or(self.start_count==0))):
        #     # self.do_nothing_flag = 0
        #     del self.start_item_list[-1]
        #     del self.end_item_list[-1]
        #     pass
        # print(position.x())

        self.end_img_x = position.x()
        self.end_img_y = position.y()
        self.end_bkspcFlag = 1


        self.end_readIn.append((position.x(),position.y()))

        # end_ptobj = _POINT(position.x(), position.y(), 0)
        # self.end_readIn_POINTObj.append(end_ptobj)
        # self.end_currReadIn_ptonj = self.end_readIn_POINTObj[-1]
        #
        self.endOK_flag = 0
        #
        # if(len(self.end_readIn_POINTObj) == 1):
        #     self.end_temp_ptobj = self.end_currReadIn_ptonj
        # else:
        #     self.end_temp_ptobj = self.end_readIn_POINTObj[-2]
        #
        # if((self.end_temp_ptobj.ok == 0) and (self.end_currReadIn_ptonj.ok == 0)):
        #     # del self.end_readIn_POINTObj[-1]
        #     # del self.end_readIn[-1]
        #     self.end_readIn_POINTObj[-1] = self.end_temp_ptobj
        #     self.end_readIn[-1] = (self.end_temp_ptobj.x, self.end_temp_ptobj.y)
        #     self.end_currReadIn_ptonj = self.end_readIn_POINTObj[-1]

        #ALEX'S IDEA:
        self.temp_end_x = position.x()
        self.temp_end_y = position.y()
        # self.end_temp_hasChanged = 1
        # if(self.end_temp_hasChanged == 1):
        #     self.endOK_flag = 0
        # else:
        #     self.endOK_flag = 1

        self.End_ColourPosGreen()

    def End_ColourPosGreen(self):

        brush = QBrush()
        pen = QPen()
        pen.setColor(QColor(0,255,0))
        brush.setColor(QColor(0,255,0))
        brush.setStyle(Qt.SolidPattern)
        # self.end_scene.addEllipse(self.end_img_x-7 ,self.end_img_y-7 , 14 , 14, pen, brush) #Interchange x & y when writing to txt file????
        # self.end_scene.addEllipse(self.end_currReadIn_ptonj.x-7 ,self.end_currReadIn_ptonj.y-7 , 14 , 14, pen, brush)

        self.end_scene.addEllipse(self.temp_end_x-7 ,self.temp_end_y-7 , 14 , 14, pen, brush)

        self.after_end_green = self.end_scene #Saving scene after green dots

        self.end_flag = 1
        self.StartPointOK()
        # if(self.do_nothing_flag != 1):
        #     self.StartPointOK()
        # else:
        #     self.StartPointNotOK()


    def Record_Correspondences(self):
        self.final_record_flag = 1
        #Start Image Points

        if(self.endOK_flag == 1):
            #Store in persist
            # self.start_persisted.append(QPointF(self.temp_start_x, self.temp_start_y))

            self.start_persisted.append((self.temp_start_x, self.temp_start_y))

            # self.start_persisted.append((self.start_currReadIn_ptonj.x, self.start_currReadIn_ptonj.y))





        with open(self.start_points_fname, "a") as fs:
            si = self.start_persisted[-1]
            # fs.writelines(str(int(si.x()))+'\t'+str(int(si.y()))+'\n')
            fs.writelines(str(int(si[0]))+'\t'+str(int(si[1]))+'\n')





        #End Image Points
        if(self.endOK_flag == 1):
            #Store in persist
            # self.end_persisted.append(QPointF(self.temp_end_x, self.temp_end_y))


            self.end_persisted.append((self.temp_end_x, self.temp_end_y))

            # self.end_persisted.append((self.end_currReadIn_ptonj.x, self.end_currReadIn_ptonj.y))




        with open(self.end_points_fname, "a") as fe:
            ei = self.end_persisted[-1]
            # fe.writelines(str(int(ei.x()))+'\t'+str(int(ei.y()))+'\n')
            fe.writelines(str(int(ei[0]))+'\t'+str(int(ei[1]))+'\n')




        self.ResetWidgets()

    def Also_Record_Correspondences(self):
        self.also_recorded_flag = 1
        self.also_final_record_flag = 1


        #For start & end image
        if(self.endOK_flag == 1):
            #Store in persist
            # self.start_persisted.append(QPointF(self.temp_start_x, self.temp_start_y))
            if((self.start_count > 1)and(self.persist_PrevPairFlag == 1)):
                self.start_persisted.append((self.start_readIn[-2][0], self.start_readIn[-2][1]))
                self.end_persisted.append((self.end_readIn[-1][0], self.end_readIn[-1][1]))

            elif((self.start_count > 1)and(self.mainWindow_flag == 0)):
                self.start_persisted.append((self.start_readIn[-2][0], self.start_readIn[-2][1]))
                self.end_persisted.append((self.end_readIn[-1][0], self.end_readIn[-1][1]))
            else:
                self.start_persisted.append((self.temp_start_x, self.temp_start_y))
                self.end_persisted.append((self.temp_end_x, self.temp_end_y))

            # self.start_persisted.append((self.start_currReadIn_ptonj.x, self.start_currReadIn_ptonj.y))

        #For writing to file
        with open(self.start_points_fname, "a") as fs:
            si = self.start_persisted[-1]
            fs.writelines(str(int(si[0]))+'\t'+str(int(si[1]))+'\n')
            # fs.writelines(str(int(si.x()))+'\t'+str(int(si.y()))+'\n')
        with open(self.end_points_fname, "a") as fe:
            ei = self.end_persisted[-1]
            fe.writelines(str(int(ei[0]))+'\t'+str(int(ei[1]))+'\n')

        self.ResetWidgets()
        #For drawing Delaunay once point is persisted & check-box is checked
        if((self.endOK_Prev == 1)and(self.chkShowTri.isChecked() == True)):
            self.DrawDelaunay2()
            self.endOK_Prev = 0







    def StartEnd_CreateDelaunay(self):
        self.start_custom_pts = _loadPoints(self.start_points_fname)
        self.start_custom_tri = Delaunay(self.start_custom_pts)
        self.end_custom_pts = _loadPoints(self.end_points_fname)
        self.end_custom_tri = Delaunay(self.end_custom_pts)
        brush = QBrush()
        pen = QPen()
        pen.setColor(QColor(0,0,255))
        brush.setColor(QColor(0,0,255))
        for triangle in (self.start_custom_tri.simplices):
            tri_s = QPolygonF()
            tri_e = QPolygonF()
            # print(triangle)
            xs1, ys1 = self.start_custom_pts[triangle[0]].flatten()
            xs2, ys2 = self.start_custom_pts[triangle[1]].flatten()
            xs3, ys3 = self.start_custom_pts[triangle[2]].flatten()

            xe1, ye1 = self.end_custom_pts[triangle[0]].flatten()
            xe2, ye2 = self.end_custom_pts[triangle[1]].flatten()
            xe3, ye3 = self.end_custom_pts[triangle[2]].flatten()

            tri_s.append(QPointF(xs1,ys1))
            tri_s.append(QPointF(xs2,ys2))
            tri_s.append(QPointF(xs3,ys3))

            tri_e.append(QPointF(xe1,ye1))
            tri_e.append(QPointF(xe2,ye2))
            tri_e.append(QPointF(xe3,ye3))

            self.start_scene.addPolygon(tri_s, pen, brush)
            self.end_scene.addPolygon(tri_e, pen, brush)
        print(self.graphicStartImg.isEnabled())
        print(self.graphicEndImg.isEnabled())


    # def End_CreateDelaunay(self):
    #     self.end_custom_pts = _loadPoints(self.end_points_fname)
    #     self.end_custom_tri = Delaunay(self.end_custom_pts)
    #     brush = QBrush()
    #     pen = QPen()
    #     pen.setColor(QColor(0,0,255))
    #     brush.setColor(QColor(0,0,255))
    #     for triangle in (self.end_custom_tri.simplices):
    #         tri_e = QPolygonF()
    #         # print(triangle)
    #
    #         xe1, ye1 = self.end_custom_pts[triangle[0]].flatten()
    #         xe2, ye2 = self.end_custom_pts[triangle[1]].flatten()
    #         xe3, ye3 = self.end_custom_pts[triangle[2]].flatten()
    #
    #
    #         tri_e.append(QPointF(xe1,ye1))
    #         tri_e.append(QPointF(xe2,ye2))
    #         tri_e.append(QPointF(xe3,ye3))
    #
    #
    #         self.end_scene.addPolygon(tri_e, pen, brush)
    #
    #     print(self.graphicEndImg.isEnabled())

    def ResetWidgets(self):
        print("In Reset widgets")
        print(self.graphicStartImg.isEnabled())
        print(self.graphicEndImg.isEnabled())

        self.graphicStartImg.setEnabled(True)
        # self.graphicEndImg.setEnabled(True)
        #########
        if(self.start_count > 1):
            self.graphicEndImg.setEnabled(True)
        else:
            self.graphicEndImg.setEnabled(False)
        #########

        print(self.graphicStartImg.isEnabled())
        print(self.graphicEndImg.isEnabled())

        if(self.start_count > 1):
            self.start_flag = 1
            self.start_count = 1
            self.start_bkspcFlag = 1
            self.endOK_Prev = self.endOK_flag
            self.endOK_flag = 0
        else:
            if(self.mainWindow_flag == 1):
                self.endOK_Prev = self.endOK_flag

            self.start_bkspcFlag = 0
            self.end_bkspcFlag = 0
            self.start_flag = 0
            self.end_flag = 0
            self.mainWindow_flag = 0
            self.do_nothing_flag = 0
            self.start_count = 0
            self.start_scene.mousePressEvent = self.getStartPos
            self.start_temp_hasChanged = 0
            self.end_temp_hasChanged = 0
            self.persist_PrevPairFlag = 0
        # self.endOK_flag = 0



    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Backspace):
            print("Backspace")

        if(self.start_bkspcFlag == 1):
            print("Deleting Start")
            #Enabling image
            self.graphicStartImg.setEnabled(True)
            self.start_bkspcFlag = 0
            self.start_count = self.start_count - 1
            #item = self.start_scene.items()[0]
            item = self.start_scene.itemAt(self.start_img_x, self.start_img_y)
            self.start_scene.removeItem(item)
            del self.start_item_list[-1]
            del self.start_readIn[-1]
            try:
                self.temp_start_x = self.start_readIn[-1][0]
                self.temp_start_y = self.start_readIn[-1][1]
            except:
                pass
            finally:
                self.start_scene.mousePressEvent = self.getStartPos
                print("Deleted Start")


        if(self.end_bkspcFlag == 1):
            print("Deleting End")
            #Enabling image
            self.graphicEndImg.setEnabled(True)
            self.end_bkspcFlag = 0
            #item = self.start_scene.items()[0]
            item = self.end_scene.itemAt(self.end_img_x, self.end_img_y)
            self.end_scene.removeItem(item)
            del self.end_item_list[-1]
            del self.end_readIn[-1]
            try:
                self.temp_end_x = self.end_readIn[-1][0]
                self.temp_end_y = self.end_readIn[-1][1]
            except:
                pass

            finally:
                self.end_scene.mousePressEvent = self.getEndPos
                print("Deleted End")

    def is_StartImg_GreyScale(self):
        im = Image.open(self.start_filePath).convert('RGB')
        w, h = im.size
        for i in range(w):
            for j in range(h):
                r,g,b = im.getpixel((i,j))
                if(r != g != b):
                    return False
                else:
                    im = Image.open(self.start_filePath).convert('L')
                    return True

    def is_EndImg_GreyScale(self):
        im = Image.open(self.end_filePath).convert('RGB')
        w, h = im.size
        for i in range(w):
            for j in range(h):
                r,g,b = im.getpixel((i,j))
                if(r != g != b):
                    return False
                else:
                    im = Image.open(self.end_filePath).convert('L')
                    return True





if __name__ == "__main__":
    currentApp = QApplication(sys.argv)
    currentForm = MorphingApp()

    currentForm.show()
    currentApp.exec_()




