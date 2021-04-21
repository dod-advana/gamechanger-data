JSON Serialization for ``numpy`` Objects
========================================

|Language| |Test| |Maintenance| |MIT License|

This is a custom ``json`` encoder/decoder for ``numpy`` objects. It's a useful utility
in a number of obvious contexts, notably storing and retrieving test data, and
in REST APIs. The advantage this class offers is primarily for ``ndarrays``. This will
preserve and restore the original ``dtype`` and ``shape``.

This implementation extends the open source PyPi package `numpyencoder`_
method for ``numpy`` arrays using the ideas in `this post`_.
In addition,  ``numpy`` types ``datetime64[D]``
and ``datetime64[ms]`` objects are supported.

Getting Started
===============
Download or clone the repository and

::

   python setup.py install

Tests can be run from ``setup`` if ``pytest`` is installed:

::

   python setup.py test

or the usual

::

   py.test -v


Example Usage
=============

``numpy`` Variables
-------------------
At present, the encoded object requires a cast to restore its ``dtype``:

::

    >>> from numpy_encoder import NumpyEncoder, ndarray_hook
    >>> import json
    >>> import numpy as np
    >>>
    >>> x = np.float64(1.0)
    >>> encoded = json.dumps(x, cls=NumpyEncoder)
    >>>
    >>> x_ = np.float64(json.loads(encoded))
    >>> x_.dtype
    dtype('float64')


Encoding a Matrix
-----------------
The majority of use-cases involve arrays.
The array *data* is extracted from the ``ndarray``, ``base64`` encoded, and stored
in a ``dict`` along with the ``dtype`` and ``shape``, *viz.*,

::

    >>> from numpy_encoder import NumpyEncoder, ndarray_hook
    >>> import json
    >>> import numpy as np
    >>>
    >>> np_object = np.eye(3, dtype=np.float32)
    >>> np_object
    array([[1., 0., 0.],
       [0., 1., 0.],
       [0., 0., 1.]], dtype=float32)
    >>>
    >>> encoded = json.dumps(np_object, cls=NumpyEncoder)
    >>> encoded
    {"__ndarray__": "AACAPwAAAAAAAAAAAAAAAAAAgD8AAAAAAAAAAAAAAAAAAIA/", "dtype": "float32", "shape": [3, 3]}


Decoding a Matrix
-----------------
::

    >>> data = json.loads(encoded, object_hook=ndarray_hook)
    >>> data.shape
    (3,3)
    >>> data.dtype
    dtype('float32')

Note the additional argument ``hook=ndarray_hook``. this reconstructs the original object
from the ``dict``. If your array object was previously stored as a `list`,
the ``hook=ndarray_hook`` is optional. However, the object will need to made into
an ``ndarray`` with the appropriate ``dtype``.

Supported ``dtypes``
--------------------
- ``np.int_`` ``np.intc`` ``np.intp`` ``np.int8`` ``np.int16`` ``np.int32`` ``np.int64``
- ``np.uint8`` ``np.uint16`` ``np.uint32`` ``np.uint64``
- ``np.float_`` ``np.float16`` ``np.float32`` ``np.float64``
- ``np.datetime64[D]``, ``np.datetime64[ms]``
- ``np.ndarray``

Contributing, Bug Reporting, etc.
=================================
Contributions are welcome. Please open a pull request.
For bug reporting or enhancement requests, etc., please use the ISSUE_TEMPLATE in
the ``/.github`` directory.


.. role::  raw-html(raw)
    :format: html

License
=======
The MIT License (MIT)

Copyright :raw-html:`&copy;` 2020 Chris Skiscim, Zachary McGregor-Dorsey

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

.. _numpyencoder: https://pypi.org/project/numpyencoder/
.. _this post: https://stackoverflow.com/questions/3488934/simplejson-and-numpy-array/24375113#24375113
.. |Language| image:: https://img.shields.io/badge/language-python3-blue.svg?maxAge=259200
.. |Test| image:: https://img.shields.io/badge/test-passed-success.svg?maxAge=259200
.. |Maintenance| image:: https://img.shields.io/badge/Maintained%3F-yes-green.svg?maxAge=259200
.. |MIT License| image:: https://img.shields.io/badge/License-MIT-blue.svg?maxAge=259200
