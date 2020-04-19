# Authors: Robert Luke <mail@robertluke.net>
#
# License: BSD (3-clause)

import os
import mne
import mne_nirs
import numpy as np
from mne_nirs.experimental_design import create_first_level_design_matrix,\
    plot_GLM_topo, run_GLM


def _load_dataset():
    """Load data and tidy it a bit"""
    fnirs_data_folder = mne.datasets.fnirs_motor.data_path()
    fnirs_raw_dir = os.path.join(fnirs_data_folder, 'Participant-1')
    raw_intensity = mne.io.read_raw_nirx(fnirs_raw_dir,
                                         verbose=True).load_data()

    raw_intensity.annotations.crop(raw_intensity.annotations.onset[0],
                                   raw_intensity.annotations.onset[-1])

    new_des = [des for des in raw_intensity.annotations.description]
    new_des = ['A' if x == "1.0" else x for x in new_des]
    new_des = ['B' if x == "2.0" else x for x in new_des]
    new_des = ['C' if x == "3.0" else x for x in new_des]
    annot = mne.Annotations(raw_intensity.annotations.onset,
                            raw_intensity.annotations.duration, new_des)
    raw_intensity.set_annotations(annot)

    picks = mne.pick_types(raw_intensity.info, meg=False, fnirs=True)
    dists = mne.preprocessing.nirs.source_detector_distances(
        raw_intensity.info, picks=picks)
    raw_intensity.pick(picks[dists > 0.01])

    assert 'fnirs_raw' in raw_intensity
    assert len(np.unique(raw_intensity.annotations.description)) == 4

    return raw_intensity


def test_create_boxcar():
    raw_intensity = _load_dataset()
    raw_intensity = raw_intensity.pick(picks=[0])  # Keep the test fast
    bc = mne_nirs.experimental_design.create_boxcar(raw_intensity)

    assert bc.shape[0] == raw_intensity._data.shape[1]
    assert bc.shape[1] == len(np.unique(raw_intensity.annotations.description))

    assert np.max(bc) == 1
    assert np.min(bc) == 0

    # The value of the boxcar should be 1 when a trigger fires
    assert bc[int(raw_intensity.annotations.onset[0] *
                  raw_intensity.info['sfreq']), :][0] == 1

    # Only one condition was ever present at a time in this data
    # So boxcar should never overlap across channels
    assert np.max(np.mean(bc, axis=1)) * bc.shape[1] == 1


def test_create_design():
    raw_intensity = _load_dataset()
    raw_intensity.crop(450, 600)  # Keep the test fast
    design_matrix = create_first_level_design_matrix(raw_intensity,
                                                     drift_order=1,
                                                     drift_model='polynomial')

    assert design_matrix.shape[0] == raw_intensity._data.shape[1]
    # Number of columns is number of conditions plus the drift plus constant
    assert design_matrix.shape[1] ==\
        len(np.unique(raw_intensity.annotations.description)) + 2


def test_run_GLM():
    raw_intensity = _load_dataset()
    raw_intensity.crop(450, 600)  # Keep the test fast
    design_matrix = create_first_level_design_matrix(raw_intensity,
                                                     drift_order=1,
                                                     drift_model='polynomial')
    raw_od = mne.preprocessing.nirs.optical_density(raw_intensity)
    raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od)
    labels, glm_estimates = run_GLM(raw_haemo, design_matrix)

    assert len(labels) == len(raw_haemo.ch_names)

    # the estimates are nested. so cycle through to check correct number
    # are generated
    num = 0
    for est in glm_estimates:
        num += glm_estimates[est].theta.shape[1]
    assert num == len(raw_haemo.ch_names)


def test_run_plot_GLM_topo():
    raw_intensity = _load_dataset()
    raw_intensity.crop(450, 600)  # Keep the test fast

    design_matrix = create_first_level_design_matrix(raw_intensity,
                                                     drift_order=1,
                                                     drift_model='polynomial')
    raw_od = mne.preprocessing.nirs.optical_density(raw_intensity)
    raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od)
    labels, glm_estimates = run_GLM(raw_haemo, design_matrix)
    fig = plot_GLM_topo(raw_haemo, labels, glm_estimates, design_matrix)
    # 5 conditions (A,B,C,Drift,Constant) * two chroma
    assert len(fig.axes) == 10

    fig = plot_GLM_topo(raw_haemo, labels, glm_estimates, design_matrix,
                        requested_conditions=['A', 'B'])
    # Two conditions * two chroma
    assert len(fig.axes) == 4
