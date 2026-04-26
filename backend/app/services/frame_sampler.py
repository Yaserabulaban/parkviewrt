class FrameSampler:
    def __init__(self, sample_every_n_frames: int = 10):
        self.sample_every_n_frames = sample_every_n_frames

    def should_process(self, frame_index: int) -> bool:
        return frame_index % self.sample_every_n_frames == 0