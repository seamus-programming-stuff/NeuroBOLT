"""Command line: python -m app.arousal_monitor --eeg run.set --marker TR --model models/vu_model_full.npz --out report/

Offline mode reads the whole recording and standardizes features within it. --stream replays the
recording in 2 s chunks through the real-time monitor and also reports per-volume compute latency.
"""
import argparse
import json

import numpy as np

from . import features, monitor, report
from .model import FrozenModel
from .stream import StreamingMonitor


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eeg", required=True, help="EEG file readable by MNE, MR artefacts already removed")
    parser.add_argument("--model", required=True)
    parser.add_argument("--marker", default=None, help="annotation marking each fMRI volume (e.g. TR, R128)")
    parser.add_argument("--tr", type=float, default=None, help="volume spacing in s, if there are no markers")
    parser.add_argument("--measured", default=None,
                        help="optional .npy of the measured global signal per volume, for validation")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    model = FrozenModel(args.model)
    raw = features.load_raw(args.eeg)
    data, prepared = features.prepare(raw)
    samples = features.frame_samples(prepared, args.marker, args.tr)
    feats, keep = features.features_at(data, samples, prepared.gap_times)
    times = samples[keep] / features.FS
    if args.stream:
        mon = StreamingMonitor(model)
        preds, vig, cursor = [], [], 0
        raw_stream = features.prepare(raw, highpass=None)[0]  # the stream filters causally itself
        for s, ok in zip(samples, keep):
            mon.push(raw_stream[:, cursor:s])
            cursor = s
            out = mon.frame()
            if out is not None and ok:  # frames touching missing EEG are not reported
                preds.append(out[0])
                vig.append(out[1])
        predictions, vigilance = np.array(preds), np.array(vig)
    else:
        predictions = model.predict(feats, standardize="self")
        vigilance = features.vigilance(feats)
    times = times[-len(predictions):]
    frames, summary = monitor.analyse(times, predictions, model.labels, vigilance)
    measured = None
    if args.measured:
        measured = np.load(args.measured)[np.flatnonzero(keep)][-len(predictions):]
    if args.stream:
        summary["latency_ms_median"] = float(np.median(mon.latency_ms))
    summary = report.write(args.out, frames, summary, measured, title=args.eeg.split("/")[-1])
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
