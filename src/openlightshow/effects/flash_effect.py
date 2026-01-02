from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from ..effect_base import Effect
import time


class FlashEffect(Effect):
    name="Flash"
    effect_class = "flash_class01"
    def __init__(self,size): super().__init__(size); self.flash_alpha=0.0; self.last_flash_ms=0; self.cooldown_ms=5000
    def update(self,dt,e,s,th):
        now=int(time.time()*1000)
        if e.get('high',0.0)>th and (now-self.last_flash_ms)>=self.cooldown_ms:
            self.flash_alpha=0.25; self.last_flash_ms=now
        self.flash_alpha=max(0.0,self.flash_alpha-(dt/1000.0)*2.0)
    def paint(self,p,b):
        if self.flash_alpha>0.0:
            overlay=QColor(255,255,255,int(255*self.flash_alpha))
            p.fillRect(0,0,self.size.width(),self.size.height(),overlay)
