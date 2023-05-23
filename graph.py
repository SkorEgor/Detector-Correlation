from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)


class Graph:
    def __init__(self, layout, widget, layout_toolbar=None):
        # Объекты графика
        self.axis = None
        self.figure = None
        self.canvas = None
        self.toolbar = None
        self.layout = layout
        self.widget = widget
        if layout_toolbar is None:
            self.layout_toolbar = layout
        else:
            self.layout_toolbar = layout_toolbar
        self.initialize()

    def initialize(self, draw=False):
        # Инициализирует фигуру matplotlib внутри контейнера GUI.
        # Вызываем только один раз при инициализации

        # Создание фигуры (self.fig и self.ax)
        self.figure = Figure()
        self.axis = self.figure.add_subplot(111)
        # Создание холста
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        if draw:
            self.canvas.draw()

        # Создание Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self.widget, coordinates=True)
        self.layout_toolbar.addWidget(self.toolbar)


