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

 ## 2 Options To Run 
 
 1) [Python Script](https://github.com/TheeChody/ChodelingApp/edit/main/README.md#1-python-install-only-need-to-do-if-using-python-to-run-app-if-using-the-packaged-exe-skip)
 2) [.exe file](https://github.com/TheeChody/ChodelingApp/edit/main/README.md#2-exe-install-only-for-running-the-exe-file-if-using-python-skip)

______________________________________________________________
### 1) Python Install; (Only need to do if using python to run app, if using the packaged .exe skip)
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
### 2) .Exe Install; (Only for running the .exe file, if using python skip)
______________________________________________________________

Download latest release 

<img width="1549" height="792" alt="image" src="https://github.com/user-attachments/assets/12083bff-070e-47d2-ae53-7ff21d82ad53" />

<img width="1563" height="802" alt="image" src="https://github.com/user-attachments/assets/6ab0e26e-3ab1-47ad-89c0-dcb2b2ea5551" />

See discord channel 'chodeling-app' pinned comment for auth file needed to launch app

Unzip where you want, and after copying over auth to documents, run Thee Chodeling App.exe and enter in the client_id and client_secret when prompted and you good to go
