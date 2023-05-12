
from flask import Flask, request, render_template, jsonify, send_file
from pytube import YouTube
from flask_socketio import SocketIO
import subprocess
from threading import Thread
from moviepy.editor import concatenate_videoclips, ImageClip
from os import rename

app = Flask(__name__)
socketio = SocketIO(app)


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
  youtube_link = request.form.get("youtube-link")
  image = request.files.get("image-upload")

  if not youtube_link:
    return jsonify({
      "uploaded": False,
      "response": "No YouTube link provided."
    })

  if image:
    # save image
    image.save("files/image.jpg")
    return jsonify({
      "uploaded": True,
      "response": "Image was UpLoaded!" + "<br>"
    })
  else:
    return jsonify({"uploaded": False, "response": "No image provided."})


@app.route('/download')
def download_file():
  try:
    return send_file("files/video.mp4", as_attachment=True)
  except Exception as e:
    return str(e)


def update_progress(stream, chunk, b_remain):
  t_bytes = stream.filesize
  r_bytes = t_bytes - b_remain
  socketio.emit(
    "logs",
    f"Downloaded: {round(r_bytes / (1024 * 1024), 2)} MB / {round(t_bytes / (1024 * 1024), 2)} MB"
  )


def download_complete(a, b):
  socketio.emit("logs", "Download is Complete!")


def download_audio(youtube_link):
  yt = YouTube(youtube_link,
               on_progress_callback=update_progress,
               on_complete_callback=download_complete)
  stream = yt.streams.filter(only_audio=True).order_by('abr').last()
  stream.download(filename="files/audio.mp3")


def process_vid(ylink):
  subprocess.run(["rm", "-rf", "files/video.mp4", "files/vid_tmp.mp4", "files/video_progress.mp4"])
  socketio.emit("logs", "Starting Download")
  try:
    download_audio(ylink)
  except Exception as e:
    socketio.emit("logs", str(e))
    return
  # when download is complete
  try:
    socketio.emit("logs", "Creating a video file")

    # Generate video
    clips = [ImageClip(m).set_duration(3600)
          for m in ['files/image.jpg']]
    
    concat_clip = concatenate_videoclips(clips, method="compose")
    concat_clip.write_videofile("files/vid_tmp.mp4", fps=1)
    # add audio
    socketio.emit("logs", "adding Audio to the Video")
    command = [
      "ffmpeg", "-i", "files/vid_tmp.mp4", "-i", "files/audio.mp3", "-map",
      "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
      "-shortest", "files/video_progress.mp4", "-y"
    ]
    subprocess.run(command)
    rename("files/video_progress.mp4", "files/video.mp4")

  except Exception as e:
    socketio.emit("logs", str(e))
    return

  socketio.emit("logs", "Video processing is Complete!")


@socketio.on('logs')
def update_log(ylink):
  Thread(target=process_vid, args=(ylink, )).start()


if __name__ == "__main__":
  socketio.run(app, host='0.0.0.0')
