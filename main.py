import sqlite3
import sys
import csv

from PyQt5 import QtGui, uic
from PyQt5.QtGui import QPixmap
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.pyplot import Figure
from matplotlib.ticker import FormatStrFormatter


class Transform(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Calculator.ui', self)  # Создаём "оболочку"
        self.logo.setPixmap(QPixmap('logo.png'))

        self.scene = QtWidgets.QGraphicsScene()  # Создание области будущего графика
        self.graph.setScene(self.scene)
        self.graphik = Figure(figsize=(7, 4))
        self.axes = self.graphik.gca()

        self.x, self.y = [], []  # Задание дефолтных значений
        self.res = []
        self.errors.setText('Нет')
        self.percnt, self.star_sum, self.tme = 0, 0, 0
        self.incom, self.indxing, self.indxing_time = 0, 0, 0
        self.sumofincome = 0

        self.sql = sqlite3.connect('sqfile.sqlite3')  # Создадим курсор БД
        self.cur = self.sql.cursor()
        [self.takefrombd.addItem(i[0]) for i in self.cur.execute("SELECT names FROM names").fetchall()]
        self.cur.close()

        self.percent.valueChanged.connect(self.per)  # Считываем и записываем все параметры
        self.start_sum.valueChanged.connect(self.start)
        self.time.valueChanged.connect(self.tim)

        self.income.valueChanged.connect(self.inc)
        self.indexing.valueChanged.connect(self.indixing)
        self.index_time.valueChanged.connect(self.in_time)

        self.get_res.clicked.connect(self.table)  # А это срабатывание кнопок для функций
        self.addtosql.clicked.connect(self.add_to_sql)
        self.takefrombd.currentTextChanged.connect(self.importbd)
        self.to_csv.clicked.connect(self.make_csv)

    def per(self):
        self.percnt = self.percent.value()

    def start(self):
        self.star_sum = self.start_sum.value()

    def tim(self):
        self.tme = self.time.value()

    def inc(self):
        self.incom = self.income.value()

    def indixing(self):
        self.indxing = self.indexing.value()

    def in_time(self):
        self.indxing_time = self.index_time.value()

    def table(self):  # Собственно, основа программы
        try:
            self.res = []  # Зануляем таблицу в случае многоразового нажатия на кнопку

            self.inc()  # Переобозначение аренды и начального инкама, ведь со временем они индексируются
            paypm = self.star_sum // self.tme
            self.sumofincome = 0

            sti = QtGui.QStandardItemModel()  # Создание таблицы
            sti.setHorizontalHeaderLabels(
                ['Ежемсячный платёж', 'Процент банку', 'Остаток по кредиту', 'Аренда', 'Денежный поток', 'Итог потока'])

            for i in range(self.tme + 1):
                if i and not (i % (self.indxing_time * 12)):  # Проверка на индексацию
                    self.incom += self.incom * self.indxing // 100

                item3 = QtGui.QStandardItem(str(self.star_sum - i * paypm))  # Вычисление каждого элемента
                item2 = QtGui.QStandardItem(str(int(item3.text()) * self.percnt // 1200))
                item1 = QtGui.QStandardItem(str(paypm + int(item2.text())))
                item4 = QtGui.QStandardItem(str(self.incom))
                item5 = QtGui.QStandardItem(str(self.incom - int(item1.text())))
                item6 = QtGui.QStandardItem('')
                if i:
                    self.sumofincome += int(item5.text())
                    item6 = QtGui.QStandardItem(str(self.sumofincome))

                sti.appendRow([item1, item2, item3, item4, item5, item6])  # Добавление полученных элементов в таблицу
                self.res.append([item1.text(), item2.text(), item3.text(), item4.text(), item5.text(), item6.text()])

                self.x.append(i)  # Добавляем по точке в наш график
                self.y.append(self.sumofincome)

            self.result.setModel(sti)  # Вывод итоговой таблицы

            self.make_graph()  # Строим график

        except ZeroDivisionError:  # Срабатывает, если какое-то значение не введено
            self.errors.setText('Вы не ввели некоторые значения, проверьте их')
        self.sql.close()

    def make_graph(self):  # Собираем график
        self.axes.clear()
        self.axes.plot(self.x, self.y, '-k')

        self.axes.set_xticks(range(0, self.tme + 1, 12))  # Настройка оси Х
        self.axes.set_xticklabels([i for i in range(0, (self.tme + 12) // 12, 1)])
        self.axes.set_xlabel('Время, год', color='blue')

        self.axes.yaxis.set_major_formatter(FormatStrFormatter('$%.2f$'))  # Настройка оси У
        self.axes.set_yticks(range(min(self.y), max(self.y) + 1, 10**6))
        self.axes.set_yticklabels([round(i / 10**6, 2) for i in range(min(self.y), max(self.y) + 1, 10**6)])
        self.axes.set_ylabel('Итог потока, млн', color='blue')

        self.axes.grid(True)  # Включаем сетку на поле

        canvas = FigureCanvas(self.graphik)  # Вырисовываем график
        self.scene.addWidget(canvas)

        self.x, self.y = [], []  # Зачищаем прошлые точки
        self.sql.close()

    def add_to_sql(self):
        try:
            self.sql = sqlite3.connect('sqfile.sqlite3')  # Создадим курсор БД
            self.cur = self.sql.cursor()

            self.cur.execute(f"INSERT INTO names VALUES ('{self.namebd.text()}')")
            self.sql.commit()

            self.cur.execute(
                f"INSERT INTO parameters(names, percents, start_sums, times, incomes, indexings, indexing_time) VALUES "
                f"('{self.namebd.text()}',{self.percnt},{self.star_sum},{self.tme},{self.income.value()},{self.indxing}"
                f", {self.indxing_time})")
            self.sql.commit()
            self.errors.setText('Нет')
        except sqlite3.IntegrityError:
            self.errors.setText('Такое имя базы уже существует')

        self.sql.close()

    def importbd(self, text):
        self.sql = sqlite3.connect('sqfile.sqlite3')  # Создадим курсор БД
        self.cur = self.sql.cursor()

        lst = [*self.cur.execute(f"SELECT * FROM parameters WHERE names = '{text}'")]
        self.namebd.setText(lst[0][0])
        self.percent.setValue(lst[0][1])
        self.start_sum.setValue(lst[0][2])
        self.time.setValue(lst[0][3])
        self.income.setValue(lst[0][4])
        self.indexing.setValue(lst[0][5])
        self.index_time.setValue(lst[0][6])
        self.sql.close()

    def make_csv(self):
        try:
            with open('table.csv', 'w', encoding='utf-8', newline='\n') as csv_table:
                writer = csv.writer(csv_table, delimiter=';')
                writer.writerows([i for i in self.res])
        except PermissionError:
            self.errors.setText('Пожалуйста, закройте таблицу')


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = except_hook
    ex = Transform()
    ex.show()
    sys.exit(app.exec_())
