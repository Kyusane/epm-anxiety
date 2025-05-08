import numpy as np, cv2, seaborn as sns
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from pykalman import KalmanFilter, UnscentedKalmanFilter

class XYTracker :
     def __init__(self):
          self.kf = KalmanFilter(initial_state_mean=[0, 0, 0, 0],  # x, y, dx, dy
                  transition_matrices=[[1, 0, 1, 0],
                                       [0, 1, 0, 1],
                                       [0, 0, 1, 0],
                                       [0, 0, 0, 1]],
                  observation_matrices=[[1, 0, 0, 0],
                                        [0, 1, 0, 0]])
          self.kalman_state = np.array([0, 0, 0, 0]) 
          self.kalman_covariance = np.eye(4)
          
     def update(self, bbox):
          self.kalman_state, self.kalman_covariance = self.kf.filter_update(
          self.kalman_state, self.kalman_covariance, bbox)
          return bbox
     
     def predict(self):
          predicted_x, predicted_y = self.kalman_state[:2]
          bbox = [int(predicted_x), int(predicted_y)]
          return bbox
      
class BBoxTracker:
    def __init__(self):
        # State: [x, y, w, h, dx, dy, dw, dh]
        self.kf = KalmanFilter(
            transition_matrices=np.array([
                [1, 0, 0, 0, 1, 0, 0, 0],
                [0, 1, 0, 0, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0, 1, 0],
                [0, 0, 0, 1, 0, 0, 0, 1],
                [0, 0, 0, 0, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 1]
            ]),
            observation_matrices=np.array([
                [1, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 0, 0, 0, 0]
            ]),
            transition_covariance=np.eye(8) * 10,
            observation_covariance=np.eye(4) * 0.2,
            initial_state_covariance=np.eye(8) * 10
        )
        self.state = np.zeros(8)  # [x, y, w, h, dx, dy, dw, dh]
        self.covariance = np.eye(8)
    
    def init(self, state):
        self.state = state
        print(self.state)
        return True

    def update(self, detection):
        """Update Kalman Filter dengan hasil deteksi YOLO (xmin, ymin, xmax, ymax)"""
        x_center = (detection[0] + detection[2]) / 2
        y_center = (detection[1] + detection[3]) / 2
        width = detection[2] - detection[0]
        height = detection[3] - detection[1]

        self.state, self.covariance = self.kf.filter_update(
            self.state,
            self.covariance,
            observation=[x_center, y_center, width, height]
        )
        return self.get_bbox()

    def predict(self):
        """Prediksi posisi bounding box berikutnya"""
        self.state, self.covariance = self.kf.filter_update(
            self.state,
            self.covariance
        )
        return self.get_bbox()

    def get_bbox(self):
        """Mengonversi hasil prediksi menjadi bounding box lengkap (xmin, ymin, xmax, ymax)"""
        x, y, w, h = self.state[:4]
        xmin = x - w / 2
        ymin = y - h / 2
        xmax = x + w / 2
        ymax = y + h / 2
        return [xmin, ymin, xmax, ymax]
    
    
class AKFTracker:
    def __init__(self):
        self.akf = KalmanFilter(
            transition_matrices=np.array([
                [1, 0, 1, 0],
                [0, 1, 0, 1],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ]),
            observation_matrices=np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0]
            ]),
            transition_covariance=np.eye(4) * 50,
            observation_covariance=np.eye(2) * 0.5,
            initial_state_mean=np.zeros(4),
            initial_state_covariance=np.eye(4) * 100
        )
        self.state = np.zeros(4)
        self.covariance = np.eye(4)
        self.process_noise_adapt = np.eye(4) * 50  # Adaptasi covariance proses
        self.measurement_noise_adapt = np.eye(2) * 0.5  # Adaptasi covariance observasi
        self.prev_innovation = np.zeros(2)

    def init(self, state):
        self.state = state
        return True

    def update(self, detection):
        """ Update dengan deteksi YOLO, adaptasi R lebih smooth """
        x_center, y_center = detection
        observation = np.array([x_center, y_center])
        predicted_observation = self.state[:2]
        innovation = observation - predicted_observation

        # Gunakan smoothing pada inovasi
        smoothed_innovation = 0.8 * self.prev_innovation + 0.2 * innovation
        self.prev_innovation = smoothed_innovation

        # R lebih halus, tidak terlalu agresif
        base_noise = np.array([1.0, 1.0])  # nilai dasar ketidakpastian deteksi
        adaptive_noise = np.abs(smoothed_innovation) * 0.5 + base_noise
        self.measurement_noise_adapt = np.diag(adaptive_noise)

        self.state, self.covariance = self.akf.filter_update(
            self.state, self.covariance,
            observation=observation,
            observation_covariance=self.measurement_noise_adapt
        )
        return self.get_position()

    def predict(self):
        """ Prediksi posisi berikutnya dengan Q adaptif tapi smooth """
        decay = 0.98
        base_q = 0.5  # makin kecil makin smooth
        self.process_noise_adapt = self.process_noise_adapt * decay + np.eye(4) * base_q

        self.state, self.covariance = self.akf.filter_update(
            self.state, self.covariance,
            transition_covariance=self.process_noise_adapt
        )
        return self.get_position()

    def get_position(self):
        """ Ambil posisi dalam format (x, y) """
        x, y, _, _ = self.state
        return [int(x), int(y)]

     
    
def transition_function(state, noise):
    """ Model dinamika untuk UKF dengan noise """
    x, y, dx, dy= state
    x_new = x + dx
    y_new = y + dy
    return np.array([x_new, y_new, dx, dy]) + noise

def observation_function(state, noise):
    """ Model observasi dengan noise """
    x, y, w, h, _, _, _, _ = state
    return np.array([x, y, w, h]) + noise

class UKFTracker:
    def __init__(self):
        self.ukf = UnscentedKalmanFilter(
            transition_functions=transition_function,
            observation_functions=observation_function,
            transition_covariance=np.eye(4) * 50,
            observation_covariance=np.eye(2) * 0.5,
            initial_state_mean=np.zeros(4),
            initial_state_covariance=np.eye(4) * 100
        )
        self.state = np.zeros(4)
        self.covariance = np.eye(4)
    
    def init(self, state):
        self.state = state
        return True

    def update(self, detection):
        """ Update UKF dengan hasil deteksi YOLO (x, y) """
        self.state, self.covariance = self.ukf.filter_update(
            self.state, self.covariance, observation=[detection[0], detection[1]]
        )
        return self.get_bbox()

    def predict(self):
        """ Prediksi posisi bounding box berikutnya """
        self.state, self.covariance = self.ukf.filter_update(self.state, self.covariance)
        return self.get_bbox()

    def get_bbox(self):
        """ Ambil bounding box dalam format (xmin, ymin, xmax, ymax) """
        predicted_x, predicted_y = self.state[:2]
        bbox = [int(predicted_x), int(predicted_y)]
        return bbox
    

    
class Trajectory:
    def __init__(self):
        self.history = []
        
    def add(self, xy):
        if xy:
            self.history.append(xy)
            
    def save2jpg(self, filename, frame):
        try :
            cv2.imwrite(f"{filename}_trajectory.jpg",frame)
            self.savekde(self.history,filename)
        except Exception as e :
            print(f"Gagal menyimpan trajektori: {e}")
    
    def savekde(self, datas, filename):
        try :
            datas = np.array(datas, dtype=np.float32)
            x = datas[:, 0]
            y = datas[:, 1]
            
            cmap = cm.get_cmap("jet")
            
            plt.figure(figsize=(8, 6))
            sns.kdeplot(x=x, y=y, fill=True, levels=100, thresh=0, cmap=cmap) 
            plt.title("Heatmap Intensity KDE")
            plt.xlabel("X")
            plt.ylabel("Y")
            plt.gca().invert_yaxis()
            
            save_path = f"{filename}_heatmap.png" 
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.clf()
            plt.close()
             
        except Exception as e :
             print(f"Gagal menyimpan heatmap: {e}")


    def reset(self):
        self.history=[]

