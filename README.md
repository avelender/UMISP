# Image Sorter (UMISP)
Ultimate Manual Image Sorter Plus

A program for fast and convenient image sorting into folders using hotkeys.

![Program Screenshot](screenshot.png)

## Features

- View images from the current directory (supports JPG, JPEG, PNG, GIF, BMP, WEBP)
- Quickly move images to folders using hotkeys
- Create, rename, and delete folders directly from the interface
- Customize hotkeys for each folder (any key can be assigned)
- Hotkey settings are saved between sessions
- Support for animated GIFs
- Fullscreen mode (F11)
- Display information about the current file (name, size)
- Open the current file in File Explorer

## How to Use

1. Download the `ImageSorter.exe` file  
2. Copy it to the folder with the images you want to sort  
3. Launch the program by double-clicking it  
4. Create folders for sorting using the "+ Add Folder" button  
5. Browse through images using the Right and Left arrow keys or Space  
6. Move images to the desired folders using buttons or hotkeys  

## Hotkeys

- **Space** – skip the image  
- **→** – next image  
- **←** – previous image  
- **Any key** – move the image to the assigned folder (customizable for each folder)  
- **Ctrl+Z** – undo the last action  
- **F11** – fullscreen mode  
- **Esc** – exit fullscreen mode  

## Configuring Hotkeys

1. Click the button with square brackets `[ ]` next to a folder  
2. In the pop-up window, press any key you want to assign to this folder  
3. The key will be automatically assigned and displayed in the interface  
4. Now you can use this key to quickly move images into that folder  

You can use any keys: letters, numbers, function keys (F1–F12), arrow keys, and others.

**Note:** Your hotkey settings are automatically saved and will be remembered the next time you run the program, even if you move the executable to a different folder.

## System Requirements

- Windows 10 or higher  
- Permission to create folders and move files in the working directory  

## Notes

- The program **moves** (not copies) files into the selected folders  
- If a file with the same name already exists in the target folder, a numeric suffix will be added to the filename  
- The program does not require Python or any additional libraries to be installed  
- All required components are included in the `.exe` file  

## For Developers

If you want to modify the program:

1. Install Python 3.6 or higher  
2. Install the required libraries:

   ```bash
   pip install pillow
   ```

3. The source code is located in the `image_sorter.py` file  
4. To build the `.exe` file, use:

   ```bash
   pip install pyinstaller
   pyinstaller --onefile --windowed image_sorter.py
   ```
