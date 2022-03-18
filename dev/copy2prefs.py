"""
version=2
python>=3.6.8

Copy to prefs

Copy the Katana supertool to a shelf for testing.
"""
import re
import subprocess
from pathlib import Path


CONFIG = {
    "source": Path("../GSVDashboard").resolve(),
    "targets": [
        Path("./prefs/shelfA/prefs/SuperTools"),
        Path("./prefs/shelfB/prefs/SuperTools")
    ]
}


def increment(source: Path):
    """
    Increment the version_publish variable in c.py
    """

    c_file = source / "v1" / "c.py"
    code = c_file.read_text(encoding="utf-8")

    version = re.search(r"v_published\s*=\s*(\d+)", code)
    assert version, f"Can't find <version_publish> in <{c_file}> !"
    new_version = int(version.group(1)) + 1
    new_code = f"v_published = {new_version}"
    new_code = code.replace(version.group(0), str(new_code))

    c_file.write_text(new_code, encoding="utf-8")
    print(f"[{__name__}][increment] Incremented c.py to {new_version}.")
    return


def copy(src: Path, target: Path):

    # build command line arguments
    args = [
        'robocopy',
        str(src),
        str(target),
        # copy option
        "/E",
        # logging options
        "/nfl",  # no file names are not to be logged.
        "/ndl",  # no directory names logged.
        "/np",  # no progress of the copying operation
        "/njh",  # no job header.
        # "/njs",  # no job summary.
    ]
    print(f"[{__name__}][copy] copying src to target ...")
    subprocess.call(args)

    print(
        f"[{__name__}][copy] Finished. Copied :\n"
        f"    <{src}> to\n"
        f"    <{target}>"
    )
    return


def run():

    src_path = CONFIG.get("source")
    target_path_list = CONFIG.get("targets")

    increment(src_path)

    for target_path in target_path_list:

        target_path = target_path / src_path.name
        copy(src=src_path, target=target_path)
        continue

    print(f"[{__name__}][run] Finished)")
    return


if __name__ == '__main__':

    run()
