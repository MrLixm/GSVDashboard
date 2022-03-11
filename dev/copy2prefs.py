"""
version=1
python=>3.6.8

Copy to prefs

Copy the Katana supertool to a shelf for testing.
"""

import subprocess
from pathlib import Path


CONFIG = {
    "source": Path("../GSVDashboard").resolve(),
    "target": Path(r"Z:\dccs\katana\library\shelf0005\content\SuperTools")
}


def run():

    src_path = CONFIG.get("source")
    target_path = CONFIG.get("target") / src_path.name

    # build command line arguments
    args = [
        'robocopy',
        str(src_path),
        str(target_path),
        # copy option
        "/E",
        # logging options
        "/nfl",  # no file names are not to be logged.
        "/ndl",  # no directory names logged.
        "/np",  # no progress of the copying operation
        "/njh",  # no job header.
        # "/njs",  # no job summary.
    ]
    print(f"[{__name__}][run] copying src to target ...")
    subprocess.call(args)

    print(
        f"[{__name__}][run] Finished. Copied :\n"
        f"    <{src_path}> to\n"
        f"    <{target_path}>"
    )
    return


if __name__ == '__main__':

    run()
