# CostSplitter
A Python-based GUI application for managing and splitting shared bills among multiple people. Designed using tkinter, the app allows users to input, calculate, and export bill data for easy cost splitting.

---

## Features

- **Bill Entry UI**  
  Add, edit, and delete multiple bills with line items. Each line item can be assigned to a predefined split code to control how the cost is divided.

- **Keyboard Shortcuts**  
  - `Enter`: Add a new bill  
  - `Delete`: Delete the selected line item  
  - `Ctrl + Delete`: Delete the last bill  
  - `Tab`: Add a new line to the current bill

- **Import Bills from Text Files**  
  Supports batch importing of bills from `.txt` files using a structured format:
  - `# Bill Name` – Start the bill with a comment-style title
  - `total` – Total amount and payer’s initial
  - `tax` – Optional; tax will be split evenly among all participants
  - `Line items` – Amount and split code (e.g., `sj`, `a`, `b`)
  - `end` – Indicates the end of a single bill

You can include multiple bills in one file by repeating the above structure.

- **Settings**  
  - Add/remove people
  - Define or edit split codes with different price distributions for each person
  - Select a custom directory to save receipts (it defaults to your working directory)
  - All changes save to an `.ini` configuration file
 
- **Receipt Exporting**  
Generates a timestamped `.txt` file showing:
  - Bill breakdown
  - Individual shares
  - Net owing matrix
  - Final payment summary
    
---

## Getting Started

### Requirements

- Python 3.x

### Run the App

python bill_splitter.py

![Screenshot 2025-04-23 003255](https://github.com/user-attachments/assets/d97453d7-2c46-48cd-85d1-c5f29da7ef88)
![Screenshot 2025-04-23 003222](https://github.com/user-attachments/assets/04541584-b948-49e9-81fa-bb3e3a2a61fb)
