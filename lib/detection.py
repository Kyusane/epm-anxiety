from ultralytics import YOLO

class Detector:
     def __init__ (self, confThd = 0.5):
          self.model = YOLO('../models/mouse-yolov8.pt')
          self.confThd = confThd
          self.coordinate = [0,0]
          
     def detect(self, imageFrame):
          results = self.model(imageFrame)
          for object in results[0].boxes :
               x1, y1, x2, y2 = map(int, object.xyxy[0])
               conf = object.conf[0]
               
               if conf < self.confThd :
                    continue
               
               centroid_x = (x1 + x2) // 2
               centroid_y = (y1 + y2) // 2
               self.coordinate = [centroid_x,centroid_y]
          
          return self.coordinate 
     
     
          
          
               
               
          
          
          