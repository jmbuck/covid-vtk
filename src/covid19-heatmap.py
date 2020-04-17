#!/usr/bin/env python

# This simple example shows how to do basic rendering and pipeline
# creation.
import datetime
from datetime import timedelta

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QTextEdit
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from argparse import ArgumentParser
import sys

frame_counter = 0
initial_date = datetime.date(2020, 1, 22)
curr_date = datetime.datetime.now().date()

def main():
    # Initialize argument and constant variables
    parser = ArgumentParser("Create isosurfacing of object")
    parser.add_argument("density")
    parser.add_argument("climate")
    parser.add_argument("sat")
    parser.add_argument("--camera", type = str, help = "Optional camera settings file")

    args = parser.parse_args()

    # Create reader for ct scan
    density_reader = vtk.vtkTIFFReader()
    density_reader.SetFileName(args.density)
    density_reader.Update()
    print(density_reader.GetOutput().GetScalarRange()[1])

    density_log = vtk.vtkImageLogarithmicScale()
    density_log.SetInputConnection(density_reader.GetOutputPort())
    density_log.SetConstant(0.435)
    density_log.Update()
    density_range = density_log.GetOutput().GetScalarRange()

    climate_reader = vtk.vtkTIFFReader()
    climate_reader.SetFileName(args.climate + "-" + str(initial_date.month.real).zfill(2) + ".tif")
    climate_reader.Update()
    climate_range = climate_reader.GetOutput().GetScalarRange()

    sat_reader = vtk.vtkJPEGReader()
    sat_reader.SetFileName(args.sat)

    max_val = 100
    color_count = 1000

    density_ctf = vtk.vtkColorTransferFunction()
    density_ctf.AddRGBPoint(0, 0, 0, 0)
    density_ctf.AddRGBPoint(10, 0, 0, 1)
    density_ctf.AddRGBPoint(30, 0, 1, 1)
    density_ctf.AddRGBPoint(50, 1, 1, 0)
    density_ctf.AddRGBPoint(65, 1, 0.5, 0)
    density_ctf.AddRGBPoint(80, 1, 0, 0)

    density_lut = vtk.vtkLookupTable()
    density_lut.SetNumberOfTableValues(color_count)
    density_lut.Build()

    rgb = list(density_ctf.GetColor(0))+[0]
    density_lut.SetTableValue(0, rgb)
    for i in range(1, color_count):
        rgb = list(density_ctf.GetColor(max_val * float(i)/color_count))+[1]
        density_lut.SetTableValue(i, rgb)

    climate_ctf = vtk.vtkColorTransferFunction()
    climate_ctf.AddRGBPoint(5, 0, 0, 1)
    climate_ctf.AddRGBPoint(35, 0, 1, 1)
    climate_ctf.AddRGBPoint(65, 1, 1, 0)
    climate_ctf.AddRGBPoint(95, 1, 0, 0)

    climate_lut = vtk.vtkLookupTable()
    climate_lut.SetNumberOfTableValues(color_count)
    climate_lut.Build()

    for i in range(0, color_count):
        rgb = list(climate_ctf.GetColor(max_val * float(i)/color_count))+[1]
        climate_lut.SetTableValue(i, rgb)

    density_mapper = vtk.vtkDataSetMapper()
    density_mapper.SetInputConnection(density_log.GetOutputPort())
    density_mapper.SetLookupTable(density_lut)
    density_mapper.SetScalarRange([0, density_range[1]])
    density_mapper.Update()

    climate_mapper = vtk.vtkDataSetMapper()
    climate_mapper.SetInputConnection(climate_reader.GetOutputPort())
    climate_mapper.SetLookupTable(climate_lut)
    climate_mapper.SetScalarRange(climate_range)
    climate_mapper.Update()

    sat_mapper = vtk.vtkDataSetMapper()
    sat_mapper.SetInputConnection(sat_reader.GetOutputPort())

    density_actor = vtk.vtkActor()
    density_actor.SetMapper(density_mapper)
    density_actor.GetProperty().SetOpacity(0.99)
    density_actor.VisibilityOn()

    climate_actor = vtk.vtkActor()
    climate_actor.SetMapper(climate_mapper)
    climate_actor.GetProperty().SetOpacity(0.6)
    climate_actor.VisibilityOff()

    sat_actor = vtk.vtkActor()
    sat_actor.SetMapper(sat_mapper)
    sat_actor.GetProperty().SetOpacity(0.7)

    # Make satellite image same size as contour map
    crange = sat_actor.GetXRange()[0] - sat_actor.GetXRange()[1]
    mrange = density_actor.GetXRange()[0] - density_actor.GetXRange()[1]
    density_actor.SetScale(crange/mrange)

    crange = sat_actor.GetXRange()[0] - sat_actor.GetXRange()[1]
    mrange = climate_actor.GetXRange()[0] - climate_actor.GetXRange()[1]
    climate_actor.SetScale(crange/mrange)

    # Initialize renderer and place actors
    ren = vtk.vtkRenderer()
    ren.AddActor(density_actor)
    ren.AddActor(climate_actor)
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

    # create the scalar_bar
    density_scalar_bar = vtk.vtkScalarBarActor()
    density_scalar_bar.SetOrientationToHorizontal()
    density_scalar_bar.SetMaximumNumberOfColors(color_count)
    density_scalar_bar.SetLookupTable(density_lut)
    density_scalar_bar.SetTitle("Density (Log 10)")

    # create the scalar_bar_widget
    density_scalar_bar_widget = vtk.vtkScalarBarWidget()
    density_scalar_bar_widget.SetInteractor(iren)
    density_scalar_bar_widget.SetScalarBarActor(density_scalar_bar)
    density_scalar_bar_widget.On()

    # create the scalar_bar
    climate_scalar_bar = vtk.vtkScalarBarActor()
    climate_scalar_bar.SetOrientationToHorizontal()
    climate_scalar_bar.SetMaximumNumberOfColors(color_count)
    climate_scalar_bar.SetLookupTable(climate_lut)
    climate_scalar_bar.SetTitle("Temparature (Celsius)")

    # create the scalar_bar_widget
    climate_scalar_bar_widget = vtk.vtkScalarBarWidget()
    climate_scalar_bar_widget.SetInteractor(iren)
    climate_scalar_bar_widget.SetScalarBarActor(climate_scalar_bar)
    climate_scalar_bar_widget.Off()

    # Function to initialize slider settings
    def slider_setup(slider, val, bounds, interv):
        slider.setOrientation(QtCore.Qt.Horizontal)
        slider.setValue(float(val))
        slider.setSliderPosition(val)
        slider.setTracking(False)
        slider.setTickInterval(interv)
        slider.setTickPosition(QSlider.TicksAbove)
        slider.setRange(bounds[0], bounds[1])

    slider_setup(ui.time_slider, 0, [0, (curr_date - initial_date).days], 1)

    window.show()
    window.setWindowState(Qt.WindowMaximized)
    iren.Initialize()

    def time_slider_callback(val):
        new_date = initial_date + timedelta(val)
        if new_date.month.real != ui.curr_month:
            ui.curr_month = new_date.month.real
            climate_reader.SetFileName(args.climate + "-" + str(ui.curr_month).zfill(2) + ".tif")
            climate_reader.Update()
            new_range = climate_reader.GetOutput().GetScalarRange()
            climate_mapper.SetScalarRange(new_range)
        ui.date_label.setText("Date (" + new_date.strftime('%m/%d/%Y') + "):")

    def density_callback():
        isOn = density_actor.GetVisibility()
        if isOn:
            density_actor.VisibilityOff()
            density_scalar_bar_widget.Off()
            ui.vtkWidget.GetRenderWindow().Render()
            ui.push_density.setText('Enable Density')
        else:
            density_actor.VisibilityOn()
            density_scalar_bar_widget.On()
            ui.vtkWidget.GetRenderWindow().Render()
            ui.push_density.setText('Disable Density')

    def climate_callback():
        isOn = climate_actor.GetVisibility()
        if isOn:
            climate_actor.VisibilityOff()
            climate_scalar_bar_widget.Off()
            ui.vtkWidget.GetRenderWindow().Render()
            ui.push_climate.setText('Enable Temperature')
        else:
            climate_actor.VisibilityOn()
            climate_scalar_bar_widget.On()
            ui.vtkWidget.GetRenderWindow().Render()
            ui.push_climate.setText('Disable Temperature')

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
    ui.time_slider.valueChanged.connect(time_slider_callback)
    ui.push_screenshot.clicked.connect(screenshot_callback)
    ui.push_camera.clicked.connect(camera_callback)
    ui.push_quit.clicked.connect(quit_callback)

    ui.push_density.clicked.connect(density_callback)
    ui.push_climate.clicked.connect(climate_callback)

    # Terminate setup for PyQT5 interface
    sys.exit(app.exec_())

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('Vector Planes Visualization')

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)
        self.time_slider = QSlider()

        self.push_screenshot = QPushButton()
        self.push_screenshot.setText('Save Screenshot')
        self.push_camera = QPushButton()
        self.push_camera.setText('Update Camera Info')
        self.push_quit = QPushButton()
        self.push_quit.setText('Quit')

        self.push_density = QPushButton()
        self.push_density.setText('Disable Density')
        self.push_density.size

        self.push_climate = QPushButton()
        self.push_climate.setText('Enable Temperature')

        self.camera_info = QTextEdit()
        self.camera_info.setReadOnly(True)
        self.camera_info.setAcceptRichText(True)
        self.camera_info.setHtml("<div style='font-weight: bold'>Camera Settings</div>")

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.date_label = QLabel("Date (" + initial_date.strftime('%m/%d/%Y') + "):")
        self.curr_month = initial_date.month.real

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
        self.gridlayout.addWidget(self.date_label, 4, 0, 1, 1)
        self.gridlayout.addWidget(self.time_slider, 4, 1, 1, 1)
        self.gridlayout.addWidget(self.push_density, 4, 4, 1, 1)
        self.gridlayout.addWidget(self.push_climate, 4, 5, 1, 1)
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