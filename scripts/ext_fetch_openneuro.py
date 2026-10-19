#!/usr/bin/env python3
"""Download selected files of an OpenNeuro dataset from its public S3 bucket (no credentials needed).

    python3 scripts/ext_fetch_openneuro.py ds006040 $M3_SCRATCH/ext/ds006040 \
        --include 'task-(EC|EO)ON?_run-1' --include 'participants|README|dataset_description' --exclude '/dwi/|/anat/'

Lists every key under the dataset prefix, keeps those matching any --include regex and no --exclude regex,
and downloads them with resume (existing files of the right size are skipped). Uses only the standard library,
so it runs on the M3 login node without the conda env. Run it there: compute nodes have no internet.
"""
import argparse
import concurrent.futures
import os
import re
import sys
import urllib.parse
import urllib.request

BUCKET = "https://s3.amazonaws.com/openneuro.org"


def list_keys(prefix):
    keys, token = [], None
    while True:
        url = f"{BUCKET}?list-type=2&prefix={urllib.parse.quote(prefix)}"
        if token:
            url += "&continuation-token=" + urllib.parse.quote(token)
        xml = urllib.request.urlopen(url, timeout=60).read().decode()
        keys += [(k, int(s)) for k, s in re.findall(r"<Key>([^<]*)</Key>.*?<Size>(\d+)</Size>", xml)]
        match = re.search(r"<NextContinuationToken>([^<]*)</NextContinuationToken>", xml)
        if not match:
            return keys
        token = match.group(1)


def fetch(key, size, root, dataset):
    path = os.path.join(root, key[len(dataset) + 1:])
    if os.path.isfile(path) and os.path.getsize(path) == size:
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    start = os.path.getsize(tmp) if os.path.isfile(tmp) else 0
    request = urllib.request.Request(f"{BUCKET}/{urllib.parse.quote(key)}",
                                     headers={"Range": f"bytes={start}-"} if start else {})
    with urllib.request.urlopen(request, timeout=120) as response, open(tmp, "ab" if start else "wb") as out:
        while True:
            chunk = response.read(1 << 22)
            if not chunk:
                break
            out.write(chunk)
    if os.path.getsize(tmp) != size:
        raise IOError(f"{key}: got {os.path.getsize(tmp)} of {size} bytes")
    os.replace(tmp, path)
    return size


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dataset")
    parser.add_argument("out")
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    keys = [(k, s) for k, s in list_keys(args.dataset + "/")
            if any(re.search(p, k) for p in args.include) and not any(re.search(p, k) for p in args.exclude)]
    total = sum(s for _, s in keys)
    print(f"{len(keys)} files, {total / 1e9:.1f} GB", flush=True)
    if args.dry_run:
        for k, s in keys[:40]:
            print(f"  {k} {s / 1e6:.1f} MB")
        return
    done = 0
    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(fetch, k, s, args.out, args.dataset): k for k, s in keys}
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                done += future.result()
            except Exception as error:  # report and carry on; a rerun resumes
                print(f"FAILED {futures[future]}: {error}", file=sys.stderr, flush=True)
            if i % 20 == 0 or i == len(keys):
                print(f"{i}/{len(keys)} files, {done / 1e9:.1f} GB new", flush=True)


if __name__ == "__main__":
    main()
