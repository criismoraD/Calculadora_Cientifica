## 2024-05-14 - PyQt5 Render Loop Optimization
**Learning:** Found string operations and regex compilations happening inside the PyQt5 `paintEvent` which gets called on every frame update.
**Action:** Always inspect `paintEvent` or render loop methods for heavy, repetitive calculations that can be cached instead of recomputed during rendering. Pre-compile regexes in class scope.
