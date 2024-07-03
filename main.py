import os
import pytube
from pytube.exceptions import RegexMatchError, VideoUnavailable, AgeRestrictedError
import string
import time
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip


def download_video(url, quality_option):
    """Downloads a YouTube video based on the provided URL and quality option."""

    try:
        # Create pytube object
        yt = pytube.YouTube(url)

        # Get available video formats (including high res)
        video_formats = yt.streams.filter(adaptive=True, file_extension='mp4').order_by('resolution').desc()
        audio_stream = yt.streams.filter(only_audio=True).first()

        # Check if video formats are available
        if not list(video_formats):
            raise ValueError("No video formats available for download.")

        # Validate quality option
        if quality_option < 0 or quality_option >= len(list(video_formats)):
            raise ValueError("Invalid quality option number.")

        # Get selected video format
        selected_format = video_formats[quality_option]

        # Create Downloads folder if it doesn't exist
        downloads_path = os.path.join(os.path.dirname(__file__), "Downloads")
        os.makedirs(downloads_path, exist_ok=True)

        # Sanitize filename using string manipulation
        valid_chars = "-_.() " + string.ascii_letters + string.digits
        filename = ''.join(c for c in yt.title if c in valid_chars).replace(' ', '_')
        video_filename = f"{filename}_video.mp4"
        audio_filename = f"{filename}_audio.mp4"
        output_filename = f"{filename}.mp4"

        print(f"========== Downloading =============: {yt.title}")

        # Download video
        video_path = selected_format.download(output_path=downloads_path, filename=video_filename)
        print("Video download completed.")

        # Download audio
        audio_path = audio_stream.download(output_path=downloads_path, filename=audio_filename)
        print("Audio download completed.")

        # Merge video and audio
        output_path = os.path.join(downloads_path, output_filename)
        success = merge_video_audio_ffmpeg(video_path, audio_path, output_path)

        if not success:
            print("FFmpeg merge failed. Trying MoviePy as an alternative...")
            merge_video_audio_moviepy(video_path, audio_path, output_path)

        # Clean up temporary files
        os.remove(video_path)
        os.remove(audio_path)

        print("\n ================== Download and merge completed! ========================")

    except AgeRestrictedError:
        print("Error: This video is age-restricted and requires authentication.")
        print("You may need to use a different method or library to download age-restricted content.")
    except (RegexMatchError, VideoUnavailable) as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def merge_video_audio_ffmpeg(video_path, audio_path, output_path):
    try:
        print("Merging video and audio using FFmpeg...")
        cmd = f'ffmpeg -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{output_path}"'
        subprocess.run(cmd, check=True, shell=True, stderr=subprocess.PIPE)
        print("FFmpeg merge completed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"FFmpeg error: {str(e)}")
        return False


def merge_video_audio_moviepy(video_path, audio_path, output_path):
    try:
        print("Merging video and audio using MoviePy...")
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        final_clip = video.set_audio(audio)
        final_clip.write_videofile(output_path)
        final_clip.close()
        audio.close()
        video.close()
        print("MoviePy merge completed.")
    except Exception as e:
        print(f"MoviePy error: {str(e)}")


def get_video_info(url):
    try:
        video = pytube.YouTube(url)
        video_formats = video.streams.filter(adaptive=True, file_extension='mp4').order_by('resolution').desc()
        return video, video_formats
    except AgeRestrictedError:
        print("Error: This video is age-restricted and requires authentication.")
        print("You may need to use a different method or library to download age-restricted content.")
        return None, None
    except Exception as e:
        print(f"An error occurred while fetching video information: {e}")
        return None, None


if __name__ == "__main__":
    while True:
        url = input("Enter the YouTube video URL (or 'q' to quit): ")
        if url.lower() == 'q':
            break

        # Fetch video information
        video, video_formats = get_video_info(url)

        if video and video_formats:
            # Prompt for quality selection
            print("\nAvailable video qualities:")
            for i, format in enumerate(video_formats):
                print(f"{i + 1}. {format.resolution}")

            quality_option = int(input("Enter the desired quality option number: ")) - 1

            download_video(url, quality_option)
        else:
            print("Unable to proceed with the download due to the errors mentioned above.")

        print("\nDo you want to download another video? (y/n)")
        download_another = input().lower()
        if download_another != 'y':
            break