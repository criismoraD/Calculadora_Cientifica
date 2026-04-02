# Calculadora Cientifica con PyQt5

Resumen del proyecto: aplicacion de escritorio con interfaz estilo LCD, funciones cientificas, sonidos y animacion de encendido/apagado.

## Objetivo 🎯

Crear una calculadora cientifica visualmente atractiva y funcional para operaciones comunes y avanzadas, con soporte de:

- Modo angular DEG/RAD
- Trigonometria directa e inversa
- Potencias, raices, factorial y modulo
- Interfaz personalizada con QSS
- Audio de interaccion y estado

## Capturas 🖼️

![Interfaz principal](img1.png)
![Operacion de ejemplo](img2.png)

## Funcionalidades principales ⚙️

- Operaciones basicas: suma, resta, multiplicacion y division
- Funciones cientificas: sin, cos, tan, asin, acos, atan, log, ln, sqrt, factorial, nthroot
- Formato visual: superindices y fracciones en pantalla LCD
- Utilidades: copiar/pegar, navegacion por cursor, encendido/apagado

## Estructura del proyecto 📁

- Calculadora.py: aplicacion principal
- calculadora.qss: estilos visuales
- PRENDER.mp3, APAGAR.mp3, click.wav: recursos de audio
- img1.png, img2.png: imagenes de documentacion

## Requisitos 📦

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecucion en modo desarrollo ▶️

```bash
python Calculadora.py
```

## Compilacion a EXE 🛠️

### Opcion A: Carpeta con EXE + dependencias (recomendada)

```bash
python -m PyInstaller --noconfirm --windowed --name Calculadora --add-data "calculadora.qss;." --add-data "PRENDER.mp3;." --add-data "APAGAR.mp3;." --add-data "click.wav;." Calculadora.py
```

Salida:

- dist/Calculadora/Calculadora.exe

### Opcion B: Un solo archivo EXE (onefile)

```bash
python -m PyInstaller --noconfirm --onefile --windowed --name Calculadora_OneFile --add-data "calculadora.qss;." --add-data "PRENDER.mp3;." --add-data "APAGAR.mp3;." --add-data "click.wav;." Calculadora.py
```

Salida:

- dist/Calculadora_OneFile.exe

## Observaciones ✅

- Si quieres maxima compatibilidad de audio/multimedia, la opcion de carpeta suele ser mas estable.
- Si prefieres distribuir un unico archivo, la opcion onefile ya esta generada y es funcional.
