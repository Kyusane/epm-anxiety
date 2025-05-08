

def strToSecond(string):
     """
     Mengubah string ke seconds
     Parameter:
          string : string time (00:00:00)
     
     return seconds : waktu dalam satuan detik
     """
     data = string.split(":")
     seconds = int(data[0])*3600 + int(data[1])*60 + int(data[2])
     return seconds

def secondToStr(seconds):
     """
     Mengubah seconds ke string time
     Parameter :
          seconds : waktu dalam detik
     
     return str_time : waktu dalam string dengan format MM:SS
     """
     minutes = seconds // 60
     seconds = seconds % 60 
     str_time = f"{minutes:02}:{seconds:02}"
     return str_time