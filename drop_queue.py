import queue


class DropQueue(queue.Queue):
    def put(self, *args, **kwargs):
        if self.full():
            try:
                self.get_nowait()
            except queue.Empty:
                pass
        queue.Queue.put(self, *args, **kwargs)
