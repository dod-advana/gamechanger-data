import json

import numpy as np
import os
import pytest

from numpy_encoder import NumpyEncoder, ndarray_hook

test_vector = np.array([1.0, 2.0, 3.0])
test_mat = np.eye(3)
here = os.path.dirname(os.path.realpath(__file__))


def write_encoded(obj, tdir):
    fp = tdir.mkdir("sub").join("obj.json")
    fp.write(obj)
    return fp


def read_encoded(fp, hook=None):
    with open(fp) as f:
        return json.load(f, object_hook=hook)


@pytest.mark.parametrize(
    "np_dtype",
    [
        np.int_,
        np.intc,
        np.intp,
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.float_,
        np.float16,
        np.float32,
        np.float64,
    ],
)
def test_number_cast(np_dtype, tmpdir):
    num = 42
    num_cast = np_dtype(num)
    encoded = json.dumps(num_cast, cls=NumpyEncoder)

    fp = write_encoded(encoded, tmpdir)
    rw_num = read_encoded(fp)

    rw_num = np_dtype(rw_num)
    assert rw_num == num_cast, num_cast


@pytest.mark.parametrize(
    "np_dtype",
    [
        np.int_,
        np.intc,
        np.intp,
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.float_,
        np.float16,
        np.float32,
        np.float64,
    ],
)
def test_array(np_dtype, tmpdir):
    test_cast = np_dtype(test_mat)
    encoded = json.dumps(test_cast, cls=NumpyEncoder)

    fp = write_encoded(encoded, tmpdir)
    mat = read_encoded(fp, hook=ndarray_hook)

    assert mat.dtype == test_cast.dtype
    assert mat.shape == test_cast.shape
    assert np.allclose(test_cast, mat)


@pytest.mark.parametrize(
    "metadata",
    ["D", "ms"],
)
def test_single_date(tmpdir, metadata):
    date_in = np.datetime64("2020-04", metadata)
    encoded = json.dumps(date_in, cls=NumpyEncoder)

    fp = write_encoded(encoded, tmpdir)
    date_out = np.datetime64(read_encoded(fp, hook=None))

    assert date_in == date_out
    assert isinstance(date_out, np.datetime64)
    assert str(date_in.dtype) == str(date_out.dtype)


def test_date_array(tmpdir):
    date_array = np.arange("2020-01-01", "2020-02-01", dtype=np.datetime64)
    encoded = json.dumps(date_array, cls=NumpyEncoder)
    fp = write_encoded(encoded, tmpdir)
    dates_out = read_encoded(fp, hook=ndarray_hook)
    assert (dates_out == date_array).all()


def test_array_as_list():
    with open(os.path.join(here, "ndarray_as_list.json")) as fp:
        float_array = np.array(json.load(fp, object_hook=ndarray_hook))
    assert isinstance(float_array, np.ndarray)
