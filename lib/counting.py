import time

def checkInBbox(point, bbox):
    """
    Mengecek apakah suatu titik berada dalam bounding box.
    
    :param point: Tuple (px, py) koordinat titik.
    :param bbox: Tuple (x, y, width, height) dari bounding box.
    :return: True jika titik berada dalam bbox, False jika tidak.
    """
    px, py = point
    x, y, w, h = bbox

    return x <= px <= x + w and y <= py <= y + h

class Counter:
     def __init__(self, regions = []):
          self.stress_stats = "UNDEFINED"
          self.regions = regions
          self.last_coordinate = [0,0]
          self.start_date = None
          self.elapsed_time = 0
          self.results =  {
               "Right" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Left" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Top" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Bottom" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0}
          }
          
     def update_region(self, region):
          if region is not None:
               found = False
               for i, reg in enumerate(self.regions):
                    if reg["position"] == region["position"]:
                         self.regions[i] = region
                         found = True
                         break
               
          if not found:
               self.regions.append(region)
               

     def update(self, xy):
          current_time = time.time()
          for reg in self.regions:
               inside = checkInBbox(xy, reg["bbox"])
               region = reg["position"]

               if inside and not self.results[region]["inside"]:
                    self.results[region]["total_entry"] += 1
                    self.results[region]["entry_time"] = current_time
                    self.results[region]["inside"] = True 

               if inside:
                    self.results[region]["total_time"] = round((current_time - self.results[region]["entry_time"]) + self.results[region]["last_time"],2)
               else:
                    if self.results[region]["inside"]:
                         self.results[region]["last_time"] = self.results[region]["total_time"]
                         self.results[region]["inside"] = False 
                         self.results[region]["entry_time"] = None
                         
          self.calculateStatus()
                         
     def calculateStatus(self):
          openTime = self.results["Right"]["total_time"] + self.results["Left"]["total_time"] 
          closeTime = self.results["Top"]["total_time"] + self.results["Bottom"]["total_time"] 
          
          if openTime > closeTime:
               result = 'RELAXED'
               self.stress_stats = result
               return result
          elif openTime == closeTime:
               result = "UNDEFINED"
               self.stress_stats = result
               return result
          else:
               result = "ANXIETY"
               self.stress_stats = result
               return result
          
     def save2txt(self, filename, desc):
          with open(filename, "w") as file:
               file.write(f"Title            : {filename.split('/')[-1:]}\n")
               file.write(f"Date             : {desc['date']}\n")
               file.write(f"Status           : {self.stress_stats}\n")
               file.write(f"Duration         : {round(desc['duration'],2)} s\n")
               file.write("=" * 40 + "\n")
               file.write(f"{'Region':<10} {'Total Entry':<15} {'Total Time':<15}\n")
               file.write("=" * 40 + "\n")

               for reg, details in self.results.items():
                    file.write(f"{reg:<10} {details['total_entry']:<15} {round(details['total_time'],2):<15}\n")
          

     def run(self, xy):
          current_time = time.time()
          for reg_position in enumerate(self.regions):
               inside = checkInBbox(xy,reg_position["bbox"])
               region =reg_position["position"]
               if inside :
                    self.results[region]["total_time"] = (current_time - self.results[region]["entry_time"] ) + self.results[region]["last_time"]
               else:
                    self.results[region]["entry_time"] = None

               
          # ####################################################################################
          # #    GENERAL CODE
          # ####################################################################################

          # self.EPM.elapsed_time = current_time - self.EPM.start_time
          # self.OBJ_X = new_x
          # self.OBJ_Y = new_y
          
     def reset(self):
          self.stress_stats = "UNDEFINED"
          self.last_coordinate = [0,0]
          self.start_date = None
          self.elapsed_time = 0
          self.results =  {
               "Right" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Left" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Top" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Bottom" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0}
          }
          
          
          

class EPM_Initial:
     def __init__(self):
          self.status_object = "UNDEFINED"
          self.elapsed_time = 0
          self.start_time = 0
          self.start_date = None
          self.chambers = {
               "Right" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Left" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Top" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0},
               "Bottom" : {"inside" : False,"total_entry" : 0, "entry_time" : None ,"last_time" : 0,"total_time" : 0}
          }
          
          
          
     def reset(self):
          self.elapsed_time = 0
          self.start_time = 0
          self.start_date = None
          for chamber in self.chambers.values():
               chamber["inside"] = False
               chamber["total_entry"] = 0
               chamber["entry_time"] = None
               chamber["last_time"] = 0
               chamber["total_time"] = 0

class Analyzer:
     def __init__(self, coordinate):
          self.FLAG_ANALYZE = False
          self.OBJ_X = coordinate[0]
          self.OBJ_Y = coordinate[1]
          self.line_pos = [0,0,0,0]
          self.EPM = EPM_Initial()
     
     def start(self):
          self.FLAG_ANALYZE = True
          self.EPM.start_time = time.time()
          gmt7_time = time.gmtime(self.EPM.start_time + 7 * 3600)
          formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", gmt7_time) 
          self.EPM.start_date = formatted_time
     
     def stop(self):
          self.FLAG_ANALYZE = False
     
     def update_line_pos(self , line_pos):
          
          x1 = line_pos[0] - line_pos[2]
          x2 = line_pos[1] + line_pos[2]
          
          y1 = line_pos[1] - line_pos[2]
          y2 = line_pos[1] + line_pos[2]
          
          self.line_pos = [x1,x2,y1,y2]
          
     def save_to_txt(self, filename):
          with open(filename, "w") as file:
               file.write(f"Test Name        : {filename.split('/')[-1:]}\n")
               file.write(f"Date             : {self.EPM.start_date}\n")
               file.write(f"Status           : {self.EPM.status_object}\n")
               file.write(f"Test Time        : {round(self.EPM.elapsed_time,2)} s\n")
               file.write("=" * 40 + "\n")
               file.write(f"{'Chamber':<10} {'Total Entry':<15} {'Total Time':<15}\n")
               file.write("=" * 40 + "\n")

               for chamber, details in self.EPM.chambers.items():
                    file.write(f"{chamber:<10} {details['total_entry']:<15} {round(details['total_time'],2):<15}\n")
          
     
     def calculateResult(self):
          result = self.EPM
          
          openTime = result.chambers["Right"]["total_time"] + result.chambers["Left"]["total_time"] 
          closeTime = result.chambers["Top"]["total_time"] + result.chambers["Bottom"]["total_time"] 
          
          if openTime > closeTime:
               result = 'RELAXED'
               self.EPM.status_object = result
               return result
          elif openTime == closeTime:
               result = "UNDEFINED"
               self.EPM.status_object = result
               return result
          else:
               result = "ANXIETY"
               self.EPM.status_object = result
               return result
          
     def run(self, new_x, new_y):
          if self.FLAG_ANALYZE : 
               current_time = time.time()

               chamber_boundaries = {
                    "Right": lambda x, y, line_pos: x > line_pos[1] and line_pos[2] < y < line_pos[3],
                    "Left": lambda x, y, line_pos: x < line_pos[0] and line_pos[2] < y < line_pos[3],
                    "Top": lambda x, y, line_pos: y < line_pos[2] and line_pos[0] < x < line_pos[1],
                    "Bottom": lambda x, y, line_pos: y > line_pos[3] and line_pos[0] < x < line_pos[1]
               }

               for chamber_name, boundary_func in chamber_boundaries.items():
                    chamber = self.EPM.chambers[chamber_name]
               
                    if boundary_func(new_x, new_y, self.line_pos):
                         if not chamber["inside"]:
                              chamber["total_entry"] += 1
                              chamber["inside"] = True
                              chamber["entry_time"] = current_time
                    else:
                         if chamber["inside"]:
                              chamber["last_time"] += current_time - chamber["entry_time"]
                              chamber["inside"] = False

                    # Update total time if inside
                    if chamber["inside"]:
                         chamber["total_time"] = (current_time - chamber["entry_time"]) + chamber["last_time"]
                    else:
                         chamber["entry_time"] = None

                    
               ####################################################################################
               #    GENERAL CODE
               ####################################################################################

               self.EPM.elapsed_time = current_time - self.EPM.start_time
               self.OBJ_X = new_x
               self.OBJ_Y = new_y