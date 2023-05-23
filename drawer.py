from graph import Graph
from data_and_processing import DataAndProcessing


# ШАБЛОН ОТРИСОВКИ ГРАФИКОВ
# Очистка и подпись графика (вызывается в начале)
def cleaning_and_chart_graph(graph: Graph, x_label, y_label, title):
    graph.toolbar.home()  # Возвращаем зум
    graph.toolbar.update()  # Очищаем стек осей (от старых x, y lim)
    # Очищаем график
    graph.axis.clear()
    # Название осей и графика
    graph.axis.set_xlabel(x_label)
    graph.axis.set_ylabel(y_label)
    graph.axis.set_title(title)


# Отрисовка (вызывается в конце)
def draw_graph(graph: Graph, chart_caption: bool = True):
    # Рисуем сетку
    graph.axis.grid()
    # Инициирует отображение названия графиков
    if chart_caption:
        graph.axis.legend()
    # Убеждаемся, что все помещается внутри холста
    graph.figure.tight_layout()
    # Показываем новую фигуру в интерфейсе
    graph.canvas.draw()


# Отрисовка при - отсутствии данных
def no_data(graph: Graph):
    graph.axis.text(0.5, 0.5, "Нет данных",
                    fontsize=14,
                    horizontalalignment='center',
                    verticalalignment='center')
    # Отрисовка, без подписи данных
    draw_graph(graph, chart_caption=False)


class Drawer:
    # График №1 Данные
    title_data = "График №1. Данные с исследуемым веществом и без."
    horizontal_axis_name_data = "Частота [МГц]"
    vertical_axis_name_data = "Гамма"

    name_without_gas = "Без вещества"
    color_without_gas = "#515151"
    name_with_gas = "C веществом"
    color_with_gas = "#DC7C02"
    list_absorbing = "Участок с линией поглощения"
    color_absorbing = "#36F62D"

    # График №2 Корреляция
    title_correlation = "График №2. Значение окна корреляции между данными."
    horizontal_axis_name_correlation = "Частота [МГц]"
    vertical_axis_name_correlation = "Корреляция"

    name_correlation = "Корреляция"
    color_correlation = "#310DEC"
    list_threshold = "Порог"
    color_threshold = "#EE2816"

    # График №3 Сглаживание
    title_smoothing = "График №3. Исходные и сглаженные данные 'без вещества'."
    horizontal_axis_name_smoothing = horizontal_axis_name_data
    vertical_axis_name_smoothing = vertical_axis_name_data

    name_smoothing = "Сглаженные данные"
    color_smoothing = "r"  # !!!!!!!!!!!!!!!ПОДБЕРИ ЦВЕЕЕЕЕЕТ!!!!!!!!!!!

    # График №4 Сигмы и разницы
    title_sigma_and_difference = "График №4. Сигма и разница между данными."
    horizontal_axis_name_sigma_and_difference = horizontal_axis_name_data
    vertical_axis_name_sigma_and_difference = vertical_axis_name_data

    name_sigma = "Сигма"
    color_sigma = "r"  # !!!!!!!!!!!!!!!ПОДБЕРИ ЦВЕЕЕЕЕЕТ!!!!!!!!!!!
    name_difference = "Разница данных"
    color_difference = "g"  # !!!!!!!!!!!!!!!ПОДБЕРИ ЦВЕЕЕЕЕЕТ!!!!!!!!!!!

    # График №5 Фильтрация по ширине участка
    title_filter_by_area_width = "График №5. Результат фильтрации по ширине участка"
    horizontal_axis_name_filter_by_area_width = horizontal_axis_name_data
    vertical_axis_name_filter_by_area_width = ""  # !!!!!!!!!!!!!!!????????!!!!!!!!!!!

    name_filter_beginning = "До"
    color_filter_beginning = "r"  # !!!!!!!!!!!!!!!ПОДБЕРИ ЦВЕЕЕЕЕЕТ!!!!!!!!!!!
    name_filter_end = "После"
    color_filter_end = "g"  # !!!!!!!!!!!!!!!ПОДБЕРИ ЦВЕЕЕЕЕЕТ!!!!!!!!!!!

    # График газов
    @staticmethod
    def updating_gas_graph(
            graph: Graph,
            data_signals: DataAndProcessing,
    ):
        # Очистка, подпись графика и осей (вызывается в начале)
        cleaning_and_chart_graph(
            # Объект графика
            graph=graph,
            # Название графика
            title=Drawer.title_data,
            # Подпись осей
            x_label=Drawer.horizontal_axis_name_data, y_label=Drawer.vertical_axis_name_data
        )

        # Данных нет
        if data_signals.data["without_gas"].empty and data_signals.data["with_gas"].empty:
            no_data(graph)
            return

        # Если есть данные без газа, строим график
        if not data_signals.data["without_gas"].empty:
            graph.axis.plot(
                data_signals.data["frequency"],
                data_signals.data["without_gas"],
                color=Drawer.color_without_gas, label=Drawer.name_without_gas)
        # Если есть данные с газом, строим график
        if not data_signals.data["with_gas"].empty:
            graph.axis.plot(
                data_signals.data["frequency"],
                data_signals.data["with_gas"],
                color=Drawer.color_with_gas, label=Drawer.name_with_gas)
        # Если интервалы корреляции найдены, строим график
        if not data_signals.data["intervals_after_correlation"].isnull().values.all():
            graph.axis.plot(
                data_signals.data["frequency"],
                data_signals.data["intervals_after_correlation"],
                color=Drawer.color_absorbing, label=Drawer.list_absorbing)

        # Отрисовка (вызывается в конце)
        draw_graph(graph)

    # График корреляции
    @staticmethod
    def updating_correlation_graph(
            graph: Graph,
            data_signals: DataAndProcessing
    ):
        # Очистка, подпись графика и осей (вызывается в начале)
        cleaning_and_chart_graph(
            # Объекты графика
            graph=graph,
            # Название графика
            title=Drawer.title_correlation,
            # Подпись осей
            x_label=Drawer.horizontal_axis_name_correlation, y_label=Drawer.vertical_axis_name_correlation
        )

        # Данных нет
        if data_signals.data["correlate"].isnull().values.all():
            no_data(graph)
            return

        # Если есть данные корреляции, строим график
        if not data_signals.data["correlate"].isnull().values.all():
            graph.axis.plot(
                data_signals.data["frequency"],
                data_signals.data["correlate"],
                color=Drawer.color_correlation, label=Drawer.name_correlation)
        # Если есть порог, строим график
        if not (data_signals.correlation_threshold is None):
            # Высчитываем порог
            threshold_data = data_signals.data_correlation_threshold()
            graph.axis.plot(
                threshold_data.index,
                threshold_data.values,
                color=Drawer.color_threshold, label=Drawer.list_threshold)

        # Отрисовка (вызывается в конце)
        draw_graph(graph)

    # График сглаженный
    @staticmethod
    def updating_smoothing_graph(
            graph: Graph,
            data_signals: DataAndProcessing
    ):
        # Очистка, подпись графика и осей (вызывается в начале)
        cleaning_and_chart_graph(
            # Объекты графика
            graph=graph,
            # Название графика
            title=Drawer.title_smoothing,
            # Подпись осей
            x_label=Drawer.horizontal_axis_name_smoothing, y_label=Drawer.vertical_axis_name_smoothing
        )

        # Данных нет (не_пустые.значения.во_всех_строчках)
        if data_signals.data["smoothed_without_gas"].isnull().values.all():
            no_data(graph)
            return

        # График без вещества
        graph.axis.plot(
            data_signals.data["frequency"],
            data_signals.data["without_gas"],
            color=Drawer.color_without_gas, label=Drawer.name_without_gas)
        # Сглаженный график без вещества
        graph.axis.plot(
            data_signals.data["frequency"],
            data_signals.data["smoothed_without_gas"],
            color=Drawer.color_smoothing, label=Drawer.name_smoothing)

        # Отрисовка (вызывается в конце)
        draw_graph(graph)

    # График сигмы и разницы
    @staticmethod
    def updating_sigma_and_difference_graph(
            graph: Graph,
            data_signals: DataAndProcessing
    ):
        # Очистка, подпись графика и осей (вызывается в начале)
        cleaning_and_chart_graph(
            # Объекты графика
            graph=graph,
            # Название графика
            title=Drawer.title_sigma_and_difference,
            # Подпись осей
            x_label=Drawer.horizontal_axis_name_sigma_and_difference,
            y_label=Drawer.vertical_axis_name_sigma_and_difference
        )

        # Данных нет (не_пустые.значения.во_всех_строчках)
        if (data_signals.data["difference"].isnull().values.all() and
                data_signals.data["sigma_with_multiplier"].isnull().values.all()):
            no_data(graph)
            return

        # Разница
        graph.axis.plot(
            data_signals.data["frequency"],
            data_signals.data["difference"],
            color=Drawer.color_difference, label=Drawer.name_difference)
        # Сигма
        graph.axis.plot(
            data_signals.data["frequency"],
            data_signals.data["sigma_with_multiplier"],
            color=Drawer.color_sigma, label=Drawer.name_sigma)

        # Отрисовка (вызывается в конце)
        draw_graph(graph)

    # График обработки ширины участка
    @staticmethod
    def updating_width_filter_graph(
            graph: Graph,
            data_signals: DataAndProcessing,
    ):
        # Очистка, подпись графика и осей (вызывается в начале)
        cleaning_and_chart_graph(
            # Объекты графика
            graph=graph,
            # Название графика
            title=Drawer.title_filter_by_area_width,
            # Подпись осей
            x_label=Drawer.horizontal_axis_name_filter_by_area_width,
            y_label=Drawer.vertical_axis_name_filter_by_area_width
        )

        # Данных нет (не_пустые.значения.во_всех_строчках)
        if data_signals.data["bool_result"].isnull().values.all():
            no_data(graph)
            return

        # Разница
        graph.axis.plot(
            data_signals.data["frequency"],
            data_signals.data["bool_difference"],
            color=Drawer.color_filter_beginning, label=Drawer.name_filter_beginning)
        # Сигма
        graph.axis.plot(
            data_signals.data["frequency"],
            data_signals.data["bool_result"],
            color=Drawer.color_filter_end, label=Drawer.name_filter_end)

        # Отрисовка (вызывается в конце)
        draw_graph(graph)
