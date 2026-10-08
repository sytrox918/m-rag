import os
import uuid
import tempfile
import yt_dlp
import cv2
from pathlib import Path
from faster_whisper import WhisperModel
from scenedetect import detect, ContentDetector
from ingestion.common.content_units import ContentUnit
from config.settings import settings
from storage.vector_store import vector_store

class VideoParser:
    def __init__(self):
        self.model = None
        self.assets_dir = Path(settings.ASSETS_DIR)
        self.assets_dir.mkdir(exist_ok=True, parents=True)

    def parse(self, url: str, document_id: str = None) -> list[ContentUnit]:
        doc_id = document_id or str(uuid.uuid4())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Download
            ydl_opts = {
                'format': 'best',
                'outtmpl': f'{tmpdir}/%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                doc_name = info.get('title', 'Unknown Video')
                video_id = info.get('id')
                ext = info.get('ext', 'mp4')
                video_file = f"{tmpdir}/{video_id}.{ext}"
                
                # 2. Audio Transcription
                if not self.model:
                    self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
                
                segments_gen, _ = self.model.transcribe(video_file, beam_size=5)
                segments = list(segments_gen)
                
                # 3. Visual Scene Detection
                scene_list = detect(video_file, ContentDetector(threshold=27.0))
                
                cap = cv2.VideoCapture(video_file)
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                scene_frames = []
                for i, scene in enumerate(scene_list):
                    start_time = scene[0].get_seconds()
                    end_time = scene[1].get_seconds()
                    frame_num = int(start_time * fps)
                    
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                    ret, frame = cap.read()
                    if ret:
                        asset_id = str(uuid.uuid4())
                        asset_path = self.assets_dir / f"{asset_id}.jpg"
                        cv2.imwrite(str(asset_path), frame)
                        vector_store.save_asset(asset_id, doc_id, str(asset_path), "video_frame")
                        
                        scene_frames.append({
                            "start_time": start_time,
                            "end_time": end_time,
                            "asset_id": asset_id
                        })
                cap.release()
                
                # 4. Temporal Alignment
                content_units = []
                for seg in segments:
                    seg_start = seg.start
                    seg_end = seg.end
                    
                    matched_assets = []
                    for scene in scene_frames:
                        if max(seg_start, scene["start_time"]) < min(seg_end, scene["end_time"]):
                            matched_assets.append(scene["asset_id"])
                            
                    unit = ContentUnit(
                        id=str(uuid.uuid4()),
                        document_id=doc_id,
                        document_name=doc_name,
                        source_type='video',
                        text=seg.text,
                        start_time=seg_start,
                        end_time=seg_end,
                        asset_ids=matched_assets,
                        extraction_methods={"text": "faster-whisper", "visual": "scenedetect"}
                    )
                    content_units.append(unit)
                    
                return content_units
