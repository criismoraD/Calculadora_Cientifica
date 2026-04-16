import sys
from unittest.mock import MagicMock

# Mocking PyQt5 to avoid GUI dependencies
class MockQWidget:
    def __init__(self, *args, **kwargs):
        pass
    def setWindowFlags(self, *args, **kwargs):
        pass
    def setAttribute(self, *args, **kwargs):
        pass
    def setWindowTitle(self, *args, **kwargs):
        pass
    def setFixedSize(self, *args, **kwargs):
        pass
    def setMinimumHeight(self, *args, **kwargs):
        pass
    def setFixedHeight(self, *args, **kwargs):
        pass
    def setFocusPolicy(self, *args, **kwargs):
        pass
    def update(self, *args, **kwargs):
        pass
    def rect(self):
        return MagicMock()
    def width(self):
        return 420
    def height(self):
        return 720
    def setLayout(self, *args, **kwargs):
        pass
    def findChildren(self, *args, **kwargs):
        return []
    def close(self):
        pass
    def show(self):
        pass
    def setContentsMargins(self, *args, **kwargs):
        pass
    def setSpacing(self, *args, **kwargs):
        pass
    def addWidget(self, *args, **kwargs):
        pass
    def addLayout(self, *args, **kwargs):
        pass
    def addStretch(self, *args, **kwargs):
        pass
    def setObjectName(self, *args, **kwargs):
        pass
    def setToolTip(self, *args, **kwargs):
        pass
    def setAccessibleName(self, *args, **kwargs):
        pass
    def setChecked(self, *args, **kwargs):
        pass
    def setEnabled(self, *args, **kwargs):
        pass
    def styleSheet(self):
        return ""
    def setStyleSheet(self, *args, **kwargs):
        pass

mock_qt = MagicMock()
sys.modules['PyQt5'] = mock_qt
sys.modules['PyQt5.QtWidgets'] = mock_qt
sys.modules['PyQt5.QtCore'] = mock_qt
sys.modules['PyQt5.QtGui'] = mock_qt
sys.modules['PyQt5.QtMultimedia'] = mock_qt

# Important: set the mock classes before importing Calculadora
mock_qt.QWidget = MockQWidget
mock_qt.QtWidgets.QWidget = MockQWidget

# Now I can import Calculadora
import Calculadora
import unittest

class TestNormalizarExpresion(unittest.TestCase):
    def setUp(self):
        # I will create a minimal instance to test _normalizar_expresion
        # because the full Calculadora init is hard to mock correctly
        class MinimalCalc:
            pass
        self.calc = MinimalCalc()
        # Bind the method from the module
        self.calc._normalizar_expresion = Calculadora.Calculadora._normalizar_expresion.__get__(self.calc, MinimalCalc)

    def test_basic_operators(self):
        self.assertEqual(self.calc._normalizar_expresion("2×3"), "2*3")
        self.assertEqual(self.calc._normalizar_expresion("6÷2"), "6/2")
        self.assertEqual(self.calc._normalizar_expresion("5−3"), "5-3")
        self.assertEqual(self.calc._normalizar_expresion("2^3"), "2**3")

    def test_superindices(self):
        self.assertEqual(self.calc._normalizar_expresion("x⁰"), "x**0")
        self.assertEqual(self.calc._normalizar_expresion("x¹"), "x**1")
        self.assertEqual(self.calc._normalizar_expresion("x²"), "x**2")
        self.assertEqual(self.calc._normalizar_expresion("x³"), "x**3")
        self.assertEqual(self.calc._normalizar_expresion("x⁴"), "x**4")
        self.assertEqual(self.calc._normalizar_expresion("x⁵"), "x**5")
        self.assertEqual(self.calc._normalizar_expresion("x⁶"), "x**6")
        self.assertEqual(self.calc._normalizar_expresion("x⁷"), "x**7")
        self.assertEqual(self.calc._normalizar_expresion("x⁸"), "x**8")
        self.assertEqual(self.calc._normalizar_expresion("x⁹"), "x**9")

    def test_complex_expression(self):
        expr = "2×(3+4)²−5÷2"
        # Expected: 2*(3+4)**2-5/2
        self.assertEqual(self.calc._normalizar_expresion(expr), "2*(3+4)**2-5/2")

    def test_no_change(self):
        self.assertEqual(self.calc._normalizar_expresion("2*3+4**2"), "2*3+4**2")

if __name__ == '__main__':
    unittest.main()
