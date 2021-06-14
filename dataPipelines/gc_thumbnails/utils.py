from pathlib import Path
import fitz
import typing as t

class ThumbnailsCreator:
    def __init__(
        self,
        input_directory: t.Union[str, Path],
        output_directory: t.Union[str, Path]
    ):
        self.input_directory = Path(input_directory).absolute()
        self.output_directory = Path(output_directory).absolute()

    def generate_thumbnails(self):
        print('\nGenerating Thumbnails\n')
        p = self.input_directory
        self.output_directory.mkdir(exist_ok=True)
        pdf_files = [x for x in p.glob('*.pdf')]
        for file_path in pdf_files:
            doc = fitz.open(str(file_path))
            page = doc.loadPage(0)  # number of page
            pix = page.getPixmap()
            output = Path(self.output_directory, file_path.with_suffix('.png').name)
            pix.writePNG(str(output))

            print("wrote PNG: ", output)

        return True
