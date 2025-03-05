import sys
import os
import json
import shutil
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QListWidget, QTabWidget, QLineEdit, QMessageBox, QListWidgetItem,
                            QDialog, QFormLayout, QTextEdit, QToolBar, QToolButton, QComboBox, 
                            QDialogButtonBox, QMenu, QShortcut, QDockWidget, QGraphicsOpacityEffect, 
                            QSizePolicy, QSpacerItem, QGroupBox, QRadioButton, QSlider, QCheckBox,
                            QProgressDialog, QGridLayout, QDateTimeEdit, QSpinBox)
from PyQt5.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QDateTime)
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request  # Request sınıfını ekledik
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from database import Database
from datetime import datetime, timedelta
from youtube_categories import YOUTUBE_CATEGORIES

# Transkript API entegrasyonu için gerekli importlar
import requests
from pathlib import Path
import tempfile
import moviepy.editor as mp
from openai import OpenAI

# Stil tanımlamaları
STYLE_SHEET = """
/* Ana tema */
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
    font-size: 16px;  /* Font boyutunu artırdık */
}

QMainWindow {
    background-color: #f5f5f7;
}

/* Form elemanları */
QLineEdit, QTextEdit, QComboBox {
    padding: 12px 15px;  /* Padding artırıldı */
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    background: white;
    min-height: 25px;
    font-size: 16px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #007AFF;
    background: #f8f8ff;
}

/* Butonlar */
QPushButton {
    padding: 12px 25px;  /* Buton boyutu artırıldı */
    font-size: 16px;
    min-height: 45px;
    background: #007AFF;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
}

QPushButton:hover {
    background: #0056b3;
}

/* Liste widget */
QListWidget {
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 10px;
    font-size: 16px;
    min-height: 400px;  /* Minimum yükseklik eklendi */
}

QListWidget::item {
    padding: 15px;
    margin: 5px 0;
    border-radius: 8px;
}

/* Tab widget */
QTabWidget::pane {
    border: none;
    background: white;
    border-radius: 15px;
}

QTabBar::tab {
    padding: 15px 30px;
    font-size: 16px;
    margin-right: 5px;
}

/* Toolbar */
QToolBar {
    padding: 10px;
    spacing: 15px;
}

QToolButton {
    min-width: 120px;
    min-height: 40px;
    padding: 10px 20px;
    font-size: 15px;
}

/* Labels */
QLabel {
    font-size: 16px;
}

QLabel#titleLabel {
    font-size: 48px;
    font-weight: bold;
    color: #007AFF;
    margin: 20px;
}

QLabel#subtitleLabel {
    font-size: 24px;
    color: #666;
    margin-bottom: 30px;
}

/* Form container */
QWidget#formContainer {
    background: rgba(255, 255, 255, 0.95);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 30px;
    min-width: 500px;
}

/* Özel input stilleri */
.login-input {
    padding-left: 45px;  /* İkon için padding */
    background-repeat: no-repeat;
    background-position: 15px center;
    min-height: 45px;
    font-size: 16px;
}

/* Dock widget */
QDockWidget {
    border: none;
    min-width: 250px;
}

QDockWidget::title {
    padding: 10px;
    background: #f5f5f7;
    font-size: 18px;
}
"""

class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = Database()
        self.check_icons()  # İkon kontrolü
        self.setup_ui()
        self.setStyleSheet(STYLE_SHEET)
        self.load_remembered_user()  # Kayıtlı kullanıcıyı yükle
        
    def setup_ui(self):
        self.setWindowTitle("YouTube Otomasyon - Giriş")
        self.setWindowIcon(QIcon('youtube_icon.png'))
        
        # Tam ekran
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        
        # Ana layout (yatay)
        main_layout = QHBoxLayout()
        
        # Sol taraf (Logo ve başlık)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setAlignment(Qt.AlignCenter)
        left_layout.setSpacing(20)
        
        # Logo
        self.logo_label = QLabel()
        logo_pixmap = QPixmap('youtube_icon.png')
        self.logo_label.setPixmap(logo_pixmap.scaled(250, 250, Qt.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignCenter)
        
        # Başlıklar
        title_label = QLabel("YouTube Otomasyon")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        
        subtitle_label = QLabel("Video Yükleme ve Kanal Yönetim Sistemi")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        left_layout.addWidget(self.logo_label)
        left_layout.addWidget(title_label)
        left_layout.addWidget(subtitle_label)
        
        # Sağ taraf (Giriş formu)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setAlignment(Qt.AlignCenter)
        
        # Form container
        form_container = QWidget()
        form_container.setObjectName("formContainer")
        form_container.setMinimumWidth(400)
        form_container.setMaximumWidth(500)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        
        # Giriş başlığı
        login_title = QLabel("Giriş Yap")
        login_title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
            }
        """)
        login_title.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(login_title)
        
        # Input alanları
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        
        # İkon kontrolü ile stil uygula
        user_icon_path = "icons/user.png"
        if os.path.exists(user_icon_path):
            self.username_input.setStyleSheet(f"""
                QLineEdit {{
                    padding: 15px 45px;
                    font-size: 16px;
                    min-height: 45px;
                    background-image: url({user_icon_path});
                    background-repeat: no-repeat;
                    background-position: 15px center;
                    border-radius: 10px;
                    border: 2px solid #ddd;
                }}
                QLineEdit:focus {{
                    border-color: #007AFF;
                }}
            """)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        # İkon kontrolü ile stil uygula
        lock_icon_path = "icons/lock.png"
        if os.path.exists(lock_icon_path):
            self.password_input.setStyleSheet(f"""
                QLineEdit {{
                    padding: 15px 45px;
                    font-size: 16px;
                    min-height: 45px;
                    background-image: url({lock_icon_path});
                    background-repeat: no-repeat;
                    background-position: 15px center;
                    border-radius: 10px;
                    border: 2px solid #ddd;
                }}
                QLineEdit:focus {{
                    border-color: #007AFF;
                }}
            """)
        
        # Beni Hatırla checkbox'ı
        self.remember_me = QCheckBox("Beni Hatırla")
        self.remember_me.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 14px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ddd;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.1);
            }
            QCheckBox::indicator:checked {
                background: #007AFF;
                border-color: #007AFF;
                image: url(icons/check.png);
            }
        """)
        form_layout.addWidget(self.remember_me)
        
        # Butonlar
        self.login_btn = QPushButton("Giriş Yap")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setStyleSheet("""
            QPushButton#loginButton {
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                background: #007AFF;
                color: white;
                min-height: 45px;
            }
            QPushButton#loginButton:hover {
                background: #0056b3;
            }
        """)
        self.login_btn.clicked.connect(self.login)
        
        self.register_btn = QPushButton("Hesabınız yok mu? Kayıt Olun")
        self.register_btn.setObjectName("registerButton")
        self.register_btn.setStyleSheet("""
            QPushButton#registerButton {
                padding: 15px;
                font-size: 14px;
                border: none;
                background: transparent;
                color: #007AFF;
            }
            QPushButton#registerButton:hover {
                color: #0056b3;
                text-decoration: underline;
            }
        """)
        self.register_btn.clicked.connect(self.show_register)
        
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.login_btn)
        form_layout.addWidget(self.register_btn)
        
        right_layout.addWidget(form_container)
        
        # Ana layout'a widget'ları ekle
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
        # Arkaplan efekti
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50,
                    stop:0.5 #3498db,
                    stop:1 #2980b9
                );
            }
            QWidget#formContainer {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
            }
        """)
        
        self.setLayout(main_layout)
        
        # Logo animasyonu başlat
        QTimer.singleShot(500, self.start_logo_animation)
        
    def start_logo_animation(self):
        self.logo_anim = QPropertyAnimation(self.logo_label, b"pos")
        self.logo_anim.setDuration(1000)
        self.logo_anim.setEasingCurve(QEasingCurve.OutBounce)
        
        start_pos = self.logo_label.pos()
        self.logo_anim.setStartValue(QPoint(start_pos.x(), start_pos.y() - 100))
        self.logo_anim.setEndValue(start_pos)
        
        QTimer.singleShot(500, self.logo_anim.start)
    
    def load_remembered_user(self):
        """Kayıtlı kullanıcı bilgilerini yükle"""
        try:
            if os.path.exists('remembered_user.json'):
                with open('remembered_user.json', 'r') as f:
                    data = json.load(f)
                    self.username_input.setText(data.get('username', ''))
                    self.password_input.setText(data.get('password', ''))
                    self.remember_me.setChecked(True)
        except Exception as e:
            print(f"Kullanıcı bilgileri yüklenemedi: {str(e)}")
    
    def save_remembered_user(self):
        """Kullanıcı bilgilerini kaydet"""
        if self.remember_me.isChecked():
            data = {
                'username': self.username_input.text(),
                'password': self.password_input.text()
            }
            try:
                with open('remembered_user.json', 'w') as f:
                    json.dump(data, f)
            except Exception as e:
                print(f"Kullanıcı bilgileri kaydedilemedi: {str(e)}")
        else:
            # Beni hatırla seçili değilse kayıtlı bilgileri sil
            if os.path.exists('remembered_user.json'):
                try:
                    os.remove('remembered_user.json')
                except:
                    pass
    
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if self.db.check_login(username, password):
            # Beni hatırla seçeneğini kontrol et
            self.save_remembered_user()
            
            # Başarılı giriş animasyonu
            self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_out_animation.setDuration(500)
            self.fade_out_animation.setStartValue(1.0)
            self.fade_out_animation.setEndValue(0.0)
            self.fade_out_animation.finished.connect(lambda: self.complete_login())
            self.fade_out_animation.start()
        else:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı veya şifre hatalı!")
    
    def complete_login(self):
        self.main_window = YouTubeManager()
        self.main_window.set_username(self.username_input.text())  # Kullanıcı adını ayarla
        self.main_window.show()
        self.close()
    
    def show_register(self):
        self.register_window = RegisterWindow()
        self.register_window.show()

    def check_icons(self):
        """Eksik ikonları kontrol et ve indir"""
        required_icons = [
            'upload', 'video', 'user', 'settings', 
            'menu', 'lock', 'check', 'search', 'youtube'
        ]
        
        missing_icons = []
        for icon in required_icons:
            if not os.path.exists(f'icons/{icon}.png'):
                missing_icons.append(icon)
        
        if missing_icons:
            reply = QMessageBox.question(
                self,
                "Eksik İkonlar",
                f"Bazı ikonlar eksik. İndirmek ister misiniz?\nEksik ikonlar: {', '.join(missing_icons)}",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    import download_icons
                    download_icons.main()
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Hata",
                        f"İkonlar indirilemedi: {str(e)}\nUygulama ikonsuz devam edecek."
                    )

class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setup_ui()
        self.setStyleSheet(STYLE_SHEET)
        
    def setup_ui(self):
        self.setWindowTitle("Kayıt Ol")
        self.setWindowIcon(QIcon('youtube_icon.png'))
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Form container
        form_container = QWidget()
        form_container.setObjectName("formContainer")
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)
        
        # Başlık
        title_label = QLabel("Yeni Hesap Oluştur")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(title_label)
        
        # Giriş alanları
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Kullanıcı Adı")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-posta")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Şifre")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.password_confirm = QLineEdit()
        self.password_confirm.setPlaceholderText("Şifre Tekrar")
        self.password_confirm.setEchoMode(QLineEdit.Password)
        
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.password_confirm)
        
        # Kayıt butonu
        self.register_btn = QPushButton("Kayıt Ol")
        self.register_btn.setObjectName("loginButton")
        self.register_btn.clicked.connect(self.register)
        form_layout.addWidget(self.register_btn)
        
        layout.addWidget(form_container)
        self.setLayout(layout)
        
        # Pencere animasyonu
        self.setWindowOpacity(0.0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(500)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.start()
    
    def register(self):
        username = self.username_input.text()
        email = self.email_input.text()
        password = self.password_input.text()
        password_confirm = self.password_confirm.text()
        
        if not all([username, email, password, password_confirm]):
            QMessageBox.warning(self, "Hata", "Tüm alanları doldurun!")
            return
        
        if password != password_confirm:
            QMessageBox.warning(self, "Hata", "Şifreler eşleşmiyor!")
            return
        
        if self.db.register_user(username, password, email):
            QMessageBox.information(self, "Başarılı", "Kayıt başarıyla tamamlandı!")
            self.close()
        else:
            QMessageBox.warning(self, "Hata", "Bu kullanıcı adı veya e-posta zaten kullanımda!")

class VideoDetailDialog(QDialog):
    def __init__(self, video_info, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Video Detayları")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        
        # Form layout
        form = QFormLayout()
        
        # Başlık
        self.title_input = QLineEdit(self.video_info['title'])
        form.addRow("Başlık:", self.title_input)
        
        # Açıklama
        self.description_input = QTextEdit()
        self.description_input.setText(self.video_info.get('description', ''))
        self.description_input.setMinimumHeight(100)
        form.addRow("Açıklama:", self.description_input)
        
        # Etiketler
        self.tags_input = QLineEdit(', '.join(self.video_info.get('tags', [])))
        form.addRow("Etiketler:", self.tags_input)
        
        # Gizlilik ayarı
        self.privacy_combo = QComboBox()
        self.privacy_combo.addItems(['private', 'unlisted', 'public'])
        self.privacy_combo.setCurrentText(self.video_info.get('privacy_status', 'private'))
        form.addRow("Gizlilik:", self.privacy_combo)
        
        # Çocuk içeriği seçimi
        self.kids_group = QGroupBox("Çocuk İçeriği")
        kids_layout = QVBoxLayout()
        
        self.kids_yes = QRadioButton("Evet, çocuklara özel")
        self.kids_no = QRadioButton("Hayır, çocuklara özel değil")
        
        # Varsayılan değeri ayarla
        if self.video_info.get('made_for_kids', False):
            self.kids_yes.setChecked(True)
        else:
            self.kids_no.setChecked(True)
        
        kids_layout.addWidget(self.kids_yes)
        kids_layout.addWidget(self.kids_no)
        self.kids_group.setLayout(kids_layout)
        form.addRow(self.kids_group)
        
        # Kategori seçimi
        self.category_combo = QComboBox()
        for id, name in YOUTUBE_CATEGORIES.items():
            self.category_combo.addItem(name, id)
        
        # Mevcut kategoriyi seç
        current_category = self.video_info.get('category_id', '22')
        index = self.category_combo.findData(current_category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        
        form.addRow("Kategori:", self.category_combo)
        layout.addLayout(form)
        
        # Durum bilgisi
        status_label = QLabel(f"Durum: {self.video_info['status']}")
        layout.addWidget(status_label)
        
        # Butonlar
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def get_updated_info(self):
        self.video_info.update({
            'title': self.title_input.text(),
            'description': self.description_input.toPlainText(),
            'tags': [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()],
            'privacy_status': self.privacy_combo.currentText(),
            'category_id': self.category_combo.currentData(),
            'made_for_kids': self.kids_yes.isChecked()  # Çocuk içeriği durumunu ekle
        })
        return self.video_info

class VideoListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = parent  # YouTubeManager referansını sakla
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def keyPressEvent(self, event):
        # Klavye kısayolları
        if event.key() == Qt.Key_Delete:
            if hasattr(self.manager, 'delete_selected_videos'):
                self.manager.delete_selected_videos()
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_A:  # Ctrl+A: Tümünü seç
                self.selectAll()
            elif event.key() == Qt.Key_E:  # Ctrl+E: Düzenle
                if hasattr(self.manager, 'edit_selected_videos'):
                    self.manager.edit_selected_videos()
            elif event.key() == Qt.Key_U:  # Ctrl+U: YouTube'a yükle
                if hasattr(self.manager, 'upload_selected_videos'):
                    self.manager.upload_selected_videos()
        super().keyPressEvent(event)
    
    def show_context_menu(self, pos):
        if not hasattr(self.manager, 'edit_selected_videos'):
            return
            
        menu = QMenu(self)
        
        edit_action = menu.addAction("Düzenle")
        edit_action.triggered.connect(self.manager.edit_selected_videos)
        
        delete_action = menu.addAction("Sil")
        delete_action.triggered.connect(self.manager.delete_selected_videos)
        
        upload_action = menu.addAction("YouTube'a Yükle")
        upload_action.triggered.connect(self.manager.upload_selected_videos)
        
        menu.exec_(self.mapToGlobal(pos))

class FilterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        
        # Arama kutusu
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Video ara...")
        self.search_box.setProperty("class", "search-box")
        self.search_box.textChanged.connect(self.filter_changed)
        
        # Durum filtresi
        self.status_combo = QComboBox()
        self.status_combo.addItems(['Tümü', 'Beklemede', 'Yüklendi', 'Hata'])
        self.status_combo.currentTextChanged.connect(self.filter_changed)
        
        # Tarih filtresi
        self.date_combo = QComboBox()
        self.date_combo.addItems(['Tümü', 'Bugün', 'Bu Hafta', 'Bu Ay'])
        self.date_combo.currentTextChanged.connect(self.filter_changed)
        
        layout.addWidget(self.search_box)
        layout.addWidget(self.status_combo)
        layout.addWidget(self.date_combo)

    def filter_changed(self):
        self.parent().apply_filters()

class YouTubeManager(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Temel değişkenleri başlangıçta tanımla
        self.current_username = None
        self.db = Database()
        
        # Client secrets'ı yükle
        try:
            with open('client_secrets.json', 'r') as f:
                self.client_secrets = json.load(f)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Hata",
                f"client_secrets.json dosyası okunamadı: {str(e)}"
            )
            sys.exit(1)
        
        # Upload dizinini oluştur
        self.base_upload_dir = "uploads/media"
        os.makedirs(self.base_upload_dir, exist_ok=True)
        
        # YouTube API değişkenleri
        self.youtube = None
        self.credentials = None
        
        # Pencere ayarları
        self.setWindowTitle("YouTube Otomasyon")
        self.setWindowIcon(QIcon('youtube_icon.png'))
        self.setStyleSheet(STYLE_SHEET)
        
        # Tam ekran
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        
        # Ana widget ve layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Tab widget oluşturma
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Sekmeleri oluştur (Video Yükleme sekmesi kaldırıldı)
        self.setup_uploaded_tab()  # Medya Havuzu
        self.setup_channel_tab()   # Kanal Yönetimi
        
        # YouTube Videolar sekmesi kaldırıldı
        
        # Sağ menü
        self.setup_right_menu()
        
        # Klavye kısayolları
        self.setup_shortcuts()
        
        # Responsive layout
        self.central_widget.setSizePolicy(
            QSizePolicy.Expanding, 
            QSizePolicy.Expanding
        )

    def setup_uploaded_tab(self):
        """Medya havuzu sekmesi"""
        self.uploaded_tab = QWidget()
        self.uploaded_layout = QVBoxLayout(self.uploaded_tab)
        self.uploaded_layout.setContentsMargins(20, 20, 20, 20)
        self.uploaded_layout.setSpacing(15)
        
        # Üst toolbar
        toolbar = QHBoxLayout()
        
        # Video yükleme butonu
        upload_btn = QPushButton("Video Yükle")
        upload_btn.setIcon(QIcon('icons/upload.png'))
        upload_btn.clicked.connect(self.show_upload_dialog)
        toolbar.addWidget(upload_btn)
        
        # Filtre widget'ı
        self.filter_widget = FilterWidget(self)
        toolbar.addWidget(self.filter_widget)
        
        # Toplu işlem butonları
        bulk_btn_layout = QHBoxLayout()
        
        transcript_btn = QPushButton("Transkript Oluştur")
        transcript_btn.clicked.connect(self.create_bulk_transcripts)
        bulk_btn_layout.addWidget(transcript_btn)
        
        auto_title_btn = QPushButton("Otomatik Başlık")
        auto_title_btn.clicked.connect(self.create_bulk_auto_titles)
        bulk_btn_layout.addWidget(auto_title_btn)
        
        category_btn = QPushButton("Kategori Değiştir")
        category_btn.clicked.connect(self.change_bulk_category)
        bulk_btn_layout.addWidget(category_btn)
        
        schedule_btn = QPushButton("Zamanlama")
        schedule_btn.clicked.connect(self.set_bulk_schedule)
        bulk_btn_layout.addWidget(schedule_btn)
        
        toolbar.addLayout(bulk_btn_layout)
        
        self.uploaded_layout.addLayout(toolbar)
        
        # Medya havuzu alanı
        media_group = QGroupBox("Medya Havuzu")
        media_layout = QVBoxLayout()
        
        # Video listesi
        self.uploaded_list = VideoListWidget(self)
        self.uploaded_list.itemDoubleClicked.connect(self.show_video_details)
        media_layout.addWidget(self.uploaded_list)
        
        # İşlem butonları
        action_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Düzenle")
        self.delete_btn = QPushButton("Sil")
        self.youtube_upload_btn = QPushButton("YouTube'a Yükle")
        
        for btn in [self.edit_btn, self.delete_btn, self.youtube_upload_btn]:
            btn.setMinimumWidth(150)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 15px 30px;
                    font-size: 16px;
                    background: #FF0000;
                    color: white;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: #CC0000;
                }
            """)
        
        self.edit_btn.clicked.connect(self.edit_selected_videos)
        self.delete_btn.clicked.connect(self.delete_selected_videos)
        self.youtube_upload_btn.clicked.connect(self.upload_selected_videos)
        
        action_layout.addWidget(self.edit_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.youtube_upload_btn)
        media_layout.addLayout(action_layout)
        
        media_group.setLayout(media_layout)
        self.uploaded_layout.addWidget(media_group)
        
        self.tabs.addTab(self.uploaded_tab, "Medya Havuzu")

    def show_upload_dialog(self):
        """Video yükleme dialogunu göster"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Video(lar) Seç",
            "",
            "Video Dosyaları (*.mp4 *.avi *.mkv *.mov);;Tüm Dosyalar (*.*)"
        )
        
        if files:
            # İlerleme dialogu
            progress = QProgressDialog(
                "Videolar yükleniyor...", 
                "İptal",
                0,
                len(files),
                self
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.setAutoClose(True)  # İşlem bitince otomatik kapansın
            
            success_count = 0
            for i, file_path in enumerate(files):
                if progress.wasCanceled():
                    break
                    
                progress.setValue(i)
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                
                if self.upload_video(file_path, file_name):
                    success_count += 1
            
            progress.setValue(len(files))
            
            if success_count > 0:
                self.refresh_uploaded_videos()
                QMessageBox.information(
                    self,
                    "Tamamlandı",
                    f"{success_count} video başarıyla yüklendi!"
                )

    def upload_video(self, file_path, title):
        """Video dosyasını medya havuzuna yükle"""
        try:
            # Hedef dizini oluştur
            target_dir = self.user_upload_dir
            os.makedirs(target_dir, exist_ok=True)
            
            # Dosya adını oluştur
            file_name = os.path.basename(file_path)
            base_name, ext = os.path.splitext(file_name)
            
            # Eğer aynı isimde dosya varsa, ismi değiştir
            if os.path.exists(os.path.join(target_dir, file_name)):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{base_name}_{timestamp}{ext}"
            
            target_path = os.path.join(target_dir, file_name)
            
            # Dosyayı kopyala
            shutil.copy2(file_path, target_path)
            
            # Video bilgilerini JSON olarak kaydet
            video_info = {
                'title': title or base_name,
                'description': '',
                'tags': [],
                'category_id': '22',  # Varsayılan: People & Blogs
                'privacy_status': 'private',
                'made_for_kids': False,
                'upload_path': target_path,
                'upload_date': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'status': 'pending'
            }
            
            json_path = os.path.splitext(target_path)[0] + '.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(video_info, f, ensure_ascii=False, indent=4)
            
            return True
            
        except Exception as e:
            print(f"Video yükleme hatası: {str(e)}")
            return False

    def setup_channel_tab(self):
        """Kanal yönetimi sekmesi"""
        self.channel_tab = QWidget()
        layout = QVBoxLayout(self.channel_tab)
        
        # Kanal yönetimi grubu
        channel_group = QGroupBox("Kanal Yönetimi")
        channel_layout = QVBoxLayout()
        
        # Kanal ekleme butonu
        self.auth_btn = QPushButton("YouTube Kanalı Ekle")
        self.auth_btn.clicked.connect(self.authenticate)
        self.auth_btn.setStyleSheet("""
            QPushButton {
                padding: 20px 40px;
                font-size: 18px;
                background: #FF0000;
                color: white;
                border-radius: 8px;
                min-width: 300px;
            }
            QPushButton:hover {
                background: #CC0000;
            }
        """)
        channel_layout.addWidget(self.auth_btn)
        
        # Kanal listesi
        self.channel_list = QListWidget()
        self.channel_list.itemClicked.connect(self.on_channel_selected)
        channel_layout.addWidget(self.channel_list)
        
        # Kanal bilgileri
        self.channel_info = QLabel("Kanal bilgileri burada görünecek")
        self.channel_info.setStyleSheet("""
            QLabel {
                font-size: 18px;
                padding: 20px;
                background: #f8f8f8;
                border-radius: 8px;
            }
        """)
        channel_layout.addWidget(self.channel_info)
        
        channel_group.setLayout(channel_layout)
        layout.addWidget(channel_group)
        
        # YouTube videolar grubu
        youtube_group = QGroupBox("YouTube Videolar")
        youtube_layout = QVBoxLayout()
        
        # Üst bilgi alanı
        info_layout = QHBoxLayout()
        self.youtube_channel_combo = QComboBox()
        self.youtube_channel_combo.currentIndexChanged.connect(self.refresh_youtube_videos)
        info_layout.addWidget(QLabel("Kanal:"))
        info_layout.addWidget(self.youtube_channel_combo)
        
        self.auto_refresh_check = QCheckBox("Otomatik Yenile")
        self.auto_refresh_check.setChecked(True)
        info_layout.addWidget(self.auto_refresh_check)
        
        youtube_layout.addLayout(info_layout)
        
        # Video listesi
        self.youtube_list = QListWidget()
        self.youtube_list.itemDoubleClicked.connect(self.edit_youtube_video)
        youtube_layout.addWidget(self.youtube_list)
        
        # Butonlar
        button_layout = QHBoxLayout()
        self.refresh_youtube_btn = QPushButton("Yenile")
        self.edit_youtube_btn = QPushButton("Düzenle")
        self.delete_youtube_btn = QPushButton("YouTube'dan Sil")
        
        for btn in [self.refresh_youtube_btn, self.edit_youtube_btn, self.delete_youtube_btn]:
            btn.setMinimumWidth(150)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 15px 30px;
                    font-size: 16px;
                    background: #FF0000;
                    color: white;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: #CC0000;
                }
            """)
        
        self.refresh_youtube_btn.clicked.connect(self.refresh_youtube_videos)
        self.edit_youtube_btn.clicked.connect(lambda: self.edit_youtube_video(self.youtube_list.currentItem()))
        self.delete_youtube_btn.clicked.connect(self.delete_from_youtube)
        
        button_layout.addWidget(self.refresh_youtube_btn)
        button_layout.addWidget(self.edit_youtube_btn)
        button_layout.addWidget(self.delete_youtube_btn)
        youtube_layout.addLayout(button_layout)
        
        youtube_group.setLayout(youtube_layout)
        layout.addWidget(youtube_group)
        
        self.channel_tab.setLayout(layout)
        self.tabs.addTab(self.channel_tab, "Kanal Yönetimi")
        
        # Mevcut kanalları yükle
        if self.current_username:
            self.refresh_channel_list()

    def setup_right_menu(self):
        """Sağ menü oluştur"""
        self.right_dock = QDockWidget("İşlemler", self)
        self.right_dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.right_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)
        
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        
        menu_buttons = [
            ("Video Yükle", "icons/upload.png", lambda: self.tabs.setCurrentIndex(0)),
            ("Videolarım", "icons/video.png", lambda: self.tabs.setCurrentIndex(1)),
            ("Kanal", "icons/user.png", lambda: self.tabs.setCurrentIndex(2)),
            ("Ayarlar", "icons/settings.png", self.show_settings)
        ]
        
        for text, icon_path, slot in menu_buttons:
            btn = QPushButton(text)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
            btn.setFixedHeight(50)
            btn.clicked.connect(slot)
            menu_layout.addWidget(btn)
        
        menu_layout.addStretch()
        self.right_dock.setWidget(menu_widget)

    def set_username(self, username):
        """Kullanıcı adını ayarla ve gerekli işlemleri yap"""
        self.current_username = username
        self.user_upload_dir = os.path.join(self.base_upload_dir, username)
        os.makedirs(self.user_upload_dir, exist_ok=True)
        
        # Kanal listesini güncelle
        self.refresh_channel_list()
        
        # Önceden yüklenmiş videoları göster
        QTimer.singleShot(500, self.refresh_uploaded_videos)

    def authenticate(self):
        try:
            SCOPES = [
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/youtube',
                'https://www.googleapis.com/auth/youtube.force-ssl'
            ]
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json',
                scopes=SCOPES
            )
            
            credentials = flow.run_local_server(
                port=0,
                access_type='offline',
                prompt='consent'
            )
            
            # Token bilgilerini kaydet
            token_data = {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'expiry': credentials.expiry.isoformat()
            }
            
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Kanal bilgilerini al
            channel_response = youtube.channels().list(
                part='snippet,statistics',
                mine=True
            ).execute()
            
            if channel_response['items']:
                channel = channel_response['items'][0]
                channel_data = {
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet'].get('description', ''),
                    'statistics': channel['statistics']
                }
                
                # Kanal bilgilerini veritabanına kaydet
                if self.db.save_channel(self.current_username, channel_data, token_data):
                    self.refresh_channel_list()
                    QMessageBox.information(
                        self,
                        "Başarılı",
                        f"YouTube kanalı başarıyla eklendi: {channel_data['title']}"
                    )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Hata",
                f"YouTube bağlantısı başarısız: {str(e)}"
            )

    def refresh_channel_list(self):
        channels = self.db.get_user_channels(self.current_username)
        
        # Kanal listelerini temizle
        self.channel_list.clear()
        self.youtube_channel_combo.clear()
        
        for channel in channels:
            # Kanal listesi için
            item = QListWidgetItem(f"{channel[3]} ({channel[2]})")
            channel_data = {
                'channel_id': channel[2],
                'access_token': channel[4],
                'refresh_token': channel[5]
            }
            item.setData(Qt.UserRole, channel_data)
            self.channel_list.addItem(item)
            
            # Combo box için
            self.youtube_channel_combo.addItem(f"{channel[3]}", channel_data)
        
        # İlk kanalı seç ve videoları yükle
        if self.youtube_channel_combo.count() > 0:
            self.youtube_channel_combo.setCurrentIndex(0)
            self.refresh_youtube_videos()

    def upload_to_youtube(self, video_info_path):
        """YouTube'a video yükleme işlemi"""
        try:
            # Kanal kontrolü
            if not hasattr(self, 'channel_list') or self.channel_list.count() == 0:
                raise Exception("Henüz bir YouTube kanalı eklenmemiş! Önce bir kanal ekleyin.")
            
            # Seçili kanalı kontrol et
            current_channel = self.channel_list.currentItem()
            if not current_channel:
                # Otomatik olarak ilk kanalı seç
                self.channel_list.setCurrentRow(0)
                current_channel = self.channel_list.currentItem()
                QMessageBox.information(
                    self,
                    "Bilgi",
                    f"Otomatik olarak '{current_channel.text()}' kanalı seçildi."
                )
            
            channel_data = current_channel.data(Qt.UserRole)
            
            # Token'ı yenile
            try:
                credentials = Credentials(
                    token=channel_data['access_token'],
                    refresh_token=channel_data['refresh_token'],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_secrets['installed']['client_id'],
                    client_secret=self.client_secrets['installed']['client_secret']
                )
                
                if credentials.expired:
                    credentials.refresh(Request())
                
                youtube = build('youtube', 'v3', credentials=credentials)
                
                # Token'ı veritabanında güncelle
                channel_data['access_token'] = credentials.token
                self.db.update_channel_token(
                    self.current_username,
                    channel_data['channel_id'],
                    credentials.token
                )
                
            except Exception as e:
                # Token yenileme başarısız olursa kanalı yeniden yetkilendir
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Kanal yetkilendirmesi süresi dolmuş. Yeniden yetkilendirme gerekiyor."
                )
                self.authenticate()
                return False, "Lütfen kanalı yeniden yetkilendirdikten sonra tekrar deneyin."
            
            # Video bilgilerini oku ve yükle
            with open(video_info_path, 'r', encoding='utf-8') as f:
                video_info = json.load(f)
            
            # Video dosyasının varlığını kontrol et
            if not os.path.exists(video_info['upload_path']):
                raise Exception("Video dosyası bulunamadı!")
            
            body = {
                'snippet': {
                    'title': video_info['title'],
                    'description': video_info['description'],
                    'tags': video_info['tags'],
                    'categoryId': video_info['category_id']
                },
                'status': {
                    'privacyStatus': video_info['privacy_status'],
                    'selfDeclaredMadeForKids': video_info.get('made_for_kids', False)  # Çocuk içeriği durumunu ekle
                }
            }
            
            media = MediaFileUpload(
                video_info['upload_path'],
                chunksize=1024*1024,
                resumable=True
            )
            
            # Yükleme işlemi
            try:
                request = youtube.videos().insert(
                    part=','.join(body.keys()),
                    body=body,
                    media_body=media
                )
                
                response = request.execute()
                
                # Video bilgilerini güncelle
                video_info['status'] = 'uploaded'
                video_info['youtube_id'] = response['id']
                video_info['upload_channel'] = channel_data['channel_id']
                video_info['upload_date_youtube'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with open(video_info_path, 'w', encoding='utf-8') as f:
                    json.dump(video_info, f, ensure_ascii=False, indent=4)
                
                return True, "Video başarıyla YouTube'a yüklendi"
                
            except Exception as e:
                error_msg = str(e)
                if "quotaExceeded" in error_msg:
                    return False, "YouTube API kotası aşıldı. Lütfen yarın tekrar deneyin."
                elif "invalidCredentials" in error_msg:
                    return False, "Kanal yetkilendirmesi geçersiz. Lütfen kanalı yeniden ekleyin."
                else:
                    return False, f"YouTube'a yükleme hatası: {error_msg}"
                
        except Exception as e:
            return False, f"İşlem hatası: {str(e)}"

    def load_saved_channel_info(self):
        """Kayıtlı kanal bilgilerini yükle"""
        try:
            channel_path = os.path.join(self.user_upload_dir, 'channel_info.json')
            if os.path.exists(channel_path):
                with open(channel_path, 'r', encoding='utf-8') as f:
                    channel_data = json.load(f)
                self.update_channel_info_display(channel_data)
                return True
            return False
        except:
            return False

    def update_channel_info_display(self, channel_data):
        """Kanal bilgilerini göster"""
        info_text = f"""
        Bağlı Kanal: {channel_data['title']}
        Abone Sayısı: {channel_data['statistics'].get('subscriberCount', '0')}
        Video Sayısı: {channel_data['statistics'].get('videoCount', '0')}
        Toplam İzlenme: {channel_data['statistics'].get('viewCount', '0')}
        """
        
        self.channel_info.setText(info_text)
        self.channel_info.setStyleSheet("""
            QLabel {
                font-size: 18px;
                padding: 20px;
                background: #f8f8f8;
                border-radius: 8px;
                line-height: 1.6;
            }
        """)
        
        # Bağlantı başarılı olduğunda butonun rengini ve metnini değiştir
        self.auth_btn.setText("Kanal Bağlantısı Aktif ✓")
        self.auth_btn.setStyleSheet("""
            QPushButton {
                padding: 20px 40px;
                font-size: 18px;
                background: #28a745;
                color: white;
                border-radius: 8px;
                min-width: 300px;
            }
            QPushButton:hover {
                background: #218838;
            }
        """)

    def upload_videos(self):
        """Videoları yükle"""
        if self.video_list.count() == 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce video ekleyin!")
            return
        
        # Doğrudan user_upload_dir'e kaydet
        target_dir = self.user_upload_dir
        
        success_count = 0
        for i in range(self.video_list.count()):
            item = self.video_list.item(i)
            source_path = item.data(Qt.UserRole)
            
            try:
                # Video dosyasını kopyala
                file_name = os.path.basename(source_path)
                target_path = os.path.join(target_dir, file_name)
                
                # Eğer aynı isimde dosya varsa, ismi değiştir
                if os.path.exists(target_path):
                    base_name, ext = os.path.splitext(file_name)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"{base_name}_{timestamp}{ext}"
                    target_path = os.path.join(target_dir, file_name)
                
                shutil.copy2(source_path, target_path)
                
                # Video bilgilerini JSON olarak kaydet
                video_info = {
                    'title': self.title_input.text() or os.path.splitext(file_name)[0],
                    'description': '',
                    'tags': [],
                    'category_id': '22',  # Varsayılan: People & Blogs
                    'privacy_status': 'private',
                    'made_for_kids': False,  # Varsayılan olarak çocuk içeriği değil
                    'upload_path': target_path,
                    'upload_date': datetime.now().strftime("%Y%m%d_%H%M%S"),
                    'status': 'pending'
                }
                
                json_path = os.path.splitext(target_path)[0] + '.json'
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(video_info, f, ensure_ascii=False, indent=4)
                
                success_count += 1
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Hata",
                    f"{file_name} yüklenemedi: {str(e)}"
                )
        
        if success_count > 0:
            QMessageBox.information(
                self,
                "Başarılı",
                f"{success_count} video başarıyla medya havuzuna eklendi!"
            )
            self.video_list.clear()
            self.title_input.clear()
            self.refresh_uploaded_videos()

    def refresh_uploaded_videos(self):
        """Yüklenen videoları listele"""
        if not self.current_username:
            return
        
        self.uploaded_list.clear()
        user_dir = os.path.join(self.base_upload_dir, self.current_username)
        
        if not os.path.exists(user_dir):
            return
        
        # Dosyaları tarih sırasına göre sırala (en yeni en üstte)
        files = []
        for filename in os.listdir(user_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(user_dir, filename)
                files.append((file_path, os.path.getmtime(file_path)))
        
        # Tarihe göre sırala (en yeni en üstte)
        files.sort(key=lambda x: x[1], reverse=True)
        
        for file_path, _ in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    video_info = json.load(f)
                
                # Video dosyasının varlığını kontrol et
                video_exists = os.path.exists(video_info['upload_path'])
                
                status_emoji = {
                    'pending': '⏳',
                    'uploaded': '✅',
                    'error': '❌'
                }.get(video_info['status'], '❓')
                
                # Dosya boyutunu al
                if video_exists:
                    size_mb = os.path.getsize(video_info['upload_path']) / (1024 * 1024)
                    size_text = f"{size_mb:.1f} MB"
                else:
                    size_text = "Dosya bulunamadı!"
                    status_emoji = '⚠️'
                
                # Yükleme tarihini formatla
                upload_date = datetime.strptime(video_info['upload_date'], "%Y%m%d_%H%M%S")
                date_text = upload_date.strftime("%d.%m.%Y %H:%M")
                
                item_text = f"{status_emoji} {video_info['title']}"
                item_text += f"\n└─ Durum: {video_info['status']}"
                item_text += f" | Boyut: {size_text}"
                item_text += f" | Tarih: {date_text}"
                
                if video_info.get('youtube_id'):
                    item_text += f"\n└─ YouTube ID: {video_info['youtube_id']}"
                
                if not video_exists:
                    item_text += "\n└─ UYARI: Video dosyası bulunamadı!"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, file_path)
                
                # Duruma göre arka plan rengi
                if not video_exists:
                    item.setBackground(Qt.yellow)
                elif video_info['status'] == 'uploaded':
                    item.setBackground(Qt.green)
                elif video_info['status'] == 'error':
                    item.setBackground(Qt.red)
                
                self.uploaded_list.addItem(item)
                
            except Exception as e:
                print(f"Hata: {file_path} dosyası okunamadı: {str(e)}")

    def show_video_details(self, item):
        """Video detaylarını göster"""
        json_path = item.data(Qt.UserRole)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                video_info = json.load(f)
            
            dialog = VideoDetailDialog(video_info, self)
            
            # Butonlar için horizontal layout
            btn_layout = QHBoxLayout()
            
            # Transkript butonu
            transcript_btn = QPushButton("Transkript Oluştur")
            transcript_btn.clicked.connect(lambda: self.generate_transcript(video_info))
            btn_layout.addWidget(transcript_btn)
            
            # Otomatik başlık butonu
            auto_title_btn = QPushButton("Otomatik Başlık Oluştur")
            auto_title_btn.clicked.connect(lambda: self.generate_auto_title(dialog, video_info))
            btn_layout.addWidget(auto_title_btn)
            
            # Zamanlama butonu
            schedule_btn = QPushButton("Zamanlama Ayarla")
            schedule_btn.clicked.connect(lambda: self.set_video_schedule(dialog, video_info))
            btn_layout.addWidget(schedule_btn)
            
            dialog.layout().insertLayout(dialog.layout().count()-1, btn_layout)
            
            if dialog.exec_() == QDialog.Accepted:
                # Güncellenmiş bilgileri kaydet
                updated_info = dialog.get_updated_info()
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_info, f, ensure_ascii=False, indent=4)
                
                # Listeyi yenile
                self.refresh_uploaded_videos()
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Video bilgileri yüklenemedi: {str(e)}")

    def generate_auto_title(self, dialog, video_info):
        """Otomatik başlık ve etiket oluştur"""
        # Önce transkript var mı kontrol et
        transcript = self.db.get_transcript(video_info['upload_path'])
        if not transcript:
            QMessageBox.warning(dialog, "Uyarı", "Önce transkript oluşturmalısınız!")
            return
            
        try:
            llm = LLMManager()
            title, tags = llm.generate_title_and_tags(
                video_info.get('description', ''),
                transcript[0]  # transcript[0] transkript metni
            )
            
            if title and tags:
                # Dialog'daki title ve tags alanlarını güncelle
                dialog.title_input.setText(title)
                dialog.tags_input.setText(','.join(tags))
                
                QMessageBox.information(
                    dialog,
                    "Başarılı",
                    "Başlık ve etiketler oluşturuldu!"
                )
        except Exception as e:
            QMessageBox.critical(
                dialog,
                "Hata",
                f"Başlık oluşturulamadı: {str(e)}"
            )
    
    def generate_transcript(self, video_info):
        """Video için transkript oluştur"""
        if not video_info.get('upload_path'):
            QMessageBox.warning(self, "Hata", "Video dosyası bulunamadı!")
            return
            
        # Önce mevcut transkript kontrolü yap
        existing_transcript = self.db.get_transcript(video_info['upload_path'])
        if existing_transcript:
            reply = QMessageBox.question(
                self,
                "Uyarı",
                "Bu video için zaten transkript oluşturulmuş. Yeniden oluşturmak istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Dil seçim dialogu
        dialog = QDialog(self)
        dialog.setWindowTitle("Transkript Dili")
        layout = QVBoxLayout(dialog)
        
        combo = QComboBox()
        combo.addItems(["Otomatik Algıla", "Türkçe", "English", "Deutsch", "Français", "Español"])
        layout.addWidget(QLabel("Videonun dilini seçin:"))
        layout.addWidget(combo)
        combo.setCurrentText("Otomatik Algıla")
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            language_map = {
                "Otomatik Algıla": "auto",
                "Türkçe": "tr",
                "English": "en",
                "Deutsch": "de",
                "Français": "fr",
                "Español": "es"
            }
            
            language = language_map[combo.currentText()]
            
            # İlerleme dialogu
            progress = QProgressDialog("Transkript oluşturuluyor...", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            try:
                transcript_manager = TranscriptManager()
                
                if language == "auto":
                    language = transcript_manager.detect_language(video_info['upload_path'])
                
                transcript = transcript_manager.get_transcript(video_info['upload_path'], language)
                if transcript:
                    # Transkripti veritabanına kaydet
                    self.db.save_transcript(
                        video_info['upload_path'],
                        transcript,
                        language
                    )
                    
                    # Transkripti video açıklamasına ekle
                    video_info['description'] = transcript + "\n\n" + video_info.get('description', '')
                    
                    # Otomatik başlık oluştur
                    llm = LLMManager()
                    title = llm.generate_title(transcript)
                    if title:
                        video_info['title'] = title
                    
                    QMessageBox.information(
                        self,
                        "Başarılı",
                        "Transkript oluşturuldu ve kaydedildi!"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Hata",
                        "Transkript oluşturulamadı!"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Hata",
                    f"Transkript işlemi başarısız: {str(e)}"
                )
            finally:
                progress.close()
    
    def edit_selected_videos(self):
        """Seçili videoları toplu düzenle"""
        selected_items = self.uploaded_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek videoları seçin!")
            return
        
        # Toplu düzenleme dialog'u
        dialog = QDialog(self)
        dialog.setWindowTitle("Toplu Video Düzenleme")
        layout = QVBoxLayout(dialog)
        
        # Gizlilik ayarı
        privacy_combo = QComboBox()
        privacy_combo.addItems(['private', 'unlisted', 'public'])
        layout.addWidget(QLabel("Gizlilik Ayarı:"))
        layout.addWidget(privacy_combo)
        
        # Etiketler
        tags_input = QLineEdit()
        layout.addWidget(QLabel("Eklenecek Etiketler (virgülle ayırın):"))
        layout.addWidget(tags_input)
        
        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            for item in selected_items:
                try:
                    json_path = item.data(Qt.UserRole)
                    with open(json_path, 'r', encoding='utf-8') as f:
                        video_info = json.load(f)
                    
                    # Bilgileri güncelle
                    video_info['privacy_status'] = privacy_combo.currentText()
                    new_tags = [tag.strip() for tag in tags_input.text().split(',') if tag.strip()]
                    video_info['tags'] = list(set(video_info.get('tags', []) + new_tags))
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(video_info, f, ensure_ascii=False, indent=4)
                        
                except Exception as e:
                    print(f"Hata: {json_path} güncellenemedi: {str(e)}")
            
            self.refresh_uploaded_videos()
    
    def delete_selected_videos(self):
        """Seçili videoları sil"""
        selected_items = self.uploaded_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek videoları seçin!")
            return
        
        reply = QMessageBox.question(
            self, "Onay", 
            f"{len(selected_items)} videoyu silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                try:
                    json_path = item.data(Qt.UserRole)
                    with open(json_path, 'r', encoding='utf-8') as f:
                        video_info = json.load(f)
                
                    # Video dosyasını sil
                    if os.path.exists(video_info['upload_path']):
                        # Önce transkripti sil
                        self.db.delete_transcript(video_info['upload_path'])
                        # Sonra videoyu sil
                        os.remove(video_info['upload_path'])
                    
                    # JSON dosyasını sil
                    os.remove(json_path)
                    
                except Exception as e:
                    print(f"Hata: {json_path} silinemedi: {str(e)}")
            
            self.refresh_uploaded_videos()
    
    def upload_selected_videos(self):
        """Seçili videoları YouTube'a yükle"""
        selected_items = self.uploaded_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen yüklenecek videoları seçin!")
            return
        
        for item in selected_items:
            json_path = item.data(Qt.UserRole)
            success, message = self.upload_to_youtube(json_path)
            
            if not success:
                reply = QMessageBox.question(
                    self, "Hata",
                    f"{message}\n\nDevam etmek istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    break
        
        self.refresh_uploaded_videos()

    def setup_shortcuts(self):
        # Global kısayollar
        QShortcut(QKeySequence("Ctrl+R"), self, self.refresh_uploaded_videos)
        QShortcut(QKeySequence("Ctrl+F"), self, self.focus_search)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self.prev_tab)
    
    def focus_search(self):
        self.filter_widget.search_box.setFocus()
    
    def next_tab(self):
        current = self.tabs.currentIndex()
        self.tabs.setCurrentIndex((current + 1) % self.tabs.count())
    
    def prev_tab(self):
        current = self.tabs.currentIndex()
        self.tabs.setCurrentIndex((current - 1) % self.tabs.count())
    
    def apply_filters(self):
        search_text = self.filter_widget.search_box.text().lower()
        status_filter = self.filter_widget.status_combo.currentText()
        date_filter = self.filter_widget.date_combo.currentText()
        
        for i in range(self.uploaded_list.count()):
            item = self.uploaded_list.item(i)
            video_info = self.get_video_info(item.data(Qt.UserRole))
            
            # Başlık araması
            title_match = search_text in video_info['title'].lower()
            
            # Durum filtresi
            status_match = True
            if status_filter != 'Tümü':
                status_map = {
                    'Beklemede': 'pending',
                    'Yüklendi': 'uploaded',
                    'Hata': 'error'
                }
                status_match = video_info['status'] == status_map[status_filter]  # statusmap yerine status_map kullanıldı
            
            # Tarih filtresi
            date_match = True
            if date_filter != 'Tümü':
                upload_date = datetime.strptime(video_info['upload_date'], "%Y%m%d_%H%M%S")
                now = datetime.now()
                
                if date_filter == 'Bugün':
                    date_match = upload_date.date() == now.date()
                elif date_filter == 'Bu Hafta':
                    week_ago = now - timedelta(days=7)
                    date_match = week_ago <= upload_date <= now
                elif date_filter == 'Bu Ay':
                    month_ago = now - timedelta(days=30)
                    date_match = month_ago <= upload_date <= now
            
            item.setHidden(not (title_match and status_match and date_match))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = event.size().width()
        
        # Font boyutlarını ekran genişliğine göre ayarla
        base_font_size = max(12, min(16, width // 100))
        self.setStyleSheet(f"""
            QWidget {{
                font-size: {base_font_size}px;
            }}
            QLabel#titleLabel {{
                font-size: {base_font_size * 3}px;
            }}
            QLabel#subtitleLabel {{
                font-size: {base_font_size * 1.5}px;
            }}
        """)
        
        try:
            # Menü konumunu ayarla
            if width < 1200:
                self.right_dock.hide()
                self.show_mobile_menu()
            else:
                self.right_dock.show()
                if hasattr(self, 'mobile_menu_btn'):
                    self.mobile_menu_btn.hide()
        except Exception as e:
            print(f"Hata: {str(e)}")

    def show_mobile_menu(self):
        # Mobil menü butu
        if not hasattr(self, 'mobile_menu_btn'):
            self.mobile_menu_btn = QPushButton(self)
            self.mobile_menu_btn.setIcon(QIcon('menu.png'))
            self.mobile_menu_btn.clicked.connect(self.toggle_mobile_menu)
            
        self.mobile_menu_btn.show()
        self.mobile_menu_btn.raise_()
        
    def toggle_mobile_menu(self):
        # Mobil menüyü göster/gizle
        if not hasattr(self, 'mobile_menu'):
            self.mobile_menu = QWidget(self)
            layout = QVBoxLayout(self.mobile_menu)
            # Menü butonlarını ekle...
            
        if self.mobile_menu.isVisible():
            self.mobile_menu.hide()
        else:
            self.mobile_menu.show()
            self.mobile_menu.raise_()

    def show_settings(self):
        """Ayarlar dialogunu göster"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ayarlar")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        
        # Tema seçimi
        theme_group = QGroupBox("Tema")
        theme_layout = QVBoxLayout()
        light_theme = QRadioButton("Açık Tema")
        dark_theme = QRadioButton("Koyu Tema")
        theme_layout.addWidget(light_theme)
        theme_layout.addWidget(dark_theme)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Font boyutu ayarı
        font_group = QGroupBox("Font Boyutu")
        font_layout = QHBoxLayout()
        font_slider = QSlider(Qt.Horizontal)
        font_slider.setMinimum(10)
        font_slider.setMaximum(20)
        font_slider.setValue(13)
        font_layout.addWidget(font_slider)
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.exec_()

    def on_channel_selected(self, item):
        """Seçili kanalın bilgilerini göster"""
        channel_data = item.data(Qt.UserRole)
        
        try:
            # Token'ı yenile ve kanal bilgilerini al
            credentials = Credentials(
                token=channel_data['access_token'],
                refresh_token=channel_data['refresh_token'],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_secrets['installed']['client_id'],
                client_secret=self.client_secrets['installed']['client_secret']
            )
            
            if credentials.expired:
                credentials.refresh(Request())
            
            youtube = build('youtube', 'v3', credentials=credentials)
            
            channel_response = youtube.channels().list(
                part='snippet,statistics',
                id=channel_data['channel_id']
            ).execute()
            
            if channel_response['items']:
                channel = channel_response['items'][0]
                info_text = f"""
                Kanal: {channel['snippet']['title']}
                Abone Sayısı: {channel['statistics'].get('subscriberCount', '0')}
                Video Sayısı: {channel['statistics'].get('videoCount', '0')}
                Toplam İzlenme: {channel['statistics'].get('viewCount', '0')}
                """
                self.channel_info.setText(info_text)
                
        except Exception as e:
            self.channel_info.setText(f"Kanal bilgileri alınamadı: {str(e)}")

    def add_video(self):
        """Video ekle"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Video Seç",
            "",
            "Video Dosyaları (*.mp4 *.avi *.mkv *.mov);;Tüm Dosyalar (*.*)"
        )
        
        if files:
            for file_path in files:
                # Video bilgilerini al
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                # Liste öğesi oluştur
                item = QListWidgetItem(f"{file_name} ({self.format_size(file_size)})")
                item.setData(Qt.UserRole, file_path)
                self.video_list.addItem(item)

    def remove_video(self):
        """Seçili videoyu listeden kaldır"""
        current_item = self.video_list.currentItem()
        if current_item:
            self.video_list.takeItem(self.video_list.row(current_item))

    def format_size(self, size):
        """Dosya boyutunu formatla"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def delete_from_youtube(self):
        """Seçili videoları YouTube'dan sil"""
        selected_items = self.youtube_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek videoları seçin!")
            return
        
        reply = QMessageBox.question(
            self, 
            "Onay",
            f"{len(selected_items)} videoyu YouTube'dan silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                data = item.data(Qt.UserRole)
                video_info = data['video_info']
                
                try:
                    # YouTube API ile videoyu sil
                    youtube = self.get_youtube_service()
                    if youtube:
                        youtube.videos().delete(
                            id=video_info['youtube_id']
                        ).execute()
                        
                        # JSON dosyasını güncelle
                        video_info['status'] = 'deleted_from_youtube'
                        video_info['youtube_id'] = None
                        with open(data['file_path'], 'w', encoding='utf-8') as f:
                            json.dump(video_info, f, ensure_ascii=False, indent=4)
                        
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Hata",
                        f"Video silinemedi: {str(e)}"
                    )
            
            self.refresh_youtube_videos()

    def get_video_info(self, json_path):
        """JSON dosyasından video bilgilerini oku"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Eğer upload_path yoksa varsayılan değerler döndür
                if 'upload_path' not in data:
                    return {
                        'title': os.path.splitext(os.path.basename(json_path))[0],
                        'status': 'error',
                        'upload_date': datetime.now().strftime("%Y%m%d_%H%M%S"),
                        'upload_path': None
                    }
                return data
        except Exception as e:
            print(f"Video bilgileri okunamadı: {str(e)}")
            return {
                'title': 'Bilinmeyen Video',
                'status': 'error',
                'upload_date': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'upload_path': None
            }

    def refresh_youtube_videos(self):
        """YouTube kanalındaki videoları listele"""
        self.youtube_list.clear()
        
        # Seçili kanalı kontrol et
        current_channel = self.youtube_channel_combo.currentData()
        if not current_channel:
            return
        
        try:
            # YouTube API'ye bağlan
            credentials = Credentials(
                token=current_channel['access_token'],
                refresh_token=current_channel['refresh_token'],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_secrets['installed']['client_id'],
                client_secret=self.client_secrets['installed']['client_secret']
            )
            
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Kanal videolarını listele
            videos = []
            next_page_token = None
            
            while True:
                # Kanal videolarını al
                playlist_request = youtube.channels().list(
                    part="contentDetails",
                    id=current_channel['channel_id']
                )
                playlist_response = playlist_request.execute()
                
                # Uploads playlist ID'sini al
                uploads_playlist_id = playlist_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                
                # Playlist'teki videoları al
                playlist_items = youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()
                
                # Video ID'lerini topla
                video_ids = [item['contentDetails']['videoId'] for item in playlist_items['items']]
                
                # Video detaylarını al
                if video_ids:
                    video_response = youtube.videos().list(
                        part="snippet,statistics,status,contentDetails",
                        id=','.join(video_ids)
                    ).execute()
                    
                    videos.extend(video_response['items'])
                
                next_page_token = playlist_items.get('nextPageToken')
                if not next_page_token:
                    break
            
            # Videoları listele
            for video in videos:
                title = video['snippet']['title']
                views = video['statistics'].get('viewCount', '0')
                likes = video['statistics'].get('likeCount', '0')
                comments = video['statistics'].get('commentCount', '0')
                privacy = video['status']['privacyStatus']
                duration = video['contentDetails']['duration'].replace('PT','').replace('H',':').replace('M',':').replace('S','')
                
                # Yükleme tarihini formatla
                upload_date = datetime.strptime(
                    video['snippet']['publishedAt'], 
                    '%Y-%m-%dT%H:%M:%SZ'
                )
                date_str = upload_date.strftime('%d.%m.%Y %H:%M')
                
                item_text = f"🎬 {title}"
                item_text += f"\n└─ Görüntülenme: {int(views):,} | Beğeni: {int(likes):,} | Yorum: {int(comments):,}"
                item_text += f"\n└─ Süre: {duration} | Tarih: {date_str} | Durum: {privacy}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, video)
                
                # Gizlilik durumuna göre renk ver
                if privacy == 'private':
                    item.setBackground(Qt.yellow)
                elif privacy == 'unlisted':
                    item.setBackground(Qt.lightGray)
                
                self.youtube_list.addItem(item)
            
            # youtube_tab yerine channel_tab kullan
            self.channel_tab.setWindowTitle(f"Kanal Yönetimi - {len(videos)} Video")
            
        except Exception as e:
            import traceback
            print("Hata detayı:", traceback.format_exc())  # Detaylı hata mesajı
            QMessageBox.warning(self, "Hata", f"Videolar alınamadı: {str(e)}")

    def auto_refresh_videos(self):
        """Otomatik yenileme kontrolü"""
        if self.auto_refresh_check.isChecked():
            self.refresh_youtube_videos()

    def edit_youtube_video(self, item):
        """YouTube video düzenleme dialog'u"""
        if not item:
            return
        
        video = item.data(Qt.UserRole)
        dialog = QDialog(self)
        dialog.setWindowTitle("Video Düzenle")
        dialog.setMinimumWidth(800)  # Genişliği artırdık
        layout = QVBoxLayout(dialog)
        
        # Form
        form = QFormLayout()
        
        # Başlık
        title_input = QLineEdit(video['snippet']['title'])
        title_input.setPlaceholderText("Video başlığı...")
        form.addRow("Başlık:", title_input)
        
        # Açıklama
        description_input = QTextEdit()
        description_input.setText(video['snippet']['description'])
        description_input.setMinimumHeight(200)  # Yüksekliği artırdık
        description_input.setPlaceholderText("Video açıklaması...")
        form.addRow("Açıklama:", description_input)
        
        # Etiketler
        tags_input = QLineEdit()
        tags_input.setText(','.join(video['snippet'].get('tags', [])))
        tags_input.setPlaceholderText("Etiketleri virgülle ayırın...")
        form.addRow("Etiketler:", tags_input)
        
        # Gizlilik
        privacy_combo = QComboBox()
        privacy_combo.addItems(['private', 'unlisted', 'public'])
        privacy_combo.setCurrentText(video['status']['privacyStatus'])
        form.addRow("Gizlilik:", privacy_combo)
        
        # Çocuk içeriği
        kids_group = QGroupBox("Çocuk İçeriği")
        kids_layout = QVBoxLayout()
        kids_yes = QRadioButton("Evet, çocuklara özel")
        kids_no = QRadioButton("Hayır, çocuklara özel değil")
        
        # Mevcut ayarı seç
        if video['status'].get('madeForKids', False):
            kids_yes.setChecked(True)
        else:
            kids_no.setChecked(True)
        
        kids_layout.addWidget(kids_yes)
        kids_layout.addWidget(kids_no)
        kids_group.setLayout(kids_layout)
        form.addRow(kids_group)
        
        # Kategori
        category_combo = QComboBox()
        for id, name in YOUTUBE_CATEGORIES.items():
            category_combo.addItem(name, id)
        
        # Mevcut kategoriyi seç
        current_category = video['snippet'].get('categoryId', '22')
        index = category_combo.findData(current_category)
        if index >= 0:
            category_combo.setCurrentIndex(index)
        form.addRow("Kategori:", category_combo)
        
        layout.addLayout(form)
        
        # İstatistikler grubu
        stats_group = QGroupBox("Video İstatistikleri")
        stats_layout = QVBoxLayout()
        
        # İstatistikleri formatlayarak göster
        views = int(video['statistics'].get('viewCount', '0'))
        likes = int(video['statistics'].get('likeCount', '0'))
        comments = int(video['statistics'].get('commentCount', '0'))
        
        stats_layout.addWidget(QLabel(f"Görüntülenme: {views:,}"))
        stats_layout.addWidget(QLabel(f"Beğeni: {likes:,}"))
        stats_layout.addWidget(QLabel(f"Yorum: {comments:,}"))
        
        # Yükleme tarihi
        upload_date = datetime.strptime(
            video['snippet']['publishedAt'], 
            '%Y-%m-%dT%H:%M:%SZ'
        )
        stats_layout.addWidget(QLabel(f"Yükleme Tarihi: {upload_date.strftime('%d.%m.%Y %H:%M')}"))
        
        # Video URL'si
        video_id = video['id']
        video_url = f"https://youtu.be/{video_id}"
        url_label = QLabel(f'<a href="{video_url}">Video URL: {video_url}</a>')
        url_label.setOpenExternalLinks(True)
        stats_layout.addWidget(url_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Butonlar
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Seçili kanalın YouTube API'sini al
                current_channel = self.youtube_channel_combo.currentData()
                credentials = Credentials(
                    token=current_channel['access_token'],
                    refresh_token=current_channel['refresh_token'],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_secrets['installed']['client_id'],
                    client_secret=self.client_secrets['installed']['client_secret']
                )
                
                youtube = build('youtube', 'v3', credentials=credentials)
                
                # Video bilgilerini güncelle
                youtube.videos().update(
                    part="snippet,status",
                    body={
                        "id": video['id'],
                        "snippet": {
                            "title": title_input.text(),
                            "description": description_input.toPlainText(),
                            "tags": [tag.strip() for tag in tags_input.text().split(',') if tag.strip()],
                            "categoryId": category_combo.currentData()
                        },
                        "status": {
                            "privacyStatus": privacy_combo.currentText(),
                            "madeForKids": kids_yes.isChecked()
                        }
                    }
                ).execute()
                
                QMessageBox.information(self, "Başarılı", "Video başarıyla güncellendi!")
                self.refresh_youtube_videos()
                
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Video güncellenemedi: {str(e)}")

    def create_bulk_transcripts(self):
        """Seçili videolar için toplu transkript oluştur"""
        selected_items = self.uploaded_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Uyarı", "Lütfen video(lar) seçin!")
            return
        
        # Transkripti olmayan videoları filtrele
        videos_to_process = []
        for item in selected_items:
            json_path = item.data(Qt.UserRole)
            with open(json_path, 'r', encoding='utf-8') as f:
                video_info = json.load(f)
            
            # Transkript kontrolü
            if not self.db.get_transcript(video_info['upload_path']):
                videos_to_process.append((json_path, video_info))
        
        if not videos_to_process:
            QMessageBox.information(self, "Bilgi", "Seçili videoların hepsi zaten transkript edilmiş!")
            return
        
        # Dil seçim dialogu ve diğer işlemler...
        # ... (mevcut kodun geri kalanı aynı kalacak, sadece selected_items yerine videos_to_process kullanılacak)

    def create_bulk_auto_titles(self):
        # ... mevcut kodlar ...
        
        # Dil seçim dialogu
        dialog = QDialog(self)
        dialog.setWindowTitle("Toplu Otomatik Başlık Oluştur")
        layout = QVBoxLayout(dialog)
        
        combo = QComboBox()
        combo.addItems(["Otomatik Algıla", "Türkçe", "English", "Deutsch", "Français", "Español"])
        layout.addWidget(QLabel("Videoların dilini seçin:"))
        layout.addWidget(combo)
        combo.setCurrentText("Otomatik Algıla")
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            language_map = {
                "Otomatik Algıla": "auto",
                "Türkçe": "tr",
                "English": "en",
                "Deutsch": "de",
                "Français": "fr",
                "Español": "es"
            }
            
            language = language_map[combo.currentText()]
            
            # İlerleme dialogu
            progress = QProgressDialog(
                "Başlıklar oluşturuluyor...", 
                "İptal",
                0,
                len(selected_items),
                self
            )
            progress.setWindowModality(Qt.WindowModal)
            
            success_count = 0
            for i, item in enumerate(selected_items):
                if progress.wasCanceled():
                    break
                    
                progress.setValue(i)
                
                try:
                    json_path = item.data(Qt.UserRole)
                    with open(json_path, 'r', encoding='utf-8') as f:
                        video_info = json.load(f)
                    
                    llm = LLMManager()
                    title = llm.generate_title_and_tags(
                        video_info.get('description', ''),
                        self.db.get_transcript(video_info['upload_path'])[0]  # transkript metni
                    )
                    
                    if title:
                        # Dialog'daki title alanını güncelle
                        video_info['title'] = title[0]
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(video_info, f, ensure_ascii=False, indent=4)
                        
                        success_count += 1
                
                except Exception as e:
                    print(f"Hata: {str(e)}")
            
            progress.setValue(len(selected_items))
            
            QMessageBox.information(
                self,
                "Tamamlandı",
                f"{success_count} video için otomatik başlık oluşturuldu!"
            )
            
            self.refresh_uploaded_videos()

    def change_bulk_category(self):
        # ... mevcut kodlar ...
        
        # Dil seçim dialogu
        dialog = QDialog(self)
        dialog.setWindowTitle("Toplu Kategori Değiştir")
        layout = QVBoxLayout(dialog)
        
        combo = QComboBox()
        combo.addItems(["Otomatik Algıla", "Türkçe", "English", "Deutsch", "Français", "Español"])
        layout.addWidget(QLabel("Yeni kategorileri virgülle ayırın:"))
        layout.addWidget(combo)
        combo.setCurrentText("Otomatik Algıla")
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            new_categories = [cat.strip() for cat in combo.currentText().split(',')]
            
            success_count = 0
            for i, item in enumerate(selected_items):
                if progress.wasCanceled():
                    break
                    
                progress.setValue(i)
                
                try:
                    json_path = item.data(Qt.UserRole)
                    with open(json_path, 'r', encoding='utf-8') as f:
                        video_info = json.load(f)
                    
                    # Yeni kategoriyi ayarla
                    video_info['category_id'] = new_categories[i]
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(video_info, f, ensure_ascii=False, indent=4)
                        
                    success_count += 1
                
                except Exception as e:
                    print(f"Hata: {str(e)}")
            
            progress.setValue(len(selected_items))
            
            QMessageBox.information(
                self,
                "Tamamlandı",
                f"{success_count} video için kategori değiştirildi!"
            )
            
            self.refresh_uploaded_videos()

    def set_bulk_schedule(self):
        # ... mevcut kodlar ...
        
        # Dil seçim dialogu
        dialog = QDialog(self)
        dialog.setWindowTitle("Toplu Zamanlama")
        layout = QVBoxLayout(dialog)
        
        combo = QComboBox()
        combo.addItems(["Otomatik Algıla", "Türkçe", "English", "Deutsch", "Français", "Español"])
        layout.addWidget(QLabel("Yeni zamanlamaları virgülle ayırın:"))
        layout.addWidget(combo)
        combo.setCurrentText("Otomatik Algıla")
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            new_schedules = [sch.strip() for sch in combo.currentText().split(',')]
            
            success_count = 0
            for i, item in enumerate(selected_items):
                if progress.wasCanceled():
                    break
                    
                progress.setValue(i)
                
                try:
                    json_path = item.data(Qt.UserRole)
                    with open(json_path, 'r', encoding='utf-8') as f:
                        video_info = json.load(f)
                    
                    # Yeni zamanlamayı ayarla
                    video_info['scheduled_time'] = new_schedules[i]
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(video_info, f, ensure_ascii=False, indent=4)
                        
                    success_count += 1
                
                except Exception as e:
                    print(f"Hata: {str(e)}")
            
            progress.setValue(len(selected_items))
            
            QMessageBox.information(
                self,
                "Tamamlandı",
                f"{success_count} video için zamanlama ayarlandı!"
            )
            
            self.refresh_uploaded_videos()

    def set_video_schedule(self, dialog, video_info):
        """Video için zamanlama ayarla"""
        schedule_dialog = QDialog(dialog)
        schedule_dialog.setWindowTitle("Zamanlama Ayarla")
        layout = QVBoxLayout(schedule_dialog)
        
        # Tarih ve saat seçici
        date_time = QDateTimeEdit()
        date_time.setDateTime(QDateTime.currentDateTime())
        date_time.setCalendarPopup(True)
        layout.addWidget(QLabel("Yayın Tarihi:"))
        layout.addWidget(date_time)
        
        # Butonlar
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(schedule_dialog.accept)
        buttons.rejected.connect(schedule_dialog.reject)
        layout.addWidget(buttons)
        
        if schedule_dialog.exec_() == QDialog.Accepted:
            video_info['scheduled_time'] = date_time.dateTime().toString(Qt.ISODate)
            # Video bilgilerini güncelle...

class TranscriptManager:
    def __init__(self):
        self.api_key = "NEtrjC5t3xb5DPEQBHgQCzkqzttoLVxW"
        self.api_url = "https://api.lemonfox.ai/v1/audio/transcriptions"
    
    def get_transcript(self, video_path, language="tr"):
        """Video dosyasından transkript al"""
        try:
            if not os.path.exists(video_path):
                print("Video dosyası bulunamadı!")
                return None
                
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "language": language,
                "response_format": "json"
            }
            
            # Doğrudan video dosyasını gönder
            files = {
                "file": open(video_path, "rb")
            }
            
            response = requests.post(
                self.api_url, 
                headers=headers, 
                files=files, 
                data=data
            )
            
            if response.status_code == 200:
                return response.json()["text"]
            else:
                print(f"API Hatası: {response.text}")
                return None
                
        except Exception as e:
            print(f"Transkript alma hatası: {str(e)}")
            return None
    
    def detect_language(self, video_path):
        """Video dosyasından dili otomatik algıla"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "language": "auto",
                "response_format": "json"
            }
            
            files = {
                "file": open(video_path, "rb")
            }
            
            response = requests.post(
                f"{self.api_url}/detect",
                headers=headers,
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                return response.json()["language"]
            return "tr"
                
        except Exception as e:
            print(f"Dil algılama hatası: {str(e)}")
            return "tr"

class LLMManager:
    def __init__(self):
        self.api_key = "ExaOsWThOOYef8CWgGrKlA2toHjetXnu"
        self.base_url = "https://api.lemonfox.ai/v1"
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def generate_title(self, transcript):
        """SEO uyumlu başlık oluştur"""
        try:
            prompt = f"""
            Bu bir YouTube videosu için SEO uyumlu başlık oluşturma görevidir.
            
            Video transkripti:
            {transcript}
            
            Lütfen video içeriğine uygun, SEO açısından optimize edilmiş, ilgi çekici bir başlık oluştur.
            Başlık 100 karakteri geçmemeli, hashtag'lerle başlamalı ve anahtar kelimeleri içermeli.
            Örnek format: #Kategori #AnahtarKelime Başlık Metni
            """
            
            completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "Sen YouTube SEO konusunda uzman bir asistansın. Görevin hashtag'li SEO başlığı oluşturmak."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="llama-8b-chat"
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM hatası: {str(e)}")
            return None

    def generate_description(self, title, transcript):
        """Video için SEO uyumlu açıklama oluştur"""
        try:
            prompt = f"""
            Bu bir YouTube videosu için SEO uyumlu açıklama oluşturma görevidir.
            
            Video başlığı:
            {title}
            
            Video transkripti:
            {transcript}
            
            Lütfen video içeriğine uygun, SEO açısından optimize edilmiş bir açıklama oluştur.
            Açıklama 5000 karakteri geçmemeli ve şunları içermeli:
            - İlk 2-3 cümlede videonun özeti
            - Anahtar kelimeler ve konuyla ilgili terimler
            - İzleyiciyi etkileşime teşvik eden bir çağrı (like, abone ol, yorum yap vb.)
            - Varsa zaman damgaları ve bölümler
            """
            
            completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": "Sen YouTube SEO konusunda uzman bir asistansın. Görevin SEO uyumlu video açıklaması oluşturmak."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model="llama-8b-chat"
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"LLM açıklama hatası: {str(e)}")
            return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Varsayılan kullanıcıyı oluştur
    db = Database()
    try:
        db.register_user("yigocreative", "Yigor3535-*", "yigocreative@example.com")
    except:
        pass  # Kullanıcı zaten varsa hata vermeyi görmezden gel
    
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec_()) 