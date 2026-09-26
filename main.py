import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QCursor

class MouseFinger(QWidget):
    def __init__(self, image_path='1.png'):
        super().__init__()
        
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 加载图片
        self.pixmap = QPixmap(image_path)
        if self.pixmap.isNull():
            print(f"错误: 无法加载图片 {image_path}")
            sys.exit(1)
        
        # 屏幕尺寸
        self.screen_rect = QApplication.primaryScreen().geometry()
        self.screen_w = self.screen_rect.width()
        self.screen_h = self.screen_rect.height()
        self.setGeometry(0, 0, self.screen_w, self.screen_h)
        
        # 图片缩放（屏幕高度的 30%）
        self.base_size = int(self.screen_h * 0.3)
        self.scaled_pixmap = self.pixmap.scaled(
            self.base_size, self.base_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.img_w = self.scaled_pixmap.width()
        self.img_h = self.scaled_pixmap.height()
        self.current_angle = 0.0
        self.current_pos = QPoint(0, 0)
        
        # 平滑参数（120FPS 下数值可以调大，因为每帧时间更短）
        self.angle_smooth = 0.45
        self.pos_smooth = 0.4
        
        # 鼠标位置
        self.mouse_pos = QPoint(self.screen_w // 2, self.screen_h // 2)
        
        # ============ 主循环：120 FPS（8ms） ============
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_state)
        self.timer.start(16)
        # ================================================
        
        # 初始居中
        self.current_pos = QPoint(
            (self.screen_w - self.img_w) // 2,
            (self.screen_h - self.img_h) // 2
        )
        
        # ============ 鼠标轮询：120 FPS（8ms） ============
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.poll_mouse)
        self.mouse_timer.start(8)
        # =================================================
        
        self.show()
    
    def poll_mouse(self):
        pos = QCursor.pos()
        self.mouse_pos = QPoint(pos.x(), pos.y())
    
    def update_state(self):
        mx, my = self.mouse_pos.x(), self.mouse_pos.y()
        
        # 图片中心到鼠标的距离 = 3像素 + 图片外接圆半径
        GAP = 3
        half = math.hypot(self.img_w, self.img_h) / 2.0
        distance = half + GAP
        
        # 屏幕中心
        center_sx = self.screen_w / 2.0
        center_sy = self.screen_h / 2.0
        
        # 从屏幕中心指向鼠标的方向
        dir_x = mx - center_sx
        dir_y = my - center_sy
        length = math.hypot(dir_x, dir_y)
        
        if length < 1:
            dir_x, dir_y, length = 1.0, 0.0, 1.0
        
        ux = dir_x / length
        uy = dir_y / length
        
        # 图片中心 = 鼠标 + 方向 * 距离
        img_cx = mx + ux * distance
        img_cy = my + uy * distance
        
        # 允许穿出屏幕约 78 像素
        OUT = 78
        img_cx = max(-OUT, min(self.screen_w + OUT, img_cx))
        img_cy = max(-OUT, min(self.screen_h + OUT, img_cy))
        
        # 目标左上角
        target_x = img_cx - self.img_w / 2
        target_y = img_cy - self.img_h / 2
        
        # 平滑移动
        cur_x = self.current_pos.x() + (target_x - self.current_pos.x()) * self.pos_smooth
        cur_y = self.current_pos.y() + (target_y - self.current_pos.y()) * self.pos_smooth
        self.current_pos = QPoint(int(cur_x), int(cur_y))
        
        # 计算指向鼠标的角度
        dx = mx - img_cx
        dy = my - img_cy
        target_angle = math.degrees(math.atan2(dy, dx)) + 90
        
        # 最短路径角度平滑
        angle_diff = target_angle - self.current_angle
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        self.current_angle += angle_diff * self.angle_smooth
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        cx = self.current_pos.x() + self.img_w / 2
        cy = self.current_pos.y() + self.img_h / 2
        
        painter.translate(cx, cy)
        painter.rotate(self.current_angle)
        painter.translate(-self.img_w / 2, -self.img_h / 2)
        painter.drawPixmap(0, 0, self.scaled_pixmap)
    
    def closeEvent(self, event):
        self.timer.stop()
        self.mouse_timer.stop()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    finger = MouseFinger('1.png')
    
    print("程序已启动！")
    print("- 120 FPS")
    print("- 按 Ctrl+C 退出")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
