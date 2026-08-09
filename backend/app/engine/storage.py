import h5py
import numpy as np

class MetricStore:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = None

    @classmethod
    def create(cls, filepath: str, num_samples: int, max_epochs: int) -> 'MetricStore':
        store = cls(filepath)
        store.file = h5py.File(filepath, 'w')
        chunk_shape = (1, num_samples)
        
        store.file.create_dataset('losses', shape=(max_epochs, num_samples), dtype='f4', chunks=chunk_shape)
        store.file.create_dataset('margins', shape=(max_epochs, num_samples), dtype='f4', chunks=chunk_shape)
        store.file.create_dataset('correctness', shape=(max_epochs, num_samples), dtype='b1', chunks=chunk_shape)
        
        return store
        
    def write_epoch(self, epoch: int, losses: np.ndarray, margins: np.ndarray, correctness: np.ndarray):
        if self.file is None:
            self.file = h5py.File(self.filepath, 'a')
        self.file['losses'][epoch, :] = losses
        self.file['margins'][epoch, :] = margins
        self.file['correctness'][epoch, :] = correctness

    def read_sample_history(self, sample_idx: int) -> dict:
        if self.file is None:
            self.file = h5py.File(self.filepath, 'r')
        return {
            'losses': self.file['losses'][:, sample_idx],
            'margins': self.file['margins'][:, sample_idx],
            'correctness': self.file['correctness'][:, sample_idx]
        }

    def read_epoch(self, epoch: int) -> dict:
        if self.file is None:
            self.file = h5py.File(self.filepath, 'r')
        return {
            'losses': self.file['losses'][epoch, :],
            'margins': self.file['margins'][epoch, :],
            'correctness': self.file['correctness'][epoch, :]
        }

    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
