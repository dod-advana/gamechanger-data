from pathlib import Path
import fitz


def generate_png(f_name, out_dir="./"):
    p = Path(out_dir)
    if not p.exists():
        p.mkdir()

    filename = str(f_name).split("/")[-1]
    doc = fitz.open(f_name)
    page = doc.loadPage(0)  # number of page
    pix = page.getPixmap()
    out_dir = str(out_dir)
    if out_dir[-1] != '/':
        out_dir += '/'
    output = out_dir + filename[:-4] + ".png"
    print(output)
    pix.writePNG(output)

    print("wrote PNG: ", output)

    return True
