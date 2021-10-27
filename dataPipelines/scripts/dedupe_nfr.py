import subprocess
import re
from time import sleep

from_bucket = "advana-data-zone/"
from_prefix = "bronze/gamechanger/tmp/nfr_flat"

to_prefix = "bronze/gamechanger/tmp/nfr_deduped"

path_re = re.compile(f'{from_prefix}.*')


def run():
    cmd = f'aws s3 ls "s3://{from_bucket}{from_prefix}" --recursive'
    print('running ls cmd:', cmd)

    result = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE
    )
    out = result.stdout.decode('utf-8')
    paths = path_re.findall(out)
    paths.sort(reverse=True)
    to_keep = {}
    to_remove = []
    for path in paths:
        first, part, last = path.rpartition('/')
        if not last:
            continue
        if last in to_keep:
            to_remove.append(path)
        else:
            to_keep[last] = path

    print('removing', len(to_remove), 'keeping', len(to_keep))

    DRY_RUN = True

    for m in to_keep.values():
        prefixpath = m.replace(from_prefix, '')
        mvfrom = f'"s3://{from_bucket}{m}"'
        mvto = f'"s3://{from_bucket}{to_prefix}{prefixpath}"'
        dry = ' --dryrun' if DRY_RUN else ''
        mvcmd = f'aws s3 cp {mvfrom} {mvto}{dry}'
        print('running cp cmd', mvfrom, mvto, sep='\n')
        result = subprocess.check_output(
            mvcmd,
            shell=True,
        )
        print(result.decode('utf-8'))
        sleep(0.01)  # helps keep the console from stuttering


if __name__ == '__main__':
    run()
