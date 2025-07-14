# BrightSign MRSS Feed Generator / Media Server

Python script and web server setup to host media from an USB drive and generate Media RSS (MRSS) feeds compatible BrightSign® digital signage players (BA:connected).

## Raspberry Pi Setup

### 1. Install Raspberry Pi OS Lite

Tested on Raspberry Pi 4 Model B with Raspberry Pi OS Lite (64-bit, Bookworm)

#### Install Raspberry Pi OS

- Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash the image to the Pi SD Card.
- Configure the username as `lucid`.
- Ensure the ssh server is enabled.

#### Connect to Pi via SSH

```bash
ssh lucid@<ip>
```

### 2. Install MRSS Generator script

```bash
cd /home/lucid
git clone git@github.com:wearelucid/brightsign-mrss-server.git
```

### 3. Install apache2 web server

#### Install apache2

```bash
sudo apt install apache2
```

#### Test web server

Visit the local ip of your raspberry pi on a web browser. You should see the apache default test page.

#### Configure web server

```bash
sudo nano /etc/apache2/sites-enabled/000-default.conf
```

Update contents

```apache
<VirtualHost *:80>
	ServerAdmin webmaster@localhost
	DocumentRoot /var/www/usb

	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined

	<Directory /var/www/usb>
		Options Indexes FollowSymLinks
		AllowOverride All
		Require all granted
	</Directory>
</VirtualHost>
```

Restart apache server

```bash
sudo service apache2 reload
```

### 2. Install usbmount

#### Install dependencies

```bash
sudo apt install git debhelper build-essential
```

#### Compile and install usbmount

```bash
cd /tmp
git clone https://github.com/rbrito/usbmount.git
cd usbmount
dpkg-buildpackage -us -uc -b
cd ..
sudo apt install ./usbmount_0.0.24_all.deb
```

#### Configure usbmount

Edit configuration file

```bash
sudo nano /etc/usbmount/usbmount.conf
```

Change the following line:

```
# Configures usbmount to mount drives with proper permissions
FS_MOUNTOPTIONS="-fstype=vfat,uid=1000,gid=1000,dmask=0007,fmask=0137"
```

### 3. Configure script auto-run on mount

```bash
sudo nano /etc/usbmount/mount.d/99_generate_mrss
```

Add the following contents:

```sh
#!/bin/sh

# Check if MEDIAUSB file exists in the mount point
if [ ! -f "$UM_MOUNTPOINT/MEDIAUSB" ]; then
    exit 1
fi

unlink /var/www/usb
ln -s $UM_MOUNTPOINT /var/www/usb
/usr/bin/python3 /home/lucid/brightsign-mrss-server/generate_mrss.py --folder $UM_MOUNTPOINT
```

Add execution permission on the script

```bash
sudo chmod +x /etc/usbmount/mount.d/99_generate_mrss
```

## Usage

### USB Drive Directory Structure

The MRSS generator script automatically scans your USB drive and creates feeds based on the directory structure. Here's how to organize your media files:

#### Basic Structure

```
USB_DRIVE/
├── MEDIAUSB # Device identification file. Usbmount will ignore all usb drives that do not have this file
├── config.json # Config file
├── video1.mp4
├── video2.mp4
├── video3.mp4
├── mrss.xml (Generated) # http://<ip>/mrss.xml
├── subfolder1/
│   ├── video4.mp4
│   ├── video5.mp4
│   └── video6.mp4
|-- subfolder1.xml (Generated) # http://<ip>/subfolder1.xml
├── subfolder2/
│   ├── video7.mp4
│   ├── video8.mp4
|-- subfolder2.xml (Generated) # http://<ip>/subfolder2.xml
```

#### Generated Feeds

When you insert the USB drive, the system automatically generates:

1. **Main Feed** (`mrss.xml`): Contains all video files from the root directory

   - URL: `http://<ip>/mrss.xml`

2. **Subfolder Feeds** (`<folder_name>.xml`): Individual feeds for each subdirectory
   - URL: `http://<ip>/<folder_name>.xml`

Example feed:

```xml
<rss xmlns:media="http://search.yahoo.com/mrss/" version="2.0">
    <channel>
        <title>MB Media</title>
        <link/>
        <description>MB</description>
        <generator>Server RSS Generator</generator>
        <item>
            <title>video1</title>
            <pubDate>2025-06-17T11:03:35.971294Z</pubDate>
            <link>http://{ip}/video1.mp4?md5=c9a07d6957a33c2be1498fbdc76ffc58</link>
            <description>http://{ip}/video1.mp4?md5=c9a07d6957a33c2be1498fbdc76ffc58</description>
            <medium>video</medium>
            <guid>video1-c9a07d6957a33c2be1498fbdc76ffc58</guid>
            <media:content url="http://{ip}/video1.mp4?md5=c9a07d6957a33c2be1498fbdc76ffc5" type="video/mp4" medium="video"/>
        </item>
        <item>...</item>
        <item>...</item>
</channel>
</rss>
```

#### Configuration file

Add an optional config file `config.json` to the USB root to configure the mrss script:

```json
{
    "BASE_URL": "http://raspberrypi.local/", # The locally accessible url for your web server
    "MEDIA_EXTENSIONS": [".mp4", ".mov", ".avi", ".mkv"] # File types to include in the mrss feed
}
```

## Use with BA:connected

The MRSS feeds can be used with BA:connected Media List and On Demand states.

Select "Populate from Feed" in the List Content Section on the State.

Configure the URL to the desired MRSS feed.

Disable the "Optimize feed updates" setting.

On the On Demand State, use the "Use a variable to specify the key" setting to access a specific key (video name) of the feed. For a video with the filename `video1.mp4`, the key name will be `video1`.

The md5 checksum added to the video url in the feed acts as a cache busting tool, so the content will always be updated if the file on the USB drive is replaced.

## License

MIT License

Copyright (c) 2025 Lucid GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
