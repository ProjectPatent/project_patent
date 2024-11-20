from fastapi import FastAPI, Request, HTTPException, Response
import asyncio
import time
from collections import deque
from random import random, randint, choice


app = FastAPI()

# 설정값
REQUEST_LIMIT_PER_SECOND = 50
QUEUE_LIMIT = 50

# 슬라이딩 윈도우를 위한 요청 타임스탬프 큐와 동기화 도구
request_timestamps = deque(maxlen=REQUEST_LIMIT_PER_SECOND)
queue_count = 0
lock = asyncio.Lock()  # 카운트 갱신용 락

async def check_rate_limit():
    global queue_count
    current_time = time.time()

    async with lock:
        # 1초 이내 요청만 슬라이딩 윈도우로 확인
        while request_timestamps and current_time - request_timestamps[0] > 1:
            request_timestamps.popleft()
        
        # 요청 수 제한 검사
        if len(request_timestamps) >= REQUEST_LIMIT_PER_SECOND:
            raise HTTPException(status_code=429, detail="요청 수 제한 초과")
        
        # 큐 제한 검사
        if queue_count >= QUEUE_LIMIT:
            raise HTTPException(status_code=429, detail="Queue 제한 초과")

        # 현재 요청 시간 기록 및 요청 카운트 증가
        request_timestamps.append(current_time)
        queue_count += 1

@app.get("/mock_api")
async def mock_api(request: Request):
    global queue_count

    # 제한 검사
    await check_rate_limit()

    try:
        # delay = random() * randint(1, 10) / 2    # 0초 이상 ~ 5초 미만의 random value
        delay = 0.1
        await asyncio.sleep(delay)  # 응답 지연 시뮬레이션
        # return {"status": "success", "message": "성공"}

        normal_xml_string = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<response> 
    <header> 
        <requestMsgID></requestMsgID> 
        <responseTime>{time.time()}</responseTime> 
        <responseMsgID></responseMsgID> 
        <successYN>Y</successYN> 
        <resultCode>00</resultCode> 
        <resultMsg>NORMAL SERVICE.</resultMsg> 
    </header> 
    <body> 
        <items> 
            <item> 
                <agentName>Dummy Agent</agentName> 
                <appReferenceNumber>Dummy Ref No</appReferenceNumber> 
                <applicantName>Dummy Applicant</applicantName> 
                <applicationDate>20241101</applicationDate> 
                <applicationNumber>1234567890123</applicationNumber> 
                <applicationStatus>Dummy Status</applicationStatus> 
                <bigDrawing>http://dummyurl.com/bigdrawing</bigDrawing> 
                <classificationCode>99</classificationCode> 
                <drawing>http://dummyurl.com/drawing</drawing> 
                <fullText>N</fullText> 
                <indexNo>1</indexNo> 
                <internationalRegisterDate>20241101</internationalRegisterDate> 
                <internationalRegisterNumber>INT123456</internationalRegisterNumber> 
                <priorityDate>20241010</priorityDate> 
                <priorityNumber>PRIOR12345</priorityNumber> 
                <publicationDate>20240101</publicationDate> 
                <publicationNumber>1234567890123</publicationNumber> 
                <regPrivilegeName>Dummy Company Inc.</regPrivilegeName> 
                <regReferenceNumber>Dummy Reg Ref</regReferenceNumber> 
                <registrationDate>20241115</registrationDate> 
                <registrationNumber>9876543210000</registrationNumber> 
                <registrationPublicDate>20241116</registrationPublicDate> 
                <registrationPublicNumber>987654321</registrationPublicNumber> 
                <title>Dummy Title</title> 
                <viennaCode>000000|999999</viennaCode> 
            </item> 
        </items> 
    </body> 
    <count> 
        <numOfRows>1</numOfRows> 
        <pageNo>1</pageNo> 
        <totalCount>49</totalCount> 
    </count> 
</response>"""

        abnormal_xml_string = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><response><header><requestMsgID></requestMsgID><responseTime>{time.time()}</responseTime><responseMsgID></responseMsgID><successYN>Y</successYN><resultCode>00</resultCode><resultMsg>NORMAL SERVICE.</resultMsg></header><body><items/></body><count><numOfRows>1</numOfRows><pageNo>1</pageNo><totalCount>0</totalCount></count></response>"""

        response_xml_string = choice([normal_xml_string, abnormal_xml_string])

        return Response(content=response_xml_string,
                        media_type="text/xml")
    finally:
        async with lock:
            queue_count -= 1  # 응답 후 큐에서 제거


'''
cd ~/mock_api_server
# 백그라운드로 서버 실행, mock_api.log 파일로 로그 저장
nohup uvicorn mock_server_for_kipris:app --host 0.0.0.0 --port 5000 --log-config log_config.ini >> /dev/null
'''
