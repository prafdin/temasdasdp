import socket
import pickle
import numpy as np
import matplotlib.pyplot as plt

img = plt.imread("12_tank.tif")
rng = np.random.default_rng()

def corrupt_img(img):
    # corrupt 20% of pixels
    img = img.copy()
    pixel_mask = rng.random(img.shape) < 0.2
    rand_bytes = rng.integers(0, 256, img.shape, dtype=np.uint8)
    img[pixel_mask] ^= rand_bytes[pixel_mask]
    return img

def send_img(sock, img):
    img = pickle.dumps(img)
    img_size = len(img)
    sock.send(img_size.to_bytes(4, "big"))
    sock.send(img)

img1 = corrupt_img(img)
img2 = corrupt_img(img)

with socket.socket() as sock:
    sock.connect(("127.0.0.1", 4321))
    send_img(sock, img1)
    send_img(sock, img2)
    
print("Sent two images. Goodbye!")
