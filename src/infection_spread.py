import vtk
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QTextEdit
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from datetime import date, timedelta
import csv
import math

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName('The Main Window')
        MainWindow.setWindowTitle('Final Project - COVID-19 Infection Spread')
        
        # in Qt, windows are made of widgets.
        # centralWidget will contains all the other widgets
        self.centralWidget = QWidget(MainWindow)
        # we will organize the contents of our setCentralWidget
        # in a grid / table layout
        self.gridlayout = QGridLayout(self.centralWidget)
        # vtkWidget is a widget that encapsulates a vtkRenderWindow
        # and the associated vtkRenderWindowInteractor. We add
        # it to centralWidget.
        # Here is a screenshot of the layout:
        # https://www.cs.purdue.edu/~cs530/projects/img/PyQtGridLayout.png
        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)
        # Sliders
        self.slider = QSlider()

        # We are now going to position our widgets inside our
        # grid layout. The top left corner is (0,0)
        # Here we specify that our vtkWidget is anchored to the top
        # left corner and spans 3 rows and 4 columns.
        self.date_label = QLabel("Date (" + MainWindow.initial_date.strftime('%m/%d/%Y') + "):")
        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
        self.gridlayout.addWidget(self.date_label, 4, 0, 1, 1)
        self.gridlayout.addWidget(self.slider, 4, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralWidget)

class InfectionSpread(QMainWindow):
    def compute_max(self, data, date):
        maximum = 0
        for i in range(len(data)):
            if(int(data[i][date+2]) > maximum):
                maximum = int(data[i][date+2])
        return maximum

    def add_case_actors(self, data, date, actors, color, max_radius, opacity):
        max_cases = self.compute_max(data, self.date)
        for i in range(len(data)):

            x = (self.sat_x / 360.0) * (180 + float(data[i][1]))
            y = (self.sat_y / 180.0) * (90 + float(data[i][0]))
            cases = int(data[i][self.date+2])

            if(cases > 0):
                radius = (math.log(cases)/math.log(max_cases)) * max_radius 
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

                self.ren.AddActor(cases_actor)
                actors.append(cases_actor)
    
    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.date = 0
        self.initial_date = date(2020, 1, 22) + timedelta(self.date)
        self.ui.setupUi(self)
        self.infections_max_radius = 50
        self.recovered_max_radius = 30
        self.deaths_max_radius = 30
        
        sat_path = sys.argv[1]
        global_cases_path = sys.argv[2]
        global_deaths_path = sys.argv[3]
        global_recovered_path = sys.argv[4]

        self.infections_data = []
        self.deaths_data = []
        self.recovered_data = []

        # Read in data for global confirmed cases
        with open(global_cases_path) as csvDataFile:
            csv_reader = csv.reader(csvDataFile)
            for row in csv_reader:
                # We do not need country/province name, so we remove the first two columns
                if(row[2] != 0 or row[3] != 0):
                    self.infections_data.append(row[2:])
        self.infections_data = self.infections_data[1:]

        # Read in data for global deaths
        with open(global_deaths_path) as csvDataFile:
            csv_reader = csv.reader(csvDataFile)
            for row in csv_reader:
                if(row[2] != 0 or row[3] != 0):
                    self.deaths_data.append(row[2:])
        self.deaths_data = self.deaths_data[1:]

        # Read in data for global recovered cases
        with open(global_recovered_path) as csvDataFile:
            csv_reader = csv.reader(csvDataFile)
            for row in csv_reader:
                if(row[2] != 0 or row[3] != 0):    
                    self.recovered_data.append(row[2:])
        self.recovered_data = self.recovered_data[1:]

        self.numDates = len(self.infections_data[0]) - 3
        
        # Read in satellite image and determine size of the image
        sat_reader = vtk.vtkJPEGReader()
        sat_reader.SetFileName(sat_path)
        sat_reader.Update()
        sat_dimensions = sat_reader.GetOutput().GetDimensions()
        self.sat_x = sat_dimensions[0]
        self.sat_y = sat_dimensions[1]
        
        # Create a plane to map the satellite image onto
        plane = vtk.vtkPlaneSource()
        plane.SetCenter(0.0, 0.0, 0.0)
        plane.SetNormal(0.0, 0.0, 1.0)
        plane.SetPoint1(self.sat_x, 0, 0)
        plane.SetPoint2(0, self.sat_y, 0)
        
        # Create satellite image texture
        texture = vtk.vtkTexture()
        texture.SetInputConnection(sat_reader.GetOutputPort())

        # Map satellite texture to plane
        texturePlane = vtk.vtkTextureMapToPlane()
        texturePlane.SetInputConnection(plane.GetOutputPort())

        # Create mapper
        sat_mapper = vtk.vtkPolyDataMapper()
        sat_mapper.SetInputConnection(texturePlane.GetOutputPort())

        # Create actor
        sat_actor = vtk.vtkActor()
        sat_actor.SetMapper(sat_mapper)
        sat_actor.SetTexture(texture)
        sat_actor.GetProperty().SetOpacity(0.6)


        # Initialize renderer
        self.ren = vtk.vtkRenderer()

        # Add infections actors for the initial date
        self.infections_actors = []
        self.add_case_actors(self.infections_data, self.date, self.infections_actors, (1, 0, 0), self.infections_max_radius, 1)

        # Add recoveries actors for the initial date
        self.recovered_actors = []
        self.add_case_actors(self.recovered_data, self.date, self.recovered_actors, (0, 1, 0), self.recovered_max_radius, 0.75)

        # Add death actors for the initial date
        self.deaths_actors = []
        self.add_case_actors(self.deaths_data, self.date, self.deaths_actors, (0, 0, 0), self.deaths_max_radius, 0.5)
        
        self.ren.AddActor(sat_actor)
        self.ren.ResetCamera()
        self.ren.SetBackground(0.25, 0.25, 0.25)

        # Initialize camera settings
        """
        cam1 = ren.GetActiveCamera()
        cam1.Azimuth(0)
        cam1.Elevation(270)
        cam1.Roll(360)
        cam1.Zoom(1)
        """

        self.ren.ResetCameraClippingRange()

        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()
 
        # Setting up widgets
        def slider_setup(slider, val, bounds, interv):
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setValue(float(val))
            slider.setTracking(False)
            slider.setTickInterval(interv)
            slider.setTickPosition(QSlider.TicksAbove)
            slider.setRange(bounds[0], bounds[1])

        slider_setup(self.ui.slider, self.date, [0, self.numDates], 1)

    def date_callback(self, val):
        self.date = val
        new_date = self.initial_date + timedelta(val)
        # TODO: Add date change update
        self.ui.date_label.setText("Date (" + new_date.strftime('%m/%d/%Y') + "):")

        # Remove old infections actors
        for i in range(len(self.infections_actors)):
            self.ren.RemoveActor(self.infections_actors[i])
        self.infections_actors = []
        
        # Remove old recovered actors
        for i in range(len(self.recovered_actors)):
            self.ren.RemoveActor(self.recovered_actors[i])
        self.recovered_actors = []

        # Remove old deaths actors
        for i in range(len(self.deaths_actors)):
            self.ren.RemoveActor(self.deaths_actors[i])
        self.deaths_actors = []

        # Add infections, recovered, and deaths actors
        self.add_case_actors(self.infections_data, val, self.infections_actors, (1, 0, 0), self.infections_max_radius, 1)
        self.add_case_actors(self.recovered_data, val, self.recovered_actors, (0, 1, 0), self.recovered_max_radius, 0.75)
        self.add_case_actors(self.deaths_data, val, self.deaths_actors, (0, 0, 0), self.deaths_max_radius, 0.5)
        
        self.ui.vtkWidget.GetRenderWindow().Render()

if __name__=="__main__":


    if len(sys.argv) != 5:
      raise ValueError('Please provide path to satellite image and global cases, recoveries and deaths data files')


    app = QApplication(sys.argv)
    window = InfectionSpread()
    window.ui.vtkWidget.GetRenderWindow().SetSize(1024, 768)
    window.show()
    window.setWindowState(Qt.WindowMaximized)  # Maximize the window
    window.iren.Initialize() # Need this line to actually show
                             # the render inside Qt

    window.ui.slider.valueChanged.connect(window.date_callback)

    sys.exit(app.exec_())