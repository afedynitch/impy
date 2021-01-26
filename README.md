# impy - (hadronic) interaction models in python

This package implements are generic user interface to popular event generators used in cosmic ray and high-energy particle physics. The purpose of the package is to simplify working with simulations of particle interactions without the need to use Fortran style interfaces to event generators, 'ASCII input cards' and files or C++ dependencies.  

Producing interactions with any of the supported event generators requires simply 

```python
from impy.definitions import *
from impy.constants import *
from impy.kinematics import EventKinematics
from impy import impy_config
import numpy as np

# Define the parameters of the collisions
event_kinematics = EventKinematics(
    ecm=13 * TeV, p1pdg=2212, p2pdg=2212)

# Create an instance of an event generator by passing
# the model name as a string
generator = make_generator_instance(
    interaction_model_by_tag['SIBYLL23D'])

# Initialize it
generator.init_generator(event_kinematics)

# Number of events to generate
nevents = 100
average_pt = 0.

for event in generator.event_generator(event_kinematics, nevents):
    event.filter_final_state_charged()
    # do something with event.p_ids, event.eta, event.en, event.pt, etc.
    # these variables are numpy arrays, that can be histogrammed or counted like
    sel = np.abs(event.p_ids) == 211
    if np.count_nonzero(sel):
        average_pt += 1/float(nevents)*np.mean(event.pt[np.abs(event.p_ids) == 211])

print('Average pT for charged pions {0:4.3f}'.format(average_pt))
```

## Installation

The package is available including the pre-compiled binaries. The installation in that case simplifies to (*this does not work yet use installation from source*):

    pip install impy

To build from source (the **recursive** flag is important to checkout the sub-modules):

    git clone --recursive https://github.com/afedynitch/impy
    cd impy
    make -j<insert number of CPU cores>

The package can be installed in editable mode with `pip install -e .` and will behave as an ordinary pip package but using this source build.

Because of the architectural transition and the many other issue on mac, building from source may be a bit complicated. Using brew gcc and python it is possible to build the code by:

    CC=gcc-10 CXX=gcc-10 FC=gfortran-10 PYTHON_EXE=/usr/local/opt/python@3.8/bin/python3 make -jXXX

Replace `gcc-10` by your version in brew. The official Mac Python is currently broken due to th transition to Apple Silicon.
 
## Requirements

- Python 2.7 - 3.8
- Linux, Mac OS X, or Windows
- pip
- particletools
- numpy
- scipy
- pyyaml
- pyhepmc-ng

## User interface

There are two ways to interact with the code.

1. As in the example above, via plain python in scripts or jupyter notebooks. Look at this [insert link] example.

2. Via a HEPMC output that can be piped in Rivet or other tools supporting the format.

## Supported models

- DPMJET-III 3.0.6
- DPMJET-III 19.1
- EPOS-LHC
- PHOJET 1.12-35
- PHOJET 19.1
- PYTHIA 6
- PYTHIA 8 (not yet bundled)
- QGSJet-01
- QGSJet-II-03
- QGSJet-II-04
- SIBYLL-2.1
- SIBYLL-2.3
- SIBYLL-2.3c
- SIBYLL-2.3d
- SOPHIA
- UrQMD 3.4


## Authors:

- Anatoli Fedynitch
- Hans Dembinski
- Sonia El Hadri
- Keito Watanabe

## LICENSE

The source code of impy is licensed under the [BSD 3-clause license (see LICENSE for detail)](LICENSE). The source codes of the event generators are individually licensed under different conditions (see the COPYING files located in the subdirectories). 
