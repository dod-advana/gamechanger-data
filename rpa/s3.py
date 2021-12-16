import subprocess


def ls(s3_path: str, recursive: bool = False) -> list:
    rec = '--recursive' if recursive else ''
    cmd = f'aws s3 ls {rec} {s3_path}'.split()

    file_list = [
        line.decode() for line
        in subprocess.check_output(cmd).splitlines()
    ]

    return file_list
