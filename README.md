# napari-particle-tracking

[![License MIT](https://img.shields.io/pypi/l/napari-particle-tracking.svg?color=green)](https://github.com/zeroth/napari-particle-tracking/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-particle-tracking.svg?color=green)](https://pypi.org/project/napari-particle-tracking)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-particle-tracking.svg?color=green)](https://python.org)
[![tests](https://github.com/zeroth/napari-particle-tracking/workflows/tests/badge.svg)](https://github.com/zeroth/napari-particle-tracking/actions)
[![codecov](https://codecov.io/gh/zeroth/napari-particle-tracking/branch/main/graph/badge.svg)](https://codecov.io/gh/zeroth/napari-particle-tracking)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-particle-tracking)](https://napari-hub.org/plugins/napari-particle-tracking)

A plugin for Particle tracking using xgboost based pixel classifier and trackpy

----------------------------------

This [napari] plugin was generated with [copier] using the [napari-plugin-template].

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/napari-plugin-template#getting-started

and review the napari docs for plugin developers:
https://napari.org/stable/plugins/index.html
-->

## Installation

You can install `napari-particle-tracking` via [pip]:

    pip install napari-particle-tracking




## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [MIT] license,
"napari-particle-tracking" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[copier]: https://copier.readthedocs.io/en/stable/
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[napari-plugin-template]: https://github.com/napari/napari-plugin-template

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/


# remove me later
1. `cd` into your new directory
    cd napari-particle-tracking
    # you probably want to install your new package into your env
    pip install -e .

2. Create a github repository for your plugin:
    https://github.com/new
3. Add your newly created github repo as a remote and push:
    git remote add origin https://github.com/your-repo-username/your-repo-name.git
    git push -u origin main
    Don't forget to add this url to setup.cfg!
    [metadata]
    url = https://github.com/your-repo-username/your-repo-name.git
4. Consider adding additional links for documentation and user support to setup.cfg
    using the project_urls key e.g.
    [metadata]
    project_urls =
        Bug Tracker = https://github.com/your-repo-username/your-repo-name/issues
        Documentation = https://github.com/your-repo-username/your-repo-name#README.md
        Source Code = https://github.com/your-repo-username/your-repo-name
        User Support = https://github.com/your-repo-username/your-repo-name/issues
5. Read the README for more info: https://github.com/napari/napari-plugin-template
6. We've provided a template description for your plugin page on the napari hub at `.napari-hub/DESCRIPTION.md`.
    You'll likely want to edit this before you publish your plugin.
7. Consider customizing the rest of your plugin metadata for display on the napari hub:
    https://github.com/chanzuckerberg/napari-hub/blob/main/docs/customizing-plugin-listing.md
