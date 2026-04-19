import sys
import unittest
from unittest.mock import MagicMock
import ast

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
    def setFocusPolicy(self, *args, **kwargs):
        pass
    def update(self, *args, **kwargs):
        pass
    def setLayout(self, *args, **kwargs):
        pass
    def findChildren(self, *args, **kwargs):
        return []

mock_qt = MagicMock()
sys.modules['PyQt5'] = mock_qt
sys.modules['PyQt5.QtWidgets'] = mock_qt
sys.modules['PyQt5.QtCore'] = mock_qt
sys.modules['PyQt5.QtGui'] = mock_qt
sys.modules['PyQt5.QtMultimedia'] = mock_qt

mock_qt.QWidget = MockQWidget
mock_qt.QtWidgets.QWidget = MockQWidget

import Calculadora

class TestEsExpresionSegura(unittest.TestCase):
    def setUp(self):
        class MinimalCalc:
            def _contexto_evaluacion(self):
                return {
                    'sin': None, 'cos': None, 'tan': None, 'asin': None,
                    'acos': None, 'atan': None, 'sqrt': None, 'log': None,
                    'ln': None, 'factorial': None, 'nthroot': None,
                    'abs': None, 'pi': None, 'e': None
                }

        self.calc = MinimalCalc()
        self.calc._es_expresion_segura = Calculadora.Calculadora._es_expresion_segura.__get__(self.calc, MinimalCalc)

    def test_happy_paths(self):
        self.assertTrue(self.calc._es_expresion_segura("1 + 1"))
        self.assertTrue(self.calc._es_expresion_segura("sin(1) * cos(pi)"))
        self.assertTrue(self.calc._es_expresion_segura("sqrt(16) + abs(-5)"))
        self.assertTrue(self.calc._es_expresion_segura("2**3 + 5%2"))

    def test_edge_cases_length(self):
        long_expr = "1+" * 501 # 1002 characters
        self.assertFalse(self.calc._es_expresion_segura(long_expr))

        limit_expr = "1+" * 499 + "1" # 999 characters
        self.assertTrue(self.calc._es_expresion_segura(limit_expr))

    def test_edge_cases_invalid_syntax(self):
        self.assertFalse(self.calc._es_expresion_segura("1 + +"))
        self.assertFalse(self.calc._es_expresion_segura("sin(1"))

    def test_security_disallowed_nodes(self):
        # Attribute access
        self.assertFalse(self.calc._es_expresion_segura("math.sqrt(4)"))
        # List
        self.assertFalse(self.calc._es_expresion_segura("[1, 2, 3]"))
        # Import (not possible in 'eval' mode usually, but good to check if someone changes it)
        # In 'eval' mode, 'import' is a syntax error anyway.

    def test_security_disallowed_names(self):
        self.assertFalse(self.calc._es_expresion_segura("eval('1+1')"))
        self.assertFalse(self.calc._es_expresion_segura("exec('1+1')"))
        self.assertFalse(self.calc._es_expresion_segura("__import__('os').system('ls')"))
        self.assertFalse(self.calc._es_expresion_segura("open('test.txt')"))

if __name__ == '__main__':
    unittest.main()
