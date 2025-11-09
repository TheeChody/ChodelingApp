 # ChodelingApp

______________________________________________________________
Twitch Dev App Setup; (Needed either way)
______________________________________________________________

Go To; [Twitch Dev Console](https://dev.twitch.tv/console/apps)
Click Register Your App

Name it whatever you want, use ; 'http://localhost:17563' (without ', and no trailing /) as the OAuth Redirect URL

Select Chat Bot as category and confidential for client type

<img width="183" height="321" alt="image" src="https://github.com/user-attachments/assets/b75c966d-3e0b-4c91-a84d-fa863576b01a" />

Keep note of your client_id and secret_id, save in a notepad, keep to yourself, don't share with anyone!

______________________________________________________________
Python Install; (Only need to do if using python to run app, if using the packaged .exe skip)
______________________________________________________________

Go To [Python 3.11.9 Download](https://www.python.org/downloads/release/python-3119/)
Scroll down find ur apporopriate install and download it

Run through the install process;

Make Sure To Add To PATH!

<img width="655" height="400" alt="Screenshot 2025-11-08 161613" src="https://github.com/user-attachments/assets/994e3a20-fb06-45c0-8da5-9c9028e8a54e" />

Not required but might as well;

<img width="656" height="403" alt="Screenshot 2025-11-08 162635" src="https://github.com/user-attachments/assets/23dae50b-860d-4187-b281-46432044d1ab" />

RESTART PC/LAPTOP

Come back here, download zip folder

<img width="515" height="436" alt="image" src="https://github.com/user-attachments/assets/76b25737-1c62-474c-bc06-827896660e9a" />

Extract where you want, then;

Open CMD, Navigate to python script path ( cd DRIVE_LETTER:/PATH/TO/FILE )

Run Following Command To Install Dependant Libaries;

pip install -r requirements.txt

See discord channel 'chodeling-app' pinned comment for auth file needed to launch app

Then Run;

py chodelingapp.py

Fill out required info (client_id & secret_id) and good to go

______________________________________________________________
.Exe Install; (Only for running the .exe file, if using python skip)
______________________________________________________________

Download latest release 

<img width="1262" height="659" alt="image" src="https://github.com/user-attachments/assets/41c34c46-4f92-4296-992a-ceec84480539" />
<img width="1313" height="1037" alt="image" src="https://github.com/user-attachments/assets/fbb172c6-34de-49de-b063-c4f0065910e1" />

See discord channel 'chodeling-app' pinned comment for auth file needed to launch app

Unzip where you want, and after copying over auth file, run Thee Chodeling App.exe and enter in the client_id and client_secret and good to go
