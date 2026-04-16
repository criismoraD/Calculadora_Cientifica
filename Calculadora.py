import sys
import os
import math
import re
import ast
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QGridLayout, QRadioButton, QCheckBox, QLabel
)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QPainter, QFont, QPen, QColor, QLinearGradient
from PyQt5.QtMultimedia import QSoundEffect, QMediaPlayer, QMediaContent


# ============================================================================
# LOGO ASCII DE SENATI
# ============================================================================
LOGO_SENATI = """
╔═════════════════════════════════════════════════╗
║  ███████╗███████╗███╗  ██╗ █████╗ ████████╗██╗  ║
║  ██╔════╝██╔════╝████╗ ██║██╔══██╗╚══██╔══╝██║  ║
║  ███████╗█████╗  ██╔██╗██║███████║   ██║   ██║  ║
║  ╚════██║██╔══╝  ██║╚████║██╔══██║   ██║   ██║  ║
║  ███████║███████╗██║ ╚███║██║  ██║   ██║   ██║  ║
║  ╚══════╝╚══════╝╚═╝  ╚══╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ║
╚═════════════════════════════════════════════════╝
"""

LOGO_ADIOS = """
╔════════════════════════════════════════╗
║   █████╗ ██████╗ ██╗ ██████╗ ███████╗  ║
║  ██╔══██╗██╔══██╗██║██╔═══██╗██╔════╝  ║
║  ███████║██║  ██║██║██║   ██║███████╗  ║
║  ██╔══██║██║  ██║██║██║   ██║╚════██║  ║
║  ██║  ██║██████╔╝██║╚██████╔╝███████║  ║
║  ╚═╝  ╚═╝╚═════╝ ╚═╝ ╚═════╝ ╚══════╝  ║
╚════════════════════════════════════════╝
"""


# ============================================================================
# CLASE PANTALLA LCD
# ============================================================================
class PantallaLCD(QWidget):
    """
    Pantalla estilo LCD con soporte para:
    - Fracciones visuales (numerador/línea/denominador)
    - Notación matemática (superíndices, raíces)
    - Animación del logo de SENATI
    - Estados de encendido/apagado
    """

    _RE_EXP_COMPLEJO = re.compile(r'\*\*\(([^)]+)\)')
    _RE_EXP_SIMPLE = re.compile(r'\*\*(\d+\.?\d*)')
    _RE_NTHROOT = re.compile(r'nthroot\(([^,]+),([^)]+)\)')

    _SUPERINDICES = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '+': '⁺', '-': '⁻', '(': '⁽', ')': '⁾', '.': '·'
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.operacion = ""
        self.operacion_visual = ""
        self.resultado = "0"
        self.modo = "DEG"
        self.encendida = False
        self.mostrando_logo = False
        self.mostrando_adios = False
        self.logo_alpha = 0
        self.setMinimumHeight(120)

    def setEncendida(self, estado):
        self.encendida = estado
        self.update()

    def setMostrandoLogo(self, estado, alpha=255, es_adios=False):
        self.mostrando_logo = estado
        self.mostrando_adios = es_adios
        self.logo_alpha = alpha
        self.update()

    def setOperacion(self, texto):
        self.operacion = texto
        self.operacion_visual = self.formato_visual(texto)
        self.update()

    def setResultado(self, valor):
        """Formatea y muestra el resultado"""
        try:
            if isinstance(valor, str):
                self.resultado = valor if valor else "0"
            else:
                num = float(valor)
                if num == int(num) and abs(num) < 1e10:
                    self.resultado = str(int(num))
                else:
                    self.resultado = f"{num:.10g}"
        except (ValueError, TypeError, OverflowError):
            self.resultado = str(valor)
        self.update()

    def setModo(self, modo):
        self.modo = modo
        self.update()

    def formato_visual(self, texto):
        """
        Convierte notación interna a notación visual:
        - **2 → ²
        - sqrt( → √(
        - nthroot(x,n) → ⁿ√(x)
        """
        def reemplazar_exp_complejo(match):
            contenido = match.group(1)
            return ''.join(self._SUPERINDICES.get(c, c) for c in contenido)

        resultado = self._RE_EXP_COMPLEJO.sub(reemplazar_exp_complejo, texto)

        def reemplazar_exp_simple(match):
            exp = match.group(1)
            return ''.join(self._SUPERINDICES.get(c, c) for c in exp)

        resultado = self._RE_EXP_SIMPLE.sub(reemplazar_exp_simple, resultado)
        resultado = resultado.replace('sqrt(', '√(')

        def reemplazar_nthroot(match):
            radicando = match.group(1)
            indice = match.group(2)
            indice_sup = ''.join(self._SUPERINDICES.get(c, c) for c in indice)
            return f'{indice_sup}√({radicando})'

        resultado = self._RE_NTHROOT.sub(reemplazar_nthroot, resultado)
        resultado = resultado.replace('nthroot(', 'ⁿ√(')
        resultado = resultado.replace('**', '^')
        return resultado

    def encontrar_fraccion(self, texto, inicio):
        """Encuentra una fracción simple (número/número) en el texto"""
        if inicio >= len(texto):
            return None

        num_start = inicio
        num_end = inicio

        # Leer numerador
        if num_start < len(texto) and texto[num_start] == '(':
            nivel = 1
            num_end = num_start + 1
            while num_end < len(texto) and nivel > 0:
                if texto[num_end] == '(':
                    nivel += 1
                elif texto[num_end] == ')':
                    nivel -= 1
                num_end += 1
        else:
            while num_end < len(texto) and (texto[num_end].isdigit() or texto[num_end] == '.'):
                num_end += 1

        if num_end >= len(texto) or texto[num_end] != '/':
            return None

        numerador = texto[num_start:num_end]
        den_start = num_end + 1
        if den_start >= len(texto):
            return None

        den_end = den_start

        # Leer denominador
        if den_start < len(texto) and texto[den_start] == '(':
            nivel = 1
            den_end = den_start + 1
            while den_end < len(texto) and nivel > 0:
                if texto[den_end] == '(':
                    nivel += 1
                elif texto[den_end] == ')':
                    nivel -= 1
                den_end += 1
        else:
            while den_end < len(texto) and (texto[den_end].isdigit() or texto[den_end] == '.'):
                den_end += 1

        denominador = texto[den_start:den_end]
        if not numerador or not denominador:
            return None

        return {
            'num': numerador, 'den': denominador,
            'start': num_start, 'end': den_end
        }

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.encendida:
            painter.fillRect(self.rect(), QColor(60, 60, 60))
            painter.setPen(QPen(QColor(40, 40, 40), 2))
            painter.drawRect(2, 2, self.width() - 4, self.height() - 4)
            return

        if self.mostrando_logo:
            self._dibujar_logo(painter)
            return

        # Fondo LCD verde
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(180, 200, 170))
        gradient.setColorAt(1, QColor(160, 180, 150))
        painter.fillRect(self.rect(), gradient)

        painter.setPen(QPen(QColor(100, 120, 90), 2))
        painter.drawRect(2, 2, self.width() - 4, self.height() - 4)

        # Indicador de modo
        font_modo = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font_modo)
        painter.setPen(QColor(80, 100, 70))
        painter.drawText(10, 18, self.modo)

        # Operación con fracciones
        self._dibujar_operacion(painter)

        # Resultado
        font_res = QFont("Consolas", 22, QFont.Bold)
        painter.setFont(font_res)
        painter.setPen(QColor(20, 40, 10))
        res_width = painter.fontMetrics().horizontalAdvance(self.resultado)
        painter.drawText(
            self.width() - res_width - 15,
            self.height() - 12,
            self.resultado
        )

    def _dibujar_logo(self, painter):
        """Dibuja el logo SENATI o ADIOS con animación fade"""
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(180, 200, 170))
        gradient.setColorAt(1, QColor(160, 180, 150))
        painter.fillRect(self.rect(), gradient)

        painter.setPen(QPen(QColor(100, 120, 90), 2))
        painter.drawRect(2, 2, self.width() - 4, self.height() - 4)

        logo_texto = LOGO_ADIOS if self.mostrando_adios else LOGO_SENATI

        font_logo = QFont("Consolas", 7)
        painter.setFont(font_logo)
        color = QColor(20, 60, 20, self.logo_alpha)
        painter.setPen(color)

        lineas = logo_texto.strip().split('\n')
        line_height = 10
        total_height = len(lineas) * line_height
        start_y = (self.height() - total_height) // 2 + line_height

        for i, linea in enumerate(lineas):
            text_width = painter.fontMetrics().horizontalAdvance(linea)
            x = (self.width() - text_width) // 2
            y = start_y + i * line_height
            painter.drawText(x, y, linea)

    def _dibujar_operacion(self, painter):
        """Dibuja la operación con fracciones visuales"""
        font_op = QFont("Consolas", 12)
        painter.setFont(font_op)
        painter.setPen(QColor(40, 60, 30))

        texto = self.operacion_visual
        x = 10
        y = 55
        i = 0

        while i < len(texto):
            frac = self.encontrar_fraccion(texto, i)

            if frac and frac['start'] == i:
                num = frac['num']
                den = frac['den']
                num_width = painter.fontMetrics().horizontalAdvance(num)
                den_width = painter.fontMetrics().horizontalAdvance(den)
                frac_width = max(num_width, den_width) + 10

                # Numerador
                painter.drawText(
                    x + (frac_width - num_width) // 2, y - 12, num
                )

                # Línea de fracción
                pen = painter.pen()
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(x, y - 2, x + frac_width, y - 2)
                pen.setWidth(1)
                painter.setPen(pen)
                painter.setPen(QColor(40, 60, 30))  # Restaurar color

                # Denominador
                painter.drawText(
                    x + (frac_width - den_width) // 2, y + 14, den
                )

                x += frac_width + 5
                i = frac['end']
            else:
                char = texto[i]
                painter.drawText(x, y, char)
                x += painter.fontMetrics().horizontalAdvance(char) + 1
                i += 1


# ============================================================================
# CLASE CALCULADORA PRINCIPAL
# ============================================================================
class Calculadora(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("Calculadora Científica")
        self.setFixedSize(420, 720)

        # Estado
        self.operacion_actual = ""
        self.cursor_pos = 0
        self.resultado_valor = 0
        self.modo_angulo = "DEG"
        self.sonido_activo = True
        self.calculadora_encendida = False
        self.drag_position = None

        # Animación logo
        self.timer_logo = QTimer()
        self.timer_logo.timeout.connect(self.animar_logo)
        self.logo_alpha = 0
        self.logo_fade_in = True
        self.animando_adios = False

        # Sonidos
        self.sonido_click = QSoundEffect()
        self._crear_sonido_click()

        self._cargar_estilos()
        self._init_ui()

        self.setFocusPolicy(Qt.StrongFocus)

        # Iniciar apagada
        self.pantalla.setEncendida(False)
        self._habilitar_botones(False)
        self._actualizar_estado_encendido()

    # ====================================================================
    # DIBUJO Y ARRASTRE DE VENTANA
    # ====================================================================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(42, 42, 42))
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    # ====================================================================
    # TECLADO
    # ====================================================================
    def keyPressEvent(self, event):
        key = event.key()
        texto = event.text()

        mapa_teclas = {
            Qt.Key_Left: lambda: self.mover_cursor(-1),
            Qt.Key_Right: lambda: self.mover_cursor(1),
            Qt.Key_Home: lambda: self.ir_a_posicion(0),
            Qt.Key_End: lambda: self.ir_a_posicion(-1),
            Qt.Key_Return: lambda: self.click_boton('='),
            Qt.Key_Enter: lambda: self.click_boton('='),
            Qt.Key_Backspace: lambda: self.borrar_elemento(),
            Qt.Key_Delete: lambda: self.borrar_elemento_adelante(),
            Qt.Key_Escape: lambda: self.click_boton('C'),
        }

        if key in mapa_teclas:
            mapa_teclas[key]()
        elif texto in '0123456789.':
            self.click_boton(texto)
        elif texto in '+-':
            self.click_boton(texto)
        elif texto == '*':
            self.click_boton('×')
        elif texto == '/':
            self.click_boton('/')
        elif texto in '()':
            self.click_boton(texto)
        else:
            super().keyPressEvent(event)

    # ====================================================================
    # SONIDOS
    # ====================================================================
    def _crear_sonido_click(self):
        """Crea archivo de sonido click si no existe"""
        import wave
        import struct

        ruta_sonido = os.path.join(os.path.dirname(__file__), "click.wav")

        if not os.path.exists(ruta_sonido):
            sample_rate = 44100
            duration = 0.05
            frequency = 800

            with wave.open(ruta_sonido, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)

                for i in range(int(sample_rate * duration)):
                    t = i / sample_rate
                    amplitude = 0.3 * math.exp(-t * 50)
                    value = int(amplitude * 32767 * math.sin(
                        2 * math.pi * frequency * t
                    ))
                    wav_file.writeframes(struct.pack('<h', value))

        self.sonido_click.setSource(QUrl.fromLocalFile(ruta_sonido))
        self.sonido_click.setVolume(0.5)

        # Sonidos MP3 de encendido/apagado
        self.sonido_prender = QMediaPlayer()
        self.sonido_apagar = QMediaPlayer()

        ruta_prender = os.path.join(os.path.dirname(__file__), "PRENDER.mp3")
        ruta_apagar = os.path.join(os.path.dirname(__file__), "APAGAR.mp3")

        if os.path.exists(ruta_prender):
            self.sonido_prender.setMedia(
                QMediaContent(QUrl.fromLocalFile(ruta_prender))
            )
        if os.path.exists(ruta_apagar):
            self.sonido_apagar.setMedia(
                QMediaContent(QUrl.fromLocalFile(ruta_apagar))
            )

    def reproducir_sonido(self):
        if self.sonido_activo and self.calculadora_encendida:
            self.sonido_click.play()

    def _reproducir_sonido_encendido(self, encender):
        if self.sonido_activo:
            player = self.sonido_prender if encender else self.sonido_apagar
            player.setPosition(0)
            player.play()

    # ====================================================================
    # ANIMACIÓN DEL LOGO
    # ====================================================================
    def animar_logo(self):
        if self.logo_fade_in:
            self.logo_alpha += 15
            if self.logo_alpha >= 255:
                self.logo_alpha = 255
                self.logo_fade_in = False
                delay = 1500 if self.animando_adios else 1000
                callback = (self._finalizar_animacion_adios
                            if self.animando_adios
                            else self._finalizar_animacion_logo)
                QTimer.singleShot(delay, callback)

        self.pantalla.setMostrandoLogo(True, self.logo_alpha, self.animando_adios)

    def _finalizar_animacion_logo(self):
        self.timer_logo.stop()
        self.pantalla.setMostrandoLogo(False)
        self.pantalla.setEncendida(True)
        self._habilitar_botones(True)

    def _finalizar_animacion_adios(self):
        self.timer_logo.stop()
        self.pantalla.setMostrandoLogo(False)
        self.pantalla.setEncendida(False)
        self.animando_adios = False

    # ====================================================================
    # ENCENDIDO / APAGADO
    # ====================================================================
    def toggle_encendido(self):
        self.calculadora_encendida = not self.calculadora_encendida
        self._reproducir_sonido_encendido(self.calculadora_encendida)

        if self.calculadora_encendida:
            self.logo_alpha = 0
            self.logo_fade_in = True
            self.animando_adios = False
            self.pantalla.setEncendida(True)
            self.pantalla.setMostrandoLogo(True, 0, False)
            self.timer_logo.start(50)
        else:
            self.timer_logo.stop()
            self._habilitar_botones(False)
            self.operacion_actual = ""
            self.cursor_pos = 0
            self.resultado_valor = 0

            self.logo_alpha = 0
            self.logo_fade_in = True
            self.animando_adios = True
            self.pantalla.setMostrandoLogo(True, 0, True)
            self.timer_logo.start(50)

        self._actualizar_estado_encendido()

    def _actualizar_estado_encendido(self):
        if hasattr(self, 'btn_encendido'):
            self.btn_encendido.setText(
                "⏼" if self.calculadora_encendida else "⏻"
            )

    def _habilitar_botones(self, estado):
        for btn in self.findChildren(QPushButton):
            if btn.objectName() not in ['btn_encendido', 'btn_cerrar']:
                btn.setEnabled(estado)
        if hasattr(self, 'radio_deg'):
            self.radio_deg.setEnabled(estado)
            self.radio_rad.setEnabled(estado)
            self.check_sonido.setEnabled(estado)

    # ====================================================================
    # INTERFAZ DE USUARIO
    # ====================================================================
    def _init_ui(self):
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(5)
        layout_principal.setContentsMargins(10, 10, 10, 10)

        # --- Barra de título ---
        titulo_layout = QHBoxLayout()
        titulo_layout.setContentsMargins(0, 0, 0, 5)

        self.btn_encendido = QPushButton("⏻")
        self.btn_encendido.setObjectName("btn_encendido")
        self.btn_encendido.setFixedSize(35, 28)
        self.btn_encendido.clicked.connect(self.toggle_encendido)
        self.btn_encendido.setToolTip("Encender/Apagar")

        titulo_label = QLabel("Calculadora Científica")
        titulo_label.setObjectName("titulo_label")
    

        btn_cerrar = QPushButton("✕")
        btn_cerrar.setObjectName("btn_cerrar")
        btn_cerrar.setFixedSize(35, 28)
        btn_cerrar.clicked.connect(self.close)
        btn_cerrar.setToolTip("Cerrar")

        titulo_layout.addWidget(self.btn_encendido)
        titulo_layout.addWidget(titulo_label, 1)
        titulo_layout.addWidget(btn_cerrar)
        layout_principal.addLayout(titulo_layout)

        # --- Pantalla LCD ---
        self.pantalla = PantallaLCD()
        self.pantalla.setFixedHeight(120)
        layout_principal.addWidget(self.pantalla)

        # --- Modo + Sonido + Copiar/Pegar ---
        modo_layout = QHBoxLayout()

        self.radio_deg = QRadioButton("DEG")
        self.radio_rad = QRadioButton("RAD")
        self.radio_deg.setChecked(True)
        self.radio_deg.setObjectName("radio_modo")
        self.radio_rad.setObjectName("radio_modo")
        self.radio_deg.toggled.connect(lambda c: c and self._cambiar_modo("DEG"))
        self.radio_rad.toggled.connect(lambda c: c and self._cambiar_modo("RAD"))

        self.check_sonido = QCheckBox("🔊")
        self.check_sonido.setChecked(True)
        self.check_sonido.setObjectName("check_sonido")
        self.check_sonido.setToolTip("Sonido On/Off")
        self.check_sonido.toggled.connect(self._toggle_sonido)

        modo_layout.addWidget(self.radio_deg)
        modo_layout.addWidget(self.radio_rad)
        modo_layout.addWidget(self.check_sonido)
        modo_layout.addStretch()

        btn_copiar = QPushButton("Copiar")
        btn_copiar.setObjectName("btn_util")
        btn_copiar.setFixedSize(60, 28)
        btn_copiar.clicked.connect(self._copiar_operacion)

        btn_pegar = QPushButton("Pegar")
        btn_pegar.setObjectName("btn_util")
        btn_pegar.setFixedSize(60, 28)
        btn_pegar.clicked.connect(self._pegar_operacion)

        modo_layout.addWidget(btn_copiar)
        modo_layout.addWidget(btn_pegar)
        layout_principal.addLayout(modo_layout)

        # --- Navegación ---
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()

        nav_data = [
            ("|◀", lambda: self.ir_a_posicion(0), "Ir al inicio (Home)"),
            ("◀", lambda: self.mover_cursor(-1), "Mover a la izquierda (Flecha Izq)"),
            ("▶", lambda: self.mover_cursor(1), "Mover a la derecha (Flecha Der)"),
            ("▶|", lambda: self.ir_a_posicion(-1), "Ir al final (End)"),
        ]

        for texto, func, tooltip in nav_data:
            btn = QPushButton(texto)
            btn.setObjectName("btn_nav")
            btn.setFixedSize(55, 32)
            btn.setToolTip(tooltip)
            btn.setAccessibleName(tooltip)
            btn.clicked.connect(func)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        layout_principal.addLayout(nav_layout)

        # --- Botones científicos ---
        grid_cientifico = QGridLayout()
        grid_cientifico.setSpacing(3)

        cientificos = [
            ('sin',  0, 0), ('cos',  0, 1), ('tan',  0, 2), ('log', 0, 3), ('ln',  0, 4),
            ('asin', 1, 0), ('acos', 1, 1), ('atan', 1, 2), ('10ˣ', 1, 3), ('eˣ',  1, 4),
            ('√',    2, 0), ('x²',   2, 1), ('xʸ',   2, 2), ('1/x', 2, 3), ('ⁿ√',  2, 4),
            ('π',    3, 0), ('e',    3, 1), ('x!',   3, 2), ('|x|', 3, 3), ('mod', 3, 4),
        ]

        for texto, fila, col in cientificos:
            btn = QPushButton(texto)
            btn.setObjectName("btn_cientifico")
            btn.setFixedSize(75, 35)
            btn.clicked.connect(
                lambda checked, t=texto: self._click_cientifico(t)
            )
            grid_cientifico.addWidget(btn, fila, col)
        layout_principal.addLayout(grid_cientifico)

        # --- Botones numéricos ---
        grid_numeros = QGridLayout()
        grid_numeros.setSpacing(3)

        botones = [
            ('7', 0, 0), ('8', 0, 1), ('9', 0, 2), ('/', 0, 3), ('C', 0, 4),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2), ('×', 1, 3), ('⌫', 1, 4),
            ('1', 2, 0), ('2', 2, 1), ('3', 2, 2), ('-', 2, 3), ('(', 2, 4),
            ('0', 3, 0), ('.', 3, 1), ('=', 3, 2), ('+', 3, 3), (')', 3, 4),
        ]

        for texto, fila, col in botones:
            btn = QPushButton(texto)
            if texto.isdigit() or texto == '.':
                btn.setObjectName("btn_numero")
            elif texto == '=':
                btn.setObjectName("btn_igual")
                btn.setToolTip("Calcular (Enter)")
                btn.setAccessibleName("Calcular (Enter)")
            elif texto in ['C', '⌫']:
                btn.setObjectName("btn_borrar")
                if texto == 'C':
                    btn.setToolTip("Limpiar todo (Esc)")
                    btn.setAccessibleName("Limpiar todo (Esc)")
                elif texto == '⌫':
                    btn.setToolTip("Borrar (Backspace)")
                    btn.setAccessibleName("Borrar (Backspace)")
            else:
                btn.setObjectName("btn_operador")
            btn.setFixedSize(75, 50)
            btn.clicked.connect(lambda checked, t=texto: self.click_boton(t))
            grid_numeros.addWidget(btn, fila, col)

        layout_principal.addLayout(grid_numeros)
        self.setLayout(layout_principal)

    def _cargar_estilos(self):
        ruta_qss = os.path.join(os.path.dirname(__file__), "calculadora.qss")
        if os.path.exists(ruta_qss):
            with open(ruta_qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _toggle_sonido(self, estado):
        self.sonido_activo = estado
        self.check_sonido.setText("🔊" if estado else "🔇")

    def _cambiar_modo(self, modo):
        self.modo_angulo = modo
        self.pantalla.setModo(self.modo_angulo)

    def _copiar_operacion(self):
        self.reproducir_sonido()
        QApplication.clipboard().setText(self.operacion_actual)

    def _pegar_operacion(self):
        self.reproducir_sonido()
        texto = QApplication.clipboard().text()
        self.operacion_actual = (
            self.operacion_actual[:self.cursor_pos]
            + texto
            + self.operacion_actual[self.cursor_pos:]
        )
        self.cursor_pos += len(texto)
        self._actualizar_pantalla()

    # ====================================================================
    # NAVEGACIÓN DEL CURSOR
    # ====================================================================

    # Elementos que se tratan como unidad atómica al navegar/borrar
    ELEMENTOS_ESPECIALES = [
        'sqrt(', 'sin(', 'cos(', 'tan(', 'log(', 'ln(',
        'asin(', 'acos(', 'atan(', 'abs(', 'factorial(',
        '10**(', 'nthroot('
    ]

    def _obtener_salto(self, pos, direccion):
        """
        Determina cuántos caracteres saltar al mover/borrar.
        Trata funciones como sqrt(, sin(, etc. como unidades atómicas.
        """
        if direccion < 0:
            # Buscar elemento especial ANTES del cursor
            for elem in self.ELEMENTOS_ESPECIALES:
                if pos >= len(elem) and self.operacion_actual[pos - len(elem):pos] == elem:
                    return len(elem)
            # Buscar exponente **(...) o **n
            texto_antes = self.operacion_actual[:pos]
            match = re.search(r'\*\*\d+$', texto_antes)
            if match:
                return len(match.group(0))
            if pos >= 2 and self.operacion_actual[pos - 2:pos] == '**':
                return 2
        else:
            # Buscar elemento especial DESPUÉS del cursor
            for elem in self.ELEMENTOS_ESPECIALES:
                if self.operacion_actual[pos:pos + len(elem)] == elem:
                    return len(elem)
            # Buscar exponente **n
            match = re.match(r'\*\*\d+', self.operacion_actual[pos:])
            if match:
                return len(match.group(0))
            if self.operacion_actual[pos:pos + 2] == '**':
                return 2

        return 1

    def mover_cursor(self, direccion):
        self.reproducir_sonido()
        salto = self._obtener_salto(self.cursor_pos, direccion)
        self.cursor_pos += direccion * salto
        self.cursor_pos = max(0, min(self.cursor_pos, len(self.operacion_actual)))
        self._actualizar_pantalla()

    def ir_a_posicion(self, pos):
        self.reproducir_sonido()
        self.cursor_pos = len(self.operacion_actual) if pos == -1 else 0
        self._actualizar_pantalla()

    # ====================================================================
    # PANTALLA
    # ====================================================================
    def _actualizar_pantalla(self):
        texto_con_cursor = (
            self.operacion_actual[:self.cursor_pos]
            + "|"
            + self.operacion_actual[self.cursor_pos:]
        )
        self.pantalla.setOperacion(texto_con_cursor)
        self.pantalla.setResultado(self.resultado_valor)

    def _insertar_texto(self, texto):
        self.reproducir_sonido()
        self.operacion_actual = (
            self.operacion_actual[:self.cursor_pos]
            + texto
            + self.operacion_actual[self.cursor_pos:]
        )
        self.cursor_pos += len(texto)
        self._actualizar_pantalla()

    def _hay_numero_antes(self):
        """¿Hay un número, ')' o 'π' justo antes del cursor?"""
        if self.cursor_pos == 0:
            return False
        c = self.operacion_actual[self.cursor_pos - 1]
        return c.isdigit() or c in (')', 'π', '.')

    # ====================================================================
    # BOTONES CIENTÍFICOS
    # ====================================================================
    def _click_cientifico(self, texto):
        if texto == 'π':
            self._insertar_texto(str(math.pi))
        elif texto == 'e':
            self._insertar_texto(str(math.e))
        elif texto == '√':
            self._insertar_texto('sqrt(')
        elif texto == 'x²':
            if self._hay_numero_antes():
                self._insertar_texto('**2')
        elif texto == 'xʸ':
            if self._hay_numero_antes():
                self._insertar_texto('**(')
        elif texto == 'ⁿ√':
            self._insertar_texto('nthroot(')
        elif texto == '10ˣ':
            self._insertar_texto('10**(')
        elif texto == 'eˣ':
            self._insertar_texto(f'{math.e}**(')
        elif texto == '1/x':
            self._insertar_texto('1/(')
        elif texto == 'x!':
            if self._hay_numero_antes():
                self._insertar_factorial()
        elif texto == '|x|':
            self._insertar_texto('abs(')
        elif texto == 'mod':
            if self._hay_numero_antes():
                self._insertar_texto('%')
        elif texto in ('sin', 'cos', 'tan', 'log', 'ln',
                       'asin', 'acos', 'atan'):
            self._insertar_texto(texto + '(')

    def _insertar_factorial(self):
        """Envuelve el número anterior en factorial()"""
        self.reproducir_sonido()
        pos = self.cursor_pos - 1
        while pos >= 0 and (
            self.operacion_actual[pos].isdigit()
            or self.operacion_actual[pos] == '.'
        ):
            pos -= 1
        pos += 1

        numero = self.operacion_actual[pos:self.cursor_pos]
        if numero:
            self.operacion_actual = (
                self.operacion_actual[:pos]
                + 'factorial(' + numero + ')'
                + self.operacion_actual[self.cursor_pos:]
            )
            self.cursor_pos = pos + len('factorial(') + len(numero) + 1
            self._actualizar_pantalla()

    # ====================================================================
    # BOTONES NUMÉRICOS Y OPERADORES
    # ====================================================================
    def click_boton(self, texto):
        self.reproducir_sonido()

        if texto.isdigit() or texto == '.':
            self.operacion_actual = (
                self.operacion_actual[:self.cursor_pos]
                + texto
                + self.operacion_actual[self.cursor_pos:]
            )
            self.cursor_pos += 1
            self._actualizar_pantalla()

        elif texto in ('(', ')', '+', '-', '×', '/'):
            real = '*' if texto == '×' else texto
            self.operacion_actual = (
                self.operacion_actual[:self.cursor_pos]
                + real
                + self.operacion_actual[self.cursor_pos:]
            )
            self.cursor_pos += 1
            self._actualizar_pantalla()

        elif texto == '=':
            self._calcular_resultado()

        elif texto == 'C':
            self.operacion_actual = ""
            self.cursor_pos = 0
            self.resultado_valor = 0
            self._actualizar_pantalla()

        elif texto == '⌫':
            self.borrar_elemento()

    def borrar_elemento(self):
        """Borra el elemento completo antes del cursor"""
        if self.cursor_pos == 0:
            return
        self.reproducir_sonido()
        salto = self._obtener_salto(self.cursor_pos, -1)
        self.operacion_actual = (
            self.operacion_actual[:self.cursor_pos - salto]
            + self.operacion_actual[self.cursor_pos:]
        )
        self.cursor_pos -= salto
        self._actualizar_pantalla()

    def borrar_elemento_adelante(self):
        """Borra el elemento completo después del cursor"""
        if self.cursor_pos >= len(self.operacion_actual):
            return
        self.reproducir_sonido()
        salto = self._obtener_salto(self.cursor_pos, 1)
        self.operacion_actual = (
            self.operacion_actual[:self.cursor_pos]
            + self.operacion_actual[self.cursor_pos + salto:]
        )
        self._actualizar_pantalla()

    # ====================================================================
    # MOTOR DE CÁLCULO
    # ====================================================================
    def _normalizar_expresion(self, expr):
        """Normaliza símbolos para que Python pueda evaluar la expresión."""
        superindices = {
            '⁰': '**0',
            '¹': '**1',
            '²': '**2',
            '³': '**3',
            '⁴': '**4',
            '⁵': '**5',
            '⁶': '**6',
            '⁷': '**7',
            '⁸': '**8',
            '⁹': '**9',
        }

        expr = expr.replace('×', '*').replace('÷', '/')
        expr = expr.replace('−', '-').replace('^', '**')

        for sup, potencia in superindices.items():
            expr = expr.replace(sup, potencia)

        return expr

    def _trig(self, fn, x):
        return fn(math.radians(x)) if self.modo_angulo == "DEG" else fn(x)

    def _inv_trig(self, fn, x):
        valor = fn(x)
        return math.degrees(valor) if self.modo_angulo == "DEG" else valor

    def _sin(self, x):
        return self._trig(math.sin, x)

    def _cos(self, x):
        return self._trig(math.cos, x)

    def _tan(self, x):
        return self._trig(math.tan, x)

    def _asin(self, x):
        return self._inv_trig(math.asin, x)

    def _acos(self, x):
        return self._inv_trig(math.acos, x)

    def _atan(self, x):
        return self._inv_trig(math.atan, x)

    @staticmethod
    def _nthroot(x, n):
        return x ** (1 / n)

    def _es_expresion_segura(self, expr):
        """
        Verifica que la expresión sea segura antes de usar eval().
        Utiliza el módulo ast para permitir sólo nodos y funciones matemáticas seguras.
        """
        if len(expr) > 1000:
            return False

        try:
            tree = ast.parse(expr, mode='eval')
        except Exception:
            return False

        nodos_permitidos = {
            'Expression', 'BinOp', 'UnaryOp', 'Add', 'Sub', 'Mult', 'Div',
            'Pow', 'Mod', 'USub', 'UAdd', 'Constant', 'Name', 'Load', 'Call'
        }

        nombres_permitidos = set(self._contexto_evaluacion().keys())

        for nodo in ast.walk(tree):
            if type(nodo).__name__ not in nodos_permitidos:
                return False
            if isinstance(nodo, ast.Name) and getattr(nodo, 'id', None) not in nombres_permitidos:
                return False

        return True

    def _contexto_evaluacion(self):
        """Funciones permitidas para la evaluación segura de expresiones."""
        return {
            'sin': self._sin,
            'cos': self._cos,
            'tan': self._tan,
            'asin': self._asin,
            'acos': self._acos,
            'atan': self._atan,
            'sqrt': math.sqrt,
            'log': math.log10,
            'ln': math.log,
            'factorial': math.factorial,
            'nthroot': self._nthroot,
            'abs': abs,
            'pi': math.pi,
            'e': math.e,
        }

    def _calcular_resultado(self):
        """Evalúa la expresión actual de forma segura"""
        try:
            if not self.operacion_actual.strip():
                return

            expr = self._normalizar_expresion(self.operacion_actual)

            # Auto-cerrar paréntesis faltantes
            parentesis_abiertos = expr.count('(') - expr.count(')')
            if parentesis_abiertos > 0:
                expr += ')' * parentesis_abiertos
                self.operacion_actual = expr
                self.cursor_pos = len(self.operacion_actual)

            # Verificar seguridad con AST antes de evaluar
            if not self._es_expresion_segura(expr):
                raise ValueError("Expresión no permitida")

            # Evaluación segura
            self.resultado_valor = eval(expr, {"__builtins__": {}}, self._contexto_evaluacion())
            self._actualizar_pantalla()

        except ZeroDivisionError:
            self.resultado_valor = "Error: ÷0"
            self._actualizar_pantalla()
        except ValueError as e:
            self.resultado_valor = f"Error: {e}"
            self._actualizar_pantalla()
        except OverflowError:
            self.resultado_valor = "Error: Overflow"
            self._actualizar_pantalla()
        except Exception as e:
            self.resultado_valor = "Error"
            self._actualizar_pantalla()
            print(f"[DEBUG] Error al calcular: {e}")  # Para depuración


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    calculadora = Calculadora()
    calculadora.show()
    sys.exit(app.exec_())