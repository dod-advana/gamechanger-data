from pathlib import Path
import fitz
import typing as t
import multiprocessing
from concurrent.futures import ProcessPoolExecutor


class ThumbnailsCreator:
    def __init__(
        self,
        input_directory: t.Union[str, Path],
        output_directory: t.Union[str, Path],
        shrink_factor: int,
        max_workers: int
    ):
        self.input_directory = Path(input_directory).absolute()
        self.output_directory = Path(output_directory).absolute()
        self.shrink_factor = shrink_factor

        # if we use all available resources
        # NOT recommended. This uses all computing power at once, will probably crash if big directory
        if max_workers < 0:
            self.max_workers = multiprocessing.cpu_count()

        elif max_workers >= 1:
            self.max_workers = max_workers

        else:
            raise ValueError(f"Invalid max_threads value given: ${max_workers}")

    def process_directory(self):
        print('\nGenerating Thumbnails\n')
        self.output_directory.mkdir(exist_ok=True)

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            executor.map(self.generate_thumbnails, (file_path for file_path in self.input_directory.glob('*.pdf')))

    def generate_thumbnails(self, file_path):
        doc = fitz.open(str(file_path))
        page = doc.loadPage(0)  # number of page
        pix = page.getPixmap()
        pix.shrink(self.shrink_factor)   # reduces image size
        output = Path(self.output_directory, file_path.with_suffix('.png').name)
        pix.writePNG(str(output))
        print("wrote PNG: ", output)

        return True
