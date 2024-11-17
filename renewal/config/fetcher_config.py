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

API_FETCHER_LOGGER = {
    'LEVEL': 'INFO',
    'DIR_PATH': './logs/',
    'FORMAT': '{time} | {level} | {org_type} | {ipr_mode} | {message}',
    'ENCODING': 'utf-8',
    'ROTATION': '00:00',
    'RETENTION': '1 week',
    'COMPRESSION': None,
}
