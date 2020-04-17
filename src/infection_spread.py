import vtk
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QTextEdit, QCheckBox
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
        

        self.centralWidget = QWidget(MainWindow)
        self.gridlayout = QGridLayout(self.centralWidget)

        self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)

        # Sliders
        self.slider = QSlider()

        # Check boxes
        self.infections_check = QCheckBox()
        self.recovered_check = QCheckBox()
        self.deaths_check = QCheckBox()

        self.infections_check.setChecked(MainWindow.default_infections_checked)
        self.recovered_check.setChecked(MainWindow.default_recovered_checked)
        self.deaths_check.setChecked(MainWindow.default_deaths_checked)

        # Labels
        self.infections_label = QLabel("Toggle Infections:")
        self.recovered_label = QLabel("Toggle Recovered:")
        self.deaths_label = QLabel("Toggle Deaths:")
        self.date_label = QLabel("Date (" + MainWindow.initial_date.strftime('%m/%d/%Y') + "):")
        # We are now going to position our widgets inside our
        # grid layout. The top left corner is (0,0)
        # Here we specify that our vtkWidget is anchored to the top
        # left corner and spans 3 rows and 4 columns.
        
        
        self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)

        self.gridlayout.addWidget(self.infections_label, 4, 0, 1, 1)
        self.gridlayout.addWidget(self.infections_check, 4, 1, 1, 1)
        self.gridlayout.addWidget(self.recovered_label, 5, 0, 1, 1)
        self.gridlayout.addWidget(self.recovered_check, 5, 1, 1, 1)
        self.gridlayout.addWidget(self.deaths_label, 6, 0, 1, 1)
        self.gridlayout.addWidget(self.deaths_check, 6, 1, 1, 1)

        self.gridlayout.addWidget(self.date_label, 7, 0, 1, 1)
        self.gridlayout.addWidget(self.slider, 7, 1, 1, 1)
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
    
    def remove_case_actors(self, actors):
        for i in range(len(actors)):
            self.ren.RemoveActor(actors[i])
        actors = []
    
    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.date = 0
        
        self.default_infections_checked = True
        self.default_recovered_checked = True
        self.default_deaths_checked = True

        self.initial_date = date(2020, 1, 22) + timedelta(self.date)
        self.ui.setupUi(self)

        self.infections_max_radius = 50
        self.recovered_max_radius = 30
        self.deaths_max_radius = 30

        self.infections_color = (1, 0, 0)
        self.recovered_color = (0, 1, 0)
        self.deaths_color = (0, 0, 0)

        self.infections_opacity = 1
        self.recovered_opacity = 0.75
        self.deaths_opacity = 0.5
        
        sat_path = sys.argv[1]
        global_infections_path = sys.argv[2]
        global_deaths_path = sys.argv[3]
        global_recovered_path = sys.argv[4]

        self.infections_data = []
        self.deaths_data = []
        self.recovered_data = []

        # Read in data for global confirmed cases
        with open(global_infections_path) as csvDataFile:
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
        if(self.ui.infections_check.isChecked()):
            self.add_case_actors(self.infections_data, self.date, self.infections_actors, self.infections_color, self.infections_max_radius, self.infections_opacity)

        # Add recoveries actors for the initial date
        self.recovered_actors = []
        if(self.ui.recovered_check.isChecked()):
            self.add_case_actors(self.recovered_data, self.date, self.recovered_actors, self.recovered_color, self.recovered_max_radius, self.recovered_opacity)

        # Add death actors for the initial date
        self.deaths_actors = []
        if(self.ui.deaths_check.isChecked()):
            self.add_case_actors(self.deaths_data, self.date, self.deaths_actors, self.deaths_color, self.deaths_max_radius, self.deaths_opacity)
        
        self.ren.AddActor(sat_actor)
        self.ren.ResetCamera()
        self.ren.GetActiveCamera().Zoom(2)
        self.ren.SetBackground(0.25, 0.25, 0.25)

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
        self.ui.date_label.setText("Date (" + new_date.strftime('%m/%d/%Y') + "):")

        # Remove old infections, recovered, and deaths actors
        self.remove_case_actors(self.infections_actors)
        self.remove_case_actors(self.recovered_actors)
        self.remove_case_actors(self.deaths_actors)

        # Add infections, recovered, and deaths actors
        if(self.ui.infections_check.isChecked()):
            self.add_case_actors(self.infections_data, self.date, self.infections_actors, self.infections_color, self.infections_max_radius, self.infections_opacity)
        if(self.ui.recovered_check.isChecked()):
            self.add_case_actors(self.recovered_data, self.date, self.recovered_actors, self.recovered_color, self.recovered_max_radius, self.recovered_opacity)
        if(self.ui.deaths_check.isChecked()):
            self.add_case_actors(self.deaths_data, self.date, self.deaths_actors, self.deaths_color, self.deaths_max_radius, self.deaths_opacity)
        
        self.ui.vtkWidget.GetRenderWindow().Render()

    def infections_callback(self):
        if(self.ui.infections_check.isChecked()):
            self.add_case_actors(self.infections_data, self.date, self.infections_actors, self.infections_color, self.infections_max_radius, self.infections_opacity)
        else:
            self.remove_case_actors(self.infections_actors)

        self.ui.vtkWidget.GetRenderWindow().Render()

    def recovered_callback(self):
        if(self.ui.recovered_check.isChecked()):
            self.add_case_actors(self.recovered_data, self.date, self.recovered_actors, self.recovered_color, self.recovered_max_radius, self.recovered_opacity)
        else:
            self.remove_case_actors(self.recovered_actors)

        self.ui.vtkWidget.GetRenderWindow().Render()

    def deaths_callback(self):
        if(self.ui.deaths_check.isChecked()):
            self.add_case_actors(self.deaths_data, self.date, self.deaths_actors, self.deaths_color, self.deaths_max_radius, self.deaths_opacity)
        else:
            self.remove_case_actors(self.deaths_actors)

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
    window.ui.infections_check.stateChanged.connect(window.infections_callback)
    window.ui.recovered_check.stateChanged.connect(window.recovered_callback)
    window.ui.deaths_check.stateChanged.connect(window.deaths_callback)

    sys.exit(app.exec_())