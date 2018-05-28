#!/usr/bin/env python3
import os
import re
import shutil
import sys
from glob import glob
from itertools import filterfalse

import configargparse
from tqdm import tqdm
from ucca.ioutil import gen_files

from semstr.util.amr import ID_PATTERN

desc = """Concatenate files according to order in reference"""


def find_ids(lines):
    for line in lines:
        m = ID_PATTERN.match(line) or re.match("#\s*(\d+).*", line) or re.match("#\s*sent_id\s*=\s*(\S+)", line)
        if m:
            yield m.group(1)


def main(args):
    with open(args.reference, encoding="utf-8") as f:
        # noinspection PyTypeChecker
        order = dict(map(reversed, enumerate(find_ids(f), start=1)))

    def _index(key_filename):
        basename = os.path.basename(key_filename)
        return order.get(basename) or order.get(basename.rpartition("_0")[0])

    files = [f for pattern in args.filenames for f in gen_files(glob(pattern) or [pattern])]
    if len(files) > len(order):
        raise ValueError("Files missing in reference: " + ", ".join(filterfalse(_index, files)))
    if len(order) > len(files):
        print("Warning: reference contains unmatched IDs", file=sys.stderr)
    t = tqdm(sorted(files, key=_index), desc="Writing " + args.out, unit=" files")
    with open(args.out, "wb") as out_f:
        for filename in t:
            t.set_postfix(f=filename)
            with open(filename, "rb") as f:
                shutil.copyfileobj(f, out_f)
                out_f.write(os.linesep.encode("utf-8"))


if __name__ == '__main__':
    argparser = configargparse.ArgParser(description=desc)
    argparser.add_argument("out", help="output file")
    argparser.add_argument("reference", help="file with headers determining the reference order")
    argparser.add_argument("filenames", nargs="+", help="directory or files to join, identified by filename")
    main(argparser.parse_args())