# Bambu Timelapse Downloader
A tool to download timelapse files from a Bambu printer.

## Demo
![demo.gif](docs%2Fimages%2Fdemo.gif)

## Usage
> ⚠️ FTP download from the bambu printer is very slow, please be patient. 🙂 
> 
> A 10mb file took ~1-2 minutes, but maybe my printer just have not the best wifi signal..

### Parameter
| Name                 | Description                                                                                               | Required | Default   |
|----------------------|-----------------------------------------------------------------------------------------------------------|----------|-----------|
| ip                   | IP address of printer.                                                                                    | Yes      | -         |
| port                 | FTP Port.                                                                                                 | No       | 990       |
| user                 | FTP User.                                                                                                 | No       | bblp      |
| access-code          | Access code shown on printer display. (Can also be specified with --password for backwards compatibility) | Yes      | -         |
| download-dir         | Download foldername.                                                                                      | No       | timelapse |
| ftp_timelapse_folder | FTP timelapse folder on ftp.                                                                              | No       | timelapse |
| convert              | Convert any avi files downloaded to mp4                                                                   | No       | false     |
| -d                   | Delete timelapse file after download.                                                                     | No       | -         |
| -v                   | Show Version                                                                                              | No       | -         |

### Conversion

Due to the codec used to create the `.avi` files on the P1* series of printers, it can often be difficult to open without specific software. Using the `--convert` command, a file can automatically be converted to `.mp4` when downloaded. This will allow for the files to be much more transportable.

> Note that this requires [ffmpeg](https://www.ffmpeg.org/) to be installed

### Examples

#### run with default parameters
```powershell
bambu_timelapse_download.exe 192.168.0.20 --password 12345678
```

#### save timelapse file in diffrent directory
```powershell
bambu_timelapse_download.exe 192.168.0.20 --password 12345678 --download_dir "C:\Video\3D Druck\Timelapse"
```

#### save timelapse file in different directory & delete timelapse files from ftp after download
```bash
bambu_timelapse_download 192.168.0.20 --password 12345678 --download_dir "~/timelapse" -d
```

#### save timelapse file and convert
```bash
bambu_timelapse_download 192.168.0.20 --password 12345678 --download_dir "~/timelapse" --convert
```

### Using Docker Image

```bash
docker run -v "/path/to/timelapse-folder:/app/timelapse" ghcr.io/stephengolub/bambu_timelapse_downloader 192.168.0.20 --access-code 12345678 --convert
```
