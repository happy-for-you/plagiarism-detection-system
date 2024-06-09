import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                             QLabel, QFileDialog, QMessageBox)


class PlagiarismCheckerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.template_path = None
        self.folder_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Plagiarism Checker')
        self.setGeometry(100, 100, 800, 600)  # Adjust size and position

        layout = QVBoxLayout()

        self.template_label = QLabel('No template selected.')
        layout.addWidget(self.template_label)
        btn_upload_template = QPushButton('Upload Template', self)
        btn_upload_template.clicked.connect(self.uploadTemplate)
        layout.addWidget(btn_upload_template)

        self.folder_label = QLabel('No folder selected.')
        layout.addWidget(self.folder_label)
        btn_select_folder = QPushButton('Select Folder', self)
        btn_select_folder.clicked.connect(self.selectFolder)
        layout.addWidget(btn_select_folder)

        btn_check = QPushButton('Check for Plagiarism', self)
        btn_check.clicked.connect(self.checkPlagiarism)
        layout.addWidget(btn_check)

        self.results_label = QLabel('Results will be shown here.')
        layout.addWidget(self.results_label)

        self.setLayout(layout)

    def uploadTemplate(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Template File', '', 'Word files (*.docx)')
        if file_path:
            self.template_path = file_path
            self.template_label.setText(f'Template Selected: {file_path}')

    def selectFolder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder_path:
            self.folder_path = folder_path
            self.folder_label.setText(f'Folder Selected: {folder_path}')

    def checkPlagiarism(self):
        if not self.template_path or not self.folder_path:
            QMessageBox.warning(self, 'Error', 'Please select both a template and a folder.')
            return

        # Here you would call your plagiarism checking code
        # For example:
        results = "Simulated results: File1.docx, File2.docx"
        self.results_label.setText(results)


# Run the application
app = QApplication(sys.argv)
ex = PlagiarismCheckerGUI()
ex.show()
sys.exit(app.exec_())
