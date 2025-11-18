import sys
import os
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime # даты для логов
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # встраиваем графики прямо в приложение
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QPushButton, QFileDialog,
                             QComboBox, QLabel, QTextEdit, QTableWidget,
                             QTableWidgetItem, QMessageBox, QScrollArea, QGroupBox,
                             QLineEdit, QDialog, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class DatasetName(QDialog): # всплывающее окно для названия и описания загруженного с цсв датасета
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить датасет")
        self.setModal(True)
        self.initUI()

    def initUI(self):
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.description_input = QLineEdit()

        layout.addRow("Название датасета:", self.name_input)
        layout.addRow("Описание:", self.description_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self): # получение данных
        return self.name_input.text(), self.description_input.text()


class DataVisualizationApp(QMainWindow): # главное приложение как класс
    def __init__(self):
        super().__init__()
        self.current_df = None
        self.db_conn = None
        self.current_dataset = None
        self.log_actions = []
        self.initUI()
        self.connect_to_database()

    def initUI(self):
        self.setWindowTitle('Data Visualization App')
        self.setGeometry(100, 100, 1400, 900)

        # центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # заголовок
        header_layout = QHBoxLayout()

        # контроль бд
        db_controls_layout = QVBoxLayout()

        # выбор датасета
        dataset_layout = QHBoxLayout()
        dataset_layout.addWidget(QLabel("Выберите датасет:"))
        self.dataset_combo = QComboBox()
        self.dataset_combo.currentTextChanged.connect(self.load_dataset)
        dataset_layout.addWidget(self.dataset_combo)

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.refresh_datasets)
        # делаем кнопку красивой, далее со всеми будем делать также
        self.refresh_btn.setStyleSheet(""" 
            QPushButton {
                background-color: #607D8B;
                color: white;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        dataset_layout.addWidget(self.refresh_btn)
        dataset_layout.addStretch()

        db_controls_layout.addLayout(dataset_layout)

        # кнопки действия в заголовке
        action_layout = QHBoxLayout()
        self.load_btn = QPushButton('Загрузить новый CSV')
        self.load_btn.clicked.connect(self.load_csv_dialog)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        # удаление датасета
        self.delete_btn = QPushButton('Удалить датасет')
        self.delete_btn.clicked.connect(self.delete_dataset)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
        """)

        action_layout.addWidget(self.load_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addStretch()

        db_controls_layout.addLayout(action_layout)
        header_layout.addLayout(db_controls_layout)

        self.status_label = QLabel('База данных не подключена')
        self.status_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        header_layout.addWidget(self.status_label)

        main_layout.addLayout(header_layout)

        # создание вкладок
        self.tabs = QTabWidget()
        self.tab1 = QWidget()  # статистика
        self.tab2 = QWidget()  # графики корреляции
        self.tab3 = QWidget()  # тепловая карта
        self.tab4 = QWidget()  # линейный график
        self.tab5 = QWidget()  # лог действий
        # задаем названия вкладок
        self.tabs.addTab(self.tab1, "📊 Статистика")
        self.tabs.addTab(self.tab2, "📈 Корреляции")
        self.tabs.addTab(self.tab3, "🎯 Тепловая карта")
        self.tabs.addTab(self.tab4, "📉 Линейный график")
        self.tabs.addTab(self.tab5, "📝 Лог действий")
        # добавляем наши созданные вкладки на главный экран
        self.setup_tab1()
        self.setup_tab2()
        self.setup_tab3()
        self.setup_tab4()
        self.setup_tab5()

        main_layout.addWidget(self.tabs)
        # добавление действия в лог
        self.add_log("Приложение запущено")
    # функция для подключения к созданной локальной БД
    def connect_to_database(self):
        try:
            self.db_conn = sqlite3.connect('data_visualization.db')
            self.status_label.setText('База данных подключена')
            self.status_label.setStyleSheet("font-weight: bold; color: #388e3c;")
            self.refresh_datasets()
            self.add_log("Подключение к базе данных установлено")

        except Exception as e:
            self.status_label.setText('Ошибка подключения к БД')
            QMessageBox.critical(self, "Ошибка",
                                 f"Не удалось подключиться к базе данных")
    # обновление списка загруженных датасетов
    def refresh_datasets(self):
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT name FROM datasets ORDER BY created_at DESC")
            datasets = cursor.fetchall()

            self.dataset_combo.clear()
            for dataset in datasets:
                self.dataset_combo.addItem(dataset[0])

            if datasets:
                self.add_log(f"Список датасетов обновлен: {len(datasets)} датасетов")
            else:
                self.add_log("База данных пуста")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке списка датасетов: {str(e)}")
    # загрузка цсв в приложение
    def load_csv_dialog(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите CSV файл", "", "CSV Files (*.csv)"
            )

            if file_path:
                # диалог для ввода названия датасета
                dialog = DatasetName(self)
                if dialog.exec_() == QDialog.Accepted:
                    name, description = dialog.get_data()
                    if name:
                        self.load_csv(file_path, name, description)
                    else:
                        QMessageBox.warning(self, "Предупреждение", "Введите название датасета")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при выборе файла: {str(e)}")
    # загрузка цсв в локальную БД
    def load_csv(self, file_path, dataset_name, description=""):
        try:
            self.add_log(f"Загрузка файла: {os.path.basename(file_path)} как '{dataset_name}'")

            # чтение CSV
            df = pd.read_csv(file_path)

            # сохранение в БД
            df.to_sql(dataset_name, self.db_conn, if_exists='fail', index=False)

            # добавление информации
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO datasets (name, description, row_count, column_count)
                VALUES (?, ?, ?, ?)
            ''', (dataset_name, description, len(df), len(df.columns)))

            self.db_conn.commit()

            # обновление интерфейса
            self.refresh_datasets()
            self.dataset_combo.setCurrentText(dataset_name)

            self.add_log(f"Датасет '{dataset_name}' успешно загружен: {len(df)} строк, {len(df.columns)} столбцов")
        # вывод ошибки при одинаковом названии
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Ошибка", "Датасет с таким названием уже существует")
            self.add_log(f"Ошибка: датасет с именем '{dataset_name}' уже существует")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке файла: {str(e)}")
            self.add_log(f"Ошибка при загрузке файла: {str(e)}")
    # загрузка датасета
    def load_dataset(self, dataset_name):
        if not dataset_name or not self.db_conn:
            return

        try:
            # загрузка данных
            self.current_df = pd.read_sql_query(f"SELECT * FROM {dataset_name}", self.db_conn)
            self.current_dataset = dataset_name

            # обновление интерфейса
            self.update_interface()

            self.add_log(f"Загружен датасет: {dataset_name}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке датасета: {str(e)}")
    # удаление датасета
    def delete_dataset(self):
        dataset_name = self.dataset_combo.currentText()
        if not dataset_name:
            return
        # предупреждение пользователя
        reply = QMessageBox.question(self, "Подтверждение",
                                     f"Вы уверены, что хотите удалить датасет '{dataset_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_conn.cursor()

                # удаление таблицы с данными
                cursor.execute(f"DROP TABLE IF EXISTS {dataset_name}")

                # удаление информации
                cursor.execute("DELETE FROM datasets WHERE name = ?", (dataset_name,))

                self.db_conn.commit()

                # обновление интерфейса
                self.refresh_datasets()
                self.current_df = None
                self.current_dataset = None
                self.update_interface()

                self.add_log(f"Датасет '{dataset_name}' удален")

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении датасета: {str(e)}")
    # первая вкладка статистика данных
    def setup_tab1(self):
        layout = QVBoxLayout(self.tab1)

        # информация о датасете
        info_layout = QHBoxLayout()
        self.dataset_info_label = QLabel('Датасет не выбран')
        self.dataset_info_label.setStyleSheet("font-weight: bold; color: #1976D2; font-size: 14px;")
        info_layout.addWidget(self.dataset_info_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        stats_group = QGroupBox("Статистика данных")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_text = QTextEdit()
        self.stats_text.setFont(QFont("Aptos", 9))
        self.stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_text)

        layout.addWidget(stats_group)

        # предпросмотр данных
        preview_group = QGroupBox("Предпросмотр данных (первые 20 строк)")
        preview_layout = QVBoxLayout(preview_group)

        self.table_preview = QTableWidget()
        preview_layout.addWidget(self.table_preview)

        layout.addWidget(preview_group)
    # графики корреляции
    def setup_tab2(self):
        layout = QVBoxLayout(self.tab2)

        # выбор конкретного графика
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Тип графика:"))
        self.corr_combo = QComboBox()
        self.corr_combo.addItems(["scatterplot", "regplot", "pairplot"])
        controls_layout.addWidget(self.corr_combo)

        self.plot_corr_btn = QPushButton("Построить график")
        self.plot_corr_btn.clicked.connect(self.plot_correlation)
        self.plot_corr_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.plot_corr_btn)
        # кнопка для очистки графиков
        self.clear_corr_btn = QPushButton("Очистить графики")
        self.clear_corr_btn.clicked.connect(self.clear_correlation_plots)
        self.clear_corr_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        controls_layout.addWidget(self.clear_corr_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # plot area
        self.corr_canvas = FigureCanvas(Figure(figsize=(10, 8)))
        layout.addWidget(self.corr_canvas)
    # вкладка с тепловой картой
    def setup_tab3(self):
        layout = QVBoxLayout(self.tab3)

        controls_layout = QHBoxLayout()

        self.heatmap_btn = QPushButton("Построить тепловую карту")
        self.heatmap_btn.clicked.connect(self.plot_heatmap)
        self.heatmap_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.heatmap_btn)
        # очистка тепловой карты
        self.clear_heatmap_btn = QPushButton("Очистить тепловую карту")
        self.clear_heatmap_btn.clicked.connect(self.clear_heatmap)
        self.clear_heatmap_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        controls_layout.addWidget(self.clear_heatmap_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # plot area
        self.heatmap_canvas = FigureCanvas(Figure(figsize=(10, 8)))
        layout.addWidget(self.heatmap_canvas)
    # постройка линейных графиков
    def setup_tab4(self):
        layout = QVBoxLayout(self.tab4)
        # выбор столбца по которому нужно строить график
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Выберите столбец:"))
        self.column_combo = QComboBox()
        controls_layout.addWidget(self.column_combo)

        self.plot_line_btn = QPushButton("Построить линейный график")
        self.plot_line_btn.clicked.connect(self.plot_line_chart)
        self.plot_line_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        controls_layout.addWidget(self.plot_line_btn)

        self.clear_line_btn = QPushButton("Очистить график")
        self.clear_line_btn.clicked.connect(self.clear_line_chart)
        self.clear_line_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
        """)
        controls_layout.addWidget(self.clear_line_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # plot area
        self.line_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        layout.addWidget(self.line_canvas)
    # вкладка с логами пользователя
    def setup_tab5(self):
        layout = QVBoxLayout(self.tab5)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        clear_btn = QPushButton("Очистить лог")
        clear_btn.clicked.connect(self.clear_log)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        layout.addWidget(clear_btn)

    def update_interface(self):
        if self.current_df is not None and self.current_dataset:
            # обновление информации о датасете
            self.dataset_info_label.setText(
                f"Текущий датасет: {self.current_dataset} | "
                f"Строк: {len(self.current_df):,} | "
                f"Столбцов: {len(self.current_df.columns)} | "
                f"Загружен: {datetime.now().strftime('%H:%M:%S')}"
            )

            # обновление комбобоксов для графиков
            self.column_combo.clear()
            numeric_columns = self.current_df.select_dtypes(include=[np.number]).columns.tolist()
            self.column_combo.addItems(numeric_columns)

            # автоматическая загрузка статистики
            self.load_dataset_stats()
        else:
            self.dataset_info_label.setText('Датасет не выбран')
            self.stats_text.clear()
            self.table_preview.setRowCount(0)
            self.table_preview.setColumnCount(0)
            self.column_combo.clear()
    # загрузка статистики датасета
    def load_dataset_stats(self):
        if self.current_df is None:
            return

        try:
            #основная информация
            stats_text = f"ОСНОВНАЯ ИНФОРМАЦИЯ:\n"
            stats_text += f"Размер данных: {self.current_df.shape[0]:,} строк × {self.current_df.shape[1]} столбцов\n"
            stats_text += f"Объем памяти: {self.current_df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB\n\n"

            # тип данных
            stats_text += f"ТИПЫ ДАННЫХ:\n"
            for col, dtype in self.current_df.dtypes.items():
                stats_text += f"  {col}: {dtype}\n"
            stats_text += f"\n"

            # статистика числовых столбцов
            numeric_df = self.current_df.select_dtypes(include=[np.number])
            if not numeric_df.empty:
                stats_text += f"СТАТИСТИКА ЧИСЛОВЫХ СТОЛБЦОВ:\n"
                stats_text += str(numeric_df.describe())
            else:
                stats_text += "Числовые столбцы не найдены\n"

            # пропуски
            missing_values = self.current_df.isnull().sum()
            if missing_values.sum() > 0:
                stats_text += f"\n ПРОПУЩЕННЫЕ ЗНАЧЕНИЯ:\n"
                for col, count in missing_values[missing_values > 0].items():
                    stats_text += f"  {col}: {count} пропусков ({count / len(self.current_df) * 100:.1f}%)\n"

            self.stats_text.setText(stats_text)

            # предпросмотр
            self.show_table_preview(self.current_df.head(20))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке статистики: {str(e)}")
    # отображение предпросмотра талиц
    def show_table_preview(self, df):
        self.table_preview.setRowCount(df.shape[0])
        self.table_preview.setColumnCount(df.shape[1])
        self.table_preview.setHorizontalHeaderLabels(df.columns)

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                item = QTableWidgetItem(str(df.iloc[i, j]))
                self.table_preview.setItem(i, j, item)

        self.table_preview.resizeColumnsToContents()
    # построение графиков корреляции
    def plot_correlation(self):
        if self.current_df is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return

        try:
            numeric_df = self.current_df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) < 2:
                QMessageBox.warning(self, "Предупреждение", "Недостаточно числовых столбцов для анализа корреляции")
                return

            plot_type = self.corr_combo.currentText()
            self.corr_canvas.figure.clear()
            ax = self.corr_canvas.figure.add_subplot(111)

            if plot_type == "scatterplot":
                col1, col2 = numeric_df.columns[:2]
                sns.scatterplot(data=numeric_df, x=col1, y=col2, ax=ax)
                ax.set_title(f'Scatter Plot: {col1} vs {col2}')

            elif plot_type == "regplot":
                col1, col2 = numeric_df.columns[:2]
                sns.regplot(data=numeric_df, x=col1, y=col2, ax=ax)
                ax.set_title(f'Regression Plot: {col1} vs {col2}')

            elif plot_type == "pairplot":
                pairplot_df = numeric_df.iloc[:, :min(4, len(numeric_df.columns))]
                self.corr_canvas.figure.clear()
                fig = sns.pairplot(pairplot_df)
                fig.figure.subplots_adjust(top=0.95)
                fig.figure.suptitle('Pairplot')
                self.corr_canvas.figure = fig.figure

            self.corr_canvas.draw()
            self.add_log(f"Построен график корреляции: {plot_type}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при построении графика: {str(e)}")
            self.add_log(f"Ошибка при построении графика корреляции: {str(e)}")
    # очистка графиков корреляции
    def clear_correlation_plots(self):
        self.corr_canvas.figure.clear()
        self.corr_canvas.draw()
        self.add_log("Графики корреляции очищены")

    def plot_heatmap(self):
        if self.current_df is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return

        try:
            numeric_df = self.current_df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) < 2:
                QMessageBox.warning(self, "Предупреждение", "Недостаточно числовых столбцов для тепловой карты")
                return

            self.heatmap_canvas.figure.clear()
            ax = self.heatmap_canvas.figure.add_subplot(111)

            # вычисление корреляционной матрицы
            corr_matrix = numeric_df.corr()

            # построение тепловой карты
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=ax)
            ax.set_title('Тепловая карта корреляций')

            self.heatmap_canvas.draw()
            self.add_log("Построена тепловая карта корреляций")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при построении тепловой карты: {str(e)}")
            self.add_log(f"Ошибка при построении тепловой карты: {str(e)}")

    def clear_heatmap(self):
        self.heatmap_canvas.figure.clear()
        self.heatmap_canvas.draw()
        self.add_log("Тепловая карта очищена")

    def plot_line_chart(self):
        if self.current_df is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала загрузите данные")
            return

        try:
            column = self.column_combo.currentText()
            if not column:
                QMessageBox.warning(self, "Предупреждение", "Выберите столбец для построения графика")
                return

            self.line_canvas.figure.clear()
            ax = self.line_canvas.figure.add_subplot(111)

            # построение линейного графика
            data = self.current_df[column].dropna()
            ax.plot(data.values, linewidth=2)
            ax.set_title(f'Линейный график: {column}')
            ax.set_ylabel(column)
            ax.set_xlabel('Номер')
            ax.grid(True, alpha=0.3)

            self.line_canvas.draw()
            self.add_log(f"Построен линейный график для столбца: {column}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при построении линейного графика: {str(e)}")
            self.add_log(f"Ошибка при построении линейного графика: {str(e)}")

    def clear_line_chart(self):
        self.line_canvas.figure.clear()
        self.line_canvas.draw()
        self.add_log("Линейный график очищен")

    def add_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_actions.append(log_entry)
        self.log_text.append(log_entry)

    def clear_log(self):
        self.log_text.clear()
        self.log_actions.clear()
        self.add_log("Лог очищен")

    def closeEvent(self, event):
        if self.db_conn:
            self.db_conn.close()
        event.accept()


def main():
    app = QApplication(sys.argv)

    # проверка существования базы данных
    if not os.path.exists('data_visualization.db'):
        reply = QMessageBox.question(None, "База данных не найдена",
                                     "База данных не найдена. Создать новую?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # создаем базу данных
                from create_database import create_database
                create_database()
                QMessageBox.information(None, "Успех", "База данных успешно создана!")
            except Exception as e:
                QMessageBox.critical(None, "Ошибка",
                                     f"Не удалось создать базу данных: {e}")
                return

    window = DataVisualizationApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()