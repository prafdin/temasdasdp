import socket
import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import convolve2d

orig = plt.imread("12_tank.tif")

# center_area = (1 / 3)**2 * 5
square_area = 1
circle_area = np.pi / 4
c = (circle_area) / (square_area)
mask = np.array([[c, 1, c], [1, 0, 1], [c, 1, c]])
mask /= mask.sum()

def show_img(img, axis, title=""):
    axis.imshow(img, cmap=plt.cm.gray, vmin=0, vmax=255)
    axis.set_title(title)

def restore_img(img1, img2):
    corrupt_pixels = img1 != img2
    filt_img = convolve2d(img1, mask, boundary="symm", mode="same")
    filt_img = np.round(filt_img).astype(np.uint8)
    return np.where(corrupt_pixels, filt_img, img1)

def recive_img(sock):
    img_size = int.from_bytes(client_socket.recv(4), "big")
    buf = bytearray(img_size)
    view = memoryview(buf)
    
    i = 0
    while i < img_size:
        i += sock.recv_into(view[i:])
        
    return pickle.loads(buf)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind(("127.0.0.1", 4321))
    server_socket.listen(1)
    print("Waiting for connections...")
    
    client_socket, client_address = server_socket.accept()
    print("Client connected:", client_address)
    
    with client_socket:
        img1 = recive_img(client_socket)
        img2 = recive_img(client_socket)

img = restore_img(img1, img2)

fig, axes = plt.subplots(2, 2, figsize=(15, 15))
axes = axes.flatten()
show_img(img1, axes[0], "Corrupted image #1")
show_img(img2, axes[1], "Corrupted image #2")
show_img(orig, axes[2], "Original image")
show_img(img, axes[3], "Restored image")
plt.tight_layout()
plt.show()
