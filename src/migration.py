#!/usr/bin/env python

# This simple example shows how to do basic rendering and pipeline
# creation.
import datetime
import math
import os
from datetime import timedelta

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QTextEdit
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from argparse import ArgumentParser
import sys
import csv

frame_counter = 0

def main():
    # Initialize argument and constant variables
    parser = ArgumentParser("Create isosurfacing of object")
    parser.add_argument("migration")
    parser.add_argument("covid")
    parser.add_argument("sat")
    parser.add_argument("--camera", type = str, help = "Optional camera settings file")

    args = parser.parse_args()

    sat_reader = vtk.vtkJPEGReader()
    sat_reader.SetFileName(args.sat)
    sat_reader.Update()
    sat_dimensions = sat_reader.GetOutput().GetDimensions()
    sat_x = sat_dimensions[0]
    sat_y = sat_dimensions[1]

    sat_mapper = vtk.vtkDataSetMapper()
    sat_mapper.SetInputConnection(sat_reader.GetOutputPort())

    sat_actor = vtk.vtkActor()
    sat_actor.SetMapper(sat_mapper)
    sat_actor.GetProperty().SetOpacity(0.7)

    ren = vtk.vtkRenderer()
    max_weight = [0]

    def create_long_lat(file):
        table = {}
        with open(file) as csvDataFile:
            csv_reader = csv.reader(csvDataFile)
            for row in csv_reader:
                try:
                    table[row[0]] = [float(row[4]), float(row[5])]
                except ValueError:
                    continue
        return table


    def add_migration_info(loc_src, loc_dst, weight):
        x1 = (sat_x / 360.0) * (180 + float(loc_src[1]))
        y1 = (sat_y / 180.0) * (90 + float(loc_src[0]))

        x2 = (sat_x / 360.0) * (180 + float(loc_dst[1]))
        y2 = (sat_y / 180.0) * (90 + float(loc_dst[0]))

        if weight > max_weight[0]:
            max_weight[0] = weight

        return {"x1": x1, "x2": x2, "y1": y1, "y2": y2, "weight": weight}

    def process_migration_actors(actors):
        arrow_actors = []
        for actor in actors:
            x1 = actor.get("x1")
            y1 = actor.get("y1")
            x2 = actor.get("x2")
            y2 = actor.get("y2")
            weight = actor.get("weight")

            if weight < 0.05 * max_weight[0]:
                continue

            line_source = vtk.vtkLineSource()
            line_source.SetPoint1(x1, y1, 0)
            line_source.SetPoint2(x2, y2, 0)

            line_mapper = vtk.vtkPolyDataMapper()
            line_mapper.SetInputConnection(line_source.GetOutputPort())

            line_actor = vtk.vtkActor()
            line_actor.SetMapper(line_mapper)
            line_actor.GetProperty().SetColor(1, 1, 1)
            line_actor.GetProperty().SetOpacity(math.sqrt(0.99 * (weight / max_weight[0])))

            ren.AddActor(line_actor)
            arrow_actors.append(line_actor)

        return arrow_actors

    # Read in data for global confirmed cases
    location_map = create_long_lat(args.covid)
    actors = []
    for filename in os.listdir(args.migration):
        if filename.endswith(".csv"):
            with open(args.migration + "\\" + filename) as csvDataFile:
                country = filename.split(".")[0]
                if country not in location_map:
                    continue
                loc_dst = location_map[country]
                csv_reader = csv.reader(csvDataFile)
                for row in csv_reader:
                    if row[2] not in location_map:
                        continue
                    loc_src = location_map[row[2]]
                    try:
                        actors.append(add_migration_info(loc_src, loc_dst, int(row[9])))
                    except ValueError:
                        continue

    arrow_actors = process_migration_actors(actors)
    # Initialize renderer and place actors
    ren.AddActor(sat_actor)
    ren.ResetCamera()
    ren.SetBackground(0, 0, 0)

    # Initialize camera settings
    cam1 = ren.GetActiveCamera()
    cam1.Azimuth(0)
    cam1.Elevation(0)
    cam1.Roll(360)
    cam1.Zoom(1)

    ren.ResetCameraClippingRange()

    if args.camera:
        reader = open(args.camera, "r")
        line = reader.readline().split(",")
        cam1.SetPosition(float(line[0]), float(line[1]), float(line[2]))
        line = reader.readline().split(",")
        cam1.SetFocalPoint(float(line[0]), float(line[1]), float(line[2]))
        line = reader.readline().split(",")
        cam1.SetViewUp(float(line[0]), float(line[1]), float(line[2]))
        line = reader.readline().split(",")
        cam1.SetClippingRange(float(line[0]), float(line[1]))
        line = reader.readline().split(",")
        cam1.SetViewAngle(float(line[0]))
        line = reader.readline().split(",")
        cam1.SetParallelScale(float(line[0]))

    # Initialize PyQT5 UI and link to renderer
    app = QApplication([])
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)
    ui.vtkWidget.GetRenderWindow().AddRenderer(ren)
    ui.vtkWidget.GetRenderWindow().SetSize(1280, 720)

    ui.vtkWidget.GetRenderWindow().AddRenderer(ren)
    ui.vtkWidget.GetRenderWindow().SetAlphaBitPlanes(True)
    ui.vtkWidget.GetRenderWindow().SetMultiSamples(False)
    iren = ui.vtkWidget.GetRenderWindow().GetInteractor()

    # Function to initialize slider settings
    def slider_setup(slider, val, bounds, interv):
        slider.setOrientation(QtCore.Qt.Horizontal)
        slider.setValue(float(val))
        slider.setSliderPosition(val)
        slider.setTracking(False)
        slider.setTickInterval(interv)
        slider.setTickPosition(QSlider.TicksAbove)
        slider.setRange(bounds[0], bounds[1])

    window.show()
    window.setWindowState(Qt.WindowMaximized)
    iren.Initialize()

    # Handle screenshot button event
    def screenshot_callback():
        save_frame(ren.GetActiveCamera(), ui.vtkWidget.GetRenderWindow(), ui.log)

    # Handle show camera settings button event
    def camera_callback():
        print_camera_settings(ren.GetActiveCamera(), ui.camera_info, ui.log)

    # Handle quit button event
    def quit_callback():
        sys.exit()

    # Register callbacks to UI
    ui.push_screenshot.clicked.connect(screenshot_callback)
    ui.push_camera.clicked.connect(camera_callback)
    ui.push_quit.clicked.connect(quit_callback)

    # Terminate setup for PyQT5 interface
    sys.exit(app.exec_())

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('Vector Planes Visualization')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        self.push_screenshot = QPushButton()
        self.push_screenshot.setText('Save Screenshot')
        self.push_camera = QPushButton()
        self.push_camera.setText('Update Camera Info')
        self.push_quit = QPushButton()
        self.push_quit.setText('Quit')

        self.camera_info = QTextEdit()
        self.camera_info.setReadOnly(True)
        self.camera_info.setAcceptRichText(True)
        self.camera_info.setHtml("<div style='font-weight: bold'>Camera Settings</div>")

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
        self.gridlayout.addWidget(self.push_screenshot, 0, 4, 1, 1)
        self.gridlayout.addWidget(self.push_camera, 0, 5, 1, 1)
        self.gridlayout.addWidget(self.camera_info, 2, 4, 1, 2)
        self.gridlayout.addWidget(self.log, 3, 4, 1, 2)
        MainWindow.setCentralWidget(self.centralWidget)

def save_frame(camera, window, log):
    global frame_counter
    # ---------------------------------------------------------------
    # Save current contents of render window to PNG file
    # ---------------------------------------------------------------
    file_name = "three_planes-" + str(frame_counter).zfill(2) + ".png"
    file_name2 = "three_planes_cam-" + str(frame_counter).zfill(2) + ".csv"
    image = vtk.vtkWindowToImageFilter()
    image.SetInput(window)
    png_writer = vtk.vtkPNGWriter()
    png_writer.SetInputConnection(image.GetOutputPort())
    png_writer.SetFileName(file_name)
    window.Render()
    png_writer.Write()
    cam = open(file_name2, "w")
    cam.write(str(camera.GetPosition()[0]) + "," + str(camera.GetPosition()[1]) + "," + str(camera.GetPosition()[2]) + "\n")
    cam.write(str(camera.GetFocalPoint()[0]) + "," + str(camera.GetFocalPoint()[1]) + "," + str(camera.GetFocalPoint()[2]) + "\n")
    cam.write(str(camera.GetViewUp()[0]) + "," + str(camera.GetViewUp()[1]) + "," + str(camera.GetViewUp()[2]) + "\n")
    cam.write(str(camera.GetClippingRange()[0]) + "," + str(camera.GetClippingRange()[1]) + "\n")
    cam.write(str(camera.GetViewAngle()) + "\n")
    cam.write(str(camera.GetParallelScale()) + "\n")
    frame_counter += 1
    log.insertPlainText('Exported {}\n'.format(file_name))

def print_camera_settings(camera, text_window, log):
    # ---------------------------------------------------------------
    # Print out the current settings of the camera
    # ---------------------------------------------------------------
    text_window.setHtml("""<div style='font-weight:bold'>Camera settings:</div><p><ul><li><div style='font-weight:bold'>
    Position:</div> {0}</li><li><div style='font-weight:bold'>Focal Point:</div> {1}</li><li><div style='font-weight:bold'>
    Up Vector:</div> {2}</li><li><div style='font-weight:bold'>Clipping Range:</div> {3}</li><li><div style='font-weight:bold'>
    View Angle:</div> {4}</li></li><li><div style='font-weight:bold'>Parallel Scale:</div> {5}</li><li><div style='font-weight:bold'>
    View Plane Normal:</div> {6}</li>""".format(camera.GetPosition(), camera.GetFocalPoint(),camera.GetViewUp(),camera.GetClippingRange(), camera.GetViewAngle(), camera.GetParallelScale(), camera.GetViewPlaneNormal()))
    log.insertPlainText('Updated camera info\n')


if __name__ == '__main__':
    main()