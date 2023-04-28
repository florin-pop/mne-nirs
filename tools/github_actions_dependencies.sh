#!/bin/bash -ef

STD_ARGS="--progress-bar off --upgrade"
EXTRA_ARGS=""
if [ ! -z "$CONDA_ENV" ]; then
	pip uninstall -yq mne-nirs
else
	# Changes here should also go in the interactive_test CircleCI job
	python -m pip install $STD_ARGS pip setuptools wheel
	echo "Numpy"
	pip uninstall -yq numpy
	echo "Date utils"
	# https://pip.pypa.io/en/latest/user_guide/#possible-ways-to-reduce-backtracking-occurring
	pip install $STD_ARGS --pre --only-binary ":all:" python-dateutil pytz joblib threadpoolctl six
    echo "pyside6"
	pip install $STD_ARGS --pre --only-binary ":all:" pyside6
	echo "NumPy/SciPy/pandas etc."
	# TODO: Currently missing dipy for 3.10 https://github.com/dipy/dipy/issues/2489
	pip install $STD_ARGS --pre --only-binary ":all:" --no-deps  --default-timeout=60 -i "https://pypi.anaconda.org/scipy-wheels-nightly/simple" numpy scipy pandas scikit-learn statsmodels dipy
	echo "H5py, pillow, matplotlib"
	pip install $STD_ARGS --pre --only-binary ":all:" --no-deps -f "https://7933911d6844c6c53a7d-47bd50c35cd79bd838daf386af554a83.ssl.cf2.rackcdn.com" h5py pillow matplotlib
	echo "Numba, nilearn"
	pip install $STD_ARGS --pre --only-binary ":all:" numba llvmlite nilearn
	echo "VTK"
	# Have to use our own version until VTK releases a 3.10 build
	wget -q https://osf.io/ajder/download -O vtk-9.1.20220406.dev0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
	pip install $STD_ARGS --pre --only-binary ":all:" vtk-9.1.20220406.dev0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
	python -c "import vtk"
	echo "PyVista"
	pip install --progress-bar off git+https://github.com/pyvista/pyvista
	echo "pyvistaqt"
	pip install --progress-bar off git+https://github.com/pyvista/pyvistaqt
	echo "imageio-ffmpeg, xlrd, mffpy"
	pip install --progress-bar off --pre imageio-ffmpeg xlrd mffpy
	if [ "$OSTYPE" == "darwin"* ]; then
	  echo "pyobjc-framework-Cocoa"
	  pip install --progress-bar off pyobjc-framework-Cocoa>=5.2.0
	fi
	EXTRA_ARGS="--pre"
fi

if [ "${MNEPYTHON}" == "dev" ]; then
	MNE_BRANCH="main"
else
	MNE_BRANCH="maint/1.2"
fi
echo "MNE"
pip install $STD_ARGS $EXTRA_ARGS git+https://github.com/mne-tools/mne-python.git@${MNE_BRANCH}

if [ -z "$CONDA_ENV" ]; then
	echo "requirements.txt"
	pip install $STD_ARGS $EXTRA_ARGS --progress-bar off -r requirements.txt
fi

echo "requirements_testing.txt"
pip install --progress-bar off -r requirements_testing.txt
