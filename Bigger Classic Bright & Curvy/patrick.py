import sys, string, random, json

from module.functions import *
from module.statics   import *

from Crypto.Cipher       import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash         import SHA256

from base64 import b64encode, b64decode

from PySide2.QtGui     import QFont, QFontDatabase, QIcon, QCursor, QColor, QPainter, QPixmap, QDesktopServices, QIntValidator
from PySide2.QtCore    import Qt, QPoint, QSize, QUrl, QTimer
from PySide2.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QFrame, QMenu, QLineEdit, QWidget, QCheckBox, QPushButton, QLabel, QPlainTextEdit, QColorDialog, QVBoxLayout, QScrollArea, QSpacerItem, QSizePolicy, QSizePolicy, QGridLayout

# Make yourself comfortable, it's quite a long read.

class Patrick(QMainWindow):
    master_key = None
    from_login = None
    from_configuration = None
    were_passwords_hidden = None

    is_add_password_enabled = False
    is_edit_mode_enabled = False

    stored_passwords = {}

    stored_password_frames = []
    stored_password_main_content = []
    stored_password_edit_content = []

    def __init__(self):
        super().__init__()

        self.setWindowTitle(NAME)
        self.setFixedSize(WIDTH * MULTIPLIER, HEIGHT * MULTIPLIER)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.initiateApplication()
    
    def initiateApplication(self):
        self.clipboard = QApplication.clipboard()

        self.loadFonts()
        
        self.configuration = readJSON(CONFIGURATION, 'configuration')
        self.default_colors = readJSON(CONFIGURATION, 'default_colors')
            
        self.lang = loadLanguage(LANG, 'en')

        self.custom_colors = self.configuration['custom_colors']

        self.windowWidgets()
        self.mainWidgets()

        window_group = {
            True: 'login',
            False: 'main',

        }.get(self.configuration['use_key'], 'register')

        if window_group == 'register' or window_group == 'login':
            self.loginWidgets()

            if window_group == 'register':
                self.registerWidgets()

        self.assembleApplication(window_group)
        self.changeWindow(window_group)

        if window_group == 'main':
            self.loadStoredPasswords()

        else:
            self.from_login = True
        
        self.applyConfiguration()

    def loadFonts(self):
        font_family = QFontDatabase.applicationFontFamilies(QFontDatabase.addApplicationFont(FONT.format('Inter-Regular')))[0]
    
        self.font_normal = QFont(font_family, FONT_SIZE)
        self.font_bold = QFont(font_family, FONT_SIZE, QFont.Bold)
        self.font_small = QFont(font_family, 8)

    def windowWidgets(self):
        self.background_frame = QFrame(self)
        self.bar_frame = QFrame(self)

        self.pin_window_check_box = QCheckBox(self)

        self.pin_window_check_box.setCursor(Qt.PointingHandCursor)
        
        self.pin_window_check_box.stateChanged.connect(lambda: self.pinWindow())
        self.pin_window_check_box.stateChanged.connect(lambda: self.setAndColorizeIcon())
        
        self.title_label = QLabel(self)
        
        self.title_label.setFont(self.font_bold)
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title_label.setWindowFlag(Qt.FramelessWindowHint)
        self.title_label.setAttribute(Qt.WA_NoSystemBackground)

        self.minimize_window_button = QPushButton(self)
        self.close_window_button = QPushButton(self)

        self.minimize_window_button.clicked.connect(lambda: self.showMinimized())
        self.close_window_button.clicked.connect(lambda: self.close())

    def registerWidgets(self):
        self.advice_frame = QFrame(self)
        self.register_frame = QFrame(self)
        self.create_key_line_frame = QFrame(self)
        self.confirm_key_line_frame = QFrame(self)

        self.create_key_line = QLineEdit(self)
        self.confirm_key_line = QLineEdit(self)

        self.create_key_line.setAlignment(Qt.AlignCenter)
        self.confirm_key_line.setAlignment(Qt.AlignCenter)
        self.create_key_line.setTextMargins(8, 0, 8, 0)
        self.confirm_key_line.setTextMargins(8, 0, 8, 0)
        self.create_key_line.setEchoMode(QLineEdit.Password)
        self.confirm_key_line.setEchoMode(QLineEdit.Password)
        self.create_key_line.setFont(self.font_small)
        self.confirm_key_line.setFont(self.font_small)

        self.create_key_line.textChanged.connect(lambda: self.enableContinue())
        self.confirm_key_line.textChanged.connect(lambda: self.enableContinue())
        self.create_key_line.returnPressed.connect(lambda: self.confirm_key_line.setFocus())
        self.confirm_key_line.returnPressed.connect(
            lambda: self.manageRegister() if self.continue_button.isEnabled() else None
        )
            
        self.create_key_label = QLabel(self)
        self.confirm_key_label = QLabel(self)
        self.advice_label = QLabel(self)

        for label, text in [
            (self.create_key_label, 'create_key_label'),
            (self.confirm_key_label, 'confirm_key_label'),
            (self.advice_label, 'advice_label')
        ]:
            label : QLabel

            label.setText(self.lang[text])
            label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            label.setWindowFlag(Qt.FramelessWindowHint)
            label.setAttribute(Qt.WA_NoSystemBackground)

        self.create_key_label.setFont(self.font_normal)
        self.confirm_key_label.setFont(self.font_normal)
        self.advice_label.setFont(self.font_small)

        self.continue_button = QPushButton(self)
        self.dismiss_key_button = QPushButton(self)

        self.continue_button.setFont(self.font_normal)
        self.dismiss_key_button.setFont(self.font_small)
        self.continue_button.setCursor(Qt.PointingHandCursor)
        self.dismiss_key_button.setCursor(Qt.PointingHandCursor)
        self.continue_button.setDisabled(True)
        self.continue_button.setText(self.lang['continue_button'])
        self.dismiss_key_button.setText(self.lang['dismiss_key_button'])

        self.continue_button.clicked.connect(lambda: self.manageRegister())
        self.dismiss_key_button.clicked.connect(lambda: self.dismissKey())

    def loginWidgets(self):
        self.login_frame = QFrame(self)
        self.enter_key_frame = QFrame(self)
        self.key_line_frame = QFrame(self)

        self.key_line = QLineEdit(self)

        self.key_line.setAlignment(Qt.AlignCenter)
        self.key_line.setTextMargins(8, 0, 8, 0)
        self.key_line.setFont(self.font_normal)
        self.key_line.setEchoMode(QLineEdit.Password)
        self.key_line.setFont(self.font_small)

        self.key_line.textChanged.connect(lambda: self.enableLogin())
        self.key_line.returnPressed.connect(
            lambda: self.submitKey() if self.submit_key_button.isEnabled() else None
        )

        self.key_label = QLabel(self)

        self.key_label.setText(self.lang['key_label'])
        self.key_label.setFont(self.font_normal)
        self.key_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.key_label.setWindowFlag(Qt.FramelessWindowHint)
        self.key_label.setAttribute(Qt.WA_NoSystemBackground)

        self.submit_key_button = QPushButton(self)

        self.submit_key_button.setFont(self.font_normal)
        self.submit_key_button.setCursor(Qt.PointingHandCursor)
        self.submit_key_button.setDisabled(True)
        self.submit_key_button.setText(self.lang['submit_key_button'])

        self.submit_key_button.mousePressEvent = lambda _: self.submitKey()

    def mainWidgets(self):
        self.information_frame = QFrame(self)
        self.fixes_frame = QFrame(self)
        self.password_frame = QFrame(self)
        self.stored_passwords_frame = QFrame(self)
        self.stored_passwords_bar_frame = QFrame(self)
        self.search_frame = QFrame(self)
        self.configuration_frame = QFrame(self)
        self.password_size_frame = QFrame(self)
        self.password_size_line_frame = QFrame(self)
        self.password_colors_frame = QFrame(self)
        self.application_colors_frame = QFrame(self)
        self.youtube_frame = QFrame(self)
        self.github_frame = QFrame(self)

        self.stored_passwords_scroll_area = QScrollArea(self)
        self.stored_password_content_widget = QWidget(self.stored_passwords_scroll_area)
        self.stored_passwords_content_layout = QVBoxLayout(self.stored_password_content_widget)

        self.stored_passwords_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.stored_passwords_scroll_area.setWidgetResizable(True)
        self.stored_passwords_scroll_area.setWidget(self.stored_password_content_widget)
        self.stored_passwords_content_layout.addItem(QSpacerItem(32 * MULTIPLIER, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.stored_passwords_content_layout.setDirection(QVBoxLayout.Direction.BottomToTop)
        self.stored_passwords_content_layout.setMargin(0)
        self.stored_passwords_content_layout.setSpacing(0)

        self.prefix_line = QLineEdit(self)
        self.subfix_line = QLineEdit(self)
        self.password_line = QLineEdit(self)
        self.information_line = QLineEdit(self)
        self.search_line = QLineEdit(self)
        self.password_size_line = QLineEdit(self)

        self.password_line.installEventFilter(self)
        self.information_line.installEventFilter(self)
        self.password_line.mousePressEvent = lambda _ : self.password_line.selectAll()

        for line, text in [
            (self.prefix_line, 'prefix_line'),
            (self.subfix_line, 'subfix_line'),
            (self.password_line, 'password_line'),
            (self.search_line, 'search_line')
        ]:
            line : QLineEdit

            line.setPlaceholderText(self.lang[text])
            line.setAlignment(Qt.AlignCenter)
            line.setTextMargins(8, 0, 8, 0)
            line.setFont(self.font_normal)

        self.information_line.setPlaceholderText(self.lang['information_line'])
        self.prefix_line.setText(self.configuration['prefix'])
        self.subfix_line.setText(self.configuration['sufix'])
        self.information_line.setAlignment(Qt.AlignCenter)
        self.information_line.setTextMargins(8, -4, 8, 0)
        self.information_line.setFont(self.font_small)

        self.password_size_line.setAlignment(Qt.AlignCenter)
        self.password_size_line.setTextMargins(8, 0, 8, 0)
        self.password_size_line.setFont(self.font_normal)
        self.password_size_line.setText(self.configuration['password_length'])
        self.password_size_line.setPlaceholderText('12')
        self.password_size_line.setValidator(QIntValidator(0, 99))
        self.password_size_line.setMaxLength(2)

        self.password_line.returnPressed.connect(
            lambda: self.information_line.setFocus() if self.password_line.text() else self.generatePassword()
        )
        self.password_line.textChanged.connect(lambda: self.isAddPasswordEnabled())
        self.information_line.returnPressed.connect(lambda: self.addStoredPasword())
        self.search_line.textChanged.connect(lambda: self.searchStoredPassword())

        self.see_password_check_box = QCheckBox(self)
        self.edit_mode_check_box = QCheckBox(self)
        self.generate_letters_check_box = QCheckBox(self)
        self.generate_accents_check_box = QCheckBox(self)
        self.generate_uppercase_check_box = QCheckBox(self)
        self.generate_lowercase_check_box = QCheckBox(self)
        self.generate_numbers_check_box = QCheckBox(self)
        self.generate_symbols_check_box = QCheckBox(self)
        self.generate_custom_text_check_box = QCheckBox(self)

        self.generate_letters_check_box.stateChanged.connect(lambda: self.checkBoxSynchronization())
        self.generate_accents_check_box.stateChanged.connect(lambda: self.checkBoxSynchronization())
        self.generate_uppercase_check_box.stateChanged.connect(lambda: self.checkBoxSynchronization(False))
        self.generate_lowercase_check_box.stateChanged.connect(lambda: self.checkBoxSynchronization(False))

        for check_box in [
            self.see_password_check_box,
            self.generate_letters_check_box,
            self.generate_accents_check_box,
            self.generate_uppercase_check_box,
            self.generate_lowercase_check_box,
            self.generate_numbers_check_box,
            self.generate_symbols_check_box,
            self.generate_custom_text_check_box
        ]:
            check_box : QCheckBox
            
            check_box.setCursor(Qt.PointingHandCursor)

        self.generate_symbols_check_box.setDisabled(True)

        self.see_password_check_box.stateChanged.connect(lambda: self.changeStoredPasswordsVisibility())
        self.edit_mode_check_box.stateChanged.connect(lambda: self.changeStoredPasswordsMode())
        self.see_password_check_box.stateChanged.connect(lambda: self.setAndColorizeIcon())
        self.edit_mode_check_box.stateChanged.connect(lambda: self.setAndColorizeIcon())

        for check_box in [
            self.generate_letters_check_box,
            self.generate_accents_check_box,
            self.generate_uppercase_check_box,
            self.generate_lowercase_check_box,
            self.generate_numbers_check_box,
            self.generate_symbols_check_box,
            self.generate_custom_text_check_box
        ]:
            check_box : QCheckBox

            check_box.mousePressEvent = lambda _: self.setAndColorizeIcon()

        self.generate_custom_text_check_box.mousePressEvent = lambda _: self.customTextSynchronization()

        self.custom_text_plain = QPlainTextEdit(self)

        self.custom_text_plain.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.custom_text_plain.setPlaceholderText(self.lang['custom_text_plain'])
        self.custom_text_plain.setFont(self.font_small)
        self.custom_text_plain.setPlainText(self.configuration['custom_text'])

        self.custom_text_plain.textChanged.connect(lambda: self.customTextSynchronization())

        self.generate_letters_clickable_label = QLabel(self)
        self.generate_accents_clickable_label = QLabel(self)
        self.generate_uppercase_clickable_label = QLabel(self)
        self.generate_lowercase_clickable_label = QLabel(self)
        self.generate_numbers_clickable_label = QLabel(self)
        self.generate_symbols_clickable_label = QLabel(self)
        self.generate_custom_text_clickable_label = QLabel(self)
        self.password_size_label = QLabel(self)
        self.password_colors_label = QLabel(self)
        self.application_colors_label = QLabel(self)
        self.youtube_label = QLabel(self)
        self.github_label = QLabel(self)
        self.youtube_image_label = QLabel(self)
        self.github_image_label = QLabel(self)
        self.information_label = QLabel(self)

        for label, text in [
            (self.generate_letters_clickable_label, 'generate_letters_check_box'),
            (self.generate_accents_clickable_label, 'generate_accents_check_box'),
            (self.generate_uppercase_clickable_label, 'generate_uppercase_check_box'),
            (self.generate_lowercase_clickable_label, 'generate_lowercase_check_box'),
            (self.generate_numbers_clickable_label, 'generate_numbers_check_box'),
            (self.generate_symbols_clickable_label, 'generate_symbols_check_box'),
            (self.password_size_label, 'password_size_label'),
            (self.password_colors_label, 'password_colors_label'),
            (self.application_colors_label, 'application_colors_label'),
            (self.youtube_label, 'youtube_label'),
            (self.github_label, 'github_label')
        ]:
            label : QLabel

            label.setText(self.lang[text])
            label.setFont(self.font_normal)
            label.setWindowFlag(Qt.FramelessWindowHint)
            label.setCursor(Qt.PointingHandCursor)
            label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            label.setAttribute(Qt.WA_NoSystemBackground)

        self.generate_custom_text_clickable_label.setText(self.lang['generate_custom_text_check_box'])
        self.information_label.setText(self.lang['information_label'])
        self.generate_custom_text_clickable_label.setFont(self.font_normal)
        self.information_label.setFont(self.font_small)
        self.generate_custom_text_clickable_label.setWindowFlag(Qt.FramelessWindowHint)
        self.information_label.setWindowFlag(Qt.FramelessWindowHint)
        self.generate_custom_text_clickable_label.setCursor(Qt.ArrowCursor)
        self.generate_custom_text_clickable_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.information_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.generate_custom_text_clickable_label.setAttribute(Qt.WA_NoSystemBackground)
        self.information_label.setAttribute(Qt.WA_NoSystemBackground)

        self.generate_letters_clickable_label.mousePressEvent = lambda _: self.generate_letters_check_box.setChecked(not self.generate_letters_check_box.isChecked())
        self.generate_accents_clickable_label.mousePressEvent = lambda _: self.generate_accents_check_box.setChecked(not self.generate_accents_check_box.isChecked())
        self.generate_uppercase_clickable_label.mousePressEvent = lambda _: self.generate_uppercase_check_box.setChecked(not self.generate_uppercase_check_box.isChecked())
        self.generate_lowercase_clickable_label.mousePressEvent = lambda _: self.generate_lowercase_check_box.setChecked(not self.generate_lowercase_check_box.isChecked())
        self.generate_numbers_clickable_label.mousePressEvent = lambda _: self.generate_numbers_check_box.setChecked(not self.generate_numbers_check_box.isChecked())
        self.generate_symbols_clickable_label.mousePressEvent = lambda _: self.generate_symbols_check_box.setChecked(not self.generate_symbols_check_box.isChecked())
        self.generate_custom_text_clickable_label.mousePressEvent = lambda _: self.generate_custom_text_check_box.setChecked(not self.generate_custom_text_check_box.isChecked())

        self.reload_password_button = QPushButton(self)
        self.configuration_button = QPushButton(self)
        self.password_color_background_button = QPushButton(self)
        self.password_color_letter_button = QPushButton(self)
        self.add_password_button = QPushButton(self)
        self.password_color_default = QPushButton(self)
        self.application_color_default = QPushButton(self)
        self.application_color_background_button = QPushButton(self)
        self.application_color_letter_button = QPushButton(self)
        self.application_color_disabled_button = QPushButton(self)
        self.exit_configuration_button = QPushButton(self)
        self.youtube_button = QPushButton(self)
        self.github_button = QPushButton(self)

        self.exit_configuration_button.setFont(self.font_normal)
        self.exit_configuration_button.setText(self.lang['exit_configuration_button'])
        
        for button in [
            self.exit_configuration_button,
            self.password_color_background_button,
            self.password_color_letter_button,
            self.application_color_background_button,
            self.application_color_letter_button,
            self.application_color_disabled_button,
            self.youtube_button,
            self.github_button
        ]:
            button : QPushButton

            button.setCursor(Qt.PointingHandCursor)

        self.reload_password_button.clicked.connect(lambda: self.generatePassword())
        self.configuration_button.clicked.connect(lambda: self.changeWindow('configuration'))
        self.application_color_default.clicked.connect(lambda: self.restoreCustomColorsDictionary())
        self.password_color_default.clicked.connect(lambda: self.restoreCustomColorsDictionary(False))
        self.exit_configuration_button.clicked.connect(lambda: self.changeWindow('main'))
        self.password_color_background_button.clicked.connect(lambda: self.saveColorSelection('--password_background'))
        self.password_color_letter_button.clicked.connect(lambda: self.saveColorSelection('--password_letter'))
        self.add_password_button.clicked.connect(lambda: self.addStoredPasword())
        self.application_color_background_button.clicked.connect(lambda: self.saveColorSelection('--background'))
        self.application_color_letter_button.clicked.connect(lambda: self.saveColorSelection('--letter'))
        self.application_color_disabled_button.clicked.connect(lambda: self.saveColorSelection('--disabled'))
        self.youtube_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://www.youtube.com/@BerdyAlexeiEN' if getLanguage() != 'es' else 'https://www.youtube.com/@BerdyAlexeiES')))
        self.github_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/BerdyAlexei/Patrick')))

    def customContextMenu(self):
        context_menu = QMenu()

        context_menu.setFont(self.font_normal)
        context_menu.setStyleSheet(loadModificableFile(FILE, 'menu', self.colors))

        action_undo = context_menu.addAction(self.lang['action_undo'])
        action_redo = context_menu.addAction(self.lang['action_redo'])

        context_menu.addSeparator()

        action_select_all = context_menu.addAction(self.lang['action_select_all'])

        context_menu.addSeparator()

        action_copy = context_menu.addAction(self.lang['action_copy'])
        action_cut = context_menu.addAction(self.lang['action_cut'])
        action_paste = context_menu.addAction(self.lang['action_paste'])

        global_mouse_position = QCursor.pos()
        context_menu_position = global_mouse_position - self.mapToGlobal(QPoint(0, 0))
        action = context_menu.exec_(self.mapToGlobal(context_menu_position))

        if action == action_undo:
            self.focusWidget().undo()
            
        if action == action_redo:
            self.focusWidget().redo()
            
        if action == action_select_all:
            self.focusWidget().selectAll()
            
        if action == action_copy:
            self.focusWidget().copy()
            
        if action == action_cut:
            self.focusWidget().cut()
            
        if action == action_paste:
            self.focusWidget().paste()

    def assembleApplication(self, window_group):
        widget_properties = [
            ('window', self.background_frame, 'alternative', 'None', WIDTH, HEIGHT, 0, 8),
            ('window', self.bar_frame, 'normal', 'top_rounded', WIDTH, WIDGET_HEIGHT, 0, 0),
            ('main', self.information_frame, 'inverted', None, 484, 12, 8, 72),
            ('main', self.fixes_frame, 'normal', 'top_rounded', 484, WIDGET_HEIGHT, 8, 40),
            ('main', self.password_frame, 'inverted', None, 324, WIDGET_HEIGHT, 88, 40),
            ('main', self.stored_passwords_frame, 'inverted', None, 484, 180, 8, 124),
            ('main', self.stored_passwords_bar_frame, 'normal', 'top_rounded', 484, WIDGET_HEIGHT, 8, 92),
            ('main', self.search_frame, 'inverted', 'full_rounded', 408, 24, 44, 96),
            ('configuration', self.configuration_frame, 'inverted', 'top_rounded', 484, 263, 8, 40),
            ('main', self.prefix_line, 'normal', None, 80, WIDGET_HEIGHT, 8, 40),
            ('configuration', self.password_size_frame, 'normal', 'full_rounded',  226, 24, 258, 49),
            ('configuration', self.password_size_line_frame, 'inverted', 'full_rounded', 52, 16, 427, 53),
            ('configuration', self.password_colors_frame, 'normal', 'full_rounded',  226, 24, 258, 81),
            ('configuration', self.application_colors_frame, 'normal', 'full_rounded', 226, 24, 258, 113),
            ('configuration', self.youtube_frame, 'normal', 'full_rounded', 226, 24, 258, 177),
            ('configuration', self.github_frame, 'normal', 'top_rounded', 226, 24, 258, 208),
            ('main', self.stored_passwords_scroll_area, 'inverted', None, 484, 180, 8, 124),
            ('main', self.stored_password_content_widget, 'inverted', None, None, None, None, None),
            ('main', self.subfix_line, 'normal', None, 80, WIDGET_HEIGHT, 412, 40),
            ('main', self.password_line, 'inverted', None, 196, WIDGET_HEIGHT, 152, 40),
            ('main', self.information_line, 'inverted', None, 484, 12, 8, 72),
            ('main', self.search_line, 'inverted', None, 408, 24, 44, 96),
            ('configuration', self.password_size_line, 'inverted', None, 52, 16, 427, 53),
            ('window', self.pin_window_check_box, 'main_window', None, WIDGET_WIDTH, WIDGET_HEIGHT, 436, 0),
            ('main', self.see_password_check_box, 'main_window', None, WIDGET_WIDTH, WIDGET_HEIGHT, 10, 92),
            ('main', self.edit_mode_check_box, 'main_window', None, WIDGET_WIDTH, WIDGET_HEIGHT, 456, 92),
            ('configuration', self.generate_letters_check_box, 'configuration_window', 'full_rounded', 226, 24, 16, 48),
            ('configuration', self.generate_accents_check_box, 'configuration_window', 'full_rounded', 226, 24, 16, 80),
            ('configuration', self.generate_uppercase_check_box, 'configuration_window', 'full_rounded', 109, 24, 16, 112),
            ('configuration', self.generate_lowercase_check_box, 'configuration_window', 'full_rounded', 109, 24, 133, 112),
            ('configuration', self.generate_numbers_check_box, 'configuration_window', 'full_rounded', 226, 24, 16, 144),
            ('configuration', self.generate_symbols_check_box, 'configuration_window', 'full_rounded', 226, 24, 16, 176),
            ('configuration', self.generate_custom_text_check_box, 'configuration_window', 'top_rounded', 226, 89, 16, 207),
            ('configuration', self.generate_custom_text_clickable_label, None, 'full_rounded', 226, 24, 16, 207),
            ('configuration', self.custom_text_plain, 'inverted', 'top_rounded', 210, 56-2, 24, 234),
            ('window', self.title_label, 'normal', 'title', GRAB_WIDTH, GRAB_HEIGHT, 0, 0),
            ('configuration', self.generate_letters_clickable_label, None, 'full_rounded', 226, 24, 16, 48),
            ('configuration', self.generate_accents_clickable_label, None, 'full_rounded', 226, 24, 16, 80),
            ('configuration', self.generate_uppercase_clickable_label, None, 'full_rounded', 109, 24, 16, 112),
            ('configuration', self.generate_lowercase_clickable_label, None, 'full_rounded', 109, 24, 133, 112),
            ('configuration', self.generate_numbers_clickable_label, None, 'full_rounded', 226, 24, 16, 144),
            ('configuration', self.generate_symbols_clickable_label, None, 'full_rounded', 226, 24, 16, 176),
            ('configuration', self.password_size_label, 'normal', None, 164, 24, 258, 49),
            ('configuration', self.password_colors_label, 'normal', None, 164, 24, 258, 81),
            ('configuration', self.application_colors_label, 'normal', None, 164, 24, 258, 113),
            ('configuration', self.youtube_label, 'normal', None, 226, 24, 258, 177),
            ('configuration', self.github_label, 'normal', None, 226, 24, 258, 208),
            ('configuration', self.youtube_image_label, None, None, 28, 28, 454, 175),
            ('configuration', self.github_image_label, None, None, 28, 28, 454, 207),
            ('configuration', self.information_label, 'inverted', None, 226, 57, 258, 239),
            ('window', self.minimize_window_button, None, None, WIDGET_WIDTH, WIDGET_HEIGHT, 404, 0),
            ('window', self.close_window_button, None, None, WIDGET_WIDTH, WIDGET_HEIGHT, 468, 0),
            ('main', self.reload_password_button, None, None, WIDGET_WIDTH, WIDGET_HEIGHT, 88, 40),
            ('main', self.configuration_button, None, None, WIDGET_WIDTH, WIDGET_HEIGHT, 120, 40),
            ('mixed', self.password_color_background_button, None, 'full_rounded', 16, 16, None, None),
            ('mixed', self.password_color_letter_button, None, 'full_rounded', 16, 16, None, None),
            ('main', self.add_password_button, None, None, WIDGET_WIDTH, WIDGET_HEIGHT, 380, 40),
            ('configuration', self.password_color_default, None, None, 16, 16, 425, 85),
            ('configuration', self.application_color_default, None, None, 16, 16, 406, 117),
            ('configuration', self.application_color_background_button, 'application_background', 'full_rounded', 16, 16, 463, 117),
            ('configuration', self.application_color_letter_button, 'application_letter', 'full_rounded', 16, 16, 444, 117),
            ('configuration', self.application_color_disabled_button, 'application_disabled', 'full_rounded', 16, 16, 425, 117),
            ('configuration', self.exit_configuration_button, 'normal', 'full_rounded', 226, 24, 258, 145),
            ('configuration', self.youtube_button, None, 'full_rounded', 226, 24, 258, 177),
            ('configuration', self.github_button, None, 'full_rounded', 226, 24, 258, 208)
        ]
        if window_group == 'register' or window_group == 'login':
            widget_properties += [
                ('login', self.login_frame, 'inverted', 'top_rounded', 242, 94, 129, 109),
                ('login', self.enter_key_frame, 'normal', 'full_rounded', 226, 46, 137, 117),
                ('login', self.key_line_frame, 'inverted', 'full_rounded', 218, 16, 141, 143),
                ('login', self.key_line, 'inverted', None, 218, 16, 141, 143),
                ('login', self.key_label, 'normal', None, 226, 26, 137, 117),
                ('login', self.submit_key_button, 'application_disabled', 'full_rounded', 226, 24, 137, 171)
            ]

            if window_group == 'register':
                widget_properties += [
                    ('register', self.advice_frame, 'inverted', 'top_rounded', 242, 200, 129, 69),
                    ('register', self.register_frame, 'normal', 'full_rounded', 226, 88, 137, 77),
                    ('register', self.create_key_line_frame, 'inverted', 'full_rounded', 218, 16, 141, 103),
                    ('register', self.confirm_key_line_frame, 'inverted', 'full_rounded', 218, 16, 141, 145),
                    ('register', self.create_key_line, 'inverted', None, 218, 16, 141, 103),
                    ('register', self.confirm_key_line, 'inverted', None, 218, 16, 141, 145),
                    ('register', self.create_key_label, 'normal', None, 226, 26, 137, 77),
                    ('register', self.confirm_key_label, 'normal', None, 226, 26, 137, 119),
                    ('register', self.advice_label, 'inverted', None, 226, WIDGET_HEIGHT, 137, 205),
                    ('register', self.continue_button, 'application_disabled', 'full_rounded', 226, 24, 137, 173),
                    ('register', self.dismiss_key_button, 'text_button', None, 92, 16, 204, 245)
                ]

        for group, widget, object_name, object_class, width, height, position_x, position_y in widget_properties:
            widget : QWidget

            widget.setObjectName(object_name)

            widget.setProperty('class', object_class)
            widget.setProperty('group', group)

            if width or height:
                widget.setFixedSize(width * MULTIPLIER, height * MULTIPLIER)

            if position_x or position_y:
                widget.move(position_x * MULTIPLIER, position_y * MULTIPLIER)

            if isinstance(widget, QLineEdit) or isinstance(widget, QPlainTextEdit):
                widget.setContextMenuPolicy(Qt.CustomContextMenu)

                widget.customContextMenuRequested.connect(self.customContextMenu)
        
        self.customTextSynchronization()
        self.enableGeneratePassword()

    def saveConfiguration(self):
        if self.were_passwords_hidden and self.is_edit_mode_enabled:
            self.edit_mode_check_box.setChecked(False)

        self.configuration = {    
            'use_key': self.configuration['use_key'],
            'position_x': self.pos().x(),
            'position_y': self.pos().y(),
            'pin_window': self.pin_window_check_box.isChecked(),
            'see_password': self.see_password_check_box.isChecked(),
            'prefix': self.prefix_line.text(),
            'sufix': self.subfix_line.text(),
            'generate_letters': self.generate_letters_check_box.isChecked(),
            'generate_accents': self.generate_accents_check_box.isChecked(),
            'generate_uppercase': self.generate_uppercase_check_box.isChecked(),
            'generate_lowercase': self.generate_lowercase_check_box.isChecked(),
            'generate_numbers': self.generate_numbers_check_box.isChecked(),
            'generate_symbols': self.generate_symbols_check_box.isChecked(),
            'generate_custom_text': self.generate_custom_text_check_box.isChecked(),
            'custom_text': self.custom_text_plain.toPlainText(),
            'password_length': self.password_size_line.text(),
            'custom_colors': self.colors
        }

        self.enableGeneratePassword()

        if self.master_key:
            self.saveStoredPasswords()

        saveJSON(CONFIGURATION, 'configuration', self.configuration)
    
    def loadWindowPosition(self):
        if self.configuration['position_x'] and self.configuration['position_y']:
            self.move(self.configuration['position_x'], self.configuration['position_y'])

    def pinWindow(self, normal_mode = True):
        if self.pin_window_check_box.isChecked() and normal_mode:
            self.setWindowFlags(Qt.WindowFlags(Qt.FramelessWindowHint) |  Qt.WindowStaysOnTopHint)
            self.show()

        else:
            self.setWindowFlags(Qt.WindowFlags(Qt.FramelessWindowHint))
            self.show()

    def loadStoredPasswords(self):
        if not self.configuration['use_key']:
            self.stored_passwords = loadFileAsText(FILE, 'password_storage')

        if self.configuration['use_key']:
            self.stored_passwords = self.decryptData(self.master_key)

        self.stored_passwords = json.loads(self.stored_passwords)

        if self.stored_passwords:
            self.generateStoredPasswordsList()
    
    def keysNormalizer(self, dictionary):
        stored_passwords = dict(dictionary)
        stored_passwords_keys = stored_passwords.keys()
        stored_passwords_names = list(stored_passwords_keys)
        stored_passwords_length = len(stored_passwords_keys)

        for index in range(stored_passwords_length):
            stored_passwords[f'{index}'] = stored_passwords.pop(f'{stored_passwords_names[index]}')

        return stored_passwords

    def saveStoredPasswords(self):

        if self.master_key:
            self.stored_passwords = self.keysNormalizer(self.stored_passwords) if self.stored_passwords else {}

        use_key = self.configuration['use_key']

        if use_key:
            self.encrypted_data = self.encryptData(
                json.dumps(self.stored_passwords), 
                self.master_key
            )

        saveFile(FILE, 'password_storage', self.stored_passwords if not use_key else self.encrypted_data)
        
    def decryptData(self, key):
        try:
            initialization_vector = b64decode(self.encrypted_data[:24])
            cipher_text = b64decode(self.encrypted_data[24:])

            cipher = AES.new(key, AES.MODE_CBC, initialization_vector)

            plain_text = unpad(cipher.decrypt(cipher_text), AES.block_size)

            return plain_text.decode('utf-8')
        
        except Exception as e:
            return str(e)

    def encryptData(self, data, key):
        cipher = AES.new(key, AES.MODE_CBC)

        cipher_text_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
        initialization_vector = b64encode(cipher.iv).decode('utf-8')
        cipher_text = b64encode(cipher_text_bytes).decode('utf-8')
        
        return initialization_vector + cipher_text

    def dismissKey(self):
        self.advice_label.setText(self.lang['are_you_sure_advice'])
        self.dismiss_key_button.setText(self.lang['yes_button'])

        self.dismiss_key_button.clicked.connect(lambda: self.manageRegister(False))

    def createKey(self):
        password = self.create_key_line.text().encode('utf-8')

        key = SHA256.new(password).digest()

        stored_passwords = {
            '0': {
                'password' : self.create_key_line.text(),
                'information': self.lang['key_information'],
                'background': self.colors['--password_background'],
                'letter': self.colors['--password_letter']
            }
        }

        data_to_encrypt = json.dumps(stored_passwords)
        encrypted_data = self.encryptData(data_to_encrypt, key)

        saveFile(FILE, 'password_storage', encrypted_data)

    def manageRegister(self, create = True):
        self.configuration['use_key'] = create
        
        saveFile(FILE, 'password_storage', '{}')

        if create:
            self.createKey()

        self.changeWindow('login' if create else 'main')

        self.saveConfiguration()

    def submitKey(self):
        self.encrypted_data = loadFileAsText(FILE, 'password_storage')

        password = self.key_line.text()
        password = password.encode('utf-8')
        key = SHA256.new(password).digest()

        decrypted_data = self.decryptData(key)

        try:
            self.stored_passwords = json.loads(decrypted_data)
            self.master_key = key

            self.changeWindow('main')

        except:
            self.key_line.clear()

            self.enter_key_frame.setObjectName('alternative')
            self.configureStyleSheet()

            self.key_label.setText(self.lang['decryption_failed_label'])

    def enableLogin(self):
        enable = getBool(self.key_line.text())

        self.key_label.setText(self.lang['key_label'])
        self.submit_key_button.setEnabled(enable)

        self.submit_key_button.setObjectName('normal' if enable else 'application_disabled')

        self.enter_key_frame.setObjectName('normal')
        self.configureStyleSheet()

    def enableContinue(self):
        enable = getBool(self.create_key_line.text() and (self.confirm_key_line.text() == self.create_key_line.text()))
        
        self.continue_button.setEnabled(enable)

        self.continue_button.setObjectName('normal' if enable else 'application_disabled')

        self.configureStyleSheet()

    def enableGeneratePassword(self):
        value : bool

        for key in [
            'generate_letters',
            'generate_accents',
            'generate_uppercase',
            'generate_lowercase',
            'generate_numbers',
            'generate_symbols'
        ]:
            value = self.configuration[key]

            if value:
                break

        if not value and self.configuration['custom_text']:
            value = self.configuration['generate_custom_text']

        try:
            password_size_line_int = int(self.password_size_line.text())

            if password_size_line_int < 1 or password_size_line_int == 12:

                self.password_size_line.clear()

        except:
            self.password_size_line.clear()

        self.is_generate_password_enabled = value

    def generatePassword(self):
        if not self.is_generate_password_enabled:
            return None
        
        generate = dict(self.configuration)

        accents_uppercase = 'ÀÈÌÒÙÁÉÍÓÚÝÂÊÎÔÛÃÑÕÄËÏÖÜŸÅÆŒÇÐØ'
        accents_lowercase = 'àèìòùáéíóúýâêîôûãñõäëïöüÿåæœçðø'
        custom_text = generate['custom_text'].split()

        characters_string = ''
        characters_list = []

        try:
            characters_length = int(generate['password_length'])

            if not characters_length > 0:
                characters_length = 12

        except:
            characters_length = 12

        if generate['generate_uppercase']:
            if generate['generate_letters']:
                characters_string += string.ascii_uppercase

            if generate['generate_accents']:
                characters_string += accents_uppercase
        
        if generate['generate_lowercase']:
            if generate['generate_letters']:
                characters_string += string.ascii_lowercase

            if generate['generate_accents']:
                characters_string += accents_lowercase
        
        if generate['generate_numbers']:
            characters_string += string.digits

        if generate['generate_symbols']:
            characters_string += string.punctuation

        characters_list += list(characters_string)

        if generate['generate_custom_text']:
            for word in custom_text:
                characters_list.append(word)

        password = ''.join(random.choices(characters_list, k = characters_length))
        password = password[:characters_length]

        self.password_line.setText(self.prefix_line.text() + password + self.subfix_line.text())

    def changeWindow(self, window_group : str):
        if window_group == 'configuration':
            self.from_configuration = True

        elif window_group == 'login':
            self.key_line.setFocus()

        elif window_group == 'register':
            self.create_key_line.setFocus()

        positions = {
            'main': {
                'letter': (351 * MULTIPLIER, 53 * MULTIPLIER),
                'background': (361 * MULTIPLIER, 43 * MULTIPLIER)
            },

            'configuration': {
                'letter': (444 * MULTIPLIER, 85 * MULTIPLIER),
                'background': (463 * MULTIPLIER, 85 * MULTIPLIER)
            }
        }

        if window_group in positions:
            x, y = positions[window_group]['letter']
            self.password_color_background_button.move(x, y)

            x, y = positions[window_group]['background']
            self.password_color_letter_button.move(x, y)

        self.title_label.setText(self.lang[window_group + '_title_label'])

        self.password_color_background_button.setObjectName(f'password_background_' + window_group)
        self.password_color_letter_button.setObjectName(f'password_letter_' + window_group)

        for widget in self.findChildren(QWidget):
            widget : QWidget

            widget_group = widget.property('group')

            is_scroll_area_child = self.stored_passwords_scroll_area.isAncestorOf(widget)
            is_plain_text_edit_child = isinstance(widget.parent(), QPlainTextEdit) # This shit almost ruined my christmas.
            is_register = window_group in {'login', 'register'} and widget_group in {window_group, 'window'}
            is_other = widget_group in {window_group, 'window', 'mixed'}

            if not is_plain_text_edit_child and not is_scroll_area_child:
                if (window_group in {'login', 'register'} and is_register) or (window_group not in {'login', 'register'} and is_other):
                    widget.show()

                else:
                    
                    widget.hide()

        if window_group == 'main':
            self.enableGeneratePassword()

            if self.from_configuration:
                self.from_configuration = False

                self.saveConfiguration()

            elif self.from_login:
                self.from_login = False

                self.loadStoredPasswords()
                
            self.stored_passwords_scroll_area.show()
            self.stored_password_content_widget.show()
            
        else:
            self.stored_passwords_scroll_area.hide()
            self.stored_password_content_widget.hide()
            
        self.configureStyleSheet()

    def saveColorSelection(self, color_name):
        is_window_pinned = self.pin_window_check_box.isChecked()
        
        if is_window_pinned:
            self.pinWindow(False)

        color_selector = QColorDialog.getColor()

        if color_selector.isValid():
            self.custom_colors[color_name] = color_selector.name()

        if is_window_pinned:
            self.pinWindow()

        self.configureStyleSheet()
    
    def isAddPasswordEnabled(self):
        self.is_add_password_enabled = getBool(self.password_line.text())

        self.setAndColorizeIcon()

    def areLettersOrCasesEnabled(self):
        self.are_letters_enabled = getBool(self.generate_letters_check_box.isChecked() or self.generate_accents_check_box.isChecked())
        self.are_cases_enabled = getBool(self.generate_uppercase_check_box.isChecked() or self.generate_lowercase_check_box.isChecked())

    def areColorsDefault(self, application = True, custom = False):
        for color in [
            '--letter',
            '--background',
            '--disabled'

        ] if application else [
            '--password_background',
            '--password_letter'

        ]:
            if custom:
                if self.custom_colors[color] != self.default_colors[color]:
                    return False

            else:
                if self.colors[color] != self.default_colors[color]:
                    return False
        
        return True

    def checkBoxSynchronization(self, letters = True):
        self.areLettersOrCasesEnabled()

        if letters:
            if not self.are_letters_enabled:
                self.generate_uppercase_check_box.setChecked(False)
                self.generate_lowercase_check_box.setChecked(False)

            if not self.are_cases_enabled and self.are_letters_enabled:
                self.generate_uppercase_check_box.setChecked(True)

        else: 
            if not self.are_cases_enabled:
                self.generate_letters_check_box.setChecked(False)
                self.generate_accents_check_box.setChecked(False)

            if not self.are_letters_enabled and self.are_cases_enabled:
                self.generate_letters_check_box.setChecked(True)     

    def customTextSynchronization(self):
        enable = self.custom_text_plain.toPlainText()

        self.generate_custom_text_check_box.setCursor(Qt.PointingHandCursor if enable else Qt.ArrowCursor)
        self.generate_custom_text_clickable_label.setCursor(Qt.PointingHandCursor if enable else Qt.ArrowCursor)

        self.generate_custom_text_check_box.setEnabled(True if enable else False)
        self.generate_custom_text_clickable_label.setEnabled(True if enable else False)

        if not enable:
            self.generate_custom_text_check_box.setChecked(False)
    
    def changeSVGColor(self, path : str, color : str, widget : QWidget): # You'd laugh at me if you knew how long it took me to get to this function (thank you StackOverflow <3).
        svg = QPixmap(path)

        painter = QPainter(svg)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(svg.rect(), QColor(color if widget.isEnabled() else '--disabled'))
        painter.end()

        return svg

    def setAndColorizeIcon(self):
        are_application_colors_default = self.areColorsDefault()
        are_password_colors_default = self.areColorsDefault(False)
        
        for widget, icon, alternative_icon, color, enabled in [
            (self.pin_window_check_box, 'pin', 'pin-solid', '--letter', True),
            (self.see_password_check_box, 'eye-closed', 'eye-solid', '--disabled' if self.is_edit_mode_enabled else '--letter', not self.is_edit_mode_enabled),
            (self.edit_mode_check_box, 'copy', 'edit-pencil', '--letter', True),
            (self.minimize_window_button, 'minus', None, '--letter', True),
            (self.close_window_button, 'xmark', None, '--letter', True),
            (self.reload_password_button, 'refresh', None, '--background' if self.is_generate_password_enabled else '--disabled', self.is_generate_password_enabled),
            (self.configuration_button, 'settings', None, '--background', True),
            (self.add_password_button, 'plus', None, '--background' if self.is_add_password_enabled else '--disabled', self.is_add_password_enabled),
            (self.application_color_default, 'refresh', None, '--disabled' if are_application_colors_default else '--letter', not are_application_colors_default),
            (self.password_color_default, 'refresh', None, '--disabled' if are_password_colors_default else '--letter', not are_password_colors_default)
        ]: 
            widget : QWidget

            widget.setIcon(
                QIcon(self.changeSVGColor(
                    SVG.format(alternative_icon if widget.isChecked() else icon),
                    self.colors[color], widget)
                )
            )

            widget.setIconSize(QSize(WIDGET_WIDTH * MULTIPLIER, WIDGET_HEIGHT * MULTIPLIER))
            widget.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)

        self.youtube_image_label.setPixmap(QPixmap(self.changeSVGColor(
                SVG.format('youtube'),
                self.colors['--letter'], widget)
            ).scaledToWidth(28 * MULTIPLIER, Qt.SmoothTransformation)
        )

        self.github_image_label.setPixmap(QPixmap(self.changeSVGColor(
                SVG.format('github'),
                self.colors['--letter'], widget)
            ).scaledToWidth(28 * MULTIPLIER, Qt.SmoothTransformation)
        )

        self.application_color_default.setIconSize(QSize(16 * MULTIPLIER, 16 * MULTIPLIER))
        self.password_color_default.setIconSize(QSize(16 * MULTIPLIER, 16 * MULTIPLIER))

    def updateCheckBoxIcon(self, check_box : QCheckBox, checked_icon : str, unchecked_icon : str):
        check_box.setIcon(QIcon(SVG.format(checked_icon if check_box.isChecked() else unchecked_icon)))

    def applyConfiguration(self):
        self.pin_window_check_box.setChecked(self.configuration['pin_window'])
        self.see_password_check_box.setChecked(self.configuration['see_password'])
        self.generate_letters_check_box.setChecked(self.configuration['generate_letters'])
        self.generate_accents_check_box.setChecked(self.configuration['generate_accents'])
        self.generate_uppercase_check_box.setChecked(self.configuration['generate_uppercase'])
        self.generate_lowercase_check_box.setChecked(self.configuration['generate_lowercase'])
        self.generate_numbers_check_box.setChecked(self.configuration['generate_numbers'])
        self.generate_symbols_check_box.setChecked(self.configuration['generate_symbols'])
        self.generate_custom_text_check_box.setChecked(self.configuration['generate_custom_text'])
        
        self.loadWindowPosition()
        self.pinWindow()

    def restoreColorsDictionary(self):
        self.colors = dict(self.default_colors)
        
    def restoreCustomColorsDictionary(self, application = True):
        self.restoreColorsDictionary()

        for color in  [
            '--background',
            '--letter',
            '--disabled'

        ] if application else [
            '--password_background',
            '--password_letter'

        ]:
            self.custom_colors[color] = self.colors[color]
        
        self.configureStyleSheet()

    def configureStyleSheet(self):
        self.restoreColorsDictionary()

        if not self.areColorsDefault(True, True):
            self.colors['--background'] = self.custom_colors['--background']
            self.colors['--letter'] = self.custom_colors['--letter']
            self.colors['--disabled'] = self.custom_colors['--disabled']

        if not self.areColorsDefault(False, True):
            self.colors['--password_background'] = self.custom_colors['--password_background']
            self.colors['--password_letter'] = self.custom_colors['--password_letter']

        self.setAndColorizeIcon()
        self.setStyleSheet(loadModificableFile(FILE, 'main', self.colors))

    def searchStoredPassword(self): # Thank you ChatGPT for so much and sorry for so little
        filter_text = self.search_line.text().lower()

        if not filter_text or filter_text.isspace():
            self.generateStoredPasswordsList()

            return None
        
        filtered_dictionary = {}

        for key, values in self.stored_passwords.items():
            values : dict

            for section, content in values.items():
                content : str

                content = content.lower()
                if section in ["password", "information"] and filter_text in content:
                    filtered_dictionary[key] = values

        filtered_dictionary = self.keysNormalizer(filtered_dictionary)
        self.generateStoredPasswordsList(True, filtered_dictionary)

    def addStoredPasword(self):
        if not self.is_add_password_enabled:
            return None
        
        if self.information_line.hasFocus():
            self.password_line.setFocus()

        self.search_line.clear()

        stored_passwords = dict(self.stored_passwords)
        stored_passwords_length = len(dict(stored_passwords).keys())

        index = stored_passwords_length

        password_to_store = {
            'password': self.password_line.text(),
            'information': self.information_line.text(),
            'background': self.colors['--password_background'],
            'letter': self.colors['--password_letter']
        }
        self.password_line.clear()

        self.stored_passwords[f'{index}'] = password_to_store
        self.createStoredPassword(password_to_store, index)

    def generateStoredPasswordsList(self, search = False, filtered_dictionary = None):
        try:
            self.stored_password_main_content.clear()
            self.stored_password_edit_content.clear()
            self.stored_password_frames.clear()

            for widget in reversed(range(self.stored_passwords_content_layout.count())):
                item = self.stored_passwords_content_layout.itemAt(widget)

                if isinstance(item.widget(), QFrame):
                    item.widget().deleteLater()

        except:
            pass
    
        stored_passwords = filtered_dictionary if search else dict(self.stored_passwords)
        stored_passwords_length = len(stored_passwords.keys())

        for index in range(stored_passwords_length):
            self.createStoredPassword(stored_passwords[f'{index}'], index)

    def changeStoredPasswordsVisibility(self):
        try:
            if self.is_edit_mode_enabled:
                if self.see_password_check_box.isChecked():
                    return None
                
                self.see_password_check_box.setChecked(True)

            show = self.see_password_check_box.isChecked()

            for widget in self.stored_password_main_content + self.stored_password_edit_content:
                widget : QWidget

                if widget.property('password'):
                    widget : QLineEdit

                    if show:
                        widget.setEchoMode(QLineEdit.Normal)

                    else:
                        widget.setEchoMode(QLineEdit.Password)

        except RuntimeError:
            pass

    def changeStoredPasswordsMode(self):
        self.is_edit_mode_enabled = self.edit_mode_check_box.isChecked()
        
        try:
            if self.is_edit_mode_enabled:
                self.were_passwords_hidden = not self.see_password_check_box.isChecked()

                for frame in self.stored_password_frames:
                    frame : QFrame

                    frame.setCursor(Qt.ArrowCursor)

                for line in self.stored_password_main_content:
                    line : QLineEdit

                    line.setDisabled(False)

                for button in self.stored_password_edit_content:
                    button : QPushButton

                    button.show()

            else:
                if self.were_passwords_hidden:
                    self.see_password_check_box.setChecked(False)

                for frame in self.stored_password_frames:
                    frame : QFrame

                    frame.setCursor(Qt.PointingHandCursor)

                for line in self.stored_password_main_content:
                    line : QLineEdit

                    line.setDisabled(True)

                for button in self.stored_password_edit_content:
                    button : QPushButton

                    button.hide()

            self.changeStoredPasswordsVisibility()

        except RuntimeError:
            pass

    def createStoredPassword(self, stored_password, index):
        colors = {
            '--background': stored_password['background'],
            '--letter': stored_password['letter'],
            '--application': self.colors['--background']
        }
        
        stored_password_frame = QFrame()
        stored_password_frame_horizontal_layout = QHBoxLayout(stored_password_frame)
        stored_password_text_vertical_layout = QVBoxLayout()

        stored_password_frame.setProperty('frame', True)
        stored_password_frame.setFixedHeight(32 * MULTIPLIER)
        stored_password_frame_horizontal_layout.setMargin(0)
        stored_password_frame_horizontal_layout.setSpacing(0)
        stored_password_text_vertical_layout.setMargin(0)
        stored_password_text_vertical_layout.setSpacing(0)

        def updateStoredPassword():
            stored_password = {
                'password': stored_password_line.text(),
                'information': stored_information_line.text(),
                'background': colors['--background'],
                'letter': colors['--letter']
            }

            self.stored_passwords[f'{index}'] = stored_password

        def setColors():
            style_sheet = (loadModificableFile(FILE, 'password', colors))

            delete_stored_password_button.setIcon(
                QIcon(changeSVGColor(
                    SVG.format('xmark'),
                    colors['--letter'])
                )
            )

            stored_password_frame.setStyleSheet(style_sheet)

        def changePasswordColor(color_name):
            is_window_pinned = self.pin_window_check_box.isChecked()
            
            if is_window_pinned:
                self.pinWindow(False)

            color_selector = QColorDialog.getColor()

            if color_selector.isValid():
                colors[color_name] = color_selector.name()

            if is_window_pinned:
                self.pinWindow()
            
            setColors()
            updateStoredPassword()

        stored_password_background_color_button = QPushButton()
        stored_password_letter_color_button = QPushButton()
        delete_stored_password_button = QPushButton()

        stored_password_background_color_button.setObjectName('background')
        stored_password_letter_color_button.setObjectName('letter')
        stored_password_background_color_button.setProperty('class', 'full_rounded')
        stored_password_letter_color_button.setProperty('class', 'full_rounded')
        stored_password_background_color_button.setCursor(Qt.PointingHandCursor)
        stored_password_letter_color_button.setCursor(Qt.PointingHandCursor)
        delete_stored_password_button.setCursor(Qt.PointingHandCursor)
        stored_password_background_color_button.setFixedSize(16 * MULTIPLIER, 16 * MULTIPLIER)
        stored_password_letter_color_button.setFixedSize(16 * MULTIPLIER, 16 * MULTIPLIER)
        delete_stored_password_button.setFixedSize(WIDGET_WIDTH * MULTIPLIER, WIDGET_HEIGHT * MULTIPLIER)
        
        stored_password_grid_layout_widget = QWidget()
        stored_password_grid_layout_widget.setFixedSize(32 * MULTIPLIER, 32 * MULTIPLIER)

        stored_password_grid_layout = QGridLayout(stored_password_grid_layout_widget)
        stored_password_grid_layout.setContentsMargins(3 * MULTIPLIER, 3 * MULTIPLIER, 10 * MULTIPLIER, 10 * MULTIPLIER)
        stored_password_grid_layout.setSpacing(0)

        stored_password_grid_layout.addWidget(stored_password_background_color_button, 1, 0)
        stored_password_grid_layout.addWidget(stored_password_letter_color_button, 0, 1)


        def changeSVGColor(path, color):
            svg = QPixmap(path)

            painter = QPainter(svg)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(svg.rect(), QColor(color))
            painter.end()

            return svg

        delete_stored_password_button.setIconSize(QSize(WIDGET_WIDTH * MULTIPLIER, WIDGET_HEIGHT * MULTIPLIER))

        def deleteStoredPassword():
            del self.stored_passwords[f'{index}']

            for widget in main_widgets:
                if widget in self.stored_password_main_content:
                    self.stored_password_main_content.remove(widget)

            for widget in edit_widgets:
                if widget in self.stored_password_edit_content:
                    self.stored_password_edit_content.remove(widget)

            self.stored_password_frames.remove(stored_password_frame)
            self.stored_passwords_content_layout.removeWidget(stored_password_frame)
            stored_password_frame.deleteLater()

        stored_password_background_color_button.mousePressEvent = lambda _: changePasswordColor('--background')
        stored_password_letter_color_button.mousePressEvent = lambda _: changePasswordColor('--letter')
        delete_stored_password_button.mousePressEvent = lambda _: deleteStoredPassword()

        stored_password_line = QLineEdit()
        stored_information_line = QLineEdit()

        stored_password_line.setFixedHeight(18 * MULTIPLIER)
        stored_information_line.setFixedHeight(14 * MULTIPLIER)
        stored_password_line.setFont(self.font_normal)
        stored_information_line.setFont(self.font_small)
        stored_password_line.setText(stored_password['password'])
        stored_information_line.setText(stored_password['information'])

        stored_password_line.textChanged.connect(lambda: updateStoredPassword())
        stored_information_line.textChanged.connect(lambda: updateStoredPassword())
        stored_password_line.returnPressed.connect(lambda: self.edit_mode_check_box.setChecked(False))
        stored_information_line.returnPressed.connect(lambda: self.edit_mode_check_box.setChecked(False))

        stored_password_line.setProperty('password', True)

        def copy_visual_feedback():
            copied_frame = QFrame(stored_password_frame)

            copied_frame.setStyleSheet(loadModificableFile(FILE, 'copy', colors))
            copied_frame.setWindowFlag(Qt.FramelessWindowHint)
            copied_frame.setFixedSize(96 * MULTIPLIER, 20 * MULTIPLIER)

            copied_label = QLabel(copied_frame)

            copied_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            copied_label.setAttribute(Qt.WA_NoSystemBackground)
            copied_label.setText(self.lang['copied_label'])
            copied_label.setFont(self.font_normal)
            copied_label.setFixedSize(96 * MULTIPLIER, 20 * MULTIPLIER)

            horizontal_position = (stored_password_frame.size().width() / 2) - 48 * MULTIPLIER
            vertical_position = (stored_password_frame.size().height() / 2) - 10 * MULTIPLIER

            copied_frame.move(horizontal_position, vertical_position)
            copied_frame.show()

            QTimer.singleShot(750, lambda: copied_frame.deleteLater())

        def copyToClipboard():
            if not self.is_edit_mode_enabled:
                self.clipboard.setText(stored_password_line.text())

                copy_visual_feedback()

        stored_password_frame.mousePressEvent = lambda _: copyToClipboard()

        main_widgets = [
            stored_password_line,
            stored_information_line
        ] 

        edit_widgets = [
            stored_password_grid_layout_widget,
            delete_stored_password_button
        ]

        for widget in main_widgets:
            stored_password_text_vertical_layout.addWidget(widget)
            self.stored_password_main_content.append(widget)

        stored_password_frame_horizontal_layout.addLayout(stored_password_text_vertical_layout)

        for widget in edit_widgets:
            stored_password_frame_horizontal_layout.addWidget(widget)
            self.stored_password_edit_content.append(widget)

        self.stored_password_frames.append(stored_password_frame)
        self.stored_passwords_content_layout.addWidget(stored_password_frame)

        setColors()

        self.changeStoredPasswordsVisibility()
        self.changeStoredPasswordsMode()

    def eventFilter(self, obj, event):
        if (obj == self.password_line or obj == self.information_line) and event.type() == event.KeyPress:
            key = event.key()

            if obj == self.password_line and key == Qt.Key_Down:
                self.information_line.setFocus()

                return True
                
            elif obj == self.information_line and key == Qt.Key_Up:
                self.password_line.setFocus()

                return True
        
        return False

    def grabTolerance(self):
        try:
            if not (self.cursor_horizontal < GRAB_WIDTH * MULTIPLIER and self.cursor_vertical < GRAB_HEIGHT * MULTIPLIER):
                return False
        except:
            return False
        
        return True
            
    def mousePressEvent(self, event): # IT'S ME, MAMA. RECYCLED CODE FROM SCMD Workshop Downloader 2™
        self.is_mouse_pressed = True

        cursor_position = QCursor.pos()
        window_position = self.pos()

        self.cursor_horizontal = cursor_position.x() - window_position.x()
        self.cursor_vertical = cursor_position.y() - window_position.y()

        if self.grabTolerance():
            self.old_position = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.is_mouse_pressed = False

    def mouseMoveEvent(self, event):
        try:
            if self.is_mouse_pressed and self.grabTolerance():
                new_position = QPoint(event.globalPos() - self.old_position)

                self.move(self.x() + new_position.x(), self.y() + new_position.y())
                self.old_position = event.globalPos()

        except AttributeError:
            pass

    def closeEvent(self, event):
        if not self.stored_passwords:
            self.stored_passwords = {}

        if not self.configuration['use_key']:
            self.stored_passwords = json.dumps(self.stored_passwords)

            self.saveStoredPasswords()
            
        self.saveConfiguration()

if __name__ == '__main__':
    application = QApplication(sys.argv)

    window = Patrick()

    application.exec_()

# ~ With love, Berdy Alexei.