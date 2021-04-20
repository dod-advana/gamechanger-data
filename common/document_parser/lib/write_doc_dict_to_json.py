from pathlib import Path
import json


def write(out_dir="./", ex_dict={}):
    outname = Path(ex_dict["filename"]).stem + '.json'

    p = Path(out_dir)
    if not p.exists():
        p.mkdir()

    with open(p.joinpath(outname), "w") as fp:
        json.dump(ex_dict, fp)

    return True
