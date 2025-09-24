import tkinter as tk
from tkinter import ttk, messagebox
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import threading

# --- Map regions to endpoints ---
REGION_TO_ENDPOINT = {
    "us-west-000": "https://s3.us-west-000.backblazeb2.com",
    "us-west-001": "https://s3.us-west-001.backblazeb2.com",
    "us-west-002": "https://s3.us-west-002.backblazeb2.com",
    "eu-central-003": "https://s3.eu-central-003.backblazeb2.com",
    "us-west-004": "https://s3.us-west-004.backblazeb2.com",
    "us-east-005": "https://s3.us-east-005.backblazeb2.com",
    "ca-east-006": "https://s3.ca-east-006.backblazeb2.com",
}

class BackblazeBucketChecker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Backblaze B2 Bucket Size Checker")
        self.geometry("500x400")
        
        # Initialize boto3 client
        self.s3_client = None
        
        # Set up GUI components
        self.create_widgets()
        
    def create_widgets(self):
        # Frame for input fields
        input_frame = ttk.LabelFrame(self, text="Bucket Information")
        input_frame.pack(padx=10, pady=10, fill="x")

        # App Key ID
        ttk.Label(input_frame, text="App Key ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.key_id_entry = ttk.Entry(input_frame, width=40)
        self.key_id_entry.grid(row=0, column=1, padx=5, pady=5)

        # App Key
        ttk.Label(input_frame, text="App Key:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.key_entry = ttk.Entry(input_frame, width=40, show="*")
        self.key_entry.grid(row=1, column=1, padx=5, pady=5)

        # Bucket Name
        ttk.Label(input_frame, text="Bucket Name:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.bucket_name_entry = ttk.Entry(input_frame, width=40)
        self.bucket_name_entry.grid(row=2, column=1, padx=5, pady=5)

        # --- NEW: Region Dropdown ---
        ttk.Label(input_frame, text="Region:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.region_var = tk.StringVar(self)
        self.region_dropdown = ttk.Combobox(input_frame, width=38, textvariable=self.region_var, state="readonly")
        self.region_dropdown['values'] = list(REGION_TO_ENDPOINT.keys())
        self.region_dropdown.grid(row=3, column=1, padx=5, pady=5)
        self.region_dropdown.set("us-west-004") # Set a default value
        
        # Frame for buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(padx=10, pady=5, fill="x")
        
        # Run Button
        self.run_button = ttk.Button(button_frame, text="Run Bucket Check", command=self.start_check_thread)
        self.run_button.pack(side="left", expand=True, fill="x", padx=5)
        
        # Reset Button
        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_fields)
        self.reset_button.pack(side="left", expand=True, fill="x", padx=5)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", mode="indeterminate")
        self.progress_bar.pack(padx=10, pady=10, fill="x")

        # Running total label
        self.running_total_label = ttk.Label(self, text="Running Total: 0.00 GB")
        self.running_total_label.pack(padx=10, pady=5)

        # Result message box
        self.result_text = tk.Text(self, height=10, state="disabled", wrap="word")
        self.result_text.pack(padx=10, pady=10, fill="both", expand=True)

    def start_check_thread(self):
        """Starts the check in a separate thread to prevent GUI freezing."""
        key_id = self.key_id_entry.get()
        key = self.key_entry.get()
        bucket_name = self.bucket_name_entry.get()
        selected_region = self.region_var.get()

        if not key_id or not key or not bucket_name or not selected_region:
            messagebox.showerror("Error", "All fields must be filled out.")
            return

        self.run_button.config(state="disabled")
        self.progress_bar.start()
        self.update_result_text("Starting bucket size calculation...")
        
        # Use a thread to run the potentially long-running operation
        threading.Thread(target=self.calculate_bucket_size, args=(key_id, key, bucket_name, selected_region)).start()
        
    def update_result_text(self, message):
        """Helper function to update the result text widget."""
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, message)
        self.result_text.config(state="disabled")

    def calculate_bucket_size(self, key_id, key, bucket_name, region):
        """Calculates the total size of the bucket, including all versions and delete markers."""
        total_size = 0
        file_count = 0
        
        try:
            # --- NEW: Get the endpoint from the selected region ---
            endpoint_url = REGION_TO_ENDPOINT.get(region)
            if not endpoint_url:
                raise ValueError("Invalid region selected.")
                
            # Initialize the boto3 client with Backblaze credentials and the selected endpoint
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                endpoint_url=endpoint_url,
                aws_access_key_id=key_id,
                aws_secret_access_key=key
            )
            
            # Use a paginator for large buckets
            paginator = self.s3_client.get_paginator('list_object_versions')
            pages = paginator.paginate(Bucket=bucket_name)

            for page in pages:
                # Iterate through all versions
                if 'Versions' in page:
                    for obj in page['Versions']:
                        total_size += obj['Size']
                        file_count += 1
                        # Update the running total display to base 10 GB
                        self.after(1, lambda s=total_size: self.running_total_label.config(text=f"Running Total: {s / (1000*1000*1000):.2f} GB"))
                
                # Iterate through all delete markers
                if 'DeleteMarkers' in page:
                    for marker in page['DeleteMarkers']:
                        file_count += 1

            # Display the final results using decimal (base 10) for MB and GB
            final_size_mb_base10 = total_size / (1000 * 1000)
            final_size_gb_base10 = total_size / (1000 * 1000 * 1000)

            # Display the final results using binary (base 2) for MB and GB
            final_size_mb_base2 = total_size / (1024 * 1024)
            final_size_gb_base2 = total_size / (1024 * 1024 * 1024)

            self.update_result_text(
                f"Bucket: {bucket_name}\n"
                f"Total Size: {total_size} bytes\n"
                f"Total Size in decimal (base 10): {final_size_mb_base10:.2f} MB ({final_size_gb_base10:.2f} GB)\n"
                f"Total Size in binary (base 2): {final_size_mb_base2:.2f} MB ({final_size_gb_base2:.2f} GB)\n"
                f"Total File Count: {file_count}"
            )
            
        except NoCredentialsError:
            self.update_result_text("Error: Invalid credentials.")
            messagebox.showerror("Error", "Invalid credentials. Please check your App Key ID and App Key.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                self.update_result_text("Error: Bucket not found.")
                messagebox.showerror("Error", "Bucket not found. Please check the bucket name.")
            else:
                self.update_result_text(f"An unexpected error occurred: {e}")
                messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        except Exception as e:
            self.update_result_text(f"An unexpected error occurred: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            self.progress_bar.stop()
            self.run_button.config(state="normal")
            
    def reset_fields(self):
        """Resets all input fields and result displays."""
        self.key_id_entry.delete(0, tk.END)
        self.key_entry.delete(0, tk.END)
        self.bucket_name_entry.delete(0, tk.END)
        self.region_dropdown.set("us-west-004") # Reset the dropdown to its default
        self.running_total_label.config(text="Running Total: 0.00 GB")
        self.update_result_text("") # Clear the result box

# --- Entry Point ---
if __name__ == "__main__":
    app = BackblazeBucketChecker()
    app.mainloop()