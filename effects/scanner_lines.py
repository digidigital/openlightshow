from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect


class ScannerLines(Effect):
    name = "Scanner lines"
    effect_class = "effect_class32"
    def __init__(self, size): super().__init__(size); self.pos=0.0; self.vertical=True
    def on_beat(self): super().on_beat(); self.vertical=not self.vertical
    def update(self, dt, e, s, th): self.pos=(self.pos+dt*(0.0009+s*0.0006*e.get('low',0.0)))%1.0
    def paint(self, p, b):
        p.save()
        w,h=self.size.width(),self.size.height()
        p.setPen(QPen(self.color,max(1.0,2*b)))
        if self.vertical: p.drawLine(0,int(self.pos*h),w,int(self.pos*h))
        else: p.drawLine(int(self.pos*w),0,int(self.pos*w),h)
        p.restore()
