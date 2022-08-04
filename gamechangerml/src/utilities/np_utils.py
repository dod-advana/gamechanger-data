"""
A collection of `numpy` utilities.
"""
import logging

import numpy as np

logger = logging.getLogger(__name__)


def is_zero_vector(v):
    """
    Tests if a vector is a zero vector.

    Args:
        v (numpy.ndarray): vector

    Returns:
        boolean: True if every element is zero
    """
    return np.all(v == 0.0)


def l2_norm_by_row(matrix):
    """
    Row by row l2 norm of a matrix using Einstein summation.

    Args:
        matrix (numpy.ndarray): the matrix

    Returns:
        numpy.ndarray

    """
    return np.sqrt(np.einsum("ij,ij->i", matrix, matrix))


def l2_normed_matrix(matrix):
    """
    Normalizes a matrix using the `l2` norm.

    Args:
        matrix (numpy.ndarray): the matrix

    Returns:
        numpy.ndarray
    """
    l2 = l2_norm_by_row(matrix)
    return matrix / l2[:, None]


def l2_norm_vector(vector):
    if not np.isfinite(vector).all() or is_zero_vector(vector):
        logger.warning("invalid vector")
        if is_zero_vector(vector):
            logger.warning("zero vector")
    norm_ = np.linalg.norm(vector)
    # logger.info("{} {}".format(vector.shape, norm_))
    return np.true_divide(vector, norm_)
