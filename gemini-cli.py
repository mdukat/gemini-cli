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

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Don\'t show errors. Debug overrides this'
    )

    # TODO argument to change gemini model. For now only use gemma-3-27b-it since it has the most "free" uses per day
    # TODO verbose argument, tho idk if needed for such simple script
    # TODO "update" argument, which would download new version and install it in place of
    #      the older script, as long as user has RW permissions to the file
    # TODO additional information about gemini token location and format

    parser.add_argument(
        'prompt',
        type=str,
        help='Prompt to send.'
    )

    # Parse the arguments
    args = parser.parse_args()

    if args.debug:
        args.quiet = False

    # Call the main functionality
    run_tool(args)


def run_tool(args):

    # prepare prompt
    prompt = args.prompt

    if args.short:
        # TODO add customization of this text by "~/.config/geminishort" file contents
        #      used for example when using another language, so in PL it would be "Odpowiadaj krótko i zwięźle. "
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
    # 40 char len test is for extra '\n' added by vim. Extra new line is removed in next if statement.
    if gemini_token is None or len(gemini_token) < 39 or len(gemini_token) > 40:
        print(f"Gemini token found in {token_location} could not be read, or is not formatted properly.")
        if args.debug:
            print(f"DEBUG: gemini_token: {gemini_token}")
            print(f"DEBUG: len(gemini_token): {len(gemini_token)}")
            print(f"DEBUG: gemini_token is None: {gemini_token is None}")
            print(f"DEBUG: len(gemini_token) < 39 or len(gemini_token) > 40: {len(gemini_token) < 39 or len(gemini_token) > 40}")
        sys.exit(2)

    if '\n' in gemini_token:
        gemini_token = gemini_token.replace('\n', '')

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

    print("Sending request...\n\n")

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

    # TODO no matter the "--keep" argument, save last prompt and response to $TMPDIR/gemini-last.txt
    tmp_directory = os.getenv("TMPDIR", default="/tmp")
    if not os.access(tmp_directory, os.W_OK):
        if not args.quiet:
            print(f"ERROR: Can't write to {tmp_directory}. No write permissions.")
    else:
        with open(f"{tmp_directory}/gemini_last", "w") as file:
            file.write("Prompt: " + prompt + "\n\n" + gemini_output)

    if args.keep:
        content_location = ("~/.gemini_logs/LOG_"
                            + str(datetime.today().strftime('%Y.%m.%d_%H.%M.%S')) +
                            "_" + str(uuid.uuid4()))
        if args.debug:
            print(f"DEBUG: content_location: {content_location}")
        print(f"Keep: Saving log to {content_location}")
        content_location = os.path.expanduser(content_location)
        os.makedirs(os.path.dirname(content_location), exist_ok=True)
        with open(content_location, "w") as file:
            file.write("Prompt: " + prompt + "\n\n" + gemini_output)
        print(f"Keep: Saved!")


if __name__ == "__main__":
    main()
