from pathlib import Path
import fitz

class ThumbnailsCreator:
    def __init__(
        self,
        file_name,
        output_directory
    ):
        self.file_name = file_name
        self.output_directory = output_directory

    def generate_png(self):
        p = Path(self.output_directory)
        if not p.exists():
            p.mkdir()

        filename = str(self.file_name).split("/")[-1]
        doc = fitz.open(self.file_name)
        page = doc.loadPage(0)  # number of page
        pix = page.getPixmap()
        out_dir = str(self.output_directory)
        if out_dir[-1] != '/':
            out_dir += '/'
        output = out_dir + filename[:-4] + ".png"
        print(output)
        pix.writePNG(output)

        print("wrote PNG: ", output)

        return True