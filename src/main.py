import json
import os
from subprocess import run, Popen, PIPE, DEVNULL


MEDIA_PATH = 'H:\\'
BASE_PATH = 'D:\\test\\'
HANDBRAKE_PRESET = 'H.265 NVENC 1080p'
AUDIO_TRACKS = 16
SUBTITLE_TRACKS = 32
MIN_TITLE_LENGTH = 20
CONTAINER_FORMAT ='.mkv'


def handle_title_scan(line: str):
    global get_scan_json
    global text_scan
    global scan_json
    if line.find('JSON Title Set: {') != -1:
                get_scan_json = True
                text_scan += '{\n'
    else:
        if get_scan_json:
            text_scan += line
            if line == '}\n':
                scan_json = json.loads(text_scan)
                get_scan_json = False


if __name__ == '__main__':

    # Scan for titles
    # HandBrakeCLI.exe -i H:\ -t 0 --scan --json

    scan_json = None
    with Popen(['HandBrakeCLI.exe', '-i', MEDIA_PATH, '--main-feature', '-t', '0', '--scan', '--json'], universal_newlines=True, stdout=PIPE, stderr=DEVNULL) as proc_out:
        text_scan = ''
        get_scan_json = False

        print('Scanning:')
        for line in proc_out.stdout:
            handle_title_scan(line)

    titles = []
    for title in scan_json['TitleList']:
        index = title['Index']
        hours = int(title['Duration']['Hours'])
        minutes = int(title['Duration']['Minutes'])
        seconds = int(title['Duration']['Seconds'])

        if (hours == 0 and minutes == 0 and seconds < MIN_TITLE_LENGTH):
            print(f'Title {index} is less than {MIN_TITLE_LENGTH} seconds, skipping...')
        else:
            titles.append(title['Index'])
            print(f"Title: {title['Index']}, Duration: {title['Duration']['Hours']}:{title['Duration']['Minutes']}:{title['Duration']['Seconds']}")


    title_paths = {}
    for title in titles:
        filename = input(f'Input name of Title {title} (N or nothing to skip): ').strip()
        if filename.lower() == 'n' or not filename:
            continue

        title_paths[title] = filename
        
        target_dir = f'{BASE_PATH}{filename}'
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)

    # Rip Titles
    # HandBrakeCLI.exe -i H:\ -o D:\test\test.mp4 -t 0 -Z "H.265 NVENC 1080p" -a "1,2,3,4" -s "scan,1,2,3,4" --subtitle-burned "none"

    for title, filename in title_paths.items():

        audio_tracks_cmd = ','.join([str(x) for x in range(1, AUDIO_TRACKS+1)])
        sub_tracks_cmd = ','.join([str(x) for x in range(1, SUBTITLE_TRACKS+1)])

        command = [
            'HandBrakeCLI.exe',
            '-i', f'{MEDIA_PATH}', '-t', f'{title}',
            '-o', f'{BASE_PATH}{filename}\{filename}{CONTAINER_FORMAT}',
            '-Z', HANDBRAKE_PRESET, '-a', audio_tracks_cmd, '-s', f'scan,{sub_tracks_cmd}', '--subtitle-burned', 'none',
        ]
        print('Executing command::', ' '.join(command))
        run(command)
        print(f'Title {title} done')

    print('all done!')
    for filename in title_paths.values():
        print(filename)
