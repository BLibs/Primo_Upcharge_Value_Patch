# Primo Upcharge Patch Script

This script automates the process of identifying discrepancies between catering tray prices and their default upcharge amounts, and patches the upcharge variable to ensure it matches the current price of the tray. This script saves considerable manual labor by eliminating the need to update each item's upcharge individually.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)

## Introduction

In the Primo catering system, each catering tray has a price and a default upcharge amount. However, the upcharge amount is not dynamic—meaning that if the price of the tray is updated, the upcharge remains the same unless manually changed. With over 3,000 items per establishment and more than 120 establishments, updating the upcharge amounts manually would require nearly 365,000 updates.

This script solves that problem by automating the process. It locates discrepancies between the tray price and the upcharge amount, and automatically patches the upcharge variable to match the tray price. The script works across two different catering categories: one for online ordering and another for traditional menus. Some items returned by the API are irrelevant and are filtered out before processing.

The script creates a dataframe of all applicable items from each establishment and filters it down to only those where the tray price and upcharge differ. These items are then grouped into a second dataframe, which is passed to the patching function. After patching, two .csv files are generated—one for failed patches and one for successful patches—allowing for post-execution review.
This script downloads the attachments, extracts the PDF files, and forwards them to the printer without the email body. The script is hosted and scheduled to run every morning on the server at Northside. Each site has its own printer address, intermediary email account, and script.

## Features

- Automatically identifies discrepancies between tray prices and upcharge values
- Supports filtering out irrelevant items from the data
- Processes data for over 3,000 items across 120+ establishments
- Splits results into two .csv files: one for successful patches and one for failed patches
- Automates what would otherwise require 365,000 manual updates

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/BLibs/Primo_Upcharge_Value_Patch/.git
    ```
2. Navigate to the project directory:
    ```sh
    cd Primo_Upcharge_Value_Patch
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

Update the `config.py` file in the project directory and define the following API variable:

```python
APIKEY = 'Put API Key here'
```

## Usage 

The script can either be ran directly as a Python file or compiled into an .exe with Pyinstaller
- Run the script to start the automation process:
    ```sh
    python main.py
    ```
- Compile the .exe which can then be ran in any environment.
    ```sh
    pyinstaller --onefile --clean main.py
    ```
