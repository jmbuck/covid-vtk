import vtk
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QTextEdit
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from datetime import date, timedelta
import csv


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
    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.initial_date = date(2020, 1, 22)
        self.ui.setupUi(self)
        self.date = 0
        
        sat_path = sys.argv[1]
        global_cases_path = sys.argv[2]
        global_deaths_path = sys.argv[3]
        global_recovered_path = sys.argv[4]

        cases_data = []
        deaths_data = []
        recovered_data = []

        # Read in data for global confirmed cases
        with open(global_cases_path) as csvDataFile:
            csv_reader = csv.reader(csvDataFile)
            for row in csv_reader:
                # We do not need country/province name, so we remove the first two columns
                if(row[2] != 0 or row[3] != 0):
                    cases_data.append(row[2:])
        cases_data = cases_data[1:]

        # Read in data for global deaths
        with open(global_deaths_path) as csvDataFile:
            csv_reader = csv.reader(csvDataFile)
            for row in csv_reader:
                if(row[2] != 0 or row[3] != 0):
                    deaths_data.append(row[2:])
        deaths_data = deaths_data[1:]

        # Read in data for global recovered cases
        with open(global_recovered_path) as csvDataFile:
            csv_reader = csv.reader(csvDataFile)
            for row in csv_reader:
                if(row[2] != 0 or row[3] != 0):    
                    recovered_data.append(row[2:])
        recovered_data = recovered_data[1:]

        self.numDates = len(cases_data[0]) - 3
        print(len(cases_data))
        print(len(deaths_data))
        print(len(recovered_data))
        
        # Read in satellite image and determine size of the image
        sat_reader = vtk.vtkJPEGReader()
        sat_reader.SetFileName(sat_path)
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

        # Create mapper
        sat_mapper = vtk.vtkPolyDataMapper()
        sat_mapper.SetInputConnection(texturePlane.GetOutputPort())

        # Create actor
        sat_actor = vtk.vtkActor()
        sat_actor.SetMapper(sat_mapper)
        sat_actor.SetTexture(texture)
        sat_actor.GetProperty().SetOpacity(0.6)

        cases_actors = []
        for i in range(len(cases_data)):

            x = (sat_x / 360.0) * (180 + float(cases_data[i][1]))
            y = (sat_y / 180.0) * (90 + float(cases_data[i][0]))

            if(int(cases_data[i][self.date+2]) > 0):
                polygon_source = vtk.vtkRegularPolygonSource()
                polygon_source.SetNumberOfSides(50)
                polygon_source.SetRadius(10)
                polygon_source.SetCenter(x, y, 0)

                cases_mapper = vtk.vtkPolyDataMapper()
                cases_mapper.SetInputConnection(polygon_source.GetOutputPort())

                cases_actor = vtk.vtkActor()
                cases_actor.SetMapper(cases_mapper)

                cases_actors.append(cases_actor)


        # Initialize renderer and place actors
        self.ren = vtk.vtkRenderer()
        self.ren.AddActor(sat_actor)
        for i in range(len(cases_actors)):
            self.ren.AddActor(cases_actors[i])
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