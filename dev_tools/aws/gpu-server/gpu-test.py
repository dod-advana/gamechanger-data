#!/opt/gc-transformer-venv-green/bin/python
import tensorflow as tf
import torch
from transformers import BertModel, BertTokenizer

def tensorflow_test():
    print("[START] Tensorflow GPU Test")
    with tf.device('/gpu:0'):
        a = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[2, 3], name='a')
        b = tf.constant([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], shape=[3, 2], name='b')
        c = tf.matmul(a, b)
        print(c)

    print("[END] Tensorflow GPU Test\n")

def torch_test():
    print("[START] Torch GPU Test")
    gpu_available = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0)
    gpu_count = torch.cuda.device_count()
    cuda_version = torch.version.cuda
    if gpu_available:
        print(f"GPU Detected")
        print(f"GPU:\t\t{gpu_name}")
        print(f"GPU count:\t{gpu_count}")
        print(f"CUDA version:\t{cuda_version}")
        print("")
        print("Test Loading Model...")
        model = BertModel.from_pretrained('bert-base-uncased')
        print("Moving model to GPU...")
        model = model.cuda()
        print("Performing test inference")
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        sample_text = "Sample Text"
        tokens = tokenizer(sample_text, return_tensors = 'pt')
        tokens = {key:value.cuda() for key, value in tokens.items()}
        outputs = model(**tokens)
        print(outputs)
        print("All tests done...")
    else:
        print(f"No GPU Detected")
    print("[END] Torch GPU Test\n")

if __name__ == "__main__":
    tensorflow_test()
    torch_test()
