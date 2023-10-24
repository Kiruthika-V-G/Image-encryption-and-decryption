# Import necessary libraries
import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import random

# Define the classes for both encryption/decryption and secret sharing
class ImageEncryptionDecryption:
    def __init__(self):
        self.permutation_order = []

    def encrypt(self, image):
        encrypted_image = np.copy(image)
        # Get height and width
        height, width = image.shape[:2]

        #Generating random permutation order (0 to width*height)
        self.permutation_order = np.random.permutation(width * height)

        for i in range(height):
            for j in range(width):
                original_index = i * width + j
                new_index = self.permutation_order[original_index]
                new_i, new_j = divmod(new_index, width)
                encrypted_image[new_i, new_j] = image[i, j]

        return encrypted_image

    def decrypt(self, encrypted_image):
        decrypted_image = np.copy(encrypted_image)
        # Get height and width
        height, width = encrypted_image.shape[:2]  

        #Sort the permutation order for decrypting
        reverse_permutation_order = np.argsort(self.permutation_order)

        for i in range(height):
            for j in range(width):
                original_index = i * width + j
                new_index = reverse_permutation_order[original_index]
                new_i, new_j = divmod(new_index, width)
                decrypted_image[new_i, new_j] = encrypted_image[i, j]

        return decrypted_image

class ImageSecretSharing:
    def __init__(self, threshold=3, n_shares=4):
        self.threshold = threshold
        self.n_shares = n_shares

    def split_image(self, secret_image_path):
        secret_image = Image.open(secret_image_path).convert('RGB')
        width, height = secret_image.size
        shares = [Image.new('RGB', (width, height)) for _ in range(self.n_shares)]

        secret_pixels = np.array(secret_image)

        for row in range(height):
            for col in range(width):
                pixel = secret_pixels[row][col]
                shares[row % self.n_shares].putpixel((col, row), tuple(pixel))

        return shares

    def polynomial_interpolation(self, x, y, degree):
        # Perform polynomial interpolation using numpy.polyfit
        coefficients = np.polyfit(x, y, degree)
        return np.poly1d(coefficients)

    def interpolate_pixel(self, pixel_values, x_values, x_interpolate):
        # Use polynomial interpolation to approximate pixel value at x_interpolate
        interpolated_pixel = [int(self.polynomial_interpolation(x_values, channel_values, 3)(x_interpolate)) for channel_values in zip(*pixel_values)]
        return tuple(interpolated_pixel)

    def interpolate_share(self, share_pixels, x_interpolate):
        width, height = share_pixels[0].size
        interpolated_image = Image.new('RGB', (width, height))

        for row in range(height):
            for col in range(width):
                r_values = [share.getpixel((col, row))[0] for share in share_pixels]
                g_values = [share.getpixel((col, row))[1] for share in share_pixels]
                b_values = [share.getpixel((col, row))[2] for share in share_pixels]
               
                # Interpolate each color channel
                interpolated_r = int(self.polynomial_interpolation(list(range(self.n_shares)), r_values, 3)(x_interpolate))
                interpolated_g = int(self.polynomial_interpolation(list(range(self.n_shares)), g_values, 3)(x_interpolate))
                interpolated_b = int(self.polynomial_interpolation(list(range(self.n_shares)), b_values, 3)(x_interpolate))

                interpolated_pixel = (interpolated_r, interpolated_g, interpolated_b)
                interpolated_image.putpixel((col, row), interpolated_pixel)

        return interpolated_image
   
    def combine_shares(self, share_pixels):
        width, height = share_pixels[0].size
        secret_pixels = np.zeros((height, width, 3), dtype=np.uint8)

        for row in range(height):
            for col in range(width):
                pixel_values = [share.getpixel((col, row)) for share in share_pixels]
                # Interpolate and combine pixel values
                secret_pixel = self.interpolate_pixel(pixel_values, list(range(self.n_shares)), 0)
                secret_pixels[row][col] = secret_pixel

        secret_image = Image.fromarray(secret_pixels)
        return secret_image

def open_image_for_encryption():
    file_path = filedialog.askopenfilename()
    input_image_path_entry_encryption.delete(0, tk.END)
    input_image_path_entry_encryption.insert(0, file_path)

def open_image_for_secret_sharing():
    file_path = filedialog.askopenfilename()
    input_image_path_entry_secret_sharing.delete(0, tk.END)
    input_image_path_entry_secret_sharing.insert(0, file_path)

def encrypt_image():
    input_image_path = input_image_path_entry_encryption.get()

    input_image = Image.open(input_image_path)
    input_image_array = np.array(input_image)

    if len(input_image_array.shape) == 2:  # Check if it's grayscale
        input_image_array = np.stack((input_image_array,) * 3, axis=-1)  # Convert to RGB

    encrypted_image_array = image_encryptor.encrypt(input_image_array)

    encrypted_image = Image.fromarray(encrypted_image_array.astype(np.uint8))
    encrypted_image.save('encrypted_image.png')

def decrypt_image():
    encrypted_image = Image.open('encrypted_image.png')
    encrypted_image_array = np.array(encrypted_image)

    decrypted_image_array = image_encryptor.decrypt(encrypted_image_array)

    decrypted_image = Image.fromarray(decrypted_image_array.astype(np.uint8))
    decrypted_image.save('decrypted_image.png')

def browse_share_path(entry_var):
    file_path = filedialog.askopenfilename()
    entry_var.set(file_path)

def split_image():
    secret_image_path = input_image_path_entry_secret_sharing.get()
    shares = secret_sharer.split_image(secret_image_path)
    for i, share in enumerate(shares):
        share.save(f"share_{i + 1}.png")

    split_status_label.config(text="Image split into shares.")

def reconstruct_image():
    share_paths = [share_path_entries[i].get() for i in range(4)]
    share_images = [Image.open(path) for path in share_paths]
    x_interpolate = 0  # Set the x-coordinate where interpolation is performed
    interpolated_secret = secret_sharer.interpolate_share(share_images, x_interpolate)
    reconstructed_secret = secret_sharer.combine_shares([interpolated_secret] * 4)  # Interpolate and combine shares
    reconstructed_secret.save("reconstructed_secret.png")
    reconstruct_status_label.config(text="Secret reconstructed from shares.")

# Create the main tkinter window
root = tk.Tk()
root.title("Image Encryption/Decryption and Secret Sharing")


# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set the window size to the screen size
root.geometry(f"{screen_width}x{screen_height}")


# Create tabs for encryption/decryption and secret sharing
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Style configuration
style = ttk.Style()

# Define a custom style for buttons
style.configure("Custom.TButton", font=("Helvetica", 12), foreground="black", background="blue")
style.map("Custom.TButton",
          foreground=[('active', 'black')],
          background=[('active', '!disabled', 'red')])

# Define a custom style for labels
style.configure("Custom.TLabel", font=("Helvetica", 12), background="lightgray", padding=(10, 10))

# Encryption/Decryption Tab
encryption_frame = ttk.Frame(notebook)
notebook.add(encryption_frame, text="Encryption/Decryption")

image_encryptor = ImageEncryptionDecryption()

input_image_label_encryption = ttk.Label(encryption_frame, text="Input Image: ", style="Custom.TLabel")
input_image_label_encryption.pack(pady=10)

input_image_path_entry_encryption = tk.Entry(encryption_frame, font=("Helvetica", 12))
input_image_path_entry_encryption.pack(pady=10)

input_image_browse_button_encryption = ttk.Button(encryption_frame, text="Browse", command=open_image_for_encryption, style="Custom.TButton")
input_image_browse_button_encryption.pack(pady=10)

encrypt_button = ttk.Button(encryption_frame, text="Encrypt Image", command=encrypt_image, style="Custom.TButton")
encrypt_button.pack(pady=10)

decrypt_button = ttk.Button(encryption_frame, text="Decrypt Image", command=decrypt_image, style="Custom.TButton")
decrypt_button.pack(pady=10)

# Secret Sharing Tab
secret_sharing_frame = ttk.Frame(notebook)
notebook.add(secret_sharing_frame, text="Secret Sharing")

secret_sharer = ImageSecretSharing(threshold=3, n_shares=4)

input_image_label_secret_sharing = ttk.Label(secret_sharing_frame, text="Input Image:", style="Custom.TLabel")
input_image_label_secret_sharing.pack(pady=10)

input_image_path_entry_secret_sharing = tk.Entry(secret_sharing_frame, font=("Helvetica", 12))
input_image_path_entry_secret_sharing.pack(pady=10)

input_image_browse_button_secret_sharing = ttk.Button(secret_sharing_frame, text="Browse", command=open_image_for_secret_sharing, style="Custom.TButton")
input_image_browse_button_secret_sharing.pack(pady=10)

split_image_button = ttk.Button(secret_sharing_frame, text="Split Image", command=split_image, style="Custom.TButton")
split_image_button.pack(pady=10)

split_status_label = tk.Label(secret_sharing_frame, text="")
split_status_label.pack(pady=10)

share_paths_label = ttk.Label(secret_sharing_frame, text="Share Paths:", style="Custom.TLabel")
share_paths_label.pack(pady=10)

share_path_entries = []
for i in range(4):
    share_path_var = tk.StringVar()
    share_path_entry = tk.Entry(secret_sharing_frame, textvariable=share_path_var)
    share_path_entry.pack(pady=10)

    share_path_button = ttk.Button(secret_sharing_frame, text="Browse", style="Custom.TButton",command=lambda var=share_path_var: browse_share_path(var))
    share_path_button.pack(pady=10)

    share_path_entries.append(share_path_var)

reconstruct_image_button = ttk.Button(secret_sharing_frame, text="Reconstruct Image", command=reconstruct_image, style="Custom.TButton")
reconstruct_image_button.pack(pady=10)

reconstruct_status_label = tk.Label(secret_sharing_frame, text="")
reconstruct_status_label.pack(pady=10)

root.mainloop()