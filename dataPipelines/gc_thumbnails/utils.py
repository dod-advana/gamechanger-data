from pathlib import Path
import fitz

class ThumbnailsCreator:
    def __init__(
        self,
        input_directory,
        output_directory
    ):
        self.input_directory = input_directory
        self.output_directory = output_directory

    def generate_thumbnails(self):
        print('generating')
        p = self.input_directory
        if not self.output_directory.exists():
            self.output_directory.mkdir(exist_ok=True)
        pdf_files = [x for x in p.glob('*.pdf')]
        print(p)
        for file_name in pdf_files:
            filename = str(file_name).split("/")[-1]
            doc = fitz.open(file_name)
            page = doc.loadPage(0)  # number of page
            pix = page.getPixmap()
            out_dir = str(self.output_directory)
            if out_dir[-1] != '/':
                out_dir += '/'
            output = out_dir + filename[:-4] + ".png"
            print(output)
            pix.writePNG(str(output))

            print("wrote PNG: ", output)

        return True
