import unittest as ut
import os

GPU_PRESENT = True if os.environ.get('GPU_PRESENT', '').lower() == 'yes' else False


class TestPackageFunctions(ut.TestCase):

    def test_tensorflow_functions(self):
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # set log level to ERROR
        import tensorflow as tf
        from tensorflow.python.client import device_lib

        def _run_test(device_id: str) -> bool:
            with tf.device(device_id):
                a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
                b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
                c = tf.matmul(a, b)

                return c is not None

        gpu_devices = [a for a in device_lib.list_local_devices() if a.device_type.lower() == 'gpu']

        if GPU_PRESENT:
            last_runtime_error = None
            gpu_count = len(gpu_devices)

            if not gpu_count:
                self.fail('No GPU devices found')
            else:
                for device_number in range(gpu_count):
                    try:
                        result = _run_test(f"/gpu:{device_number}")
                        if result:
                            self.assertIsNotNone(result)
                            last_runtime_error = None
                            break
                    except RuntimeError as e:
                        last_runtime_error = e
                if last_runtime_error:
                    raise last_runtime_error
        else:
            self.assertTrue(_run_test("/cpu:0"))


    def test_torch_functions(self):
        import torch
        import math

        def _run_test(device_id: str) -> bool:
            dtype = torch.float
            device = torch.device(device_id)

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

                return all([a,b,c,d])

        if GPU_PRESENT:
            last_runtime_error = None
            gpu_count = torch.cuda.device_count()

            if not gpu_count:
                self.fail('No GPU devices found')
            else:
                for device_number in range(gpu_count):
                    try:
                        result = _run_test(f"cuda:{device_number}")
                        if result:
                            self.assertIsNotNone(result)
                            last_runtime_error = None
                            break
                    except RuntimeError as e:
                        last_runtime_error = e
                if last_runtime_error:
                    raise last_runtime_error
        else:
            self.assertTrue(_run_test("cpu"))

