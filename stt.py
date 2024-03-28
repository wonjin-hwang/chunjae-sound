import pyaudio
import wave
import matplotlib.pyplot as plt
import scipy.io as sio
import numpy as np
import threading

from sttapi import SttApi
#파이오디오 설정값
FORMAT = pyaudio.paInt16
CHANNELS = 1#모노?스테레오?
CHUNK = 1024
RATE = 16000 #디바이스로 들어오면 대부분 만육천이래용
RECORD_SECONDS=30

KEYWORD = "안녕"
FILE_NAME = "output.wav"
#마이크로 들어온 음성을 변수에 저장
p = pyaudio.PyAudio()

stream = p.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                frames_per_buffer = CHUNK)#p.open으로 마이크가 오픈되고 그 데이터가 stream에 쌓여

print("Start to recode the audio.")


#Create 함수 호출하여 STTAPI 음성인식 객체 생성
stt = SttApi.create(RATE,CHUNK,RECORD_SECONDS)




#Prepare 함수로 Prepare Api를 통해 STT서버 채널 할당
sttId = stt.prepare(KEYWORD)


#SendData 함수를 호출하여 음성인식 서버에 데이터 송신
thdSend = threading.Thread(target = stt.sendBody, args = (sttId,stream))
thdSend.start()

for i in range(0, int(RATE/CHUNK*RECORD_SECONDS)):#1초에 청크가 대략 15개
    print(i)
    data = stream.read(CHUNK)
    stt.setData(data)

    if not (stt.STT_STATUS == "P01" or stt.STT_STATUS == "P02"):
        break

print("Recording is finished")
#마이크 입력 종료
stream.stop_stream()
stream.close()
p.terminate()




# 음성인식 끝난 후 Finish 함수 호출(return 받기)
res = stt.finish(sttId)

print("====================================================")
print(res.json())
print("====================================================")




# 발성한 음성은 wav파일로 저장
wf = wave.open("output.wav", "wb")
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(stt.getData()))
wf.close()
# 발성한 음성 시각화(pyplot)

rate,data = sio.wavfile.read(FILE_NAME)
size = len(data)
times = np.arange(size)/float(rate)

print(type(times))

print(f"sample size : {size}")
print(f"shape of data : {data.shape}")
print(f"sampling rate :{rate}")
print(f"play time : {times[-1]}")

plt.plot(times,data)
plt.xlim(times[0],times[-1])

plt.xlabel("time(s)")
plt.ylabel("amplitude")
plt.show()