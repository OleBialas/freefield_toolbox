Freefield: A Toolbox for Conducting Psychoacoustic Experiments
##############################################################

Freefield is the software we are using to run psychoacoustical experiments (mostly concerning spatial hearing) at the
university of Leipzig. The name is a term from the field of acoustics and describes a situation where no sound reflections occur.
While the code is tailored to our experimental setup, some elements (e.g. handling TDT device, head pose estimation) might have broader applicability.

The Setup
---------
Our setup consists of an arc and a dome shaped array of 48 loudspeakers in a anechoic chamber. The loudspeakers are driven
by two RX8 real time processors from Tucker Davis Technologies (TDT).

.. _Installation:

Installation
------------

First of all, you need to have Python (version >= 3.6) installed. If you don't have it yet, I recommend taking a look
at the installation guide for the `Anaconda distribution <https://docs.anaconda.com/anaconda/install/>`_ .

Now you can install this package from github by typing:

.. code-block:: bash

  pip install git+https://github.com/OleBialas/freefield.git

In the same way, you can install slab, another package from our lab which this package depends on:

.. code-block:: bash

  pip install git+https://github.com/DrMarc/soundlab.git

All other dependencies can be installed using pip as well:

.. code-block:: bash

  pip install tensorflow opencv-python numpy setuptools pandas matplotlib pillow scipy

If you are only interested in playing around with the code, this is already sufficient and you can head
to the getting started section. However, if you want to use the experimental setup (only possible on a Windows machine)
there is more work to be done.

To use the functionalities of the processors you have to download and install the drivers from the
`TDT Hompage <https://www.tdt.com/support/downloads/>`_   (install TDT Drivers/RPvdsEx as well as ActiveX Controls).

The communication with these processors relies on the pywin32 package. Since installing it with pip can result
in a faulty version, using conda is preferred :\
`conda install pywin32`

Finally, to use cameras from the manufacturer FLIR systems, you have to install their Python API (Python version >3.8 is not supported).
Go to the `download page <https://meta.box.lenovo.com/v/link/view/a1995795ffba47dbbe45771477319cc3>`_ and select the correct file for your OS and Python version. For example, if you are using
a 64-Bit Windows and Python 3.8 download spinnaker_python-2.2.0.48-cp38-cp38-win_amd64.zip.
Unpack the .zip file and select the folder. There should be a file inside that ends with .whl - install it using pip:\
`pip install spinnaker_python-2.2.0.48-cp38-cp38-win_amd64.whl`

Getting Startet
---------------
If the installation has worked out you should be able to import the package and initialize the setup

.. code-block:: python

  import freefield
  freefield.main.initialize_setup(setup="dome", default_mode="play_rec", camera_type="web")

Something went wrong? Check out the `issues section <https://github.com/OleBialas/freefield/issues>`_ on the projects GitHub.
It Works? Great, no you can check out the other sections of the documentation. If you want to understand how the handling
of the processors works you can check out the section "Working with TDT devices" - this is necessary if you want to
run experimental paradigms that are not yet implemented. If you want to test the standard functions of the setup you
could run a "Localization Test". The section "Loudspeaker Equalization" describes a procedure for measuring and correcting
slight differences between the transfer functions of individual loudspeakers. In "Head Pose Estimation", you will learn
how freefield uses a deep neuronal network to extract the head pose from images.

.. toctree::
  :caption: Contents
  :maxdepth: 2
  :titlesonly:

  procs
  loctest
  equalization
  headpose
  reference

**Index of functions and classes:** :ref:`genindex`

**Searchgthe documentation:** :ref:`search`