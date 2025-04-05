# gemini-cli
CLI tool for quick Google Gemini-3 AI access

## How to use

1. Create Google AI Studio account and grab your API key at [Get API key](https://aistudio.google.com/app/apikey) (it's free!)
2. Put your key in any of these files in your environment:
    * `./.geminitoken` - To keep your API key in same directory as the `gemini-cli` script
    * `~/.geminitoken` - To keep it in your home directory
    * `~/.config/geminitoken` - To keep it in your `.config` directory
3. Run the script! For example: `gemini-cli.py "Explain how to pull git repository"`

## Requirements

* Linux environment (tested on Android Termux, works fine!)
* Python 3
* `requests` library
