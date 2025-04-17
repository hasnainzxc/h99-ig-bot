# Instagram DM Bot

An automated Instagram Direct Message bot built with Python that engages users through hashtag targeting and natural conversation flows.

## Features

- Automated login handling
- Hashtag-based user targeting
- Natural conversation flow with delayed responses
- Customizable message templates
- Rate limiting and safety delays
- Error handling and logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hasnainzxc/h99-ig-bot.git
cd h99-ig-bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up your configuration:
```bash
copy bot\config.py.example bot\config.py
```
Then edit `config.py` with your Instagram credentials.

## Configuration

1. Update `bot/config.py` with your Instagram credentials:
```python
USERNAME = "your_username"
PASSWORD = "your_password"
```

2. Customize message templates in `bot/message_sender.py`
3. Adjust timing delays in `bot/utils.py`
4. Modify target hashtags in `main.py`

## Usage

Run the bot:
```bash
python main.py
```

## Project Structure

```
instagram_bot/
│
├── bot/
│   ├── __init__.py          # Package initializer
│   ├── config.py            # Configuration settings
│   ├── login.py             # Login handling
│   ├── hashtag_scraper.py   # Hashtag scraping functionality
│   ├── message_sender.py    # Message handling and sending
│   └── utils.py             # Utility functions
│
├── main.py                  # Main entry point
└── requirements.txt         # Project dependencies
```

## Safety Guidelines

- Use delays between actions to avoid rate limits
- Don't spam users or send unsolicited messages
- Follow Instagram's terms of service
- Use at your own risk

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Disclaimer

This bot is for educational purposes only. Use it responsibly and in accordance with Instagram's terms of service. The developers are not responsible for any misuse or consequences.

## License

This project is licensed under the MIT License - see the LICENSE file for details.