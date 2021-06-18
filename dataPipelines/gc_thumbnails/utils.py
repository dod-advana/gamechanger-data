from pathlib import Path
import fitz
import typing as t
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

class ThumbnailsCreator:
    def __init__(
        self,
        input_directory: t.Union[str, Path],
        output_directory: t.Union[str, Path],
        max_threads: int
    ):
        self.input_directory = Path(input_directory).absolute()
        self.output_directory = Path(output_directory).absolute()
        self.max_threads = max_threads

    def process_directory(self):
        print('\nGenerating Thumbnails\n')
        self.output_directory.mkdir(exist_ok=True)
        paths = self.input_directory.glob('*.pdf')

        # if we use all available resources
        # NOT recommended. This uses all computing power at once, will probably crash if big directory
        if self.max_threads < 0:
            max_workers = multiprocessing.cpu_count()

        # if we don't use multithreading or if we do partitioned multithreading
        elif self.max_threads >= 1:
            max_workers = self.max_threads

        # else, bad value inserted for max_threads
        else:
            raise ValueError(f"Invalid max_threads value given: ${self.max_threads}")
        print(max_workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.generate_thumbnails, (file_path for file_path in paths))

    def generate_thumbnails(self, file_path):
        doc = fitz.open(str(file_path))
        page = doc.loadPage(0)  # number of page
        pix = page.getPixmap()
        output = Path(self.output_directory, file_path.with_suffix('.png').name)
        pix.writePNG(str(output))
        print("wrote PNG: ", output)

        return True
