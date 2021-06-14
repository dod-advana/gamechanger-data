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
        print('generating')
        p = self.input_directory
        if not self.output_directory.exists():
            self.output_directory.mkdir(exist_ok=True)
        pdf_files = [x for x in p.glob('*.pdf')]
        print(p)
        for file_path in pdf_files:
            file_title = file_path.name
            doc = fitz.open(str(file_path))
            page = doc.loadPage(0)  # number of page
            pix = page.getPixmap()
            out_dir = str(self.output_directory)
            if out_dir[-1] != '/':
                out_dir += '/'
            output = out_dir + file_title[:-4] + ".png"
            print(output)
            pix.writePNG(str(output))

            print("wrote PNG: ", output)

        return True
