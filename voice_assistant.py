from ast import While
from email.mime import audio
from tkinter import N
import speech_recognition as sr
import pyttsx3 #used for 32bit text to speech engine (used if no interent connection or no google cloud account)
import random
import time
import os
from bs4 import BeautifulSoup as bs
import requests
from google.cloud import texttospeech # outdated or incomplete comparing to v1
from google.cloud import texttospeech_v1
import smtplib 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from playsound import playsound
import requests, json
import argparse


def synthesize_text(text):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"google_api.json"
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB",
        name="en-GB-Standard-A",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )
    # The response's audio_content is binary.
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
    audio_file = os.path.dirname(__file__) + '\output.mp3'
    playsound(audio_file)
    os.remove(audio_file)

def determine_speech(recognizer, microphone):

    #Check if recognizer and microphone objects where passed
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    #Start 1 second ambient noise check and then listen for user audio input
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, 0.5)
        print("Speak now!")
        audio = recognizer.listen(source)
    cls = lambda: os.system('cls')
    cls()
    #Dictionary of values to return for success or failure
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response

def guessing_game (recognizer, microphone):

    number = random.randint(1, 100)
    number_of_guesses = 0
    retry_limit = 5
    
    instructions = "I am thinking of a number between 1 and 100. You will try to guess the number I am thinking of. I will tell you if your number is lower or higher than mine!"
    synthesize_text(instructions)

    number_guessed = False
    game_stopped = False

    while not (number_guessed):
        number_of_guesses += 1 
        for i in range(retry_limit):
            synthesize_text("What is your guess?")
            guess = determine_speech(r,mic)
            if guess['transcription']:
                if "i do not" in guess["transcription"] or "want to play" in guess["transcription"]:
                        game_stopped = True
                        break
                try:
                    int(guess["transcription"])
                    break
                except:
                    synthesize_text("Looks like you didn't guess a number, try again")
            if not guess['success']:
                break
            synthesize_text("Sorry I didn't get that")
        
        if guess["error"]:
            print("ERROR: {}".format(guess["error"]))
            break

        if (game_stopped):
            break
        synthesize_text("I heard that you said:{}".format(guess['transcription']))

        prepositions = ["Your guess was wrong again", "You really aren't good at this","Wrong answer again","I am starting to get bored of you guessing wrong","I would start thinking about your guesses longer"]

        if int(guess['transcription']) == number:
            synthesize_text("You guessed the correct number {}!".format(number))
            number_guessed = True
        elif int(guess['transcription']) < number:
            if number - int(guess['transcription']) > 30:
                synthesize_text("wow")
                synthesize_text("that wasn't even close")
                synthesize_text("My number is higher")
            else:
                if number_of_guesses == 1:
                    synthesize_text("Your first guess was not a good one")
                    synthesize_text("My number is higher")
                else:
                    synthesize_text(random.choice(prepositions))
                    synthesize_text("My number is higher")
        elif int(guess['transcription']) > number:
            if int(guess['transcription']) - number > 30:
                synthesize_text("wow")
                synthesize_text("that wasn't even close")
                synthesize_text("My number is lower")
            else:
                if number_of_guesses == 1:
                    synthesize_text("Your first guess was not a good one")
                    synthesize_text("My number is lower")
                else:
                    synthesize_text(random.choice(prepositions))
                    synthesize_text("My number is lower")

def get_Weather(region="", location="", type="today"):
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"
    LANGUAGE = "en-US,en;q=0.5"
    URL = "https://www.google.com/search?q=weather"

    parser = argparse.ArgumentParser(description="Quick Script for Extracting Weather data using Google Weather")
    parser.add_argument("region", nargs="?", help="""Region to get weather for, must be available region.
                                        Default is your current location determined by your IP Address""", default=region)
    if location != "":
        URL += "+ {}".format(location)
    # parse arguments
    args = parser.parse_args()
    region = args.region
    URL += region
    
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    html = session.get(URL)

    soup = bs(html.text, "html.parser")
    result = {}

    #Get the current weather
    if type == "current":
        result['temp_now'] = soup.find("span", attrs={"id": "wob_tm"}).text
        
        if location != "":
            synthesize_text("The current weather in {} is {}".format(location, result["temp_now"]))
        else:
            synthesize_text("The current weather is {} degrees.".format(result["temp_now"]))
    #Get the weather with the high and low
    elif type == "today":
        
        day_names = [] #store names of the days in the 7-day forecast in order
        temp_list = {'max_temp' : [], 'low_temp' : []} #Dict to hold highs and lows of temps in the 7-day forecast
        days = soup.find("div", attrs={"id": "wob_dp"}) 
        for day in days.findAll("div", attrs={"class": "wob_df"}):
            temp = day.findAll("span", {"class": "wob_t"})
            day_names.append(day.findAll("div")[0].attrs['aria-label'])
            temp_list['max_temp'].append(temp[0].text) #Stores the day's max_temp in F
            temp_list['low_temp'].append(temp[2].text) #Stores the day's low_temp in F
        result['temp_now'] = soup.find("span", attrs={"id": "wob_tm"}).text
        
        if location != "":
            synthesize_text("The current weather in {} is {}. The high today is {} and the low is {}.".format(location, result["temp_now"], temp_list["max_temp"][0],temp_list["low_temp"][0]))
        else:
            synthesize_text("The current weather is {} degrees. The high today is {} and the low is {}.".format(result["temp_now"], temp_list["max_temp"][0],temp_list["low_temp"][0]))

def send_text(to, body: str):
    #Grab email credentials currently needs to be manually added in 'config.json'
    with open ("config.json", "r") as f:
        creds = json.load(f)
    email = creds["email"] 
    password = creds["email_pass"]

    """ -----Carrier extensions-----
        AT&T: [number]@txt.att.net
        Sprint: [number]@messaging.sprintpcs.com or [number]@pm.sprint.com
        T-Mobile: [number]@tmomail.net
        Verizon: [number]@vtext.com
        Boost Mobile: [number]@myboostmobile.com
        Cricket: [number]@sms.mycricket.com
        Metro PCS: [number]@mymetropcs.com
        Tracfone: [number]@mmst5.tracfone.com
        U.S. Cellular: [number]@email.uscc.net
        Virgin Mobile: [number]@vmobl.com 
    """

    sms_gateway = to + "@vtext.com" #defaults to verizon----add dynamic choices later
    # The server we use to send emails
    # and port is also provided by the email provider.
    smtp = "smtp.gmail.com" 
    port = 587
    # This will start our email server
    server = smtplib.SMTP(smtp,port)
    # Starting the server
    server.starttls()
    # log in to email server (app access needs to be turned on in account management for gmail)
    server.login(email,password)

    # Now we use the MIME module to structure our message.
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = sms_gateway

    msg['Subject'] = "This was sent via a AI."

    msg.attach(MIMEText(body, 'plain'))

    sms = msg.as_string()

    server.sendmail(email,sms_gateway,sms)

if __name__ == "__main__":

    #Sets Recognizer and Microphone class
    r = sr.Recognizer()
    mic = sr.Microphone()

    #See if user's name has been saved. If not ask the user for their name and save it to config.json
    with open("config.json", "r") as f:
       config = json.load(f)

    if config["name"] == "":
        introduction = "Hello my name is crystal. like the ball. I am an all knowing artificial intelligence. What is your name?"
        synthesize_text(introduction)
        response = determine_speech(r,mic)
        config["name"] = response["transcription"]
        with open("config.json", "w") as f:
            json.dump(config, f)
        say = "I will now call you {} from now on. How can I help you?".format(config["name"])
        synthesize_text(say)
        response = determine_speech(r,mic)

    else:
        introduction = "Hello {}, how can I help you?".format(config["name"])
        synthesize_text(introduction)
        response = determine_speech(r,mic) 
        
    #Conversation Loop
    while True:
        if "weather" in response["transcription"]:
            if "in" in response["transcription"]:
                request = response["transcription"].split('in')
                if "my location" in request[1]:
                    if "current" in response["transcription"]:
                        get_Weather(type="current")
                    else:
                        get_Weather()
                else:
                    if "current" in response["transcription"]:
                        get_Weather(location=request[1],type="current")
                    else:
                        get_Weather(location=request[1])
            else:
                get_Weather()
        elif "how are you" in response["transcription"]:
            feelings_phrases = ["I am currently contemplating life.", "Feelings have not been implemented in my programming", "It is very cold inside of your computer."]
            synthesize_text(random.choice(feelings_phrases))
        elif "play a game" in response["transcription"]:
            synthesize_text("ok. Let's play a number guessing game. Here are the rules.")
            guessing_game(r,mic)
        elif "send a text" in response["transcription"]:
            if "to" in response["transcription"]:
                response = response["transcription"].split("to")
                if response[1] in config["contacts"]:
                    synthesize_text("Ok. what do you want me to say")
                    body = determine_speech(r,mic)
                    send_text(config["contacts"][response[1]], body["transcription"])
                else:
                    synthesize_text("it looks like the {} is not in your contacts.".format(response[1]))
            else:
                synthesize_text("ok. Who do you want me to send a text message to?")
                response = determine_speech(r,mic)
                if response["transcription"] in config["contacts"]:
                    synthesize_text("Ok. what do you want me to say")
                    body = determine_speech(r,mic)
                    send_text(config["contacts"][response["transcription"]], body["transcription"])
                else:
                    synthesize_text("it looks like the {} is not in your contacts.".format(response["transcription"]))
        elif "nothing" == response["transcription"] or "no" in response["transcription"]:
            break
            
        synthesize_text("Anything else I can help you with?")
        response = determine_speech(r,mic) 
        
        

    