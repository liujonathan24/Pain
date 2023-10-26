# Serious Grid World Game (now with zombies!)

BWSI Serious Grid World. A project based approach to learning serious games with AI.

This README will help you get the game running so that you can start your own modifications.

## Prerequisites / Installation

If anyone sees this, it worked :D

First, you need to have Python on your system. If you think you already have python on your computer, you can double
check with the following: Open either `cmd` (Windows) or Terminal (macOS) and type `python --version`. 
If this throws an error, or shows a version less than Python 3.8, please follow the instructions below to install 
python version 3.8 (the code was tested on 3.8.5). 

We will also need a code editor; either PyCharm or Visual Studio Code works if you already have it downloaded. If not, download PyCharm Community Edition [here](https://www.jetbrains.com/pycharm/download/). Be careful to click the one that says Community Edition.

We are using Anaconda for our python package manager. Anaconda is nice because it comes include with a number of 
packages we will need. While we can provide an Anaconda env file for the project, we've found this actually complicates 
installation. Our plan for installation is to provide pip installation (another python package manager) of the 
packages that we need that are not in Anaconda.

Here are instructions for downloading anaconda. Download the latest version or one that comes with python 3.8 or greater.
Graphical installers [found here](https://www.anaconda.com/products/individual). The Anaconda download includes 
python so downloading Anaconda will get you most of the way there.



Once Anaconda abd Python are installed, here are a list of packages that still need to be installed. To install 
these, use pip as follows:
`pip install tensorflow keras keras-rl2 gym==0.2.3 pygame argparse uuid xlrd pandas matplotlib`

## Getting Started
Step 0: Install python and the required packages by following the Prerequisites / Installation above.
Step 1: Download Github Desktop

Click the green "Code" button again and then click open with Github Desktop

This (should) get all the repository files on your system. Python files in the main directory can be run to get
an idea of how to use the game.

# Game Details
Out of the box, this is a command line interface (CLI) game and can be ran from a command prompt (or terminal) or 
from an integrated development environment (IDE). The entry points for the code have "RUN" as a prefix. 

This should run the game itself from terminal (although you must be in the right file):
```
python RUN_Human.py
```

More details about the game and this software implementation will be provided over time via lectures.
