
import threading
import progressbar
import time
import random


def do():
    pb = progressbar.ProgressBar(min_value=0, max_value=100).start()

    for i in range(1, 101):
        pb.update(i)
        time.sleep(random.randrange(1, 5) / 10.0)

    pb.finish()
    threads.remove(threading.current_thread())


threads = []

for _ in range(10):
    t = threading.Thread(target=do)
    t.daemon = True
    threads += [t]
    t.start()


while threads:
    time.sleep(0.2)

