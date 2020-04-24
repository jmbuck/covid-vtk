import datetime
from datetime import timedelta

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QTextEdit, QCheckBox
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from argparse import ArgumentParser
import sys
import math
import csv

frame_counter = 0
initial_date = datetime.date(2020, 1, 22)
sat_x = 0
sat_y = 0
max_cases = 0
max_radius = 40
date = 0

infections_color = (1, 0, 0)
recovered_color = (0, 1, 0)
deaths_color = (0, 0, 0)

infections_opacity = 0.6
recovered_opacity = 0.6
deaths_opacity = 0.6

infections_data = []
recovered_data = []
deaths_data = []

legend_circle_actors = []
legend_text_actors = []

ren = None

def compute_max(date):
    maximum = 0
    for i in range(len(infections_data)):
        if(int(infections_data[i][date+2]) > maximum):
            maximum = int(infections_data[i][date+2])

    for i in range(len(recovered_data)):
        if(int(recovered_data[i][date+2]) > maximum):
            maximum = int(recovered_data[i][date+2])

    for i in range(len(deaths_data)):
        if(int(deaths_data[i][date+2]) > maximum):
            maximum = int(deaths_data[i][date+2])
    
    return maximum

def add_case_actors(date, data, actors, color, opacity):
    for i in range(len(data)):

        x = (sat_x / 360.0) * (180 + float(data[i][1]))
        y = (sat_y / 180.0) * (90 + float(data[i][0]))
        cases = int(data[i][date+2])

        if(cases > 0 and (float(data[i][1]) != 0 or float(data[i][0]) != 0)):
            radius = (math.log2(cases)/math.log2(max_cases)) * max_radius 
            polygon_source = vtk.vtkRegularPolygonSource()
            polygon_source.SetNumberOfSides(50)
            polygon_source.SetRadius(radius)
            polygon_source.SetCenter(x, y, 0)

            cases_mapper = vtk.vtkPolyDataMapper()
            cases_mapper.SetInputConnection(polygon_source.GetOutputPort())

            cases_actor = vtk.vtkActor()
            cases_actor.SetMapper(cases_mapper)
            cases_actor.GetProperty().SetColor(color[0], color[1], color[2])
            cases_actor.GetProperty().SetOpacity(opacity)

            ren.AddActor(cases_actor)
            actors.append(cases_actor)

def remove_case_actors(actors):
    for i in range(len(actors)):
        ren.RemoveActor(actors[i])
    actors = []

def remove_legend_actors():
    for i in range(len(legend_circle_actors)):
        ren.RemoveActor(legend_circle_actors[i])
        ren.RemoveActor(legend_text_actors[i])

def add_legend_actors():
  # TODO: Potentially change scale to use hardcoded values (e.g., 5, 10, 50, 100, 500, 1000....) and pick 4 evenly spaced values from this list (all parts of this list smaller than the max_cases)
  for i in range(4):
      cases = math.pow(2, (math.log2(max_cases) / (i+1)))
      radius = (math.log2(cases)/math.log2(max_cases)) * max_radius
      legend_polygon_source = vtk.vtkRegularPolygonSource()
      legend_polygon_source.SetNumberOfSides(50)
      legend_polygon_source.SetRadius(radius)
      legend_polygon_source.SetCenter(0, 0, 0)

      circle_mapper = vtk.vtkPolyDataMapper2D()
      circle_mapper.SetInputConnection(legend_polygon_source.GetOutputPort())

      circle_actor = vtk.vtkActor2D()
      circle_actor.SetMapper(circle_mapper)
      
      circle_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
      circle_actor.GetPositionCoordinate().SetValue(.05, .1 + .075 * i)

      text_actor = vtk.vtkTextActor()
      text_actor.SetInput(str(int(cases)) + " cases")

      text_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
      text_actor.GetPositionCoordinate().SetValue(.075, .1 + .075 * i)
      text_actor.GetTextProperty().SetFontSize(25)

      ren.AddActor(circle_actor)
      legend_circle_actors.append(circle_actor)
      ren.AddActor(text_actor)
      legend_text_actors.append(text_actor)

def main():
    # Initialize argument and constant variables
    parser = ArgumentParser("Create isosurfacing of object")
    parser.add_argument("infections")
    parser.add_argument("recovered")
    parser.add_argument("deaths")
    parser.add_argument("density")
    parser.add_argument("climate")
    parser.add_argument("sat")
    parser.add_argument("--camera", type = str, help = "Optional camera settings file")

    args = parser.parse_args()

    global sat_x
    global sat_y
    global max_cases
    global max_radius

    global infections_color
    global recovered_color
    global deaths_color

    global infections_opacity
    global recovered_opacity
    global deaths_opacity

    global infections_data
    global recovered_data
    global deaths_data

    global legend_circle_actors
    global legend_text_actors

    global ren

    app = QApplication([])
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)

    # Read in data for global confirmed cases
    with open(args.infections) as csvDataFile:
        csv_reader = csv.reader(csvDataFile)
        for row in csv_reader:
            # We do not need country/province name, so we remove the first two columns
            if(row[2] != 0 or row[3] != 0):
                infections_data.append(row[2:])
    infections_data = infections_data[1:]

    # Read in data for global deaths
    with open(args.deaths) as csvDataFile:
        csv_reader = csv.reader(csvDataFile)
        for row in csv_reader:
            if(row[2] != 0 or row[3] != 0):
                deaths_data.append(row[2:])
    deaths_data = deaths_data[1:]

    # Read in data for global recovered cases
    with open(args.recovered) as csvDataFile:
        csv_reader = csv.reader(csvDataFile)
        for row in csv_reader:
            if(row[2] != 0 or row[3] != 0):    
                recovered_data.append(row[2:])
    recovered_data = recovered_data[1:]

    numDates = len(infections_data[0]) - 3
    max_cases = compute_max(date)

    # Create reader for density file
    density_reader = vtk.vtkTIFFReader()
    density_reader.SetFileName(args.density)
    density_reader.Update()

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
    sat_reader.Update()
    sat_dimensions = sat_reader.GetOutput().GetDimensions()
    sat_x = sat_dimensions[0]
    sat_y = sat_dimensions[1]

    # Create a plane to map the satellite image onto
    plane = vtk.vtkPlaneSource()
    plane.SetCenter(0.0, 0.0, 0.0)
    plane.SetNormal(0.0, 0.0, 1.0)
    plane.SetPoint1(sat_x, 0, 0)
    plane.SetPoint2(0, sat_y, 0)

    # Create satellite image texture
    texture = vtk.vtkTexture()
    texture.SetInputConnection(sat_reader.GetOutputPort())

    # Map satellite texture to plane
    texturePlane = vtk.vtkTextureMapToPlane()
    texturePlane.SetInputConnection(plane.GetOutputPort())

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
    
    # Create mappers
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

    sat_mapper = vtk.vtkPolyDataMapper()
    sat_mapper.SetInputConnection(texturePlane.GetOutputPort())

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
    sat_actor.SetTexture(texture)
    sat_actor.GetProperty().SetOpacity(0.6)

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

    # Add legend actors
    add_legend_actors()

    # Add infections, recovered, and deaths actors
    infections_actors = []
    if(ui.infections_check.isChecked()):
        add_case_actors(date, infections_data, infections_actors, infections_color, infections_opacity)

    recovered_actors = []
    if(ui.recovered_check.isChecked()):
        add_case_actors(date, recovered_data, recovered_actors, recovered_color, recovered_opacity)

    deaths_actors = []
    if(ui.deaths_check.isChecked()):
        add_case_actors(date, deaths_data, deaths_actors, deaths_color, deaths_opacity)

    ren.AddActor(sat_actor)
    ren.ResetCamera()
    ren.SetBackground(0, 0, 0)

    # Initialize camera settings
    cam1 = ren.GetActiveCamera()
    cam1.Azimuth(0)
    cam1.Elevation(0)
    cam1.Roll(360)
    cam1.Zoom(1.5)

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

    slider_setup(ui.time_slider, 0, [0, numDates], 1)

    window.show()
    window.setWindowState(Qt.WindowMaximized)
    iren.Initialize()

    def time_slider_callback(val):
        global max_cases
        global date
        date = val
        new_date = initial_date + timedelta(val)
        if new_date.month.real != ui.curr_month:
            ui.curr_month = new_date.month.real
            climate_reader.SetFileName(args.climate + "-" + str(ui.curr_month).zfill(2) + ".tif")
            climate_reader.Update()
            new_range = climate_reader.GetOutput().GetScalarRange()
            climate_mapper.SetScalarRange(new_range)
        ui.date_label.setText("Date (" + new_date.strftime('%m/%d/%Y') + "):")

        # Remove old infections, recovered, and deaths actors
        remove_case_actors(infections_actors)
        remove_case_actors(recovered_actors)
        remove_case_actors(deaths_actors)
        remove_legend_actors()

        # Recompute max cases
        max_cases = compute_max(date)

        # Add infections, recovered, and deaths actors
        if(ui.infections_check.isChecked()):
            add_case_actors(date, infections_data, infections_actors, infections_color, infections_opacity)
        if(ui.recovered_check.isChecked()):
            add_case_actors(date, recovered_data, recovered_actors, recovered_color, recovered_opacity)
        if(ui.deaths_check.isChecked()):
            add_case_actors(date, deaths_data, deaths_actors, deaths_color, deaths_opacity)
        add_legend_actors()

        ui.vtkWidget.GetRenderWindow().Render()

    def infections_callback():
        if(ui.infections_check.isChecked()):
            add_case_actors(date, infections_data, infections_actors, infections_color, infections_opacity)
        else:
            remove_case_actors(infections_actors)

        ui.vtkWidget.GetRenderWindow().Render()

    def recovered_callback():
        if(ui.recovered_check.isChecked()):
            add_case_actors(date, recovered_data, recovered_actors, recovered_color, recovered_opacity)
        else:
            remove_case_actors(recovered_actors)

        ui.vtkWidget.GetRenderWindow().Render()

    def deaths_callback():
        if(ui.deaths_check.isChecked()):
            add_case_actors(date, deaths_data, deaths_actors, deaths_color, deaths_opacity)
        else:
            remove_case_actors(deaths_actors)

        ui.vtkWidget.GetRenderWindow().Render()

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

    ui.infections_check.stateChanged.connect(infections_callback)
    ui.recovered_check.stateChanged.connect(recovered_callback)
    ui.deaths_check.stateChanged.connect(deaths_callback)

    ui.push_density.clicked.connect(density_callback)
    ui.push_climate.clicked.connect(climate_callback)

    # Terminate setup for PyQT5 interface
    sys.exit(app.exec_())

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('COVID 19 Visualization')

        self.default_infections_checked = True
        self.default_recovered_checked = True
        self.default_deaths_checked = True

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

        # Check boxes
        self.infections_check = QCheckBox()
        self.recovered_check = QCheckBox()
        self.deaths_check = QCheckBox()

        self.infections_check.setChecked(self.default_infections_checked)
        self.recovered_check.setChecked(self.default_recovered_checked)
        self.deaths_check.setChecked(self.default_deaths_checked)

        # Labels
        self.infections_label = QLabel("Toggle Infections:")
        self.recovered_label = QLabel("Toggle Recovered:")
        self.deaths_label = QLabel("Toggle Deaths:")
        self.date_label = QLabel("Date (" + initial_date.strftime('%m/%d/%Y') + "):")
        self.curr_month = initial_date.month.real

        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
        
        self.gridlayout.addWidget(self.infections_label, 4, 0, 1, 1)
        self.gridlayout.addWidget(self.infections_check, 4, 1, 1, 1)
        self.gridlayout.addWidget(self.recovered_label, 5, 0, 1, 1)
        self.gridlayout.addWidget(self.recovered_check, 5, 1, 1, 1)
        self.gridlayout.addWidget(self.deaths_label, 6, 0, 1, 1)
        self.gridlayout.addWidget(self.deaths_check, 6, 1, 1, 1)

        self.gridlayout.addWidget(self.date_label, 7, 0, 1, 1)
        self.gridlayout.addWidget(self.time_slider, 7, 1, 1, 1)
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
    file_name = "covid_viz-" + str(frame_counter).zfill(2) + ".png"
    file_name2 = "covid_viz_cam-" + str(frame_counter).zfill(2) + ".csv"
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