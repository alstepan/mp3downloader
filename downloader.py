import youtube_dl
import PySimpleGUI as sg
import validators
from PIL import Image
import requests
import io
import clipboard

videos_to_download=[['', '', '']]
layout = [  [sg.Text('Youtube video URL'), sg.Input(key='__URL__', enable_events=True), sg.Button('Paste'), sg.Button('Add')],
			[sg.Table(key='_download_list_', 
					  headings=['Title'], 
					  values=videos_to_download,
					  col_widths=[40],
       				  auto_size_columns = False,
					  justification = "left",
					  enable_events=True),
				 sg.Graph(key='_preview_', 
             		 		background_color='black',
					  		canvas_size=(200, 150),
       				  		graph_bottom_left=(0, 0),
					  		graph_top_right=(200, 150)	
                        )
			],
			[ sg.Button('Delete'), sg.Button('Clear')],
			[sg.Text('Save to folder:'), sg.Input(key='_file_input_'), sg.FolderBrowse(key='__SAVE_TO_FILE__')],
			[sg.Text('Downloading progress:', key='_download_label_', size=(50,1))], 
			[sg.ProgressBar(100, orientation='h', size=(40,20), key='__DOWNLOAD_PROGRESS__')],
			[sg.Button('Download...'), sg.Button('Exit')] ]

window = sg.Window('Video downloader', layout)
download_progress_bar = window.find_element('__DOWNLOAD_PROGRESS__')

def downloadProgress(d):
	received = d['downloaded_bytes']
	total = d['total_bytes']
	percent = 100 * received / total
	global download_progress_bar
	download_progress_bar.UpdateBar(percent)
	window.find_element('_download_label_').Update(value=f"Downloading {d['filename']} ...")
 
def getVideoInfo(url):
	ydl = youtube_dl.YoutubeDL({'outtmpl': '%(title)s.%(ext)s'})
	with ydl:
		info = ydl.extract_info(url, download=False)
	video = info['entries'][0] if 'entries' in info else info
	return video
 
def updatePreview(url):
	video = getVideoInfo(url)
	title = video['title']
	thumb = video['thumbnails'][0]
	response = requests.get(thumb['url'], stream=True)
	response.raw.decode_content = True
	image_data = io.BytesIO(response.raw.read())
	image = Image.open(image_data)
	with io.BytesIO() as output:
		image.save(output, format="PNG")
		data = output.getvalue()
	window.find_element('_preview_').DrawImage(data=data, location=(0,150))
	
def addUrlToList(url):
	try:
		video = getVideoInfo(url)
		if videos_to_download == [['','','']]:
			videos_to_download.clear()
		videos_to_download.append([video['title'], url])
		window.find_element('_download_list_').Update(values=videos_to_download)
	except Exception as err:
		sg.PopupError("Error", f"Error adding an item to download list:\n {err}")
		
def downloadVideo(urls, path):
	ydl_opts = {
		'format': 'bestaudio/best',       
		'outtmpl': path + '/' + '%(title)s.%(ext)s',        
		'noplaylist' : True,        
		'progress_hooks': [downloadProgress],
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192'
	  	}]  
	}
	window.find_element('Download...').Update(disabled=True)
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		ydl.download(urls)
	window.find_element('Download...').Update(disabled=False)

def main():
	global videos_to_download
	while True:
		event, values = window.Read(timeout=100)
		if event is None or event == 'Exit':
			break
		elif event == '__URL__':
			download_progress_bar.Update(0)
		elif event == 'Paste':
			url = clipboard.paste()
			window.find_element('__URL__').Update(url)
		elif event == 'Add':
			url = values['__URL__']
			if not validators.url(url):
				sg.PopupError('Please enter a valid video URL')
			else:
				addUrlToList(url)
				window.find_element('__URL__').Update('')
		elif event == '_download_list_':
			table = window.find_element('_download_list_')
			if len(table.SelectedRows) > 0:
				updatePreview(videos_to_download[table.SelectedRows[0]][1])
		elif event == 'Delete':
			table = window.find_element('_download_list_')
			if len(table.SelectedRows) > 0:
				videos_to_download.pop(table.SelectedRows[0])
				window.find_element('_download_list_').Update(values=videos_to_download)
				window.find_element('_preview_').Erase()
		elif event == 'Clear':
			videos_to_download=[['', '', '']]
			window.find_element('_download_list_').Update(values=videos_to_download)
			window.find_element('_preview_').Erase()
		elif event == 'Download...':
			file_name = values['_file_input_']
			download_progress_bar.Update(0)
			downloadVideo([x[1] for x in videos_to_download], file_name)
						
		elif event == '__SAVE_TO_FILE__':				
			file_input = window.find_element('_file_input_')
			file_input.TextInputDefault = values['__SAVE_TO_FILE__']

main()
