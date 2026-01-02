from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import random


class Starfield(Effect):
    name="Starfield"
    effect_class = "particle_class01"
    def __init__(self,size,spacing_px:int=50):
        super().__init__(size); self.spacing_px=spacing_px; self.points=[]; self._make_points()
    def resize(self,size): super().resize(size); self._make_points()
    def set_spacing(self,spacing_px:int): self.spacing_px=max(10,spacing_px); self._make_points()
    def _make_points(self):
        w,h=self.size.width(),self.size.height(); self.points.clear()
        step=self.spacing_px; jitter=step*0.4; cols=max(1,int(w/step)); rows=max(1,int(h/step))
        for i in range(cols+1):
            for j in range(rows+1):
                x=min(w-1,max(0,i*step+random.uniform(-jitter,jitter)))
                y=min(h-1,max(0,j*step+random.uniform(-jitter,jitter)))
                vx=random.uniform(-15,15); vy=random.uniform(-15,15)
                self.points.append((QPointF(x,y),QPointF(vx,vy)))
    def update(self,dt,e,s,th):
        dt=dt/1000.0; w,h=self.size.width(),self.size.height()
        for i in range(len(self.points)):
            pos,vel=self.points[i]; x=pos.x()+vel.x()*dt; y=pos.y()+vel.y()*dt
            if x<0: x+=w
            if x>=w: x-=w
            if y<0: y+=h
            if y>=h: y-=h
            self.points[i]=(QPointF(x,y),vel)
    def paint(self,p,b):
        p.setPen(QPen(self.color,max(1.0,2*b)))
        for pos,_ in self.points: p.drawPoint(pos)
