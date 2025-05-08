import cv2, time

from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal
class VideoExportThread(QThread):
     progress_update = pyqtSignal(int)  # Sinyal untuk update progress

     def __init__(self, records, filename, w, h, fps):
          super().__init__()
          self.records = records
          self.filename = filename
          self.fps = fps
          self.width = w
          self.height = h

     def run(self):
          if not self.records:
               self.progress_update.emit(100)
               return

          frame_width = self.width
          frame_height = self.height
          fourcc = cv2.VideoWriter_fourcc(*'MJPG')
          video_output = cv2.VideoWriter(
               f'{self.filename}_record.avi',
               fourcc,
               self.fps,
               (frame_width, frame_height)
          )

          total_frames = len(self.records)
          for i, frame in enumerate(self.records):
               if frame is None:
                    continue
               frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
               video_output.write(frame)
               progress = int(((i + 1) / total_frames) * 100)
               self.progress_update.emit(progress)

          video_output.release()
          self.progress_update.emit(100)  # Kirim 100% setelah selesai

class VideoRecorder:
     def __init__(self, parents):
          self.records = []
          self.parents = parents
          self.frame_w = None
          self.frame_h = None
          self.last_time = time.time()
          self.fps = 20

     def update(self, record):
          current_time = time.time()
          if current_time-self.last_time >= int(1/self.fps):
               self.records.append(record)
          
     def define_shape(self, w, h):
          self.frame_w = w
          self.frame_h = h
     
     def start_export(self, filename):
          self.progress_dialog = QProgressDialog("Exporting video...", "Cancel", 0, 100, self.parents)
          self.progress_dialog.setWindowTitle("Exporting")
          self.progress_dialog.setWindowModality(True)
          self.progress_dialog.setAutoClose(True)
          self.progress_dialog.setValue(0)

          # Jalankan proses ekspor di thread terpisah
          self.export_thread = VideoExportThread(self.records, filename, self.frame_w, self.frame_h, self.fps)
          self.export_thread.progress_update.connect(self.progress_dialog.setValue)
          self.export_thread.start()

          # Menutup progress dialog jika selesai
          self.export_thread.finished.connect(self.progress_dialog.close)
          self.records = []