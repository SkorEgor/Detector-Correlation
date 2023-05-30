# coding: utf-8
from gui import Ui_Dialog
from data_and_processing import DataAndProcessing
from graph import Graph
from update_graphics import UpdateGraphics
from color_theme import ColorTheme

import functools

import pandas as pd

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

import matplotlib

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
def check_float_and_positive(val, field_name, icon=None, message=False):
    try:
        val = float(val)

    except ValueError:
        if message:
            QMessageBox.warning(icon, "Ошибка ввода", f'Введите число в поле "{field_name!r}".')
        return False

    # Проверка положительности
    if val < 0:
        if message:
            QMessageBox.warning(icon, "Ошибка ввода", f'Введите положительное число в поле "{field_name!r}".')
        return False

    return True


# Целое, больше нуля (для окна корреляции)
def check_int_and_positive(val, field_name, icon=None, message=False):
    try:
        val = int(val)

    except ValueError:
        if message:
            QMessageBox.warning(icon, "Ошибка ввода", f'Введите целое число в поле "{field_name!r}".')
        return False

    # Проверка положительности
    if val < 0:
        if message:
            QMessageBox.warning(icon, "Ошибка ввода", f'Введите положительное число в поле "{field_name!r}".')
        return False

    return True


# Дробное, от 0 до 100 (для процентов и ширины окна просмотра)
def check_float_and_0to100(val, field_name, icon=None, message=False):
    try:
        val = float(val)

    except ValueError:
        if message:
            QMessageBox.warning(icon, "Ошибка ввода", f'Введите число в поле "{field_name!r}".')
        return False

    # Проверка на диапазон
    if val < 0 or 100 < val:
        if message:
            QMessageBox.warning(icon, "Ошибка ввода", f'Введите число от 0 до 100 в поле "{field_name!r}".')
        return False

    return True


# Дробное, от -100 до 100 (для процентов и ширины окна просмотра)
def check_float_and_100to100(val, field_name, icon=None, message=False):
    try:
        val = float(val)

    except ValueError:
        if message:
            QMessageBox.warning(icon, "Ошибка ввода", f'Введите число в поле "{field_name!r}".')
        return False

    # Проверка на диапазон
    if val < -100 or 100 < val:
        if message:
            QMessageBox.warning(icon, "Ошибка ввода", f'Введите число от -100 до 100 в поле "{field_name!r}".')
        return False

    return True


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

        # Параметры 1 графика
        self.graph_1 = Graph(
            layout=self.layout_plot_1,
            widget=self.widget_plot_1,
            layout_toolbar=self.layout_toolbar_1
        )

        # Параметры 2 графика
        self.graph_2 = Graph(
            layout=self.layout_plot_2,
            widget=self.widget_plot_2,
            layout_toolbar=self.layout_toolbar_graphics_2
        )

        # Синхронизация отображения данных на 1 графике
        self.update_graphics_1 = UpdateGraphics(
            graph=self.graph_1,
            data=self.data_signals,
            radio_button_data=self.radioButton_data_graph_1,
            radio_button_correlation=self.radioButton_correlation_graph_1,
            radio_button_sigma=self.radioButton_sigma_grapgh_1,
            radio_button_noise=self.radioButton_noise_graph_1,
            radio_button_width=self.radioButton_width_graph_1,
        )

        # Синхронизация отображения данных на 1 графике
        self.update_graphics_2 = UpdateGraphics(
            graph=self.graph_2,
            data=self.data_signals,
            radio_button_data=self.radioButton_data_graph_2,
            radio_button_correlation=self.radioButton_correlation_graph_2,
            radio_button_sigma=self.radioButton_sigma_grapgh_2,
            radio_button_noise=self.radioButton_noise_graph_2,
            radio_button_width=self.radioButton_width_graph_2,
        )

        # Обработчик переключения цветовой темы
        self.checkBox_color_theme.toggled.connect(self.update_color_theme)

        # Обработчики нажатий - кнопок порядка работы
        self.pushButton_reading_file_no_gas.clicked.connect(self.plotting_without_noise)  # Загрузить данные с вакуума
        self.pushButton_reading_file_with_gas.clicked.connect(self.signal_plotting)  # Загрузить данные с газом
        self.pushButton_menu_calculate.clicked.connect(self.processing)  # Обработка сигнала

        # ИЗМЕНЕНИЕ ПОЛЕЙ ВВОДА В МЕНЮ
        # Режим диапазона частот обновился
        self.radioButton_all_range.clicked.connect(self.updating_frequency_range)
        self.radioButton_selected_range.clicked.connect(self.updating_frequency_range)
        # Изменение данных корреляции - Проверка ввода
        self.lineEdit_correlation.textEdited.connect(lambda: self.check_correlation_width(False))
        self.lineEdit_threshold_correlation.textEdited.connect(lambda: self.check_threshold_correlation(False))
        # Проверка ввода шума
        self.lineEdit_smoothing.textEdited.connect(lambda: self.check_smoothing_width(False))
        self.lineEdit_smoothing_sigma_window_width.textEdited.connect(lambda: self.check_sigma_window_width(False))
        self.lineEdit_sigma_multiplier.textEdited.connect(lambda: self.check_sigma_multiplier(False))
        # Проверка ввода ширина участка
        self.lineEdit_erosion.textEdited.connect(lambda: self.check_erosion(False))
        self.lineEdit_extension.textEdited.connect(lambda: self.check_extension(False))

        # Таблица
        self.initialize_table()  # Инициализация пустой таблицы с заголовками
        self.pushButton_save_table_to_file.clicked.connect(self.saving_data)  # Сохранить данные из таблицы в файл
        self.tableWidget_frequency_absorption.cellClicked.connect(self.get_clicked_cell)  # Выбрана строка таблицы
        self.comboBox_select_table_view.currentIndexChanged.connect(self.table)
        self.lineEdit_window_width.textEdited.connect(
            lambda: self.check_window_width(False))  # Обновился текст ширины окна просмотра
        # Выбран заголовок таблицы
        self.tableWidget_frequency_absorption.horizontalHeader().sectionClicked.connect(self.click_handler)

        # Отрисовка (Задержка учета расчета геометрии окна)
        QTimer.singleShot(100, self.update_graphics)

    # Смена цветового стиля интерфейса
    def update_color_theme(self, state):
        if state:
            self.widget_style_sheet.setStyleSheet(ColorTheme.dark_style_sheet)
        else:
            self.widget_style_sheet.setStyleSheet(ColorTheme.light_style_sheet)

    # Инициализация: Пустая таблица
    def initialize_table(self):
        self.tableWidget_frequency_absorption.clear()
        self.tableWidget_frequency_absorption.setColumnCount(3)
        self.tableWidget_frequency_absorption.setHorizontalHeaderLabels(["Частота МГц", "Гамма", ""])
        self.tableWidget_frequency_absorption.horizontalHeaderItem(0).setTextAlignment(Qt.AlignHCenter)
        self.tableWidget_frequency_absorption.horizontalHeaderItem(1).setTextAlignment(Qt.AlignHCenter)
        self.tableWidget_frequency_absorption.resizeColumnsToContents()

    ######################################
    #           ПРОВЕРКИ ВВОДА
    # (*) Шаблон проверки поля
    def check(self, line_edit, check_function, check_box, field_name, message=False):
        # Запрос порогового значения
        val = line_edit.text()
        if check_function(
                val=val,
                field_name=field_name,
                icon=self.label_imag_app,
                message=message
        ):
            # Статус - Ок
            check_box.setCheckState(Qt.Checked)
            return True

        # Статус - ошибка
        check_box.setCheckState(Qt.Unchecked)
        return False

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
        QMessageBox.warning(self.label_imag_app, "Ошибка входных данных",
                            'Загрузите файл данных "Без исследуемого вещества"')
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
        QMessageBox.warning(self.label_imag_app, "Ошибка входных данных",
                            'Загрузите файл данных "C исследуемым веществом"')
        return False

    # (1.1) Диапазон частот
    # Начало
    def check_start_frequency(self):
        return check_float_and_positive(
            val=self.lineEdit_start_range.text(),
            field_name="Частота от",
            icon=self.label_imag_app,
            message=True
        )

    # Конец
    def check_end_frequency(self):
        return check_float_and_positive(
            val=self.lineEdit_end_range.text(),
            field_name="Частота до",
            icon=self.label_imag_app,
            message=True
        )

    def check_frequency_range(self):
        return self.check_start_frequency() and self.check_end_frequency

    # (2) Корреляция
    # Ширина
    def check_correlation_width(self, message=False):
        return self.check(
            line_edit=self.lineEdit_correlation,
            check_function=check_int_and_positive,
            check_box=self.checkBox_status_correlation,
            field_name="Ширина окна корреляция",
            message=message
        )

    # Порог
    def check_threshold_correlation(self, message=False):
        return self.check(
            line_edit=self.lineEdit_threshold_correlation,
            check_function=check_float_and_100to100,
            check_box=self.checkBox_status_threshold_correlation,
            field_name="Пороговое значение",
            message=message
        )

    # (3) ШУМ
    # Ширина сглаживания
    def check_smoothing_width(self, message=False):
        return self.check(
            line_edit=self.lineEdit_smoothing,
            check_function=check_int_and_positive,
            check_box=self.checkBox_status_smoothing,
            field_name="Ширина окна сглаживания",
            message=message
        )

    # Ширина сигмы
    def check_sigma_window_width(self, message=False):
        return self.check(
            line_edit=self.lineEdit_smoothing_sigma_window_width,
            check_function=check_int_and_positive,
            check_box=self.checkBox_status_sigma_window_width,
            field_name="Ширина окна сигмы",
            message=message
        )

    # Проверка множителя сигмы
    def check_sigma_multiplier(self, message=False):
        return self.check(
            line_edit=self.lineEdit_sigma_multiplier,
            check_function=check_float_and_positive,
            check_box=self.checkBox_status_sigma_multiplier,
            field_name="Множитель сигмы",
            message=message
        )

    # (4) Ширина участка
    # Сжатие
    def check_erosion(self, message=False):
        return self.check(
            line_edit=self.lineEdit_erosion,
            check_function=check_int_and_positive,
            check_box=self.checkBox_status_erosion,
            field_name="Сжатие",
            message=message
        )

    # Расширение
    def check_extension(self, message=False):
        return self.check(
            line_edit=self.lineEdit_extension,
            check_function=check_int_and_positive,
            check_box=self.checkBox_status_extension,
            field_name="Расширение",
            message=message
        )

    # (*) Ширина окна просмотра
    def check_window_width(self, message=False):
        return self.check(
            line_edit=self.lineEdit_window_width,
            check_function=check_float_and_positive,
            check_box=self.checkBox_status_window_width,
            field_name="Ширина окна просмотра",
            message=message
        )

    # (ALL) Корректность всех данных обработки
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
                self.check_sigma_multiplier(message) and
                self.check_sigma_window_width(message) and
                # (4) Ширина участка
                self.check_erosion(message) and
                self.check_extension(message)
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
            # Проверяем корректность диапазона
            if not self.check_frequency_range():
                return

            # Считываем "Частоту от" и приводим к дробному
            start_frequency = float(self.lineEdit_start_range.text())
            # Считываем "Частоту до" и приводим к дробному
            end_frequency = float(self.lineEdit_end_range.text())

            # Проверка на правильность границ
            if end_frequency < start_frequency:
                QMessageBox.warning(self.label_imag_app, "Ошибка ввода", "Частота 'от' больше 'до', в фильтре чтения. ")
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
                self.data_signals.clear_data()
                # Заносим новые частоты
                self.data_signals.data["frequency"] = pd.Series(frequency)

        # Загружаем гамму
        self.data_signals.data["without_gas"] = pd.Series(gamma)
        ####################################################

        # Отрисовка
        self.update_graphics()

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
            # Проверяем корректность диапазона
            if not self.check_frequency_range():
                return

            # Считываем "Частоту от" и приводим к дробному
            start_frequency = float(self.lineEdit_start_range.text())
            # Считываем "Частоту до" и приводим к дробному
            end_frequency = float(self.lineEdit_end_range.text())

            # Проверка на правильность границ
            if end_frequency < start_frequency:
                QMessageBox.warning(self.label_imag_app, "Ошибка ввода", "Частота 'от' больше 'до', в фильтре чтения. ")
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
                self.data_signals.clear_data()
                # Заносим новые частоты
                self.data_signals.data["frequency"] = pd.Series(frequency)

        # Загружаем гамму
        self.data_signals.data["with_gas"] = pd.Series(gamma)
        ####################################################

        # Отрисовка
        self.update_graphics()

    # Основная программа - (3) Расчет разницы, порога, интервалов, частот поглощения, отображение на графиках
    def processing(self):
        # Данные не корректны, сброс
        if not self.checking_all_processing_parameters(True):
            return

        # Проверяем диапазон чтения и обновляем исходные данные
        self.updating_frequency_range()

        # ЗАПРОС ПАРАМЕТРОВ ОБРАБОТКИ
        # (1) Запрос окна корреляции значения
        correlation_window_width = int(self.lineEdit_correlation.text())
        # Порог корреляции
        correlation_threshold = float(self.lineEdit_threshold_correlation.text()) / 100
        # (2.1) Ширина окна сглаживания
        smooth_window_width = int(self.lineEdit_smoothing.text())
        # Ширина окна сигмы
        sigma_window_width = int(self.lineEdit_smoothing_sigma_window_width.text())
        # (2.2) Множитель сигмы
        sigma_multiplier = float(self.lineEdit_sigma_multiplier.text())
        # (3) Запрашиваем параметры ширина участка
        erosion = int(self.lineEdit_erosion.text())
        dilation = int(self.lineEdit_extension.text())

        # ОБРАБОТКА
        self.data_signals.all_processing(
            correlation_window_width=correlation_window_width,
            correlation_threshold=correlation_threshold,
            smooth_window_width=smooth_window_width,
            sigma_window_width=sigma_window_width,
            sigma_multiplier=sigma_multiplier,
            erosion=erosion,
            dilation=dilation)

        # Отрисовка
        self.update_graphics()
        self.table(
            self.comboBox_select_table_view.currentIndex()  # Индекс выбранного элемента
        )

    # РАБОТА С ТАБЛИЦЕЙ
    # Основная программа - (4) Заполение таблицы
    def table(self, index_filter):
        # Нет точек поглощения - сброс
        if self.data_signals.point_absorption_after_correlation.empty:
            return
        print("ok")
        # Задаем кол-во столбцов и строк
        self.tableWidget_frequency_absorption.setColumnCount(3)  # Столбцы
        # Строки
        number_rows = None
        # Фильтр Крест
        if index_filter == 1:
            number_rows = (~self.data_signals.point_absorption_after_correlation["status"]) \
                .sum()
        # Фильтр Галочка
        elif index_filter == 2:
            number_rows = self.data_signals.point_absorption_after_correlation["status"] \
                .sum()
        # Фильтр - отображать все
        else:
            number_rows = self.data_signals.point_absorption_after_correlation["status"] \
                .count()
        self.tableWidget_frequency_absorption.setRowCount(number_rows)
        print("ok")
        # Задаем название столбцов
        self.tableWidget_frequency_absorption.setHorizontalHeaderLabels(["Частота МГц", "Гамма"])

        # Устанавливаем начальное состояние иконки таблицы
        # Фильтр Крест
        if index_filter == 1:
            self.icon_now = 'empty'
        # Фильтр Галочка
        elif index_filter == 2:
            self.icon_now = 'selected'
        # Фильтр - отображать все
        else:
            # Если все элементы True - то всё выбрано
            if self.data_signals.point_absorption_after_correlation["status"].all():
                self.icon_now = 'selected'
            # Хотя бы один True - смешанный вариант
            elif self.data_signals.point_absorption_after_correlation["status"].any():
                self.icon_now = 'mixed'
            else:
                self.icon_now = 'empty'
            self.update_table_icon(self.icon_now)
        print("ok")
        # Заполняем таблицу
        index = 0
        count_check = 0
        for f, g, status, index_data in zip(
                self.data_signals.point_absorption_after_correlation["frequency"],
                self.data_signals.point_absorption_after_correlation["gamma"],
                self.data_signals.point_absorption_after_correlation["status"],
                list(self.data_signals.point_absorption_after_correlation.index)
        ):
            # Значение True и фильтр Крест - не отображать
            if status and index_filter == 1:
                continue
            # Значение False и фильтр Галочка - не отображать
            if (not status) and index_filter == 2:
                continue
            # значения частоты и гаммы для 0 и 1 столбца
            self.tableWidget_frequency_absorption.setItem(index, 0, QTableWidgetItem(str('%.3f' % f)))
            self.tableWidget_frequency_absorption.setItem(index, 1, QTableWidgetItem(str('%.7E' % g)))

            # Элемент 2 столбца - checkbox, сохранения данных
            check_box = QtWidgets.QCheckBox()  # Создаем объект чекбокс
            if status:
                check_box.setCheckState(Qt.Checked)  # Задаем состояние - нажат
                count_check += 1
            else:
                check_box.setCheckState(Qt.Unchecked)  # Задаем состояние - нажат
            # Обработчик нажатия, с передачей отправителя
            check_box.toggled.connect(
                functools.partial(
                    self.frequency_selection, check_box, index_data
                )
            )
            self.tableWidget_frequency_absorption.setCellWidget(index, 2, check_box)  # Вводим в таблицу

            index += 1
        print("ok")
        # Размеры строк выровнять под содержимое
        self.tableWidget_frequency_absorption.resizeColumnsToContents()
        # Начальные данные для статистики
        # Всего строк
        # Альтернатива self.data_signals.point_absorption_after_correlation[
        #             self.data_signals.point_absorption_after_correlation.columns[0]].count()
        self.total_rows = index
        # Выбранных строк
        # Альтернатива self.data_signals.point_absorption_after_correlation["status"].value_counts()[True]
        self.selected_rows = count_check
        print("ok")
        self.frequency_selection()

    # Выбран check box таблицы, обновляем статистику под таблицей
    def frequency_selection(self, sender=None, index=None):

        # Если передали отправителя, проверяем состояние
        if sender is not None:
            # Если новое состояние - нажатое, то прибавляем к числу выбранных
            if sender.checkState() == Qt.CheckState.Checked:
                self.selected_rows += 1
            else:
                self.selected_rows -= 1

        # Если передали индекс, инвертируем состояние
        if index is not None:
            self.data_signals.point_absorption_after_correlation.at[index, "status"] = \
                not self.data_signals.point_absorption_after_correlation["status"][index]

        # Процент выбранных
        if self.total_rows == 0:
            percent_chosen = 0
        else:
            percent_chosen = self.selected_rows / self.total_rows

        # Создаем строки статистики
        text_statistics \
            = f'Выбрано {self.selected_rows} из {self.total_rows} ( {percent_chosen:.2%} ) '
        print(text_statistics)
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
        # Проверка на корректность ширины окна просмотра
        if not self.check_window_width(True):
            return

        # Запрашиваем ширину окна просмотра
        window_width = self.lineEdit_window_width.text()
        window_width = float(window_width)

        frequency_left_or_right = window_width / 2

        # Приближаем область с выделенной частотой
        # находим границы области
        frequency_peak = self.data_signals.point_absorption_after_correlation["frequency"].iloc[row]

        frequency_start = frequency_peak - frequency_left_or_right
        frequency_end = frequency_peak + frequency_left_or_right

        # Включаем верхний график, в режим данных
        self.radioButton_data_graph_1.setChecked(Qt.CheckState.Checked)  # Включаем кнопку
        self.update_graphics_1.radio_button_updated(self.radioButton_data_graph_1)  # Обновляем график

        self.graph_1.zoom_area(
            x_min=frequency_start,
            x_max=frequency_end,
            y_min=self.data_signals.data["with_gas"][
                self.data_signals.data["frequency"].between(frequency_start, frequency_end)].min(),
            y_max=self.data_signals.point_absorption_after_correlation["gamma"].iloc[row] * 1.2
        )

    # Кнопка сохранения таблицы
    def saving_data(self):
        # Проверка, что данные для сохранения есть
        if self.data_signals.point_absorption_after_correlation.empty:
            QMessageBox.warning(None, "Ошибка данных", "Нет данных для сохранения.")
            return

        # Рек-мое название файла
        recommended_file_name = f'F{self.data_signals.data["frequency"].iloc[0]}-' \
                                f'{self.data_signals.data["frequency"].iloc[-1]}_correlate'

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

    # ВСЯКОЕ
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

    # Обновить графики
    def update_graphics(self):
        self.update_graphics_1.update_graph()
        self.update_graphics_2.update_graph()
