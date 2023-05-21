from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)


class Graph:
    def __init__(self, layout, widget):
        # Объекты графика
        self.axis = None
        self.figure = None
        self.canvas = None
        self.toolbar = None
        self.layout = layout
        self.widget = widget

    def initialize(self):
        # Инициализирует фигуру matplotlib внутри контейнера GUI.
        # Вызываем только один раз при инициализации

        # Создание фигуры (self.fig и self.ax)
        self.figure = Figure()
        self.axis = self.figure.add_subplot(111)
        # Создание холста
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.canvas.draw()
        # Создание Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self.widget, coordinates=True)
        self.layout.addWidget(self.toolbar)