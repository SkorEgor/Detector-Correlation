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
            "intervals_after_correlation",  # Интервалы поглощения после корреляции
        ]
        self.data = pd.DataFrame(columns=self.names_data + self.names_processing)

        # Пороговое значение для корреляции
        self.correlation_threshold = None

        # Точки линий поглощения, от корреляции (строчки: индекс и гамма)
        self.point_absorption_after_correlation = pd.DataFrame()

        # Точки линий поглощения, после всех обработок (строчки: индекс и частота)
        self.point_absorption_after_processing = pd.Series()

    # (*) Чистит данные процесса обработки
    def clear_data_processing(self):
        self.data[self.names_processing] = np.nan
        self.correlation_threshold = None
        self.point_absorption_after_correlation = pd.DataFrame()

    # (*) Чистит все данные (альтернатива:  self.data = self.data.head(0))
    def clear_data(self):
        self.data = self.data.head(0)
        self.correlation_threshold = None
        self.point_absorption_after_correlation = pd.DataFrame()

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
            .rolling(window_width) \
            .corr(self.data["with_gas"])
        # ПО СМЫСЛУ ДОЛЖЕН БЫТЬ СДВИГ!!! .shift(periods=-window_width//2)
        # или .rolling(window_width, center=True)

    # ОБРАБОТКА (1.1):Возвращаем серию "порогового значения корреляции" для построения
    def data_correlation_threshold(self):
        data_frequency_star = self.data["correlate"].first_valid_index()
        data_frequency_end = self.data["correlate"].last_valid_index()
        return pd.Series([self.correlation_threshold] * 2,
                         index=[self.data["frequency"][data_frequency_star],
                                self.data["frequency"][data_frequency_end]])

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

    # ОБРАБОТКА (*): ИНТЕРВАЛЫ И ТОЧКИ ЛИНИЙ ПОГЛОЩЕНИЯ
    # ОБЩИЕ МЕТОДЫ
    # (1) ИНТЕРВАЛА ПОГЛОЩЕНИЯ
    # Поиск участков выше порога -> получение индексов начала и конца интервала
    # ---------------------------------------------------------------------
    # В формате индекс: начало интервала; значение: конец интервала. Пример, при пороге 4:
    # ind: 0 1 2 3 4 5 6 7 8 9 10-> ind: 1 5 9 -> (пары: с 1 по 2; с 5-6; с 9 по 9)
    # val: 1 5 8 1 3 9 8 1 0 8 0 -> val: 2 6 9
    @staticmethod
    def find_intervals_borders(samples, threshold):
        bool_samples = samples[samples >= threshold]
        xx = bool_samples.groupby((bool_samples.index != bool_samples.index.to_series().shift() + 1)
                                  .cumsum()).apply(lambda grp: (grp.index[0], grp.index[-1]))
        return pd.Series(xx.str[1].values, index=xx.str[0])

    # (2) ТОЧКИ ПОГЛОЩЕНИЯ
    # (2.1) Поиск участков выше порога -> на участке применяем функцию поиск ТОЧКИ ПОГЛОЩЕНИЯ
    # ---------------------------------------------------------------------
    # В формате индекс: начало интервала; значение: конец интервала. Пример, при пороге 4:
    # ind: 0 1 2 3 4 5 6 7 8 9 10-> ind: 2 5 9 -> (в интервале от 1-2: 1 мах 8;...)
    # val: 1 5 8 1 3 9 8 1 0 8 0 -> val: 8 9 8
    # Пример samples: bool_samples = samples[samples >= threshold] - массив индексов и значений
    # без пар индексов не подходящих под условие
    @staticmethod
    def find_point(samples):
        xx = samples.groupby((samples.index != samples.index.to_series().shift() + 1)
                             .cumsum()).apply(lambda grp: (DataAndProcessing.max_index_val(grp)))
        return pd.Series(xx.str[1].values, index=xx.str[0].values)

    # (2.2) Метод поиска линии поглощения на участке
    @staticmethod
    def max_index_val(mass):
        index = mass.idxmax()
        val = mass[index]
        return index, val

    # ОБРАБОТКА (*): ИНТЕРВАЛЫ И ТОЧКИ ЛИНИЙ ПОГЛОЩЕНИЯ
    # АЛГОРИТМ ПОСЛЕ КОРРЕЛЯЦИИ
    # (1) Интервалы линий поглощение после корреляции
    def find_intervals_after_correlation(self):
        # нет данных - сброс
        if self.correlation_threshold is None:
            return

        # Все что выше порога, приобретает значение корреляции
        self.data.loc[
            self.data["correlate"] <= self.correlation_threshold, "intervals_after_correlation"] = self.data["with_gas"]

    # (2) Точки линий поглощения, от корреляции (строчки: индекс и гамма)
    def find_point_after_correlation(self):
        self.point_absorption_after_correlation = pd.DataFrame({
            "gamma": DataAndProcessing.find_point(
                self.data["with_gas"][  # В качестве значений - гамма с веществом
                    self.data["correlate"] <= self.correlation_threshold  # Оставляем элементы ниже порога
                    ]
            )})
        self.point_absorption_after_correlation["frequency"] = \
            self.data["frequency"][self.point_absorption_after_correlation.index]
        self.point_absorption_after_correlation["status"] = False

    # АЛГОРИТМ ПОСЛЕ КОРРЕЛЯЦИИ

    def find_intervals_after_processing(self):
        processing = self.data["frequency"][self.data["bool_result"]]
        self.point_absorption_after_correlation["status"] = self.point_absorption_after_correlation["status"].index.\
            isin(processing.index)
        print("status",self.point_absorption_after_correlation["status"] )

    def find_intervals_after_processing2(self):
        samples = self.data["frequency"][self.data.bool_result]
        self.point_absorption_after_correlation=samples[
            samples.index.isin(self.point_absorption_after_correlation.index)]
