import requests
import zipfile
import os
import platform

def install_chromedriver():
    """Download and install ChromeDriver automatically"""
    try:
        # Get Chrome version (simplified)
        chrome_version = "119.0.6045.105"  # Use stable version
        
        # Download ChromeDriver
        if platform.system() == "Windows":
            url = f"https://chromedriver.storage.googleapis.com/119.0.6045.105/chromedriver_win32.zip"
            filename = "chromedriver.zip"
        else:
            url = f"https://chromedriver.storage.googleapis.com/119.0.6045.105/chromedriver_linux64.zip"
            filename = "chromedriver.zip"
        
        print("Downloading ChromeDriver...")
        response = requests.get(url)
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        # Extract
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # Cleanup
        os.remove(filename)
        
        print("ChromeDriver installed successfully!")
        return True
        
    except Exception as e:
        print(f"Error installing ChromeDriver: {e}")
        print("Please download ChromeDriver manually from: https://chromedriver.chromium.org/")
        return False

if __name__ == "__main__":
    install_chromedriver()