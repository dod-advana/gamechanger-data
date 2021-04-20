import typing as t
import unittest as ut
import os


class Test_ML_API_Package_Functions(ut.TestCase):

    def test_tensorflow_functions(self):
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # set log level to ERROR
        import tensorflow as tf

        a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
        b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
        c = tf.matmul(a, b)

        self.assertIsNotNone(c)

    def test_torch_functions(self):
        import torch
        import math

        dtype = torch.float
        device = torch.device("cpu")
        # device = torch.device("cuda:0") # Uncomment this to run on GPU

        # Create random input and output data
        x = torch.linspace(-math.pi, math.pi, 2000, device=device, dtype=dtype)
        y = torch.sin(x)

        # Randomly initialize weights
        a = torch.randn((), device=device, dtype=dtype)
        b = torch.randn((), device=device, dtype=dtype)
        c = torch.randn((), device=device, dtype=dtype)
        d = torch.randn((), device=device, dtype=dtype)

        learning_rate = 1e-6
        for t in range(10):
            # Forward pass: compute predicted y
            y_pred = a + b * x + c * x ** 2 + d * x ** 3

            # Compute and print loss
            loss = (y_pred - y).pow(2).sum().item()
            if t % 100 == 99:
                print(t, loss)

            # Backprop to compute gradients of a, b, c, d with respect to loss
            grad_y_pred = 2.0 * (y_pred - y)
            grad_a = grad_y_pred.sum()
            grad_b = (grad_y_pred * x).sum()
            grad_c = (grad_y_pred * x ** 2).sum()
            grad_d = (grad_y_pred * x ** 3).sum()

            # Update weights using gradient descent
            a -= learning_rate * grad_a
            b -= learning_rate * grad_b
            c -= learning_rate * grad_c
            d -= learning_rate * grad_d

            self.assertIsNotNone(a)
            self.assertIsNotNone(b)
            self.assertIsNotNone(c)
            self.assertIsNotNone(d)