import streamlit as st
import tempfile
import os
import sys

# Ensure we can import from our project
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ingestion_service import ingestion_service
from services.answer_service import answer_service

st.set_page_config(page_title="MULTIMODAL RAG TESTER", layout="wide")

st.title("MULTIMODAL RAG TESTER")

st.header("INGEST")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("PDF")
    pdf_file = st.file_uploader("Upload PDF", type=['pdf'])
    if pdf_file and st.button("Ingest PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(pdf_file.getvalue())
            tmp_path = tmp.name
        
        with st.spinner("Ingesting PDF..."):
            try:
                metrics = ingestion_service.ingest_pdf(tmp_path)
                st.success("PDF ingested successfully")
                st.json(metrics)
            except Exception as e:
                import traceback
                st.error(f"❌ PDF ingestion failed\nReason: {e}\n{traceback.format_exc()}")
        try:
            os.unlink(tmp_path)
        except:
            pass

with col2:
    st.subheader("PPTX")
    pptx_file = st.file_uploader("Upload PPTX", type=['pptx'])
    if pptx_file and st.button("Ingest PPTX"):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp:
            tmp.write(pptx_file.getvalue())
            tmp_path = tmp.name
            
        with st.spinner("Ingesting PPTX..."):
            try:
                metrics = ingestion_service.ingest_pptx(tmp_path)
                st.success("PPTX ingested successfully")
                st.json(metrics)
            except Exception as e:
                import traceback
                st.error(f"❌ PPTX ingestion failed\nReason: {e}\n{traceback.format_exc()}")
        try:
            os.unlink(tmp_path)
        except:
            pass

with col3:
    st.subheader("VIDEO")
    yt_url = st.text_input("YouTube URL")
    if yt_url and st.button("Ingest Video"):
        with st.spinner("Ingesting Video..."):
            try:
                metrics = ingestion_service.ingest_video(yt_url)
                st.success("Video ingested successfully")
                st.json(metrics)
            except Exception as e:
                import traceback
                st.error(f"❌ Video ingestion failed\nReason: {e}\n{traceback.format_exc()}")

st.divider()

st.header("ASK")

question = st.text_input("What does the lecture explain about...?")

if st.button("Ask") and question:
    with st.spinner("Generating answer..."):
        try:
            result = answer_service.answer_question(question)
            
            st.divider()
            st.header("ANSWER")
            
            st.write(f"**Grounding:** {result['grounding']}")
            st.write(f"**Answerability:** {result['grounding']}")
            st.write(result['answer'])
            
            st.divider()
            st.header("SOURCES")
            
            evidence_map = {d["evidence_id"]: d for d in result["evidence"]}
            
            # Show claims and their sources
            for i, claim in enumerate(result['claims']):
                st.markdown(f"**Claim {i+1}:** {claim['text']}")
                for eid in claim['evidence_ids']:
                    if eid in evidence_map:
                        doc = evidence_map[eid]
                        source_info = f"[{eid}] {doc['source_type'].upper()} • "
                        if doc['source_type'] == 'pdf':
                            source_info += f"Page {doc['page']}"
                        elif doc['source_type'] == 'pptx':
                            source_info += f"Slide {doc['slide']}"
                        elif doc['source_type'] == 'video':
                            source_info += f"{doc['start_time']} - {doc['end_time']}"
                            
                        # Show full document context mapping to the evidence ID
                        with st.expander(source_info):
                            st.write(doc['document_name'])
                            
                            content_excerpt = doc.get('page_content', 'No text excerpt available')
                            if not content_excerpt and 'text' in doc:
                                content_excerpt = doc['text']
                                
                            st.text_area("Excerpt", value=content_excerpt, height=150, disabled=True)
                            
                            if doc.get('asset_ids'):
                                st.write("**Assets:**")
                                for asset_id in doc['asset_ids']:
                                    st.write(f"- `{asset_id}`")
                            
            st.divider()
            with st.expander("DEBUG ▼"):
                st.json({
                    "Latency": result['latency'],
                    "Claims": result['claims'],
                    "Grounding": result['grounding'],
                    "Evidence Count": len(result['evidence']),
                    "Raw Evidence": result['evidence']
                })
        except Exception as e:
            import traceback
            st.error(f"❌ Answer generation failed\nStage: LLM\nReason: {e}\n{traceback.format_exc()}")
