# Skåne Bus Stop Project

An e-paper display project for showing real-time public transport information in Skåne, Sweden, using a Raspberry Pi Zero and Waveshare E-Paper display.

<img src="https://github.com/user-attachments/assets/9bee613a-ca5f-402b-ac05-6c876270b318" width="480">

## Hardware Requirements

- Raspberry Pi Zero
- Waveshare 7.5 Inch E-Paper Display Panel V2 (800x480)
- Fotoram Tallinn (Clas Ohlson picture frame)
- Micro USB charger

## Functionality

The display operates in different modes throughout the day:

1. **Journey Mode** (06:00 - 10:00)
   - Shows real-time departure information for configured routes
   - Displays current time, departure times, arrival times, and track numbers
   - Indicates delays and cancellations with special symbols
   - Split screen showing multiple routes simultaneously

2. **Art Mode** (10:00 - 22:00)
   - Displays random artwork from the `img` folder

3. **Sleep Mode** (22:00 - 06:00)
   - Display goes to sleep to preserve screen life

## Installation

```bash
sudo raspi-config
Choose Interfacing Options -> SPI -> Yes to enable SPI interface
sudo reboot
sudo apt-get update
sudo apt-get install python3-pip python3-pil python3-numpy python3-spidev python3-gpiozero git
wget https://files.pythonhosted.org/packages/5f/57/df1c9157c8d5a05117e455d66fd7cf6dbc46974f832b1058ed4856785d8a/pytz-2025.1.tar.gz
tar -xzf pytz-2025.1.tar.gz
cd pytz-2025.1
python3 setup.py install --user
```


### Functionality tests

```bash
cat /boot/firmware/config.txt | grep dtparam=spi=on
> dtparam=spi=on
ls /dev/spi*
> /dev/spidev0.0 and /dev/spidev0.1
git clone https://github.com/waveshare/e-Paper.git
cd e-Paper/RaspberryPi_JetsonNano/
cd python/examples/
python3 epd_7in5_V2_test.py
```

### Run on startup

Save the following service configurations in  `/etc/systemd/system/display.service`
```
[Unit]
Description=display
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/project/main.py
WorkingDirectory=/home/pi/project
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Enable the service

```
sudo systemctl daemon-reload
sudo systemctl enable display.service
sudo reboot
```

## Configuration

### Changing Bus Routes

To configure different bus routes, modify the `journeys` list in `config.py`:

```python
self.journeys = [
    JourneyConfig("FROM_POINT_ID", "TO_POINT_ID", "Display Name"),
    # Add more routes as needed
]
```

To find point IDs:
1. Visit skanetrafiken.se
2. F12 to open the developer console -> Network
3. Search for your jurney
4. Find the journey request `https://www.skanetrafiken.se/gw-tps/api/v2/Journey`
5. Get the `fromPointId` and `toPointId`


https://github.com/user-attachments/assets/dbf0911a-7e22-4356-a530-44d72bb854a5



## Notes

- Be careful with the number of refresh of the screen, frequent update might damage the screen.
- Images for art mode should be placed in the `img` folder


## Contributing

Feel free to submit issues and pull requests for improvements or bug fixes.
