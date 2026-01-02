from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect


class ClassicHorizontalScan(Effect):
    name="Classic horizontal scan line"
    effect_class = "centereffect_class05"
    def __init__(self,size): super().__init__(size); self.pos=0.0; self.dir=1
    def update(self,dt,e,s,th):
        self.pos+=self.dir*dt*(0.00015+0.00025*e.get('low',0.0))
        if self.pos>=1.0: self.pos=1.0; self.dir=-1
        elif self.pos<=0.0: self.pos=0.0; self.dir=1
    def paint(self,p,b):
        w,h=self.size.width(),self.size.height(); y=int(self.pos*h)
        p.setPen(QPen(self.color,max(1.0,2*b))); p.drawLine(0,y,w,y)
