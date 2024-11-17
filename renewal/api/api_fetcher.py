import asyncio
import json
import sys

import aiofiles
import aiohttp
from loguru import logger
from tqdm.asyncio import tqdm
import xmltodict

from api.api_query_generator import APIQueryGenerator
from config.fetcher_config import TOKEN_BUCKET, WORKER, AIOHTTP, API_FETCHER_LOGGER
from utils.time_utils import get_today_yyyymmdd, get_timestamp


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

        self.progress_bar = tqdm(
            total=self.request_queue.qsize(),
            desc="Requests",
            unit="req",
            ascii=True,
            ncols=128,
        ) if enable_progress_bar else None
        self.logger = logger.add(
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
                await self.token_bucket.acquire()  # 가용 토큰 발생까지 대기
                try:
                    async with session.get(
                        url=request["url"],
                        params=request["params"],
                        connector=self.connector
                    ) as response:
                        if response.status == 200:
                            try:
                                xml_data = await response.text()
                                json_data = xmltodict.parse(xml_data)

                                # 페이지네이션 처리
                                if self.ipr_mode == 'applicant_no':
                                    paged_requests_list = self.api_query_generator.generate_paged_fetch_query(
                                        response_json=json_data, request=request)
                                    for paged_request in paged_requests_list:
                                        await self.request_queue.put(paged_request)

                                items = json_data.get('root', {}).get(
                                    'items', {}).get('item', [])

                                # 'items'가 단일 element인 경우, list로 처리
                                if isinstance(items, dict):
                                    items = [items]

                                # items별 applicantNo 값 추가
                                for item in items:
                                    if self.ipr_mode != 'applicant_no':
                                        item['applicantNo'] = request["params"]["applicantName"]

                                    # JSON 파일에 추가
                                    async with output_file_lock:
                                        await file.write(json.dumps(item, ensure_ascii=False) + ',\n')
                            except Exception as e:
                                self.logger.error(f"XML 파싱 오류: {e}")
                                json_data = {}

                        else:
                            response.raise_for_status()
                finally:
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
