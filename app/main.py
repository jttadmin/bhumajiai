import sys
import traceback
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Qt, QSettings, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QTextEdit, QPushButton, QComboBox, QCheckBox,
    QLineEdit, QMessageBox, QSystemTrayIcon, QMenu, QStyle, QFileDialog, QTabWidget, QListWidget)
import keyring
from .audio import MicrophoneRecorder
from .ai import transcribe_audio, generate_answer, evaluate_answer, ROLES
from .resume import read_resume
from .history import save as save_history, recent as recent_history

SERVICE = 'DevOpsInterviewAssistant'
ACCOUNT = 'openai_api_key'

class Signals(QObject):
    done = Signal(object)
    error = Signal(str)

class Job(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.signals = Signals()
    def run(self):
        try:
            self.signals.done.emit(self.fn())
        except Exception as e:
            self.signals.error.emit(f'{type(e).__name__}: {e}')

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('BhumajiAI', 'UniversalInterviewAssistant')
        self.pool = QThreadPool.globalInstance()
        self.recorder = MicrophoneRecorder()
        self.recording = False
        self.busy = False
        self.jobs = []
        self.resume_text = ""
        self.live = False
        self.live_pending = False
        self.last_question = ""
        self.live_timer = QTimer(self)
        self.live_timer.setInterval(8000)
        self.live_timer.timeout.connect(self.live_chunk)
        self.setWindowTitle('Universal AI Interview Assistant V4')
        self.resize(670, 660)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addWidget(QLabel('Universal AI Interview Practice — choose any job role'))
        layout.addWidget(QLabel('Use only where AI assistance is allowed. Audio is sent to OpenAI for transcription.'))

        row = QHBoxLayout()
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText('OpenAI API key (save to Windows Credential Manager)')
        save = QPushButton('Save API key')
        save.clicked.connect(self.save_key)
        row.addWidget(self.key)
        row.addWidget(save)
        layout.addLayout(row)
        if keyring.get_password(SERVICE, ACCOUNT):
            self.key.setPlaceholderText('API key saved securely (leave blank to keep it)')

        role_row = QHBoxLayout()
        self.role = QComboBox()
        self.role.addItems(ROLES)
        saved_role = str(self.settings.value('role', 'General Interview'))
        self.role.setCurrentText(saved_role if saved_role in ROLES else 'Custom role...')
        self.role.currentTextChanged.connect(self.role_changed)
        self.custom_role = QLineEdit(str(self.settings.value('custom_role', '')))
        self.custom_role.setPlaceholderText('Custom job title (e.g. SAP Consultant)')
        self.custom_role.textChanged.connect(lambda value: self.settings.setValue('custom_role', value))
        role_row.addWidget(QLabel('Interview role'))
        role_row.addWidget(self.role)
        role_row.addWidget(self.custom_role)
        layout.addLayout(role_row)
        self.role_changed(self.role.currentText())
        layout.addWidget(QLabel('Job description / target responsibilities (optional)'))
        self.job_description = QTextEdit()
        self.job_description.setPlaceholderText('Paste a job description to tailor answers and mock interview feedback')
        self.job_description.setMaximumHeight(75)
        layout.addWidget(self.job_description)

        opts = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(['Concise', 'Detailed', 'Scenario', 'STAR'])
        self.model = QLineEdit(str(self.settings.value('model', 'gpt-4.1-mini')))
        self.model.setPlaceholderText('OpenAI response model')
        self.top = QCheckBox('Always on top')
        self.top.setChecked(self.settings.value('top', False, type=bool))
        self.top.toggled.connect(self.change_top)
        opts.addWidget(QLabel('Answer mode'))
        opts.addWidget(self.mode)
        opts.addWidget(QLabel('Model'))
        opts.addWidget(self.model)
        opts.addWidget(self.top)
        layout.addLayout(opts)

        resume_row = QHBoxLayout()
        self.resume_label = QLabel('No resume loaded (in memory only)')
        load_resume = QPushButton('Load resume (TXT/PDF/DOCX)')
        load_resume.clicked.connect(self.load_resume)
        resume_row.addWidget(load_resume)
        resume_row.addWidget(self.resume_label)
        layout.addLayout(resume_row)
        self.remove_resume_btn = QPushButton('Remove resume')
        self.remove_resume_btn.clicked.connect(self.remove_resume)
        resume_row.addWidget(self.remove_resume_btn)
        self.live_btn = QPushButton('Start continuous listening (8-second microphone segments)')
        self.live_btn.clicked.connect(self.toggle_live)
        layout.addWidget(self.live_btn)
        self.auto_answer = QCheckBox('Automatically answer detected questions (practice / permitted use only)')
        layout.addWidget(self.auto_answer)
        layout.addWidget(QLabel('Question (type or record)'))
        self.question = QTextEdit()
        self.question.setPlaceholderText('Example: How would you troubleshoot EKS pods stuck in CrashLoopBackOff?')
        self.question.setMaximumHeight(125)
        layout.addWidget(self.question)
        actions = QHBoxLayout()
        self.record_btn = QPushButton('Start recording')
        self.record_btn.clicked.connect(self.toggle_record)
        self.ask_btn = QPushButton('Ask AI')
        self.ask_btn.clicked.connect(self.ask)
        clear = QPushButton('Clear')
        clear.clicked.connect(self.clear)
        actions.addWidget(self.record_btn)
        actions.addWidget(self.ask_btn)
        actions.addWidget(clear)
        layout.addLayout(actions)

        layout.addWidget(QLabel('AI Answer'))
        self.answer = QTextEdit()
        self.answer.setReadOnly(True)
        layout.addWidget(self.answer)
        bottom = QHBoxLayout()
        copy = QPushButton('Copy answer')
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.answer.toPlainText()))
        bottom.addWidget(copy)
        bottom.addWidget(QLabel('Shortcuts: Ctrl+Enter ask · Ctrl+R record · Ctrl+Shift+I show/hide'))
        layout.addLayout(bottom)
        layout.addWidget(QLabel('Mock interview: enter your own answer, then request feedback'))
        self.mock_answer = QTextEdit()
        self.mock_answer.setMaximumHeight(75)
        self.mock_answer.setPlaceholderText('Your spoken or written answer to the question')
        layout.addWidget(self.mock_answer)
        evaluate = QPushButton('Evaluate my mock answer')
        evaluate.clicked.connect(self.evaluate_mock)
        layout.addWidget(evaluate)
        history_row = QHBoxLayout()
        self.history_list = QComboBox()
        self.history_list.setMinimumWidth(280)
        self.history_list.currentIndexChanged.connect(self.show_history)
        refresh = QPushButton('Refresh history')
        refresh.clicked.connect(self.refresh_history)
        history_row.addWidget(QLabel('Saved history'))
        history_row.addWidget(self.history_list)
        history_row.addWidget(refresh)
        layout.addLayout(history_row)
        self.history_rows = []
        self.refresh_history()
        self.statusBar().showMessage('Ready')
        self.setCentralWidget(root)

        ask_action = QAction(self)
        ask_action.setShortcut(QKeySequence('Ctrl+Return'))
        ask_action.triggered.connect(self.ask)
        self.addAction(ask_action)
        rec_action = QAction(self)
        rec_action.setShortcut(QKeySequence('Ctrl+R'))
        rec_action.triggered.connect(self.toggle_record)
        self.addAction(rec_action)

        self.tray = QSystemTrayIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), self)
        menu = QMenu()
        show_action = menu.addAction('Show / Hide')
        show_action.triggered.connect(self.toggle_visible)
        quit_action = menu.addAction('Quit')
        quit_action.triggered.connect(QApplication.instance().quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.toggle_visible() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.tray.show()
        self.change_top(self.top.isChecked())
        self.register_global_hotkey()

    def role_changed(self, role):
        self.custom_role.setVisible(role == 'Custom role...')
        self.settings.setValue('role', role)

    def selected_role(self):
        return self.custom_role.text().strip() if self.role.currentText() == 'Custom role...' else self.role.currentText()

    def remove_resume(self):
        self.resume_text = ''
        self.resume_label.setText('No resume loaded (in memory only)')

    def register_global_hotkey(self):
        # Optional: Windows global shortcut. Some systems/security tools may block this.
        try:
            import keyboard
            from PySide6.QtCore import QTimer
            self.hotkey_bridge = Signals()
            self.hotkey_bridge.done.connect(lambda _: self.toggle_visible())
            keyboard.add_hotkey('ctrl+shift+i', lambda: self.hotkey_bridge.done.emit(None))
            self.statusBar().showMessage('Ready · global Ctrl+Shift+I enabled')
        except Exception:
            self.statusBar().showMessage('Ready · global hotkey unavailable; tray icon still works')

    def toggle_visible(self):
        if self.isVisible():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def change_top(self, checked):
        self.settings.setValue('top', checked)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()

    def save_key(self):
        value = self.key.text().strip()
        if not value:
            QMessageBox.information(self, 'API key', 'Enter an API key to save it.')
            return
        try:
            keyring.set_password(SERVICE, ACCOUNT, value)
            self.key.clear()
            self.key.setPlaceholderText('API key saved securely (leave blank to keep it)')
            self.statusBar().showMessage('API key saved')
        except Exception as e:
            QMessageBox.critical(self, 'Credential storage failed', str(e))

    def get_key(self):
        value = self.key.text().strip()
        if value:
            return value
        return keyring.get_password(SERVICE, ACCOUNT)

    def launch(self, fn, on_done):
        self.busy = True
        self.ask_btn.setEnabled(False)
        self.record_btn.setEnabled(False)
        job = Job(fn)
        self.jobs.append(job)
        def done(result):
            self.finish(job)
            on_done(result)
        def error(message):
            self.finish(job)
            self.statusBar().showMessage('Error')
            QMessageBox.warning(self, 'Operation failed', message)
        job.signals.done.connect(done)
        job.signals.error.connect(error)
        self.pool.start(job)

    def finish(self, job):
        self.busy = False
        self.ask_btn.setEnabled(True)
        self.record_btn.setEnabled(True)
        if job in self.jobs:
            self.jobs.remove(job)

    def load_resume(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Select resume', '', 'Documents (*.txt *.md *.pdf *.docx)')
        if not filename: return
        try:
            self.resume_text = read_resume(filename)
            self.resume_label.setText(f'Loaded {len(self.resume_text)} characters')
        except Exception as e:
            QMessageBox.warning(self, 'Resume error', str(e))

    def refresh_history(self):
        self.history_rows = recent_history()
        self.history_list.blockSignals(True)
        self.history_list.clear()
        self.history_list.addItem('Choose a saved entry', -1)
        for i, (at, kind, question, answer) in enumerate(self.history_rows):
            self.history_list.addItem(f'{kind}: {question[:65]}', i)
        self.history_list.blockSignals(False)

    def show_history(self, index):
        idx = self.history_list.currentData()
        if idx is None or idx < 0: return
        _, _, question, answer = self.history_rows[idx]
        self.question.setPlainText(question)
        self.answer.setPlainText(answer)

    def evaluate_mock(self):
        if self.busy or self.live: return
        question = self.question.toPlainText().strip()
        candidate = self.mock_answer.toPlainText().strip()
        key = self.get_key()
        if not question or not candidate or not key:
            QMessageBox.information(self, 'Missing input', 'Enter a question, your answer, and API key.')
            return
        model = self.model.text().strip() or 'gpt-4.1-mini'
        role = self.selected_role()
        description = self.job_description.toPlainText().strip()
        resume = self.resume_text
        self.answer.setPlainText('Evaluating...')
        self.launch(lambda: evaluate_answer(key, question, candidate, model, resume, role, description),
                    lambda result: self.save_and_display('mock evaluation', question, result))

    def save_and_display(self, kind, question, result):
        self.answer.setPlainText(result)
        save_history(kind, question, result)
        self.refresh_history()
        self.statusBar().showMessage('Ready')

    def toggle_live(self):
        if self.live:
            self.live = False
            self.live_timer.stop()
            try:
                if self.recording:
                    self.recorder.stop()
                    self.recording = False
            except Exception: pass
            self.live_btn.setText('Start continuous listening (8-second microphone segments)')
            self.statusBar().showMessage('Continuous listening stopped')
            return
        if self.busy or self.recording: return
        if not self.get_key():
            QMessageBox.warning(self, 'Missing API key', 'Save your OpenAI API key first.')
            return
        try:
            self.recorder.start()
            self.recording = True
            self.live = True
            self.live_btn.setText('Stop continuous listening')
            self.live_timer.start()
            self.statusBar().showMessage('Listening via microphone; 8-second segments')
        except Exception as e:
            QMessageBox.warning(self, 'Microphone error', str(e))

    def live_chunk(self):
        if not self.live or self.live_pending: return
        try:
            audio = self.recorder.stop()
            self.recording = False
            self.recorder.start()
            self.recording = True
            self.live_pending = True
            key = self.get_key()
            job = Job(lambda: transcribe_audio(key, audio))
            self.jobs.append(job)
            def done(text):
                self.jobs.remove(job)
                self.live_pending = False
                if self.live: self.on_live_transcript(text)
            def error(message):
                self.jobs.remove(job)
                self.live_pending = False
                self.statusBar().showMessage('Transcription error: ' + message[:100])
            job.signals.done.connect(done)
            job.signals.error.connect(error)
            self.pool.start(job)
        except Exception as e:
            self.statusBar().showMessage('Audio error: ' + str(e))
            self.toggle_live()

    def on_live_transcript(self, text):
        if not text.strip(): return
        self.question.setPlainText(text)
        self.statusBar().showMessage('Latest transcription: ' + text[:90])
        # Conservative heuristic: explicit question mark or question starter.
        starters = ('how ', 'what ', 'why ', 'when ', 'where ', 'which ', 'can you ', 'could you ',
                    'explain ', 'describe ', 'tell me ', 'walk me through ', 'have you ')
        candidate = text.strip()
        detected = '?' in candidate or candidate.lower().startswith(starters)
        if self.auto_answer.isChecked() and detected and candidate != self.last_question and not self.busy:
            self.last_question = candidate
            self.ask()

    def toggle_record(self):
        if self.busy or self.live:
            return
        if not self.recording:
            try:
                self.recorder.start()
                self.recording = True
                self.record_btn.setText('Stop & transcribe')
                self.statusBar().showMessage('Recording microphone...')
            except Exception as e:
                QMessageBox.warning(self, 'Microphone error', str(e))
            return
        self.recording = False
        self.record_btn.setText('Start recording')
        try:
            audio = self.recorder.stop()
            key = self.get_key()
            if not key:
                QMessageBox.warning(self, 'Missing API key', 'Save your OpenAI API key first.')
                return
            self.statusBar().showMessage('Transcribing audio...')
            self.launch(lambda: transcribe_audio(key, audio), self.on_transcribed)
        except Exception as e:
            QMessageBox.warning(self, 'Audio error', str(e))

    def on_transcribed(self, text):
        self.question.setPlainText(text)
        self.statusBar().showMessage('Transcribed. Review the question, then click Ask AI.')

    def ask(self):
        if self.busy:
            return
        question = self.question.toPlainText().strip()
        if not question:
            QMessageBox.information(self, 'Question required', 'Type or transcribe a question first.')
            return
        key = self.get_key()
        if not key:
            QMessageBox.warning(self, 'Missing API key', 'Enter and save your OpenAI API key.')
            return
        model = self.model.text().strip() or 'gpt-4.1-mini'
        self.settings.setValue('model', model)
        mode = self.mode.currentText()
        role = self.selected_role()
        job_description = self.job_description.toPlainText().strip()
        self.answer.setPlainText('Generating answer...')
        self.statusBar().showMessage('Generating answer...')
        self.launch(lambda: generate_answer(key, question, mode, model, self.resume_text, role, job_description), lambda result: self.save_and_display('AI answer', question, result))

    def on_answer(self, text):
        self.answer.setPlainText(text)
        self.statusBar().showMessage('Answer ready')

    def clear(self):
        self.question.clear()
        self.answer.clear()

    def closeEvent(self, event):
        if self.live:
            self.live_timer.stop()
        if self.recording:
            try:
                self.recorder.stop()
            except Exception:
                pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = Window()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
