from abc import ABCMeta, abstractmethod

class IInterfaceReciever:
    __metaclass__ = ABCMeta

    @classmethod
    def version(self): return "1.0"
    @abstractmethod
    def start_streaming(self): raise NotImplementedError
    @abstractmethod
    def stop_streaming(self): raise NotImplementedError
    @abstractmethod
    def IsStreaming(self): raise NotImplementedError
    @abstractmethod
    def get_frame_raw(self): raise NotImplementedError
    @abstractmethod
    def cv_start_streaming(self): raise NotImplementedError
    @abstractmethod
    def cv_get_frame_raw(self): raise NotImplementedError
    @abstractmethod
    def get_devices(self): raise NotImplementedError
    @abstractmethod
    def change_devices(self): raise NotImplementedError
    def update(self): raise NotImplementedError
