# coding: utf-8
from gui import Ui_Dialog
from data_and_processing import DataAndProcessing

import functools

import pandas as pd

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)

matplotlib.use('TkAgg')


# ПАРСЕРЫ ДАННЫХ
# Входной список, парсит по столбцам
def parser_all_data(string_list):
    frequency_list = list()
    gamma_list = list()

    skipping_first_line = True  # Пропускаем первую строку?

    for line in string_list:
        # Пропуск первой строки
        if skipping_first_line:
            skipping_first_line = False
            continue

        # Если звездочки, конец файла
        if line[0] == "*":
            break

        # Разделяем строку по пробелу в список
        row = line.split()

        frequency_list.append(float(row[1]))
        gamma_list.append(float(row[4]))

    return frequency_list, gamma_list


# Входной список, парсит по столбцам, в заданных частотах
def parser(string_list, start_frequency=None, end_frequency=None):
    frequency_list = list()
    gamma_list = list()

    skipping_first_line = True  # Пропускаем первую строку?

    for line in string_list:
        # Пропуск первой строки
        if skipping_first_line:
            skipping_first_line = False
            continue

        # Если звездочки, конец файла
        if line[0] == "*":
            break

        # Разделяем строку по пробелу в список
        row = line.split()

        # Если частота в диапазоне частот берем
        if start_frequency <= float(row[1]) <= end_frequency:
            frequency_list.append(float(row[1]))
            gamma_list.append(float(row[4]))

    return frequency_list, gamma_list


# ФУНКЦИИ ПРОВЕРКИ ВВЕДЕННЫХ ДАННЫХ
# Дробное, больше нуля (для частоты)
def check_float_and_positive(val, field_name, message=False):
    try:
        val = float(val)

    except ValueError:
        if message:
            QMessageBox.warning(None, "Ошибка ввода", f'Введите число в поле "{field_name!r}".')
        return False

    # Проверка положительности
    if val < 0:
        if message:
            QMessageBox.warning(None, "Ошибка ввода", f'Введите положительное число в поле "{field_name!r}".')
        return False

    return True


# Целое, больше нуля (для окна корреляции)
def check_int_and_positive(val, field_name, message=False):
    print(val, field_name, message)
    try:
        val = int(val)

    except ValueError:
        if message:
            QMessageBox.warning(None, "Ошибка ввода", f'Введите целое число в поле "{field_name!r}".')
        return False

    # Проверка положительности
    if val < 0:
        if message:
            QMessageBox.warning(None, "Ошибка ввода", f'Введите положительное число в поле "{field_name!r}".')
        return False

    return True


# Дробное, от 0 до 100 (для процентов и ширины окна просмотра)
def check_float_and_0to100(val, field_name, message=False):
    try:
        val = float(val)

    except ValueError:
        if message:
            QMessageBox.warning(None, "Ошибка ввода", f'Введите число в поле "{field_name!r}".')
        return False

    # Проверка на диапазон
    if val < 0 or 100 < val:
        if message:
            QMessageBox.warning(None, "Ошибка ввода", f'Введите число от 0 до 100 в поле "{field_name!r}".')
        return False

    return True


# Дробное, от -100 до 100 (для процентов и ширины окна просмотра)
def check_float_and_100to100(val, field_name, message=False):
    try:
        val = float(val)

    except ValueError:
        if message:
            QMessageBox.warning(None, "Ошибка ввода", f'Введите число в поле "{field_name!r}".')
        return False

    # Проверка на диапазон
    if val < -100 or 100 < val:
        if message:
            QMessageBox.warning(None, "Ошибка ввода", f'Введите число от -100 до 100 в поле "{field_name!r}".')
        return False

    return True


# Шаблон проверки поля
def check(line_edit, check_function, check_box, field_name, message=False):
    # Запрос порогового значения
    val = line_edit.text()
    if check_function(val, field_name, message):
        # Статус - Ок
        check_box.setCheckState(Qt.Checked)
        return True

    # Статус - ошибка
    check_box.setCheckState(Qt.Unchecked)
    return False


# КЛАСС АЛГОРИТМА ПРИЛОЖЕНИЯ
class GuiProgram(Ui_Dialog):
    def __init__(self, dialog):
        # ПОЛЯ КЛАССА
        # Объект данных и обработки
        self.data_signals = DataAndProcessing()

        # Название файлов
        self.file_name_without_gas = None
        self.file_name_with_gas = None
        # Строки файла
        self.lines_file_without_gas = None
        self.lines_file_with_gas = None

        # Параметры 1 графика
        self.ax1 = None
        self.fig1 = None
        self.canvas1 = None
        self.toolbar1 = None
        self.title1 = "График №1. Данные с исследуемым веществом и без."
        self.horizontal_axis_name1 = "Частота [МГц]"
        self.vertical_axis_name1 = "Гамма"

        self.name_without_gas = "Без вещества"
        self.color_without_gas = "#515151"
        self.name_with_gas = "C веществом"
        self.color_with_gas = "#DC7C02"
        self.list_absorbing = "Участок с линией поглощения"
        self.color_absorbing = "#36F62D"

        # Параметры 2 графика
        self.ax2 = None
        self.fig2 = None
        self.canvas2 = None
        self.toolbar2 = None
        # Для корреляции
        self.title_correlation = "График №2. Значение окна корреляции между данными."
        self.horizontal_axis_name_correlation = "Частота [МГц]"
        self.vertical_axis_name_correlation = "Корреляция"

        self.name_correlation = "Корреляция"
        self.color_correlation = "#310DEC"
        self.list_threshold = "Порог"
        self.color_threshold = "#EE2816"

        # Статистика таблицы
        self.total_rows = 0
        self.selected_rows = 0

        # Иконки checkbox в заголовке таблицы
        self.icon_now = 'selected'
        self.icon_status = {
            'empty': QIcon('./resource/table_checkbox/var2_color_image/no_red_24dp.png'),
            'mixed': QIcon('./resource/table_checkbox/var2_color_image/mixed_yellow_24dp.png'),
            'selected': QIcon('./resource/table_checkbox/var2_color_image/yes_green_24dp.png')
        }

        # ДЕЙСТВИЯ ПРИ ВКЛЮЧЕНИИ
        # Создаем окно
        Ui_Dialog.__init__(self)
        dialog.setWindowFlags(  # Передаем флаги создания окна
            QtCore.Qt.WindowCloseButtonHint |  # Кнопка закрытия
            QtCore.Qt.WindowMaximizeButtonHint |  # Кнопка развернуть
            QtCore.Qt.WindowMinimizeButtonHint  # Кнопка свернуть
        )
        # Устанавливаем пользовательский интерфейс
        self.setupUi(dialog)

        # Инициализируем фигуру в нашем окне
        figure1 = Figure()  # Готовим пустую фигуру
        axis1 = figure1.add_subplot(111)  # Пустой участок
        self.initialize_figure(figure1, axis1)  # Инициализируем!

        # Аналогично для второго графика
        figure2 = Figure()
        axis2 = figure2.add_subplot(111)
        self.initialize_figure2(figure2, axis2)

        # Обработчики нажатий - кнопок порядка работы
        self.pushButton_reading_file_no_gas.clicked.connect(self.plotting_without_noise)  # Загрузить данные с вакуума
        self.pushButton_reading_file_with_gas.clicked.connect(self.signal_plotting)  # Загрузить данные с газом
        self.pushButton_menu_calculate.clicked.connect(self.processing)  # Обработка сигнала

        # Режим диапазона частот обновился
        self.radioButton_all_range.clicked.connect(self.updating_frequency_range)
        self.radioButton_selected_range.clicked.connect(self.updating_frequency_range)
        # Изменение данных корреляции - Проверка ввода
        self.lineEdit_correlation.textEdited.connect(lambda: self.check_correlation_width(False))
        self.lineEdit_threshold_correlation.textEdited.connect(lambda: self.check_threshold_correlation(False))
        # Проверка ввода шума
        self.lineEdit_smoothing.textEdited.connect(lambda: self.check_smoothing_width(False))
        self.lineEdit_sigma_multiplier.textEdited.connect(lambda: self.check_sigma_multiplier(False))

        # Таблица
        self.initialize_table()  # Инициализация пустой таблицы с заголовками
        self.pushButton_save_table_to_file.clicked.connect(self.saving_data)  # Сохранить данные из таблицы в файл
        self.tableWidget_frequency_absorption.cellClicked.connect(self.get_clicked_cell)  # Выбрана строка таблицы
        self.lineEdit_window_width.textEdited.connect(self.check_window_width)  # Обновился текст ширины окна просмотра
        # Выбран заголовок таблицы
        self.tableWidget_frequency_absorption.horizontalHeader().sectionClicked.connect(self.click_handler)

    # ИНИЦИАЛИЗАЦИЯ
    # Пустой верхний график
    def initialize_figure(self, fig, ax):
        # Инициализирует фигуру matplotlib внутри контейнера GUI.
        # Вызываем только один раз при инициализации

        # Создание фигуры (self.fig и self.ax)
        self.fig1 = fig
        self.ax1 = ax
        # Создание холста
        self.canvas1 = FigureCanvas(self.fig1)
        self.layout_plot_1.addWidget(self.canvas1)
        self.canvas1.draw()
        # Создание Toolbar
        self.toolbar1 = NavigationToolbar(self.canvas1, self.widget_plot_1,
                                          coordinates=True)
        self.layout_plot_1.addWidget(self.toolbar1)

        # Пустой нижний график

    def initialize_figure2(self, fig, ax):
        # Инициализирует фигуру matplotlib внутри контейнера GUI.
        # Вызываем только один раз при инициализации

        # Создание фигуры (self.fig и self.ax)
        self.fig2 = fig
        self.ax2 = ax
        # Создание холста
        self.canvas2 = FigureCanvas(self.fig2)
        self.layout_plot_2.addWidget(self.canvas2)
        self.canvas2.draw()
        # Создание Toolbar
        self.toolbar2 = NavigationToolbar(self.canvas2, self.widget_plot_2,
                                          coordinates=True)
        self.layout_plot_2.addWidget(self.toolbar2)

    # Инициализация: Пустая таблица
    def initialize_table(self):
        self.tableWidget_frequency_absorption.clear()
        self.tableWidget_frequency_absorption.setColumnCount(3)
        self.tableWidget_frequency_absorption.setHorizontalHeaderLabels(["Частота МГц", "Гамма", ""])
        self.tableWidget_frequency_absorption.horizontalHeaderItem(0).setTextAlignment(Qt.AlignHCenter)
        self.tableWidget_frequency_absorption.horizontalHeaderItem(1).setTextAlignment(Qt.AlignHCenter)

        # Инициализация: Пустой верхний график

    ######################################
    #           ПРОВЕРКИ ВВОДА
    # (1) ДАННЫЕ
    # Без вещества
    def check_data_without_gas(self):
        # Если есть список строк из файла, возвращаем True
        if self.lines_file_without_gas:
            # Отображаем имя файла
            self.label_text_file_name_no_gas.setText(self.file_name_without_gas)
            # Статус загрузки  - Ок
            self.checkBox_download_no_gas.setCheckState(Qt.Checked)
            return True

        self.label_text_file_name_no_gas.setText("Нет данных")
        self.checkBox_download_no_gas.setCheckState(Qt.Unchecked)
        QMessageBox.warning(None, "Ошибка входных данных", 'Загрузите файл данных "Без исследуемого вещества"')
        return False

    # С веществом
    def check_data_with_gas(self):
        # Если есть список строк из файла, возвращаем True
        if self.lines_file_with_gas:
            # Отображаем имя файла
            self.label_text_file_name_with_gas.setText(self.file_name_with_gas)
            # Статус загрузки  - Ок
            self.checkBox_download_with_gas.setCheckState(Qt.Checked)
            return True

        self.label_text_file_name_with_gas.setText("Нет данных")
        self.checkBox_download_with_gas.setCheckState(Qt.Unchecked)
        QMessageBox.warning(None, "Ошибка входных данных", 'Загрузите файл данных "C исследуемым веществом"')
        return False

    # (2) Корреляция
    # Ширина
    def check_correlation_width(self, message=False):
        return check(
            line_edit=self.lineEdit_correlation,
            check_function=check_int_and_positive,
            check_box=self.checkBox_status_correlation,
            field_name="Ширина окна корреляция",
            message=message
        )

    # Порог
    def check_threshold_correlation(self, message=False):
        return check(
            line_edit=self.lineEdit_threshold_correlation,
            check_function=check_float_and_100to100,
            check_box=self.checkBox_status_threshold_correlation,
            field_name="Пороговое значение",
            message=message
        )

    # (3) ШУМ
    # Ширина сглаживания
    def check_smoothing_width(self, message=False):
        return check(
            line_edit=self.lineEdit_smoothing,
            check_function=check_int_and_positive,
            check_box=self.checkBox_status_smoothing,
            field_name="Ширина окна сглаживания",
            message=message
        )

    # Проверка множителя сигмы
    def check_sigma_multiplier(self, message=False):
        return check(
            line_edit=self.lineEdit_sigma_multiplier,
            check_function=check_float_and_positive,
            check_box=self.checkBox_status_sigma_multiplier,
            field_name="Множитель сигмы",
            message=message
        )

    # Ширина окна просмотра
    def check_window_width(self):
        return check(
            line_edit=self.lineEdit_window_width,
            check_function=check_float_and_positive,
            check_box=self.checkBox_status_window_width,
            field_name="Ширина окна просмотра",
            message=False
        )

    # (*) Корректность всех данных обработки
    def checking_all_processing_parameters(self, message=False):
        return (
                # (1) ДАННЫЕ
                self.check_data_without_gas() and
                self.check_data_with_gas() and
                # (2) Корреляция
                self.check_correlation_width(message) and
                self.check_threshold_correlation(message) and
                # (3) ШУМ
                self.check_smoothing_width(message) and
                self.check_sigma_multiplier(message)
                )

    ######################################
    #          ОСНОВНАЯ ПРОГРАММА
    # Основная программа - (1) Чтение и построение сигнала без шума
    def plotting_without_noise(self, skip_read=False):

        # Для чтения файла (если файл тот же - пропускаем)
        if not skip_read:
            # Вызов окна выбора файла
            # filename, filetype = QFileDialog.getOpenFileName(None,
            #                                                  "Выбрать файл без шума",
            #                                                  ".",
            #                                                  "Spectrometer Data(*.csv);;All Files(*)")
            self.file_name_without_gas = "25empty.csv"

            # Если имя файла не получено, сброс
            if not self.file_name_without_gas:
                return

            # Чтение данных
            with open(self.file_name_without_gas) as f:
                self.lines_file_without_gas = f.readlines()  # Читаем по строчно, в список

        # Проверяем статус чтения файла
        if not self.check_data_without_gas():
            return

        # В зависимости от режима - парсим
        if self.radioButton_selected_range.isChecked():
            # Считываем "Частоту от"
            start_frequency = self.lineEdit_start_range.text()
            # Проверка
            if not check_float_and_positive(start_frequency, "Частота от"):
                return
            # Приводим к дробному
            start_frequency = float(start_frequency)

            # Считываем "Частоту до"
            end_frequency = self.lineEdit_end_range.text()
            # Проверка
            if not check_float_and_positive(end_frequency, "Частота до"):
                return
            # Приводим к дробному
            end_frequency = float(end_frequency)

            # Проверка на правильность границ
            if end_frequency < start_frequency:
                QMessageBox.warning(None, "Ошибка ввода", "Частота 'от' больше 'до', в фильтре чтения. ")
                return
            # Парс данных в заданных частотах
            frequency, gamma = parser(self.lines_file_without_gas, start_frequency, end_frequency)
        else:
            # Парс данных
            frequency, gamma = parser_all_data(self.lines_file_without_gas)

        ####################################################
        # Нет частот -> Задаем
        if self.data_signals.data["frequency"].empty:
            self.data_signals.data["frequency"] = pd.Series(frequency)
        # Есть частоты -> Совпадют (загружаем гамму) или разные (чистим, загружаем гамму и частоты)
        else:
            # Частоты начала и конца
            data_frequency_star = self.data_signals.data["frequency"].iloc[0]
            data_frequency_end = self.data_signals.data["frequency"].iloc[-1]

            # Начало и конец не совпадает
            if data_frequency_star != frequency[0] or data_frequency_end != frequency[-1]:
                # Чистим данные
                self.data_signals.data = self.data_signals.data.head(0)
                # Заносим новые частоты
                self.data_signals.data["frequency"] = pd.Series(frequency)

        # Загружаем гамму
        self.data_signals.data["without_gas"] = pd.Series(gamma)
        ####################################################

        # Отрисовка
        self.updating_gas_graph()

    # Основная программа - (2) Чтение и построение полезного сигнала
    def signal_plotting(self, skip_read=False):
        if not skip_read:
            # Вызов окна выбора файла
            # filename, filetype = QFileDialog.getOpenFileName(None,
            #                                                  "Выбрать файл сигнала",
            #                                                  ".",
            #                                                  "Spectrometer Data(*.csv);;All Files(*)")
            self.file_name_with_gas = "25DMSO.csv"

            # Если имя файла не получено, сброс
            if not self.file_name_with_gas:
                return

            # Чтение данных
            with open(self.file_name_with_gas) as f:
                self.lines_file_with_gas = f.readlines()  # Читаем по строчно, в список

        if not self.check_data_with_gas():
            return

        if self.radioButton_selected_range.isChecked():
            # Считываем "Частоту от"
            start_frequency = self.lineEdit_start_range.text()
            # Проверка
            if not check_float_and_positive(start_frequency, "Частота от"):
                return
            # Приводим к дробному
            start_frequency = float(start_frequency)

            # Считываем "Частоту до"
            end_frequency = self.lineEdit_end_range.text()
            # Проверка
            if not check_float_and_positive(end_frequency, "Частота до"):
                return
            # Приводим к дробному
            end_frequency = float(end_frequency)

            # Проверка на правильность границ
            if end_frequency < start_frequency:
                QMessageBox.warning(None, "Ошибка ввода", "Частота 'от' больше 'до', в фильтре чтения. ")
                return

            # Парс данных в заданных частотах
            frequency, gamma = parser(self.lines_file_with_gas, start_frequency, end_frequency)
        else:
            # Парс данных
            frequency, gamma = parser_all_data(self.lines_file_with_gas)

        ####################################################
        # Нет частот -> Задаем
        if self.data_signals.data["frequency"].empty:
            self.data_signals.data["frequency"] = pd.Series(frequency)
        # Есть частоты -> Совпадют (загружаем гамму) или разные (чистим, загружаем гамму и частоты)
        else:
            # Частоты начала и конца
            data_frequency_star = self.data_signals.data["frequency"].iloc[0]
            data_frequency_end = self.data_signals.data["frequency"].iloc[-1]

            # Начало и конец не совпадает
            if data_frequency_star != frequency[0] or data_frequency_end != frequency[-1]:
                # Чистим данные
                self.data_signals.data = self.data_signals.data.head(0)
                # Заносим новые частоты
                self.data_signals.data["frequency"] = pd.Series(frequency)

        # Загружаем гамму
        self.data_signals.data["with_gas"] = pd.Series(gamma)
        ####################################################

        # Отрисовка
        self.updating_gas_graph()

    # Основная программа - (3) Расчет разницы, порога, интервалов, частот поглощения, отображение на графиках
    def processing(self):
        # Данные не корректны, сброс
        if not self.checking_all_processing_parameters(True):
            return

        # Запрос окна корреляции значения
        correlation_window_width = int(self.lineEdit_correlation.text())
        # Вызов расчета корреляции
        self.data_signals.correlate(correlation_window_width)

        # Расчет значения порога корреляции
        correlation_threshold = float(self.lineEdit_threshold_correlation.text()) / 100
        # Частоты начала и конца
        half_window_width = correlation_window_width // 2
        data_frequency_star = self.data_signals.data["frequency"].iloc[half_window_width]
        data_frequency_end = self.data_signals.data["frequency"].iloc[-half_window_width]
        # Данные о линии порога
        correlation_threshold_signal = pd.Series([correlation_threshold] * 2,
                                                 index=[data_frequency_star, data_frequency_end])
        # Отрисовка графика
        self.updating_correlation_graph(correlation_threshold_signal)

        # # Запрос порогового значения
        # threshold = float(self.lineEdit_threshold.text())
        #
        # # Если разницы нет, считать новую
        # if self.data_signals.data_difference.empty:
        #     # Вычитаем отсчеты сигнала с ошибкой и без
        #     self.data_signals.data_difference = self.data_signals.difference_empty_and_signal()
        #
        # # Значение порога от макс. значения графика ошибки
        # self.data_signals.threshold = self.data_signals.data_difference.max() * threshold / 100.
        #
        # # Перерисовка графика отклонений
        # threshold_signal = [self.data_signals.threshold] * self.data_signals.data_difference.size
        # self.updating_deviation_graph(threshold_signal)
        #
        # # Находим промежутки выше порога
        # self.data_signals.range_above_threshold(self.data_signals.threshold)
        #
        # # Перерисовка графика газа
        # self.updating_gas_graph(self.data_signals.absorption_line_ranges)
        #
        # # Нахождение пиков
        # self.data_signals.search_peaks()
        #
        # # Вывод данных в таблицу
        # self.table()

        # Переводим состояние интерфейса
        # self.state4_completed_processing()

    # РАБОТА С ТАБЛИЦЕЙ
    # Основная программа - (4) Заполение таблицы
    def table(self):
        # Задаем кол-во столбцов и строк
        self.tableWidget_frequency_absorption.setRowCount(len(self.data_signals.frequency_peak))
        self.tableWidget_frequency_absorption.setColumnCount(3)

        # Задаем название столбцов
        self.tableWidget_frequency_absorption.setHorizontalHeaderLabels(["Частота МГц", "Гамма"])

        # Устанавливаем начальное состояние иконки таблицы
        self.icon_now = 'selected'
        self.tableWidget_frequency_absorption.horizontalHeaderItem(2).setIcon(
            QIcon('./resource/table_checkbox/var2_color_image/yes_green_24dp.png')
        )
        # Заполняем таблицу
        index = 0
        for f, g in zip(self.data_signals.frequency_peak, self.data_signals.gamma_peak):
            # значения частоты и гаммы для 0 и 1 столбца
            self.tableWidget_frequency_absorption.setItem(index, 0, QTableWidgetItem(str('%.3f' % f)))
            self.tableWidget_frequency_absorption.setItem(index, 1, QTableWidgetItem(str('%.7E' % g)))

            # Элемент 2 столбца - checkbox, сохранения данных
            check_box = QtWidgets.QCheckBox()  # Создаем объект чекбокс
            check_box.setCheckState(Qt.Checked)  # Задаем состояние - нажат
            # Обработчик нажатия, с передачей отправителя
            check_box.toggled.connect(
                functools.partial(
                    self.frequency_selection, check_box
                )
            )
            self.tableWidget_frequency_absorption.setCellWidget(index, 2, check_box)  # Вводим в таблицу

            index += 1

        # Размеры строк выровнять под содержимое
        self.tableWidget_frequency_absorption.resizeColumnsToContents()
        # Начальные данные для статистики
        self.total_rows = len(self.data_signals.frequency_peak)
        self.selected_rows = self.total_rows
        self.frequency_selection()

    # Выбран check box таблицы, обновляем статистику под таблицей
    def frequency_selection(self, sender=None):
        # Если передали отправителя, проверяем состояние
        if sender is not None:
            # Если новое состояние - нажатое, то прибавляем к числу выбранных
            if sender.checkState() == Qt.CheckState.Checked:
                self.selected_rows += 1
            else:
                self.selected_rows -= 1

        # Создаем строки статистики
        text_statistics \
            = f'Выбрано {self.selected_rows} из {self.total_rows} ( {self.selected_rows / self.total_rows:.2%} ) '

        # Вывод в label под таблицей
        self.label_statistics_on_selected_frequencies.setText(text_statistics)

        # Обновляем статус у checkbox в заголовке
        if self.selected_rows == self.total_rows:
            self.update_table_icon('selected')
        elif self.selected_rows == 0:
            self.update_table_icon('empty')
        else:
            self.update_table_icon('mixed')

        # Возвращает текст статистики
        return text_statistics

    # Выбрана строка таблицы
    def get_clicked_cell(self, row):
        # Запрашиваем из окна, значение порога
        window_width = self.lineEdit_window_width.text()

        # Проверка на цифры и положительность
        if not self.check_window_width():
            return

        window_width = float(window_width)

        frequency_left_or_right = window_width / 2
        # Приближаем область с выделенной частотой
        frequency_start = self.data_signals.frequency_peak[row] - frequency_left_or_right
        frequency_end = self.data_signals.frequency_peak[row] + frequency_left_or_right

        self.ax1.set_xlim([frequency_start, frequency_end])

        self.ax1.set_ylim([
            self.data_signals.data_with_gas[frequency_start:frequency_end].min(),
            self.data_signals.gamma_peak[row] * 1.2
        ])

        # Перерисовываем
        self.canvas1.draw()

    # Кнопка сохранения таблицы
    def saving_data(self):
        # Проверка, что данные для сохранения есть
        if not self.data_signals.frequency_peak or not self.data_signals.gamma_peak:
            QMessageBox.warning(None, "Ошибка данных", "Нет данных для сохранения.")
            return

        # Рек-мое название файла
        recommended_file_name = f'F{self.data_signals.data_without_gas.index[0]}-' \
                                f'{self.data_signals.data_without_gas.index[-1]}'  # \
        # f'_threshold-{self.lineEdit_threshold.text()}'

        # Окно с выбором места сохранения
        file_name, file_type = QFileDialog.getSaveFileName(
            None,
            'Сохранение',
            recommended_file_name,
            "Text(*.txt);;Spectrometer Data(*.csv);;All Files(*)"
        )

        # Если имя не получено, прервать
        if not file_name:
            return

        # Открываем файл для чтения
        with open(file_name, "w") as file:

            # Заголовок/Название столбцов
            file.write("FREQUENCY:\tGAMMA:\n")

            # Перебираем по парно частоты и гаммы пиков; Записываем по строчно в файл
            for i in range(self.tableWidget_frequency_absorption.rowCount()):
                if self.tableWidget_frequency_absorption.cellWidget(i, 2).checkState() == Qt.CheckState.Checked:
                    f = self.tableWidget_frequency_absorption.item(i, 0).text()
                    g = self.tableWidget_frequency_absorption.item(i, 1).text()
                    file.write(f'{f}\t{g}\n')

            # Конец файла
            file.write('''***********************************************************\n''')
            file.write(self.frequency_selection())

    # Нажатие по заголовку и изменение состояния check box заголовка
    def click_handler(self, column):
        if column != 2:
            return

        if self.icon_now == 'selected':
            self.state_check_box_all_rows(False)
            self.update_table_icon('empty')
        else:
            self.state_check_box_all_rows(True)
            self.update_table_icon('selected')

    # Установить значение во все checkBox таблицы
    def state_check_box_all_rows(self, state):
        if state:
            state_check_box = Qt.Checked
        else:
            state_check_box = Qt.Unchecked

        # Перебираем строки
        for i in range(self.tableWidget_frequency_absorption.rowCount()):
            self.tableWidget_frequency_absorption.cellWidget(i, 2).setCheckState(state_check_box)

    # ОБНОВЛЕНИЕ
    # График газов
    def updating_gas_graph(self, list_absorbing=None):
        # Данных нет - сброс
        if self.data_signals.data["without_gas"].empty and self.data_signals.data["with_gas"].empty and list_absorbing:
            return

        # Отрисовка
        self.toolbar1.home()  # Возвращаем зум
        self.toolbar1.update()  # Очищаем стек осей (от старых x, y lim)
        # Очищаем график
        self.ax1.clear()
        # Название осей и графика
        self.ax1.set_xlabel(self.horizontal_axis_name1)
        self.ax1.set_ylabel(self.vertical_axis_name1)
        self.ax1.set_title(self.title1)
        # Если есть данные без газа, строим график
        if not self.data_signals.data["without_gas"].empty:
            self.ax1.plot(
                self.data_signals.data["frequency"],
                self.data_signals.data["without_gas"],
                color=self.color_without_gas, label=self.name_without_gas)
        # Если есть данные с газом, строим график
        if not self.data_signals.data["with_gas"].empty:
            self.ax1.plot(
                self.data_signals.data["frequency"],
                self.data_signals.data["with_gas"],
                color=self.color_with_gas, label=self.name_with_gas)
        # Выделение промежутков
        if list_absorbing:

            self.ax1.plot(
                list_absorbing[0].index, list_absorbing[0].values,
                color=self.color_absorbing, label=self.list_absorbing
            )

            for i in list_absorbing:
                self.ax1.plot(i.index, i.values, color=self.color_absorbing)
        # Рисуем сетку
        self.ax1.grid()
        # Инициирует отображение названия графика и различных надписей на нем.
        self.ax1.legend()
        # Убеждаемся, что все помещается внутри холста
        self.fig1.tight_layout()
        # Показываем новую фигуру в интерфейсе
        self.canvas1.draw()

    # График корреляции
    def updating_correlation_graph(self, threshold=None):
        # Данных нет - сброс
        if self.data_signals.data["correlate"].isnull().values.all() and not (threshold is None):
            return

        # Отрисовка
        self.toolbar2.home()  # Возвращаем зум
        self.toolbar2.update()  # Очищаем стек осей (от старых x, y lim)
        # Очищаем график
        self.ax2.clear()
        # Название осей и графика
        self.ax2.set_xlabel(self.horizontal_axis_name_correlation)
        self.ax2.set_ylabel(self.vertical_axis_name_correlation)
        self.ax2.set_title(self.title_correlation)
        # Если есть данные корреляции, строим график
        if not self.data_signals.data["correlate"].isnull().values.all():
            self.ax2.plot(
                self.data_signals.data["frequency"],
                self.data_signals.data["correlate"],
                color=self.color_correlation, label=self.name_correlation)
        # Если есть порог, строим график
        if not (threshold is None):
            self.ax2.plot(
                threshold.index,
                threshold.values,
                color=self.color_threshold, label=self.list_threshold)
        # Рисуем сетку
        self.ax2.grid()
        # Инициирует отображение названия графика и различных надписей на нем.
        self.ax2.legend()
        # Убеждаемся, что все помещается внутри холста
        self.fig2.tight_layout()
        # Показываем новую фигуру в интерфейсе
        self.canvas2.draw()
        self.toolbar2.push_current()  # Сохранить текущий статус zoom как домашний

    # График отклонений
    def updating_deviation_graph(self, threshold=None):
        # Данных нет - сброс
        if self.data_signals.data_difference.empty and not threshold:
            return

        # Отрисовка
        self.toolbar2.home()  # Возвращаем зум
        self.toolbar2.update()  # Очищаем стек осей (от старых x, y lim)
        # Очищаем график
        self.ax2.clear()
        # Название осей и графика
        self.ax2.set_xlabel(self.horizontal_axis_name2)
        self.ax2.set_ylabel(self.vertical_axis_name2)
        self.ax2.set_title(self.title2)
        # Если есть данные отклонения, строим график
        if not self.data_signals.data_difference.empty:
            self.ax2.plot(
                self.data_signals.data_difference.index,
                self.data_signals.data_difference.values,
                color=self.color_difference, label=self.name_difference)
        # Если есть порог, строим график
        if threshold:
            self.ax2.plot(
                self.data_signals.data_difference.index,
                threshold,
                color=self.color_threshold, label=self.list_threshold)
        # Рисуем сетку
        self.ax2.grid()
        # Инициирует отображение названия графика и различных надписей на нем.
        self.ax2.legend()
        # Убеждаемся, что все помещается внутри холста
        self.fig2.tight_layout()
        # Показываем новую фигуру в интерфейсе
        self.canvas2.draw()
        self.toolbar2.push_current()  # Сохранить текущий статус zoom как домашний

    # Диапазон частот
    def updating_frequency_range(self):
        # Если данных нет, сброс иначе обновляем
        if not self.lines_file_without_gas:
            return
        self.plotting_without_noise(True)

        # Если данных нет, сброс иначе обновляем
        if not self.lines_file_with_gas:
            return
        self.signal_plotting(True)

    # Обновляет иконку заголовка в соответствии со статусом
    def update_table_icon(self, status):
        # Запоминаем статус для следующего раза
        self.icon_now = status
        update_icon = self.icon_status[self.icon_now]  # Получаем новую иконку

        self.tableWidget_frequency_absorption.horizontalHeaderItem(2).setIcon(
            update_icon  # Вставляем новую иконку
        )