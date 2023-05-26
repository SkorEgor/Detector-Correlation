from graph import Graph
from drawer import Drawer as drawer
from data_and_processing import DataAndProcessing

from PyQt5.QtWidgets import QRadioButton
import functools


# ЦЕЛЬ: Связать 1 поле отображения графика С несколькими данными
# каждые данные связанны с кнопкой переключения
class UpdateGraphics:
    def __init__(self,
                 graph: Graph,
                 data: DataAndProcessing,
                 radio_button_data: QRadioButton,
                 radio_button_correlation: QRadioButton,
                 radio_button_sigma: QRadioButton,
                 radio_button_noise: QRadioButton,
                 radio_button_width: QRadioButton,
                 radio_button_now=None):
        # Объект графики для отрисовки данных
        self.graph = graph

        # Объект данных
        self.data = data

        # Связь кнопок и данных
        self.linking_buttons_with_data = {
            radio_button_data: drawer.updating_gas_graph,
            radio_button_correlation: drawer.updating_correlation_graph,
            radio_button_sigma: drawer.updating_smoothing_graph,
            radio_button_noise: drawer.updating_sigma_and_difference_graph,
            radio_button_width: drawer.updating_width_filter_graph
        }
        # Вышаем обработчики нажатий
        self.radio_button_connect()

        # Нажатая кнопка
        # Кнопки нет -> ищем; Если передали -> запоминаем
        if radio_button_now is None:
            self.radio_button_now = self.radio_button_check()
        else:
            self.radio_button_now = radio_button_now

    # Метод проверки, какая клавиша нажата (можно вызвать в начале)
    def radio_button_check(self):
        # Перебираем кнопки
        for radio_button in self.linking_buttons_with_data:
            # Кнопка нажата -> возвращаем объект кнопки
            if radio_button.isChecked():
                return radio_button

    # Метод подписи на изменение состояния кнопок
    def radio_button_connect(self):
        # Проходим по всем кнопкам
        for radio_button in self.linking_buttons_with_data:
            # Добавляем слушателя нажатия
            radio_button.clicked.connect(functools.partial(
                # При нажатии обновляем кнопку, на переданную и перерисовываем график
                self.radio_button_updated, radio_button))

    # Обновились кнопки
    def radio_button_updated(self, radio_button: QRadioButton):
        # Запоминаем новую кнопку
        self.radio_button_now = radio_button
        # Обновляем график
        self.update_graph()

    # Вызвается для обновления графика (при изменении: данных или кнопки)
    def update_graph(self):
        # В словаре, по ключу-кнопке -> вызываем соответсвующую функцию с параметрами
        self.linking_buttons_with_data[self.radio_button_now](self.graph, self.data)
