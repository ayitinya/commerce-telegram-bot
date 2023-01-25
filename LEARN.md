# Commerce Telegram Bot

A Telegram bot that interacts with users to create orders from an admin updated store.
The [PyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/) is used to interact with the Telegram API.
Store data is stored in a sqlite database and interactions with the database are handled
by [SQLAlchemy](https://www.sqlalchemy.org/).

## Requirements

* Python 3.10 and up (Should work in 3.9, but you would have to convert `match-case` statements to `if` statements)
* [Cloudinary](https://cloudinary.com) account (for image uploads), or just modify the code to use a different image
  hosting service, or just
  remove the image upload functionality.

## Installation

Using a virtual environment is recommended.

```bash
python3 -m venv venv
source venv/bin/activate
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements
from [requirements.txt](requirements.txt).

```bash
pip install -r requirements.txt
```

Copy the [.env.example](.env.example) file to .env and fill in the values.

## Usage

The project was meant to be hosted on [pythonanywhere](https://www.pythonanywhere.com/), so the `main.py` file is meant
to be run as a flask web app.

To run the bot locally, you can use the `bot.py` file.

```bash
python bot.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
