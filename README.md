# Commerce Telegram Bot

A Telegram bot that interacts with users to create orders from an admin updated store.
The [PyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/) is used to interact with the Telegram API.
Store data is stored in a cloud firestore database and interactions

## Requirements

* Python 3.11 and up
* [Firebase](https://firebase.com) account for image uploads, cloud functions, and hosting of [FireCMS](https://firecms.co)

## Installation

Using a virtual environment is recommended.

```bash
python3 -m venv venv
source venv/bin/activate
```

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements
from [requirements.txt](functions/requirements.txt).

```bash
pip install -r requirements.txt
```

Copy the [.env.example](.env.example) file to .env and fill in the values.

## Usage

To run the bot locally, you can use the `bot.py` file.

```bash
python bot.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
