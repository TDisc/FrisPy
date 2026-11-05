FrisPy
======

This repository contains a physical model for a flying disc. Using this code,
one can simulate trajectories of discs with varying initial conditions, while
also changing the underlying physical modlel. This is useful for analyzing
the mechanics of a disc in terms of its design, as well as creating simulated
throws for things like disc launchers or other helpful tools.

This is a pure Python rebuild of the old FrisPy code, which included a version
of the integrator written in C for speed. To obtain a fast version of the
modeling code, either roll back to an old version or check out the
`Frisbee_Simulator <https://github.com/tmcclintock/Frisbee_Simulator>`_
repository.

Installation
------------

For staged HTTP compression and compact rendering responses, see
`Opt-in flight responses <docs/flight-response-options.rst>`_.

From an Anaconda environment
----------------------------

The preferred method of installation is with
`anaconda
<https://docs.conda.io/projects/conda/en/latest/index.html>`_
You can install all the requirements into a compatible environment called
``frispy`` by running the following command:

.. code-block:: bash

   conda env create -f environment.yml

You can then install the package the usual way

.. code-block:: bash

   python setup.py install

You can also use ``pip`` to install the requirements from the
``requirements.txt`` file by running:

.. code-block:: bash

   pip install -r requirements.txt

Then follow this by using the ``setup.py`` file to install.

Testing
-------

Verify your installation by running:

.. code-block:: bash

   pytest

Please report any problems you encounter on the `issues page
<https://github.com/tmcclintock/FrisPy/issues>`_. Thank you!

Running
-------

This can be run in a few different ways.

Google Cloud Run
**********

This can be build and run directly in google cloud run by forking the repo.

Run locally
**********

.. code-block:: bash

  python3 -m pip install -r requirements.txt
  python3 service/main.py

Run From Docker
**********

https://hub.docker.com/r/techdisc/frispy-flight-api
runs on port localhost:8000

