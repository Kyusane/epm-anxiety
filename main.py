from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from PyQt5.uic import loadUi

from lib.detection import Detector
from lib.tracking import Trajectory , AKFTracker
from lib.counting import Counter
from lib.recorder import VideoRecorder
from lib.utils import strToSecond, secondToStr
import cv2, sys, random, numpy as np, time, os
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

DEFAULT_INDEX = config.getint("Camera","default_index")
USE_DSHOW = config.getboolean("Camera","use_dshow")
MAX_CAMERAS = config.getint("Camera","max_cameras")
FRAME_SKIP_INV = config.getint("Tracker","interval")
SHOW_FPS = config.getboolean("Evaluate","show_fps")
USE_POINT = config.getboolean("Trajectory","use_point")
TRACKER = AKFTracker()


class EpmUI(QMainWindow):
     def __init__(self, datas, parent = None):
          super(EpmUI, self).__init__()

          loadUi("epm_responsive.ui", self)
          self.parent = parent 
          self.testDescription = datas
          self.setWindowTitle(f"Elevated Plus Maze - {datas.get('title', 'EPM_X')}")
          self.timer_display.setText(secondToStr(self.testDescription["duration"]))
          self.timer_display.setStyleSheet("""
               font-size: 18pt;
               font-weight: bold;
               color: white;
               background-color: #3B4252;
               border: 1px solid #4C566A;
               border-radius: 5px;
          """)
          self.timer_display.setAlignment(Qt.AlignCenter)

          self.cap = None
          self.interval = FRAME_SKIP_INV
          self.regions = []
          self.timer = QTimer()
          self.detector = Detector()
          self.tracker = TRACKER
          self.counter = Counter(self.regions)
          self.trajectory = Trajectory()
          self.recorder = VideoRecorder(self)
          self.timer.timeout.connect(self.update_frame)
          
          self.frameCount = 0
          self.frame = None
          self.frame_source = None
          self.frame_trajectory = None
          self.count_start_time = None
          
          # Variabel evaluasi fps
          self.eval_start_time = 0
          self.eval_fps = 0
          self.eval_fps_sum = 0
          self.eval_fps_count = 0
          self.eval_fps_avg = 0
          
          # Mendeteksi Kamera yang Tersedia
          self.detect_cameras()

          # Event saat memilih kamera
          self.comboBox_Camera.currentIndexChanged.connect(self.start_video)
          self.pushButton_R.clicked.connect(lambda: self.selectRegionHandler("Right"))
          self.pushButton_L.clicked.connect(lambda: self.selectRegionHandler("Left"))
          self.pushButton_T.clicked.connect(lambda: self.selectRegionHandler("Top"))
          self.pushButton_B.clicked.connect(lambda: self.selectRegionHandler("Bottom"))
          self.pushButton_start.clicked.connect(self.runCount)
          self.pushButton_select_video.clicked.connect(self.start_file)
          
          self.FLAG_ANALYZE = False
          self.start_video()
          
     def selectRegionHandler(self, position):
          """
          Memilih region counting
          """
          if self.cap and self.cap.isOpened():
               try:
                    region = cv2.selectROI("Select Region", self.frame, showCrosshair=True, fromCenter=False)
                    cv2.destroyWindow("Select Region")
                    
                    # Jika ROI dibatalkan atau semua nilai 0
                    if region == (0, 0, 0, 0):
                         return
                    
                    region_data = {
                         "position": position,
                         "bbox": region,
                         "color": (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    }
                    
                    self.counter.update_region(region_data)
                    self.regions = self.counter.regions
               
               except cv2.error:
                    cv2.destroyAllWindows()
                    return
          else:
               QMessageBox.warning(self, "Error", "Tolong pilih sumber video")
             
     def detect_cameras(self):
          """
          Deteksi daftar kamera yang tersedia dan masukkan ke ComboBox
          """
          self.comboBox_Camera.clear()
          available_cameras = []

          for i in range(MAX_CAMERAS):
               if USE_DSHOW:
                    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
               else:
                    cap = cv2.VideoCapture(i)

               if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                         available_cameras.append(f"Camera {i}")
                    cap.release()
               else:
                    cap.release()

          if available_cameras:
               self.comboBox_Camera.addItems(available_cameras)
               self.comboBox_Camera.setCurrentIndex(DEFAULT_INDEX)
          else:
               self.comboBox_Camera.addItem("No Camera Found")
                         
     def start_file(self):
          """
          Memulai Video menggunakan file
          """
          cv2.destroyAllWindows()
          if self.cap:
               self.cap.release()

          file_path, _ = QFileDialog.getOpenFileName(None, "Pilih file video", "", "Video Files (*.mp4 *.avi *.mov)")
          if file_path:
               self.pushButton_select_video.setText(file_path)
               self.cap = cv2.VideoCapture(file_path)

               if self.cap.isOpened():
                    self.timer.start(30) 
                    self.video_status.setText(f"File Video Running")
                    self.frame_source = "file"
               else:
                    QMessageBox.warning(self, "Error", "Gagal membuka file video!")
          
          self.frameCount = 0 

     def start_video(self):
          """
          Memulai Video menggunakan camera (Real-time)
          """
          cv2.destroyAllWindows()
          if self.cap:
               self.cap.release() 

          selected_index = self.comboBox_Camera.currentIndex()
          if selected_index == -1:
               return

          camera_index = int(self.comboBox_Camera.currentText().split()[-1])
          
          if USE_DSHOW:
               self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
          else:     
               self.cap = cv2.VideoCapture(camera_index)
               
          self.recorder.define_shape(int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

          if self.cap.isOpened():
               self.timer.start(30) 
               self.video_status.setText(f"Camera {camera_index} Running")
               self.frame_source = "camera"
          else:
               QMessageBox.warning(self, "Error", "Gagal membuka kamera!")
          self.frameCount = 0
          

     def stop_video(self):
          """
          Hentikan streaming video
          """
          if self.cap and self.cap.isOpened():
               self.timer.stop()
               self.cap.release()
               self.label_Frame1.clear()
               self.Label_status.setText("Video Stopped")
     
     def update_results(self):
          """
          Mengubah data hasil analisis
          """
          result = self.counter.results
          for position in result:
               if position == "Right":
                    self.Result_RC.setText(str(result[position]["total_entry"]))
                    self.Result_RT.setText(str(result[position]["total_time"]))
               if position == "Left":
                    self.Result_LC.setText(str(result[position]["total_entry"]))
                    self.Result_LT.setText(str(result[position]["total_time"]))
               if position == "Top":
                    self.Result_TC.setText(str(result[position]["total_entry"]))
                    self.Result_TT.setText(str(result[position]["total_time"]))
               if position == "Bottom":
                    self.Result_BC.setText(str(result[position]["total_entry"]))
                    self.Result_BT.setText(str(result[position]["total_time"]))
          
          self.Label_status.setText(str(self.counter.stress_stats))
          self.Label_status.setStyleSheet("""
               font-size: 16pt;
               font-weight: bold;
               color: white;
               background-color: #3B4252;
               border: 1px solid #4C566A;
               border-radius: 5px;
               padding: 5px;
          """)
          self.Label_status.setAlignment(Qt.AlignCenter)
          
     def preproc_frame(self, frame):
          """
          Menyesuaikan ukuran frame video agar sesuai dengan ukuran canvas
          Parameter : 
               frame : frame video mentah
          
          return frame : frame video yang disesuaikan
          """
          # Ambil ukuran canvas dari QLabel atau QWidget
          canvas_width = self.label_Frame1.width()
          canvas_height = self.label_Frame1.height()
          frame_height, frame_width = frame.shape[:2]

          # Resize frame sambil mempertahankan aspek rasio
          aspect_ratio_frame = frame_width / frame_height
          aspect_ratio_canvas = canvas_width / canvas_height

          if aspect_ratio_frame > aspect_ratio_canvas:
               # Frame lebih lebar dari canvas
               new_width = canvas_width
               new_height = int(canvas_width / aspect_ratio_frame)
          else:
               # Frame lebih tinggi dari canvas
               new_height = canvas_height
               new_width = int(canvas_height * aspect_ratio_frame)

          # Resize frame
          frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
          return frame

     def update_frame(self):
          """
               Update tampilan video ke QLabel.
          """
          if self.cap:
               ret, frame = self.cap.read()
               if ret:
                    frame = cv2.resize(frame, (800, 600))
                    # Evaluate FPS
                    if self.frameCount == 0 :
                         self.eval_start_time == time.time()
                    
                    if self.frameCount <= 20:
                         self.frame = frame
                    
                    if self.frameCount <= self.interval or self.frameCount % self.interval == 0:
                         results = self.detector.detect(frame)
                         self.tracker.update(results)
               
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    if self.FLAG_ANALYZE:
                         if self.frame_source == "camera":
                              self.recorder.update(frame)
                         coordinate = self.tracker.predict()
                         cv2.circle(frame,(coordinate[0],coordinate[1]), 5, (0,0,255),-1)
                         self.counter.update([coordinate[0],coordinate[1]])
                         self.update_results()
                         self.trajectory.add(coordinate)
                         self.display_timer()  
                    
                    for reg in self.regions :
                         if reg["bbox"]:
                              x, y, w, h = reg["bbox"]
                              cv2.rectangle(frame, (x,y), (x + w, y + h), reg["color"], 2)
                              
                    if SHOW_FPS :          
                         cv2.putText(frame, f"FPS         : {self.eval_fps:.2f}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                         cv2.putText(frame, f"FPS Average : {self.eval_fps_avg:.2f}", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                    
                    frame = self.preproc_frame(frame)     
                    h, w, ch = frame.shape
                    bytes_per_line = ch * w
                    q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    self.label_Frame1.setPixmap(QPixmap.fromImage(q_img))
                    self.trajectory_frame((h, w, ch)) 
                    
                    # Evaluating FPS
                    if SHOW_FPS:
                         if self.frameCount % 10 == 0 and self.frameCount > 0:
                              current_time = time.time()
                              elapsed_time = current_time - self.eval_start_time
                              self.eval_fps = 1/(elapsed_time/10)
                              self.eval_fps_sum += self.eval_fps
                              self.eval_fps_count +=1
                              self.eval_fps_avg = self.eval_fps_sum / self.eval_fps_count
                              self.eval_start_time = current_time

                    self.frameCount += 1
                    
     def runCount(self):
          """
               Memulai analisis
          """
          if self.cap and self.cap.isOpened():
               self.counter.reset()
               self.trajectory.reset()
               self.count_start_time = time.time()
               self.FLAG_ANALYZE = True
          else:
               QMessageBox.warning(self, "Peringatan", "Tolong pilih sumber video")
          
     def stopCount(self):
          """
               Menghentikan analisis, menyimpan hasil, dan memberikan notifikasi kepada pengguna.
          """
          self.count_start_time = None
          self.FLAG_ANALYZE = False

          try:
               timestamp = time.strftime("%H-%M-%S", time.localtime())
               unique_fn = f"{self.testDescription['title'].replace(' ', '_')}_{timestamp}"
               output_path = f"{self.testDescription['output_path']}/{unique_fn}"

               os.makedirs(output_path, exist_ok=True)

               self.counter.save2txt(f"{output_path}/{unique_fn}_summary.txt",self.testDescription)
               self.trajectory.save2jpg(f"{output_path}/{unique_fn}",self.frame_trajectory)

               if self.frame_source == "camera":
                    self.recorder.start_export(f"{output_path}/{unique_fn}")

               QMessageBox.information(self, "Status", "Pengujian selesai, memulai menyimpan hasil ... ")

          except Exception as e:
               QMessageBox.critical(self, "Error", f"Gagal menyimpan hasil: {str(e)}")
          
                    
     def display_timer(self):
          """
               Menampilkan timer 
          """
          current_time = time.time()
          elapsed_time = int(current_time - self.count_start_time)
          remaining_time = self.testDescription["duration"] - elapsed_time

          if remaining_time < 0:
               remaining_time = 0
               self.stopCount() 

          minutes = remaining_time // 60
          seconds = remaining_time % 60 

          str_time = f"{minutes:02}:{seconds:02}"
          self.timer_display.setText(str(str_time))
          self.timer_display.setStyleSheet("""
               font-size: 18pt;
               font-weight: bold;
               color: white;
               background-color: #3B4252;
               border: 1px solid #4C566A;
               border-radius: 5px;
          """)
          self.timer_display.setAlignment(Qt.AlignCenter)
          
               
     def trajectory_frame(self, shape):
          """
               Menampilkan Trajectory
          """
          black_screen = np.zeros(shape, dtype=np.uint8)
          
          if USE_POINT:
               for i in range(len(self.trajectory.history)):
                    point = self.trajectory.history[i]
                    cv2.circle(black_screen,(point[0],point[1]), 2, (0,0,255),-1)
          else :
               for i in range(len(self.trajectory.history) - 1):
                    start_point = tuple(self.trajectory.history[i])
                    end_point = tuple(self.trajectory.history[i + 1])
                    cv2.line(black_screen, start_point, end_point, (0, 0, 255), thickness=2)
          
          frame_track = cv2.resize(black_screen, (300, 300), interpolation=cv2.INTER_LINEAR)
          frame_track_rgb = cv2.cvtColor(frame_track, cv2.COLOR_BGR2RGB)
          self.frame_trajectory = frame_track_rgb

          h, w, ch = frame_track_rgb.shape
          bytes_per_line = ch * w
          q_img = QImage(frame_track_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
          self.label_Frame2.setPixmap(QPixmap.fromImage(q_img))
                  
     def closeEvent(self, event):
          """
               Pastikan kamera dilepas saat aplikasi ditutup.
          """
          self.stop_video()
          if self.parent:
               self.parent.show()
          event.accept()
          
          
class EpmFormUI(QMainWindow):
     def __init__(self):
          super(EpmFormUI,self).__init__()
          loadUi("epm_form.ui", self)
          self.pushButton_submit.clicked.connect(self.open_epm_window)
          self.pushButton_output_location.clicked.connect(self.select_out_path)

     def open_epm_window(self):
          """
               Membuka window Elevated Plus Maze
          """
          title = self.test_name.toPlainText().strip()
          date = self.test_date.toPlainText()
          output_path = self.test_output_path.toPlainText()
          duration = self.test_duration.time().toString()
          
          if not title or not date or not output_path or not duration or duration == "00:00:00":
               QMessageBox.warning(self, "Peringatan", "Harap isi semua data sebelum melanjutkan ")
               return
          
          datas = {
               "title" : title ,
               "date" : date,
               "output_path" : output_path,
               "duration" : strToSecond(duration)
          }
          
          self.epm_window = EpmUI(datas, self)
          self.epm_window.show()
          self.close()
          
     def select_out_path(self):
          """
          Memilih output folder path
          """
          folder_path = QFileDialog.getExistingDirectory(None, "Pilih Folder")
          if folder_path:
               self.test_output_path.setText(folder_path)
          

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = EpmFormUI()
    ui.show()
    sys.exit(app.exec())
