TOKEN_BUCKET = {
    'TOKENS_PER_SECOND': 30,
    'MAX_TOKENS': 30,
}

WORKER = {
    'WORKER_COUNT': 6,
    'INTERVAL': 0.02,
}

AIOHTTP = {
    'MAX_CONNECTIONS_LIMIT': 30,
}

# 메트릭 관련 설정 추가 
METRICS = {
    'ENABLED': True,
    'PREFIX': 'kipris_',  # 메트릭 이름 접두사
    'PORTS': {
        'patuti': 8000,
        'design': 8001,
        'trademark': 8002,
        'applicant': 8003,
        'mock_server': 8004,
    },
    'LABELS': {  # 공통으로 사용할 레이블
        'service': 'kipris_api',
        'environment': 'production'
    },
    'BUCKETS': {  # 히스토그램용 버킷 설정
        'response_time': (0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
        'batch_size': (10, 50, 100, 500, 1000, 5000)
    }
}

API_FETCHER_LOGGER = {
    'LEVEL': 'INFO',
    'DIR_PATH': './logs/',
    'FORMAT': '{time} | {level} | {org_type} | {ipr_mode} | {message}',
    'ENCODING': 'utf-8',
    'ROTATION': '00:00',
    'RETENTION': '1 week',
    'COMPRESSION': None,
}
