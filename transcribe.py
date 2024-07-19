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
from collections import Counter
import math

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

def cosine_similarity(str1, str2):
    # Create frequency counters for each string
    count1 = Counter(str1)
    count2 = Counter(str2)

    # Create a set of all unique characters in both strings
    all_items = set(count1.keys()).union(set(count2.keys()))

    # Create vectors from the frequency counts, filling missing characters with 0
    vec1 = [count1.get(item, 0) for item in all_items]
    vec2 = [count2.get(item, 0) for item in all_items]

    # Compute the dot product of the two vectors
    dot_product = sum(x * y for x, y in zip(vec1, vec2))

    # Compute the magnitude of the two vectors
    magnitude1 = math.sqrt(sum(x**2 for x in vec1))
    magnitude2 = math.sqrt(sum(x**2 for x in vec2))

    # Calculate cosine similarity
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    else:
        return dot_product / (magnitude1 * magnitude2)

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
            question = "None"

            if not sentence:
                return

            if result.is_final:
                is_finals.append(sentence)

                if result.speech_final:
                    utterance = " ".join(is_finals)
                    utterance_cleaned = clean_string(utterance)

                    catCosines = []
                    for category in categories:
                        category_cleaned = clean_string(category)
                        catCosine = cosine_similarity(category_cleaned, utterance)
                        catCosines.append(catCosine)

                    if catCosines:
                        max_cosine_val = max(catCosines)

                        if max_cosine_val > 0:
                            index_max = catCosines.index(max_cosine_val)
                            finalCategory = categories[index_max]

                        print(catCosines)
                        #print("The category chosen:", finalCategory)

                        if "list categories" in utterance_cleaned:
                            print("Available categories:")
                            for i, cat in enumerate(categories):
                                print(f"{i+1}. {cat}")

                        print(f"Category Matched: {finalCategory}")
                        category_df = pickCategory(finalCategory, game)

                        #print(category_df.iloc[:, 4:5])

                        values = category_df[' Value'].tolist()
                        values = ["Final Jeopardy" if isinstance(val, float) or val == "None" else val for val in values]
                        values = [val.replace(",", "") for val in values if isinstance(val, str)]

                        cosine_vals = []
                        for val in values:
                            cosine_val = cosine_similarity(val, utterance)
                            #print(f"Cosine similarity for value {val} and utterance '{utterance}': {cosine_val}")
                            cosine_vals.append(cosine_val)

                        if cosine_vals:
                            max_cosine_val = max(cosine_vals)

                            if max_cosine_val > 0.1:
                                index_max = cosine_vals.index(max_cosine_val)
                                value = str(values[index_max])
                                print("Value", value)
                                question_row = pickQuestionRow(category_df, value)
                                print(question_row[' Question'])

                    is_finals = []
                else:
                    print(f"Is Final: {sentence}")
            else:
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