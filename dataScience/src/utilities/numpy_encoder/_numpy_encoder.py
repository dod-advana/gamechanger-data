import base64
import json

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """
    Custom json encoder for various numpy `dtypes`.

    C Skiscim, Strider Mcgregor
    """

    def default(self, obj):
        if isinstance(
            obj,
            (
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
            ),
        ):
            return int(obj)
        elif isinstance(obj, (np.ndarray,)):
            enc = self._obj_data(obj)
            output_dict = dict(
                __ndarray__=enc, dtype=str(obj.dtype), shape=obj.shape
            )
            return output_dict
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.datetime64,)):
            return str(obj)
        super(NumpyEncoder, self).default(obj)

    @staticmethod
    def _obj_data(obj):
        if str(obj.dtype).startswith("datetime"):
            return list(obj)
        elif obj.flags["C_CONTIGUOUS"]:
            obj_data = obj.data
        else:
            cont_obj = np.ascontiguousarray(obj)
            assert cont_obj.flags["C_CONTIGUOUS"]
            obj_data = cont_obj.data

        base64_bytes = base64.b64encode(obj_data)
        base64_str = base64_bytes.decode("utf-8")
        return base64_str


def ndarray_hook(obj):
    """
    Decodes a previously encoded numpy `ndarray` with proper `shape` and
    `dtype`. Otherwise, the `obj` argument is returned.

    Args:
        obj (dict): Encoded `ndarray`

    Returns
        (numpy.ndarray): if the input was encoded with the `NumpyEncoder`.
            Otherwise, the `obj` argument is returned.

    """
    if isinstance(obj, dict) and "__ndarray__" in obj:
        if obj["dtype"].startswith("datetime64"):
            return np.array(obj["__ndarray__"], dtype=np.datetime64)
        data = base64.b64decode(obj["__ndarray__"])
        return np.frombuffer(data, obj["dtype"]).reshape(obj["shape"])
    return obj
