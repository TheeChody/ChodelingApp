# ChodelingApp

______________________________________________________________
Twitch Dev App Setup;
______________________________________________________________

Go To; [Twitch Dev Console](https://dev.twitch.tv/console/apps)
Click Register Your App

Name it whatever you want, select chat bot as app type and use ; 'http://localhost:17563' (without ', and no trailing /) as the OAuth Redirect URL

<img width="183" height="321" alt="image" src="https://github.com/user-attachments/assets/b75c966d-3e0b-4c91-a84d-fa863576b01a" />

Keep note of your client_id and secret_id, save in a notepad, keep to yourself, don't share with anyone!

______________________________________________________________
Python Install;
______________________________________________________________

Go To [Python 3.11.9 Download](https://www.python.org/downloads/release/python-3119/)
Scroll down find ur apporopriate install and download it

______________________________________________________________
Run through the install process;
______________________________________________________________
Make Sure To Add To PATH!

<img width="655" height="400" alt="Screenshot 2025-11-08 161613" src="https://github.com/user-attachments/assets/994e3a20-fb06-45c0-8da5-9c9028e8a54e" />

Not required but might as well;

<img width="656" height="403" alt="Screenshot 2025-11-08 162635" src="https://github.com/user-attachments/assets/23dae50b-860d-4187-b281-46432044d1ab" />

RESTART PC/LAPTOP

Open CMD, Navigate to python script path ( cd DRIVE_LETTER:/PATH/TO/FILE )

Run Following Command To Install Dependant Libaries;

pip install -r requirements.txt

Then Run;

py chodelingapp.py

Fill out required info (client_id & secret_id) and good to go
