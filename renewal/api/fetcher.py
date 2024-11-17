import asyncio
import time

import aiohttp
from tqdm.asyncio import tqdm


async def refill_token_bucket(semaphore, tokens_per_second, max_tokens):
    while True:
        try:
            if semaphore._value < max_tokens:
                semaphore.release()
        except ValueError:
            # 세마포어가 최대값에 도달했을 때 발생하는 예외 무시
            pass
        await asyncio.sleep(1 / tokens_per_second)

async def worker(queue, session, semaphore, progress_bar, delay):
    await asyncio.sleep(delay)  # 작업 시작 지연
    while True:
        url = await queue.get()
        await semaphore.acquire()  # 가용 토큰 발생까지 대기
        try:
            async with session.get(url) as response:
                # 응답 처리 로직
                # print(f"응답 상태 코드: {response.status}")
                pass
        finally:
            queue.task_done()
            progress_bar.update(1)

async def main():
    tokens_per_second = 30  # 속도 제한: 초당 요청 수
    max_tokens = 30         # 버킷 내 최대 토큰 수

    # 토큰 버킷 세마포어를 초기화합니다.
    token_bucket = asyncio.BoundedSemaphore(max_tokens)
    for _ in range(max_tokens):
        await token_bucket.acquire()  # 토큰 버킷 비우기

    # 버킷에 토큰 생성
    asyncio.create_task(refill_token_bucket(token_bucket, tokens_per_second, max_tokens))

    url_queue = asyncio.Queue()

    connector = aiohttp.TCPConnector(limit=30)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 총 API 호출 수 설정
        total_requests = int(input("테스트할 API 호출 수를 입력하세요: "))

        # tqdm(progress bar) 초기화
        progress_bar = tqdm(
            total=total_requests, 
            desc='Requests', 
            unit='req',
            ascii=True,
            ncols=128,
            )

        # worker task 시작
        num_workers = 5
        tasks = []
        start_time = time.time()

        for i in range(num_workers):
            task = asyncio.create_task(
                worker(
                    url_queue,
                    session,
                    token_bucket,
                    progress_bar,
                    0.02 * i
                    )
                )
            tasks.append(task)

        url = "http://43.203.191.28:5000/mock_api"

        # 작업 큐에 각 요청 추가
        for _ in range(total_requests):
            await url_queue.put(url)

        # 작업 큐의 모든 작업이 처리될 때까지 대기
        await url_queue.join()
        end_time = time.time()


        # worker task 취소
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        rps = total_requests / (end_time - start_time)
        print(f"\n초당 평균 {rps}개의 요청이 처리되었습니다.")

# 메인 코루틴 실행
asyncio.run(main())
