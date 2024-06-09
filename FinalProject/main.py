import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, \
    QTableWidgetItem, QTableWidget, QHeaderView, QComboBox, QListWidget
from load import WordProcessor
from algorithm import TextSimilarityCalculator, CodeSimilarityCalculator
import json
from datetime import datetime


class HistoryWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('历史记录')
        self.setGeometry(150, 150, 600, 400)
        self.layout = QVBoxLayout(self)

        self.history_list = QListWidget(self)
        self.load_history_files()
        self.history_list.itemDoubleClicked.connect(self.load_selected_history)
        self.layout.addWidget(self.history_list)

        self.load_button = QPushButton('加载选中记录', self)
        self.load_button.setIcon(QIcon('icons/load.png'))
        self.load_button.clicked.connect(self.load_selected_history)
        self.layout.addWidget(self.load_button)

        self.delete_button = QPushButton('删除选中记录', self)
        self.delete_button.setIcon(QIcon('icons/delete.png'))
        self.delete_button.clicked.connect(self.delete_selected_history)
        self.layout.addWidget(self.delete_button)

        self.close_button = QPushButton('关闭', self)
        self.close_button.setIcon(QIcon('icons/close.png'))
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.close_button)

    def load_history_files(self):
        history_dir = self.parent().ensure_history_folder_exists()
        files = [f for f in os.listdir(history_dir) if f.endswith('.json')]
        self.history_list.addItems(files)

    def load_selected_history(self):
        selected_item = self.history_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, '警告', '请选择一个历史记录。')
            return

        file_name = selected_item.text()
        history_dir = self.parent().ensure_history_folder_exists()
        file_path = os.path.join(history_dir, file_name)

        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                results = json.load(jsonfile)
                if not isinstance(results, list):
                    raise ValueError("JSON 文件格式不正确")

                self.parent().update_table_with_loaded_results(results)
                QMessageBox.information(self, '加载成功', f'已成功加载记录: {file_name}')
        except FileNotFoundError:
            QMessageBox.critical(self, '错误', f'未找到文件: {file_name}')
        except json.JSONDecodeError:
            QMessageBox.critical(self, '错误', f'JSON 解析错误: {file_name}')
        except ValueError as e:
            QMessageBox.critical(self, '错误', str(e))

    def delete_selected_history(self):
        selected_item = self.history_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, '警告', '请选择一个历史记录。')
            return

        file_name = selected_item.text()
        history_dir = self.parent().ensure_history_folder_exists()
        file_path = os.path.join(history_dir, file_name)

        reply = QMessageBox.question(self, '确认删除', f'确定要删除记录 {file_name} 吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                self.history_list.takeItem(self.history_list.row(selected_item))
                QMessageBox.information(self, '删除成功', f'已成功删除记录: {file_name}')
            except FileNotFoundError:
                QMessageBox.critical(self, '错误', f'未找到文件: {file_name}')
            except Exception as e:
                QMessageBox.critical(self, '错误', str(e))


class PlagiarismCheckerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.processor = WordProcessor()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('抄袭检测系统alpha·1')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
            }
            QTableWidget {
                background-color: white;
            }
            QListWidget {
                background-color: white;
            }
        """)

        layout = QVBoxLayout()

        self.template_label = QLabel('未选择模板文件。')
        layout.addWidget(self.template_label)
        btn_upload_template = QPushButton('上传模板文件', self)
        btn_upload_template.setIcon(QIcon('icons/upload.png'))
        btn_upload_template.clicked.connect(self.uploadTemplate)
        layout.addWidget(btn_upload_template)

        self.folder_label = QLabel('未选择文件夹。')
        layout.addWidget(self.folder_label)
        btn_select_folder = QPushButton('选择文件夹', self)
        btn_select_folder.setIcon(QIcon('icons/folder.png'))
        btn_select_folder.clicked.connect(self.selectFolder)
        layout.addWidget(btn_select_folder)

        btn_check = QPushButton('开始检测抄袭', self)
        btn_check.setIcon(QIcon('icons/check.png'))
        btn_check.clicked.connect(self.checkPlagiarism)
        layout.addWidget(btn_check)

        self.sort_combo_box = QComboBox(self)
        self.sort_combo_box.addItems(['按总结果排序', '标准排序', '按文本查重结果排序', '按代码查重结果排序'])
        self.sort_combo_box.currentIndexChanged.connect(self.update_table_sorting)
        layout.addWidget(self.sort_combo_box)

        self.table_widget = QTableWidget(self)
        self.table_widget.setRowCount(0)
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(
            ['Document Name', 'Text Score', 'Code Score', 'Average Score', 'Timestamp'])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_widget)

        btn_save_results = QPushButton('保存结果', self)
        btn_save_results.setIcon(QIcon('icons/save.png'))
        btn_save_results.clicked.connect(self.save_results)
        layout.addWidget(btn_save_results)

        btn_show_history = QPushButton('历史记录', self)
        btn_show_history.setIcon(QIcon('icons/history.png'))
        btn_show_history.clicked.connect(self.show_history)
        layout.addWidget(btn_show_history)

        btn_exit = QPushButton('退出程序', self)
        btn_exit.setIcon(QIcon('icons/exit.png'))
        btn_exit.clicked.connect(self.close)
        layout.addWidget(btn_exit)

        self.setLayout(layout)

    def uploadTemplate(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择模板文件', '', 'Word 文件 (*.docx)')
        if file_path:
            self.template_path = file_path
            self.template_label.setText(f'已选择模板文件: {file_path}')
            template_text = self.processor.read_docx(file_path)
            self.processor.set_template(template_text)

    def selectFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, '选择文件夹')
        if folder_path:
            self.folder_path = folder_path
            self.folder_label.setText(f'已选择文件夹: {folder_path}')

    def checkPlagiarism(self):
        template_path = getattr(self, 'template_path', None)
        folder_path = getattr(self, 'folder_path', None)

        if not template_path or not folder_path:
            QMessageBox.warning(self, '错误', '请选择模板文件和文件夹。')
            return

        template_text = self.processor.read_docx(template_path)
        self.processor.set_template(template_text)
        self.processor.process_folder(folder_path)

        document_texts = [self.processor.documents[name]['自然语言内容'] for name in self.processor.documents]
        code_texts = [self.processor.documents[name]['代码内容'] for name in self.processor.documents]
        self.text_calculator = TextSimilarityCalculator(document_texts)
        self.code_calculator = CodeSimilarityCalculator(code_texts)

        text_scores = self.text_calculator.calculate_scores()
        code_scores = self.code_calculator.calculate_jaccard_scores()

        results = []
        for name, text_score, code_score in zip(self.processor.documents.keys(), text_scores, code_scores):
            average_score = (text_score + code_score) / 2
            results.append((name, text_score, code_score, average_score))

        results_sorted = sorted(results, key=lambda x: x[3], reverse=True)
        total_documents = len(results_sorted)
        results_to_save = []
        for i, (name, text_score, code_score, average_score) in enumerate(results_sorted):
            percentile = (i / total_documents) * 100
            equivalent_score = self.calculate_equivalent_score(percentile)
            results_to_save.append({
                'Document Name': name,
                'Text Score': text_score,
                'Code Score': code_score,
                'Average Score': average_score,
                'Equivalent Score': equivalent_score,
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.update_table_with_results(i, name, text_score, code_score, average_score, equivalent_score)

        self.save_results_to_json(results_to_save)

    def save_results(self):
        results = []
        for row in range(self.table_widget.rowCount()):
            result = {
                'Document Name': self.table_widget.item(row, 0).text(),
                'Text Score': float(self.table_widget.item(row, 1).text()),
                'Code Score': float(self.table_widget.item(row, 2).text()),
                'Average Score': float(self.table_widget.item(row, 3).text()),
                'Equivalent Score': float(self.table_widget.item(row, 4).data(Qt.UserRole)),  # Store equivalent score
                'Timestamp': self.table_widget.item(row, 4).text()
            }
            results.append(result)

        file_name, _ = QFileDialog.getSaveFileName(self, '保存结果', self.ensure_history_folder_exists(),
                                                   'JSON 文件 (*.json)')
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as jsonfile:
                    json.dump(results, jsonfile, ensure_ascii=False, indent=4)
                QMessageBox.information(self, '保存成功', f'结果已保存到 {file_name}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'保存文件时发生错误: {str(e)}')

    def update_table_with_loaded_results(self, results):
        self.table_widget.setRowCount(len(results))
        for row, result in enumerate(results):
            self.table_widget.setItem(row, 0, QTableWidgetItem(result['Document Name']))
            self.table_widget.setItem(row, 1, QTableWidgetItem(f"{result['Text Score']:.2f}"))
            self.table_widget.setItem(row, 2, QTableWidgetItem(f"{result['Code Score']:.2f}"))
            self.table_widget.setItem(row, 3, QTableWidgetItem(f"{result['Average Score']:.2f}"))

            item = QTableWidgetItem(result['Timestamp'])
            item.setData(Qt.UserRole, result['Equivalent Score'])  # Store equivalent score
            self.table_widget.setItem(row, 4, item)

            self.colorize_row(row, result['Equivalent Score'])
        self.table_widget.resizeColumnsToContents()

    def save_results_to_json(self, results):
        history_dir = self.ensure_history_folder_exists()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(history_dir, f'results_{timestamp}.json')
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(results, jsonfile, ensure_ascii=False, indent=4)

    def ensure_history_folder_exists(self):
        history_dir = os.path.join(os.getcwd(), 'history')
        os.makedirs(history_dir, exist_ok=True)
        return history_dir

    def update_table_with_results(self, row, name, text_score, code_score, average_score, equivalent_score):
        self.table_widget.insertRow(row)
        self.table_widget.setItem(row, 0, QTableWidgetItem(name))
        self.table_widget.setItem(row, 1, QTableWidgetItem(f"{text_score:.2f}"))
        self.table_widget.setItem(row, 2, QTableWidgetItem(f"{code_score:.2f}"))
        self.table_widget.setItem(row, 3, QTableWidgetItem(f"{average_score:.2f}"))

        item = QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        item.setData(Qt.UserRole, equivalent_score)  # Store equivalent score
        self.table_widget.setItem(row, 4, item)

        self.colorize_row(row, equivalent_score)

    def colorize_row(self, row, equivalent_score):
        for col in range(self.table_widget.columnCount()):
            item = self.table_widget.item(row, col)
            if equivalent_score >= 80:
                item.setBackground(QColor(255, 0, 0))  # Red
            elif equivalent_score >= 60:
                item.setBackground(QColor(255, 255, 0))  # Yellow
            else:
                item.setBackground(QColor(0, 255, 0))  # Green

    def calculate_equivalent_score(self, percentile):
        return 100 - percentile

    def update_table_sorting(self):
        current_sorting = self.sort_combo_box.currentText()
        if current_sorting == '标准排序':
            self.sort_table_by_column(0)
        elif current_sorting == '按文本查重结果排序':
            self.sort_table_by_column(1)
        elif current_sorting == '按代码查重结果排序':
            self.sort_table_by_column(2)
        else:
            self.sort_table_by_column(3)

    def sort_table_by_column(self, column):
        self.table_widget.sortItems(column, Qt.DescendingOrder)

    def show_history(self):
        self.history_window = HistoryWindow(self)
        self.history_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlagiarismCheckerGUI()
    window.show()
    sys.exit(app.exec_())
