from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math


class ScannerWindmill(Effect):
    name="Scanner windmill"
    effect_class = "centereffect_class01"
    def __init__(self,size): super().__init__(size); self.angle=0.0; self.dir=1
    def on_beat(self): super().on_beat(); self.dir*=-1
    def update(self,dt,e,s,th):
        self.angle+=self.dir*(dt/1000.0)*(0.8+2.2*s*e.get('high',0.0)); self.angle%=2*math.pi
    def paint(self,p,b):
        p.setPen(QPen(self.color,max(1.0,3*b)))
        w,h=self.size.width(),self.size.height(); cx,cy=w/2,h/2; L=math.hypot(w,h)
        ex=cx+math.cos(self.angle)*L; ey=cy+math.sin(self.angle)*L
        sx=cx-math.cos(self.angle)*L; sy=cy-math.sin(self.angle)*L
        p.drawLine(int(sx),int(sy),int(ex),int(ey))
