import numpy as np
import pandas as pd
from scipy import ndimage


# Поиск значений поглощения на интервале
def search_for_peak_on_interval(frequency_list, gamma_list):
    index_max_gamma = 0
    # Перебираем индексы в интервале и находим с макс значением
    for i in range(1, len(gamma_list)):
        if gamma_list[index_max_gamma] < gamma_list[i]:
            index_max_gamma = i
    # Возвращаем частоту и гамму поглощения
    return frequency_list[index_max_gamma], gamma_list[index_max_gamma]


# Класс хранения данных сигналов с шумом и без, разницы, списки частот поглощения
# Методов обработки и получения данных
class DataAndProcessing:
    def __init__(self):
        self.names_data = [
            "frequency",  # Без шума
            "without_gas",  # Без шума
            "with_gas",  # Сигнал
        ]
        self.names_processing = [
            "correlate",  # Корреляция
            "smoothed_without_gas",  # Сглаженный сигнал без шума
            "sigma",  # Сигма
            "sigma_with_multiplier",  # Сигма с множителем
            "difference",  # Разница сигналов
            "bool_difference",  # Логический массив, разница данных выше сигмы
            "bool_result",  # Логический массив, после обработки на ширину
        ]
        self.data = pd.DataFrame(columns=self.names_data + self.names_processing)

        # Пороговое значение для корреляции
        self.correlation_threshold = None

        # Без шума
        self.data_without_gas = pd.Series()

        # Сигнал
        self.data_with_gas = pd.Series()

        # Корреляция
        self.data_correlate = pd.Series()

        # Сглаженный сигнал без шума
        self.data_smoothed_without_gas = pd.Series()

        # Сигма
        self.data_sigma = pd.Series()

        # Разница сигналов
        self.data_difference = pd.Series()

        # Логический массив, разница данных выше сигмы
        self.bool_difference = pd.Series()

        # Логический массив, после обработки на ширину
        self.bool_result = pd.Series()

        # Список диапазонов пиков
        self.absorption_line_range = pd.Series()
        self.absorption_line_ranges = []

        # Список пиков
        self.gamma_peak = []
        self.frequency_peak = []

    # (*) Чистит данные процесса обработки
    def clear_data_processing(self):
        self.data[self.names_processing] = np.nan

    # (*) Чистит все данные (альтернатива:  self.data = self.data.head(0))
    def clear_data(self):
        self.data = self.data.head(0)

    # ОБРАБОТКА (1): Считаем корреляцию между данными
    def correlate(self, window_width):
        # Нет данных - сброс
        if self.data["without_gas"].isnull().values.all() or self.data["with_gas"].isnull().values.all():
            return

        # Если четное, доводим до не четного
        if window_width % 2 == 0:
            window_width += 1

        # Считаем корреляцию окном с корреляцией, результирующее значение в середину окна
        self.data["correlate"] = (self.data["without_gas"]) \
            .rolling(window_width, center=True) \
            .corr(self.data["with_gas"])

    # ОБРАБОТКА (2): Шум
    # (2.1): Сглаживание данных без вещества
    def smoothing_data_without_gas(self, window_width):
        # Если четное, доводим до не четного
        if window_width % 2 == 0:
            window_width += 1

        # Проходим окном со средним
        self.data["smoothed_without_gas"] = self.data["without_gas"].rolling(window_width, center=True).mean()

    # (2.2): Среднеквадратичное отклонение данных без газа со сглаживанием и без, в окне
    def sigma_finding(self, window_width):
        # Если четное, доводим до не четного
        if window_width % 2 == 0:
            window_width += 1

        # Находим разницу сглаженного и исходного сигнала без газа; Считаем среднеквадратичное отклонение
        self.data["sigma"] = (self.data["smoothed_without_gas"] - self.data["without_gas"]) \
            .rolling(window_width, center=True).std()

    # (2.3) Разница данных с газом и без (положительная часть)
    def difference_empty_and_signal(self):
        self.data["difference"] = (self.data["with_gas"] - self.data["without_gas"]).clip(lower=0)
        # Порог для корреляции задан -> Разница на участках меньше корреляции
        if not (self.correlation_threshold is None):
            self.data["difference"] = self.data["difference"] * (self.data["correlate"] < self.correlation_threshold)

    # (2.4) Домноженная сигма
    def multiply_sigma(self, sigma_multiplier):
        self.data["sigma_with_multiplier"] = self.data["sigma"] * sigma_multiplier

    # (2.5) Сравнение сигмы с разницей данных
    def remove_below_sigma(self, sigma_multiplier):
        # Если разницы нет - считаем
        if self.data["difference"].isnull().values.all():
            self.difference_empty_and_signal()

        # Если сигмы с множителем нет - считаем
        if self.data["sigma_with_multiplier"].isnull().values.all():
            self.multiply_sigma(sigma_multiplier)

        # Логический массив, разница данных выше сигмы
        self.data["bool_difference"] = self.data["difference"] > self.data["sigma_with_multiplier"]

    # ОБРАБОТКА (3): Ширина участка
    def width_filter(self, erosion=1, dilation=8):
        # Для результата, задаем начальное значение
        self.data["bool_result"] = self.data["bool_difference"]
        # Сворачиваем
        for i in range(erosion):
            self.data["bool_result"] = ndimage.binary_erosion(self.data["bool_result"])
        # Расширяем
        for i in range(dilation):
            self.data["bool_result"] = ndimage.binary_dilation(self.data["bool_result"])

    # ОБРАБОТКА (*): поиск индекс-значение линий поглощения, в данных выше порога

    # Находит интервалы индексов, значения которых выше порога
    def calculation_frequency_indexes_above_threshold(self, threshold_value):
        self.frequency_indexes_above_threshold.clear()
        index_interval = []
        last_index = 0
        for i in range(1, self.data_difference.size):
            # Если i-тый отсчет оказался больше порога
            if self.data_difference[self.data_difference.index[i]] >= threshold_value:
                # Если индекс идут друг за другом, записываем их в общий промежуток
                if last_index + 1 == i:
                    index_interval.append(i)
                # Иначе сохраняем интервал в общий список и начинаем новый
                else:
                    if index_interval:
                        self.frequency_indexes_above_threshold.append(index_interval)
                    index_interval = [i]
                # Сохраняем индекс последнего индекса
                last_index = i

        # Сохраняем результат в класс
        self.frequency_indexes_above_threshold.append(index_interval)

    # Интервалы значений выше порога, по интервалам индексов
    def index_to_val_range(self):
        # Очищаем от старых данных
        self.absorption_line_ranges.clear()

        # Перебираем интервалы индексов
        for interval_i in self.frequency_indexes_above_threshold:
            x = []
            y = []
            # Строим интервал значений
            for i in interval_i:
                x.append(self.data_with_gas.index[i])
                y.append(self.data_with_gas[self.data_with_gas.index[i]])

            # Интервал значений добавляем к общему списку
            self.absorption_line_ranges.append(pd.Series(y, index=x))

    # Находим интервалы значений выше порога
    def range_above_threshold(self, threshold_value):
        # Находим интервалы индексов выше порога
        self.calculation_frequency_indexes_above_threshold(threshold_value)
        # Находим интервалы значений
        self.index_to_val_range()

    # Перебирает интервалы значений и находит частоту поглощения
    def search_peaks(self):
        # Списки частот и гамм поглощения
        frequency_peaks = []
        gamma_peaks = []

        # Перебираем интервалы выше порога
        for i in self.absorption_line_ranges:
            # Находим значение поглощения
            f, g = search_for_peak_on_interval(list(i.index), list(i.values))

            # Записываем в общий список
            frequency_peaks.append(f)
            gamma_peaks.append(g)

        # Сохраняем в классе
        self.frequency_peak = frequency_peaks
        self.gamma_peak = gamma_peaks

        # Возвращаем списки частот и гамм поглощения
        return frequency_peaks, gamma_peaks
