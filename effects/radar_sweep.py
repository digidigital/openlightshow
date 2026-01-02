from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math


class RadarSweep(Effect):
    name="Radar sweep"
    effect_class = "centereffect_class01"
    def __init__(self,size): super().__init__(size); self.angle=0.0; self.dir=1
    def on_beat(self): super().on_beat(); self.dir*=-1
    def update(self,dt,e,s,th):
        self.angle+=self.dir*(dt/1000.0)*(1.0+2.0*s*e.get('mid',0.0)); self.angle%=2*math.pi
    def paint(self,p,b):
        p.setPen(QPen(self.color,max(1.0,3*b)))
        w,h=self.size.width(),self.size.height(); cx,cy=w/2,h/2
        dx,dy=math.cos(self.angle),math.sin(self.angle); candidates=[]
        if dx!=0: candidates+=[(0-cx)/dx,(w-cx)/dx]
        if dy!=0: candidates+=[(0-cy)/dy,(h-cy)/dy]
        t=[t for t in candidates if t>0]
        if t:
            tmin=min(t); x=cx+dx*tmin; y=cy+dy*tmin
            p.drawLine(int(cx),int(cy),int(x),int(y))
