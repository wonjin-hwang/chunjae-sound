import base64
import json
import threading
import requests
import time


class SttApi:

    def __init__(self, RATE, CHUNK, RECORD_SECONDS):
        self.host = 'https://t-stt.chunjaeai.com' #호출하는 도매인,뒤에다가 /stt/prepare이런식으로 붙이는거임
        self.STT_STATUS = 'P01'  # P01 진행중, P02 첫음검출, P03 끝음검출
        self.RATE = RATE #
        self.CHUNK = CHUNK
        self.RECORD_SECONDS = RECORD_SECONDS
        self.index = 0

        self.frames = []

    @staticmethod#이거는 클래스 객체를 생성하지 않아도 사용할 수 있는 함수일 때 꼭 작성하기
    #클래스 객체를 생성하지 않아도 사용할 수 있는 함수란?: 클래스 내부 변수or내부 함수를 참조하지 않는 함수
    #그니까 클래스 밖에 있어도 상관이 없는애임
    def create(RATE, CHUNK, RECORD_SECONDS):
        #sttapi객체 생성 후 리턴하는 함수
        return SttApi(RATE, CHUNK, RECORD_SECONDS)

    def post(self, url, field_data):
        #rest api를 송신 후 수신된 결과(json)를 리턴받는 함수
        # 필수 헤더값(key,사용 api url,인자값(json)을 http 프로토콜을 통해서 웹으로 전송
        headers = {'API-KEY-ID': 'ACADEMY_SPEECH', 'API-KEY': '키를 넣으세요', 'Content-Type': 'application/json'}
        return requests.post(url, headers=headers, data=field_data)

    def setData(self, data):
        #sttapi객체 내부 변수인 frames 버퍼(리스트)에 음성데이터를 쌓는 함수
        self.frames.append(data)

    def getData(self):
        #sttapi객체에 쌓인 음성 데이터중 서버에 전송된(처리 완료된) 데이터 리턴
        #self.index변수는 self.sendBody()에서 데이터를 서버로 송신 후 index가 증가함
        return self.frames[0:self.index]

    def sendData(self, i, data):
        if self.STT_STATUS == 'P01' or self.STT_STATUS == 'P02':
            # 서버가 처리할 수 있는 데이터 타입으로 인코딩 포맷 변경
            bdata = base64.b64encode(data).decode('utf8')
            #서버로 보낼 데이터 json형태로 만들고 서버로 송신
            field_data = json.dumps({'sttId': self.sttId, 'dataIndex': i + 1, 'data': bdata})
            url = self.host + '/stt/sendData'
            res = self.post(url, field_data)

            jsonObject = json.loads(json.dumps(res.json()))
            #실시간으로 계속 서버에 데이터를 전송하고 그때마다 음성인식 진행상태를 리턴 받는다.
            #실시간으로 리턴받는 상태변수를 (P01,P02,P03...) 클래스 내부 self.STT_STATUS에 업데이트(stt.py 테스트 코드에서 계속 확인함)
            self.STT_STATUS = jsonObject.get('analysisResult').get('progressCode')

            return res

    def sendBody(self, sttId, stream):
        self.sttId = sttId

        #음성인식 서버의 상태가 인식 중이면(P01,P02)계속 동작하면서
        #sendData()함수를 사용해서 서버에 데이터 청크 송신
        while self.STT_STATUS == 'P01' or self.STT_STATUS == 'P02':
            if len(self.frames) > (self.index + 1):
                #데이터 전송 함수
                self.sendData(self.index, self.frames[self.index])
                self.index = self.index + 1


            # 0.01초 딜레이를 주는 이유:
            # 순서대로 보내지만 반복문 속도도 빠르고, 통신 네트워크에 따라서 서버에 음성 청크 도착순서가 꼬일 수 있기 때문

            time.sleep(0.01)

    def prepare(self, keywordlist):
        #음성인식 API를 할당받기 위한 파라미터를 세팅하고 (무슨 모델 쓸건지,자동으로 끝점을 검출 할 건지 등등.. 이건 api문서에 명시)
        #음성인식 서버의 채널을 할당받는 함수
        #그래서 서버에서는 할당한 ID를 리턴해주고 앞으로 음성인식을 할 때 해당 ID를 사용
        field_data = json.dumps({'modelId': '1', 'useEpd': '1', 'codec': '1', 'midResult': '1', 'pitchResult': '1',
                                 'keywordList': keywordlist})
        url = self.host + '/stt/prepare'
        res = self.post(url, field_data)
        jsonObject = json.loads(json.dumps(res.json()))
        sttId = jsonObject.get('sttId')
        print(res)
        return sttId

    def finish(self, sttId):
        #음성인식 api 사용 후에 할당받았던 id를 반납하고 최종 인식 결과를 리턴받는 함수
        field_data = json.dumps({'sttId': sttId})
        url = self.host + '/stt/finish'
        res = self.post(url, field_data)
        return res
