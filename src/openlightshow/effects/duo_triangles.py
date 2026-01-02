from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from PySide6.QtGui import QPolygonF
from ..effect_base import Effect
import math


class DuoTriangles(Effect):
    name="Duo triangles"
    effect_class = "centereffect_class06"
    def __init__(self,size): super().__init__(size); self.angle=0.0
    def update(self,dt,e,s,th): self.angle+=(dt/1000.0)*0.5
    def paint(self,p,b):
        w,h=self.size.width(),self.size.height(); r=(w/3.0)/2.0; spacing=w/4.0
        centers=[QPointF(w/2.0-spacing,h/2.0),QPointF(w/2.0+spacing,h/2.0)]
        p.setPen(QPen(self.color,max(1.0,2*b)))
        for c in centers:
            pts=[QPointF(c.x()+r*math.cos(self.angle+i*2*math.pi/3),
                         c.y()+r*math.sin(self.angle+i*2*math.pi/3)) for i in range(3)]
            p.drawPolygon(QPolygonF(pts))
