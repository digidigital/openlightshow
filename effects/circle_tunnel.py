from PySide6.QtCore import QPointF
from PySide6.QtCore import QRectF
from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import random


class CircleTunnel(Effect):
    name="Circle tunnel"
    effect_class = "centereffect_class03"
    def __init__(self,size):
        super().__init__(size)
        self.center=QPointF(size.width()/2,size.height()/2)
        self.radius=min(size.width(),size.height())*0.25
        self.target=QPointF(self.center); self.speed=0.25
    def on_beat(self):
        super().on_beat()
        max_r=min(self.size.width(),self.size.height())*0.5
        self.radius=random.uniform(max_r*0.1,max_r*0.5)
        m=self.radius
        self.target=QPointF(random.uniform(m,self.size.width()-m),
                            random.uniform(m,self.size.height()-m))
    def update(self,dt,e,s,th):
        mid=e.get('mid',0.0); alpha=min(1.0,(dt/1000.0)*(self.speed+mid*s))
        self.center.setX(self.center.x()+(self.target.x()-self.center.x())*alpha)
        self.center.setY(self.center.y()+(self.target.y()-self.center.y())*alpha)
        self.radius*=1.0+0.02*(e.get('low',0.0)-0.5)
        self.radius=max(10.0,min(self.radius,min(self.size.width(),self.size.height())*0.5))
        cx=min(max(self.center.x(),self.radius),self.size.width()-self.radius)
        cy=min(max(self.center.y(),self.radius),self.size.height()-self.radius)
        self.center=QPointF(cx,cy)
    def paint(self,p,b):
        p.setPen(QPen(self.color,max(1.0,2*b)))
        r=self.radius; c=self.center
        p.drawEllipse(QRectF(c.x()-r,c.y()-r,2*r,2*r))
