## Python Fullstack Example: PIXEL INSPIRATION
As a hobbyist amateur pixel art artist and animator, I find myself in need of inspiration for composition, texture, and even color palette. This app is designed to accept simple image-generator prompts and then produce sequences of useful displays of silhouetting, texture, and color palettes, as well as provide permalinks for future reference for those! By prompting the app, you can receive a highly-processed image output, with some useful utilities for quickly grabbing the color palette, viewing the original materials, or even copypasting the pixel-sized information.

This should also, hopefully, demonstrate the DB caching, the feedback-focused UI, and the integration with the AI model, such as it is. Happy reviewing, reviewer!

## Requirements

Want to run this? Here's some things you'll need.
- An installation of [Python 3](https://www.python.org/downloads/).
- About 6GB of free space for the associated models.
- No apps currently running that use port 5000.

## Recommendations
It's nice to have these, and they will significantly speed up generation or access rates.
- One or more graphics cards with CUDA compatibility.
- CUDA drivers.
- A [MySQL DB](https://dev.mysql.com/downloads/installer/) installed.
- An environmental variable set to the URI of that DB at `LUCRA_AI_QUERIES_DATABASE_URI`. See setup instructions if more details are needed.

## Setup Process
### Windows/Linux
Install and activate a [MySQL database](https://dev.mysql.com/downloads/installer/), using the [provided documentation](https://dev.mysql.com/doc/mysql-getting-started/en/). Make sure a new schema has been named and a new user and password have been created.

Set the environment variable `LUCRA_AI_QUERIES_DATABASE_URI` to a MySQL URI formatted like `mysql+pymysql://user:pass@domain/name`. For example, set it to `mysql+pymysql://testuser:h3ll0Lucra37894@localhost/aiquerycache`. You can double-check that this was successful by opening a new window for the command line and typing "echo %LUCRA_AI_QUERIES_DATABASE_URI%" if you're on Windows, or "echo $LUCRA_AI_QUERIES_DATABASE_URI" if you're on Linux, and confirming you can see your URI.

Install [Python 3](https://www.python.org/downloads/) and confirm its installation by opening a new command line window and typing `python --version`. If you see a Python 3 version, you have successfully installed.

Install CUDA drivers appropriate to your graphics card hardware, if applicable. This will accelerate performance for the app by orders of magnitude.

### Windows
Double-click "setup.bat" in the main folder, and enjoy the app by navigating to the [front page](http://127.0.0.1:5000/)!

### Linux
Double-click "setup.sh" in the main folder, and enjoy the app by navigating to the [front page](http://127.0.0.1:5000/)!



### I'm a developer reviewing a take-home project and I already know all that, plus I already have most of that set up. My eye was caught by this header when I skimmed this readme!

All you need is the `LUCRA_AI_QUERIES_DATABASE_URI` variable set to the MySQL URI, the app will self-establish its own table. If no DB is found, it'll revert to DBless behavior. You can just run main.py with python and go to http://127.0.0.1:5000/.
