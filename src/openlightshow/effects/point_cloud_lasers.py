from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math
import random


class PointCloudLasers(Effect):
    name="Point cloud lasers"
    effect_class = "particle_class01"
    def __init__(self,size):
        super().__init__(size)
        self.points=[QPointF(random.uniform(0,size.width()),random.uniform(0,size.height())) for _ in range(180)]
        self.angle=0.0
    def on_beat(self): super().on_beat(); self.angle+=random.uniform(-0.3,0.3)
    def update(self,dt,e,s,th):
        dt=dt/1000.0; self.angle+=dt*(0.5+e.get('high',0.0)*s); ca,sa=math.cos(self.angle),math.sin(self.angle)
        cx,cy=self.size.width()/2,self.size.height()/2; new=[]
        for p in self.points:
            dx,dy=p.x()-cx,p.y()-cy
            x=cx+dx*ca-dy*sa; y=cy+dx*sa+dy*ca
            if x<0: x+=self.size.width()
            if x>self.size.width(): x-=self.size.width()
            if y<0: y+=self.size.height()
            if y>self.size.height(): y-=self.size.height()
            new.append(QPointF(x,y))
        self.points=new
    def paint(self,p,b):
        p.setPen(QPen(self.color,max(1.0,2*b)))
        for pt in self.points: p.drawPoint(pt)
