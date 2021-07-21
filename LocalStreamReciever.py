import threading
import cv2
from StreamReciever import IInterfaceReciever
import imutils
import time
from threading import Thread
import sys

# import the Queue class from Python 3
if sys.version_info >= (3, 0):
    import queue
    from queue import Queue
    from queue import LifoQueue
# otherwise, import the Queue class for Python 2.7
'''else:
	from Queue import Queue'''

class MyThread(Thread):
    def __init__(self, *args, **kwargs):
        super(MyThread, self).__init__(*args, **kwargs)
        self._stopper = threading.Event()

    def stop_it(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.is_set()

class LocalStreamReciever(IInterfaceReciever):
    def __init__(self, url="rtsp://root:admin@192.168.5.100/axis-media/media.amp?fps=4&compression=10", frame_rate=None):
        self._stream_uri = url
        self._cameras = None
        self._video_stream = []
        self.is_opened = False
        self.Q = Queue(maxsize=128)
        # intialize thread
        self.stopped = False
        self.thread = MyThread(target=self.update, args=())
        self.thread.daemon = True
        self.frame_rate = frame_rate
        self.fps = 0

    def __del__(self):
        pass

    def get_cameras(self):
        # empy for now
        return self._cameras


    def cv_start_streaming(self):
        try:
            self._video_stream = []
            self._video_stream.append(cv2.VideoCapture(self._stream_uri))
            self.fps = int(self._video_stream[0].get(cv2.CAP_PROP_FPS))
            if self.frame_rate is None:
                self.frame_rate = self.fps if self.fps > 0 else 1
            print("fps=", self.fps)
            self.is_opened = True
            self.thread.start()
            print("[INFO] starting video file thread...")
        except Exception as e:
            print("ERROR!! -----", e)
            return 0
        return 1

    def update(self) -> None:
        # keep looping infinitely
        prev_time = 0
        while self.is_opened:    
            try:       
                if self.stopped:
                    return
                (grabbed, frame) = self._video_stream[0].read()
                if not grabbed:
                        self.stopped = True
                time_elapsed = time.time() - prev_time
                if time_elapsed >= (1./self.frame_rate) * 0.95:
                    prev_time = time.time()
                    # add the frame to the queue
                    self.Q.put(frame)
            except cv2.error as e:
                self.is_opened = False
                print(e)


    def is_streaming(self):
        # check current state
        return self.is_opened

    def stop_streaming(self):
        try:
            # simple stop
            self.stopped = True
            self.is_opened = False
            self.thread.stop_it()
            print("wait exit from thread..")
            self.thread.join()
            self._video_stream[0].release()
        except Exception as e:
            print(e)

    def cv_get_frame_raw(self, timeout):
        # todo frame checker
        try:
            frame = self.Q.get(timeout=timeout)
        except Exception as e:
            print("ERROR!! -----", e)
            return None
        return frame


if __name__ == '__main__':
    camera = LocalStreamReciever("rtsp://root:admin@192.168.1.71/axis-media/media.amp?videocodec=h264")
    camera.cv_start_streaming()

    while (camera._video_stream[0].isOpened()):
        frame = camera.cv_get_frame_raw(5)
        if frame is None:
            camera.stop_streaming()
            sys.exit(1)
        frame = imutils.resize(frame, width=1024)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    camera.stop_streaming()

