import asyncio
import json
import sys
import time
import aiofiles
import aiohttp
from loguru import logger
from tqdm.asyncio import tqdm
import xmltodict

from api.api_query_generator import APIQueryGenerator
from config.fetcher_config import TOKEN_BUCKET, WORKER, AIOHTTP, API_FETCHER_LOGGER
from utils.time_utils import get_today_yyyymmdd, get_timestamp

# prometheus_client 라이브러리를 사용하여 메트릭을 수집
from prometheus_client import Counter, Summary, Gauge, start_http_server
from config.fetcher_config import METRICS

# Prometheus 메트릭 정의
REQUEST_COUNTER = Counter(
    f'{METRICS["PREFIX"]}requests_total',
    'Total number of API requests',
    ['ipr_mode', 'org_type', 'status']
)

RESPONSE_TIME = Summary(
    f'{METRICS["PREFIX"]}response_seconds',
    'Response time in seconds',
    ['ipr_mode', 'org_type']
)

ERROR_COUNTER = Counter(
    f'{METRICS["PREFIX"]}errors_total',
    'Number of errors encountered',
    ['ipr_mode', 'org_type', 'error_type']
)

ACTIVE_REQUESTS = Gauge(
    f'{METRICS["PREFIX"]}active_requests',
    'Number of currently active requests',
    ['ipr_mode', 'org_type']
)

QUEUE_SIZE = Gauge(
    f'{METRICS["PREFIX"]}queue_size',
    'Current size of the request queue',
    ['ipr_mode', 'org_type']
)

TOKEN_BUCKET_GAUGE = Gauge(
    f'{METRICS["PREFIX"]}token_bucket_tokens',
    'Current number of available tokens in the bucket',
    ['ipr_mode', 'org_type']
)


class APIFetcher:
    def __init__(self, org_type: str, ipr_mode: str, requests_list: list[dict], enable_progress_bar: bool = True):
        self.token_bucket = asyncio.BoundedSemaphore(
            TOKEN_BUCKET["MAX_TOKENS"])  # 토큰 버킷 세마포어를 초기화
        self.TOKENS_PER_SECOND = TOKEN_BUCKET["TOKENS_PER_SECOND"]
        self.MAX_TOKENS = TOKEN_BUCKET["MAX_TOKENS"]
        self.WORKER_COUNT = WORKER["WORKER_COUNT"]
        self.WORKER_INTERVAL = WORKER["INTERVAL"]
        self.connector = aiohttp.TCPConnector(
            limit=AIOHTTP["MAX_CONNECTIONS_LIMIT"])

        self.org_type = org_type if org_type in ['univ', 'corp'] else 'invalid'
        if self.org_type == 'invalid':
            raise ValueError(f"지원하지 않는 org_type: {org_type}")
        self.ipr_mode = ipr_mode if ipr_mode in [
            'patuti', 'design', 'trademark', 'applicant_no'] else 'invalid'
        if self.ipr_mode == 'invalid':
            raise ValueError(f"지원하지 않는 ipr_mode: {ipr_mode}")

        self.requests_list = requests_list
        self.request_queue = asyncio.Queue()
        self.api_query_generator = APIQueryGenerator()

        # 메트릭 서버 시작
        start_http_server(METRICS['PORTS'][self.ipr_mode])

        self.progress_bar = tqdm(
            total=self.request_queue.qsize(),
            desc="Requests",
            unit="req",
            ascii=True,
            ncols=128,
        ) if enable_progress_bar else None
        self.logger = logger
        self.logger.add(
            f"{API_FETCHER_LOGGER['DIR_PATH']}{self.ipr_mode}_{get_today_yyyymmdd()}_{self.org_type}.log",
            level=API_FETCHER_LOGGER['LEVEL'],
            format=API_FETCHER_LOGGER['FORMAT'],
            encoding=API_FETCHER_LOGGER['ENCODING'],
            rotation=API_FETCHER_LOGGER['ROTATION'],
            retention=API_FETCHER_LOGGER['RETENTION'],
            compression=API_FETCHER_LOGGER['COMPRESSION'],
        )
        self.logger.bind(
            org_type=self.org_type,
            ipr_mode=self.ipr_mode,
        )
        sys.excepthook = lambda exc_type, exc_value, exc_traceback: \
            self.logger.exception("Unhandled exception:", exc_info=(
                exc_type, exc_value, exc_traceback))

    async def _refill_token_bucket(self):
        while True:
            try:
                if self.token_bucket._value < self.MAX_TOKENS:
                    self.token_bucket.release()
                    TOKEN_BUCKET_GAUGE.labels(
                        ipr_mode=self.ipr_mode,
                        org_type=self.org_type
                    ).set(self.token_bucket._value)
            except ValueError:
                pass  # 세마포어가 최대값에 도달했을 때 발생하는 예외 무시
            await asyncio.sleep(1 / self.TOKENS_PER_SECOND)

    async def _fetch_and_save_worker(
            self,
            session: aiohttp.ClientSession,
            delay: float,
            output_file_lock: asyncio.Lock,
            output_file_path: str
    ):
        await asyncio.sleep(delay)  # 작업 시작 지연

        async with aiofiles.open(output_file_path, "a") as file:
            while True:
                request = await self.request_queue.get()

                # 큐 크기 메트릭 업데이트
                QUEUE_SIZE.labels(
                    ipr_mode=self.ipr_mode,
                    org_type=self.org_type
                ).set(self.request_queue.qsize())

                await self.token_bucket.acquire()  # 가용 토큰 발생까지 대기

                # 활성 요청 메트릭 증가
                ACTIVE_REQUESTS.labels(
                    ipr_mode=self.ipr_mode,
                    org_type=self.org_type
                ).inc()

                try:
                    start_time = time.time() # 응답 시간 측정을 위해서 시작 시간 추가하기.
                    async with session.get(
                        url=request["url"],
                        params=request["params"],
                    ) as response:
                        duration = time.time() - start_time 
                        
                        # 응답 시간 메트릭
                        RESPONSE_TIME.labels(
                            ipr_mode=self.ipr_mode,
                            org_type=self.org_type
                        ).observe(duration)

                        if response.status == 200:
                            
                            # 성공 카운터
                            REQUEST_COUNTER.labels(
                                ipr_mode=self.ipr_mode,
                                org_type=self.org_type,
                                status="success"
                            ).inc()
                            
                            try:
                                xml_data = await response.text()
                                json_data = xmltodict.parse(xml_data)
                                print(json_data)
                                items = json_data.get('response', {}).get('body', {}).get('items', [])

                                if items is None:
                                    continue

                                # 페이지네이션 처리
                                if self.ipr_mode != 'applicant_no':
                                    paged_requests_list = self.api_query_generator.generate_paged_fetch_query(
                                        response_json=json_data, request=request)
                                    for paged_request in paged_requests_list:
                                        await self.request_queue.put(paged_request)

                                    items = json_data.get('response', {}).get(
                                        'body', {}).get('items', {}).get('item', [])
                                else:
                                    items = json_data.get('response', {}).get('body', {}).get('items', {}).get('corpBsApplicantInfo', [])

                                # 'items'가 단일 element인 경우, list로 처리
                                if isinstance(items, dict):
                                    items = [items]

                                # items별 applicantNo 값 추가
                                for idx in range(len(items)):
                                    if self.ipr_mode != 'applicant_no':
                                        if self.ipr_mode == 'patuti':
                                            items[idx]['applicantNo'] = request["params"]["applicant"]
                                        else:
                                            items[idx]['applicantNo'] = request["params"]["applicantName"]

                                    # JSON 파일에 추가
                                    async with output_file_lock:
                                        await file.write(json.dumps(items[idx], ensure_ascii=False) + ',\n')
                            except Exception as e:
                                # 일반 에러 카운터 증가
                                ERROR_COUNTER.labels(
                                    ipr_mode=self.ipr_mode,
                                    org_type=self.org_type,
                                    error_type="parsing_error"
                                ).inc()
                                
                                self.logger.error(f"XML 파싱 오류: {e}")
                                json_data = {}

                        else:
                            # HTTP 에러 카운터 증가
                            ERROR_COUNTER.labels(
                                ipr_mode=self.ipr_mode,
                                org_type=self.org_type,
                                error_type="http_error"
                            ).inc()
                            response.raise_for_status()
                finally:
                    # 활성 요청 메트릭 감소
                    ACTIVE_REQUESTS.labels(
                        ipr_mode=self.ipr_mode,
                        org_type=self.org_type
                    ).dec()
                    
                    self.request_queue.task_done()
                    if self.progress_bar:
                        self.progress_bar.update(1)

    async def start(self):
        for _ in range(self.MAX_TOKENS):
            await self.token_bucket.acquire()  # 토큰 버킷 비우기

        # 버킷에 토큰 생성
        asyncio.create_task(
            self._refill_token_bucket()
        )

        # JSON 파일 초기화
        output_file_path = f"./data/{self.ipr_mode}_{get_today_yyyymmdd()}_{self.org_type}.json"

        # JSON metadata 초기화
        initial_json_data = {
            'metadata': {
                'org_type': self.org_type,
                'ipr_mode': self.ipr_mode,
                'start_datetime': get_timestamp(),
            },
        }
        async with aiofiles.open(output_file_path, "w") as file:
            await file.write('{\n')
            await file.write('"metadata": ' + json.dumps(initial_json_data["metadata"], ensure_ascii=False) + ',\n')
            await file.write('"data": [\n')

        # 비동기 파일 쓰기 Lock 생성
        output_file_lock = asyncio.Lock()

        async with aiohttp.ClientSession(connector=self.connector) as session:
            tasks = []
            for i in range(self.WORKER_COUNT):
                task = asyncio.create_task(
                    self._fetch_and_save_worker(
                        session,
                        self.WORKER_INTERVAL * i,
                        output_file_lock=output_file_lock,
                        output_file_path=output_file_path,
                    )
                )
                tasks.append(task)

            # 작업 큐에 각 요청 추가
            for request in self.requests_list:
                await self.request_queue.put(request)

            # 작업 큐의 모든 작업이 처리될 때까지 대기
            await self.request_queue.join()

            # fetch_data tasks 취소
            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

        # JSON 파일 종료
        async with aiofiles.open(output_file_path, "a") as file:
            await file.write('\n]}')
