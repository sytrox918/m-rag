import tempfile
import yt_dlp
from faster_whisper import WhisperModel
import uuid
from ingestion.common.content_units import ContentUnit

class VideoParser:
    def __init__(self):
        self.model = None

    def parse(self, url: str, document_id: str = None) -> list[ContentUnit]:
        doc_id = document_id or str(uuid.uuid4())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{tmpdir}/%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                doc_name = info.get('title', 'Unknown Video')
                video_id = info.get('id')
                audio_file = f"{tmpdir}/{video_id}.mp3"
                
                if not self.model:
                    self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
                    
                segments, info_whisper = self.model.transcribe(audio_file, beam_size=5)
                
                content_units = []
                for segment in segments:
                    unit = ContentUnit(
                        id=str(uuid.uuid4()),
                        document_id=doc_id,
                        document_name=doc_name,
                        source_type='video',
                        text=segment.text,
                        start_time=segment.start,
                        end_time=segment.end
                    )
                    content_units.append(unit)
                    
                return content_units
