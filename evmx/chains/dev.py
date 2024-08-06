import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evmx.settings")
    django.setup()


def block_count():
    while 1:
        time.sleep(2)


with ThreadPoolExecutor(max_workers=30) as pool:
    futures = [pool.submit(block_count) for _ in range(30)]
    for future in as_completed(futures):
        future.result()  # 获取线程的结果或异常
