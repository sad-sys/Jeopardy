# Copyright 2023-2024 Deepgram SDK contributors. All Rights Reserved.
# Use of this source code is governed by a MIT license that can be found in the LICENSE file.
# SPDX-License-Identifier: MIT

from dotenv import load_dotenv
import logging
from deepgram.utils import verboselogs
import pandas as pd
pd.set_option('display.max_colwidth', None)  # None means no truncation
from time import sleep
import re
from fuzzywuzzy import process

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

def clean_string(s):
    return re.sub(r'[^\w\s]', '', s).strip().lower()

# Function to pick a game based on the air date
def pickGame(airDate, df):
    return df[df[' Air Date'].str.strip() == airDate]

# Function to list unique categories within a game
def listCategories(game):
    categories = game[' Category'].unique().tolist()
    return categories

# Function to pick questions from a specific category within a game
def pickCategory(category, game):
    # Convert the input category to upper case for standardization
    category = category.upper()
    
    # Get list of unique categories from the DataFrame
    unique_categories = game[' Category'].str.upper().unique()
    
    # Find the best match for the category within the list of unique categories
    best_match, score = process.extractOne(category, unique_categories)
    
    # You can specify a threshold for score to decide when to accept the match
    if score > 50:  # This threshold can be adjusted based on how strict you want the matching to be
        return game[game[' Category'].str.upper() == best_match]
    else:
        return None  # or however you want to handle cases where no good match is found


# Function to pick a value from a particular category
def pickQuestionRow(category, value):
    category = category
    return category[category[' Value'].str.strip() == value]

load_dotenv()

# We will collect the is_final=true messages here so we can use them when the person finishes speaking
is_finals = []


def main():
    try:
        # example of setting up a client config. logging values: WARNING, VERBOSE, DEBUG, SPAM
        # config = DeepgramClientOptions(
        #     verbose=verboselogs.DEBUG, options={"keepalive": "true"}
        # )
        # deepgram: DeepgramClient = DeepgramClient("", config)
        # otherwise, use default config
        deepgram: DeepgramClient = DeepgramClient()

        dg_connection = deepgram.listen.live.v("1")

        air_date = "2004-12-31"

        df = pd.read_csv("jeopardySmall.csv")

        game = pickGame(air_date, df)

        categories = listCategories(game)
        print("Available categories:")
        for i, cat in enumerate(categories):
            print(f"{i+1}. {cat}")

        def on_open(self, open, **kwargs):
            print(f"Connection Open")

        def clean_string(s):
            return re.sub(r'[^\w\s]', '', s).strip().lower()

        def on_message(self, result, **kwargs):
            global is_finals
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            if result.is_final:
                is_finals.append(sentence)
                if result.speech_final:
                    utterance = " ".join(is_finals)
                    # Remove punctuation for comparison
                    utterance_cleaned = clean_string(utterance)
                    #print(f"Speech Final: {utterance}")
                    #print(f"Cleaned Utterance: {utterance_cleaned}")

                    categoryChosen = "None"
                    valueChosen = "None"

                    for i in range(len(categories)):
                        category_cleaned = clean_string(categories[i])
                        #print (category_cleaned)
                        if category_cleaned in utterance_cleaned:
                            print(f"Category Matched: {categories[i]}")

                            category = pickCategory(category_cleaned, game)
                            categoryChosen = category
                            print (category.iloc[:, 4:5])
                            values = categoryChosen[' Value'].tolist()
                            print("Values are", values)

                            if "None" in values:
                                values.replace("None","$0")

                            for i in values:
                                modified_i = i.replace(",", "")  # Replace commas in the string

                            for i in range(len(values)):
                                if values[i] in utterance:
                                    #print(f"Value Matched: {values[i]}")
                                    value = str(values[i])
                                    print("Value", value)
                                    questionRow = pickQuestionRow(category,value)
                                    print(questionRow[' Question'])
                        
                        if not categoryChosen.empty:
                            print(" Not None")
                            values = categoryChosen[' Value'].tolist()
                            for i in range(len(values)):
                                if values[i] in utterance:
                                    #print(f"Value Matched: {values[i]}")
                                    value = str(values[i])
                                    print("Value", value)
                                    questionRow = pickQuestionRow(categoryChosen,value)
                                    print(questionRow[' Question'])

                    if "categories" in utterance_cleaned:
                        for i in categories:
                            print (i)


                    is_finals = []
                else:
                    print(f"Is Final: {sentence}")
            else:
                #pass
                print(f"Interim Results: {sentence}")

        def on_metadata(self, metadata, **kwargs):
            print(f"Metadata: {metadata}")

        def on_speech_started(self, speech_started, **kwargs):
            print(f"Speech Started")
            pass
            print(f"Speech Started")

        def on_utterance_end(self, utterance_end, **kwargs):
            #print(f"Utterance End")
            global is_finals
            if len(is_finals) > 0:
                utterance = " ".join(is_finals)
                print(f"Utterance End: {utterance}")
                is_finals = []
        def on_close(self, close, **kwargs):
            print(f"Connection Closed")

        def on_error(self, error, **kwargs):
            print(f"Handled Error: {error}")

        def on_unhandled(self, unhandled, **kwargs):
            print(f"Unhandled Websocket Message: {unhandled}")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

        options: LiveOptions = LiveOptions(
            model="nova-2",
            language="en-US",
            # Apply smart formatting to the output
            smart_format=True,
            # Raw audio format details
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            # To get UtteranceEnd, the following must be set:
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            # Time in milliseconds of silence to wait for before finalizing speech
            endpointing=20,
        )

        addons = {
            # Prevent waiting for additional numbers
            "no_delay": "true"
        }

        print("\n\nPress Enter to stop recording...\n\n")
        if dg_connection.start(options, addons=addons) is False:
            print("Failed to connect to Deepgram")
            return

        # Open a microphone stream on the default input device
        microphone = Microphone(dg_connection.send)

        # start microphone
        microphone.start()

        # wait until finished
        input("")

        # Wait for the microphone to close
        microphone.finish()

        # Indicate that we've finished
        dg_connection.finish()

        print("Finished")
        # sleep(30)  # wait 30 seconds to see if there is any additional socket activity
        # print("Really done!")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return


if __name__ == "__main__":
    main()