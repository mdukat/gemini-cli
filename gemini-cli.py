#!/usr/bin/env python3
import uuid
from datetime import datetime
import requests
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="gemini-cli - CLI tool for Google Gemini assistant")

    parser.add_argument(
        '-s', '--short',
        action='store_true',
        help='Add "Keep your answer short" to sent prompt.'
    )

    parser.add_argument(
        '-k', '--keep',
        action='store_true',
        help='Keep prompt and answer in text file. Will save to "~/.gemini_logs".'
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Debug script. Will print your token to console! Use with care!'
    )

    # TODO argument to change gemini model. For now only use gemma-3-27b-it since it has the most "free" uses per day
    # TODO verbose argument, tho idk if needed for such simple script
    # TODO additional information about gemini token location and format

    parser.add_argument(
        'prompt',
        type=str,
        help='Prompt to send.'
    )

    # Parse the arguments
    args = parser.parse_args()

    # Call the main functionality
    run_tool(args)


def run_tool(args):

    # prepare prompt
    prompt = args.prompt

    if args.short:
        prompt = f"Keep your answer short. {args.prompt}"

    if args.debug:
        print(f"DEBUG: prompt: {prompt}")

    # prepare token
    possible_token_locations = ["./.geminitoken", "~/.geminitoken", "~/.config/geminitoken"]
    token_location = None
    for possible_token_location in possible_token_locations:
        possible_token_location = os.path.expanduser(possible_token_location)
        if os.path.exists(possible_token_location) and os.access(possible_token_location, os.R_OK):
            token_location = possible_token_location

    if token_location is None:
        print("Could not find token file! Please make sure it exists in any of these locations, has read permissions "
              "and is properly formatted:")
        for location in possible_token_locations:
            print(location)
        sys.exit(1)

    gemini_token = None
    with open(token_location, "r") as file:
        gemini_token = file.read()

    # TODO don't know if all tokens are 39 chars long. Please open new issue if your token has different length.
    if gemini_token is None or len(gemini_token) != 39:
        print(f"Gemini token found in {token_location} could not be read, or is not formatted properly.")
        if '\n' in gemini_token:
            print("File should have only single line. Make sure it has only the token value in first line,"
                  " nothing else.")
        sys.exit(2)

    if args.debug:
        print(f"DEBUG: gemini_token: {gemini_token}")

    # prepare request stuff
    headers = {
        'Content-Type': 'application/json',
    }

    params = {
        'key': gemini_token,
    }

    json_data = {
        'contents': [
            {
                'parts': [
                    {
                        'text': prompt,
                    },
                ],
            },
        ],
    }

    print("Sending request...")

    response = requests.post(
        'https://generativelanguage.googleapis.com/v1beta/models/gemma-3-27b-it:generateContent',
        params=params,
        headers=headers,
        json=json_data,
    )

    if not response.ok:
        error_content_location = "~/.gemini_logs/ERROR_" + str(uuid.uuid4())
        print(f"Something went wrong... Dumping output to {error_content_location}")
        error_content_location = os.path.expanduser(error_content_location)
        os.makedirs(os.path.dirname(error_content_location), exist_ok=True)
        with open(error_content_location, "w") as file:
            file.write(response.text)
        exit(1)

    j = response.json()
    gemini_output = j["candidates"][0]["content"]["parts"][0]["text"]
    print(gemini_output)

    if args.keep:
        content_location = ("~/.gemini_logs/LOG_"
                            + str(datetime.today().strftime('%Y.%m.%d_%H.%M.%S')) +
                            "_" + str(uuid.uuid4()))
        if args.debug:
            print(f"DEBUG: content_location: {content_location}")
        content_location = os.path.expanduser(content_location)
        os.makedirs(os.path.dirname(content_location), exist_ok=True)
        with open(content_location, "w") as file:
            file.write(gemini_output)


if __name__ == "__main__":
    main()
