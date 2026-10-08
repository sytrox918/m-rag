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

st.header("KNOWLEDGE GRAPH")
st.write("Traverse the structural prerequisites network built by the LLM.")
target_concept = st.text_input("Enter a concept you want to learn (e.g. 'neural networks')")

if st.button("Generate Learning Path") and target_concept:
    from services.graph_service import graph_service
    path_data = graph_service.get_learning_path(target_concept)
    
    if "error" in path_data:
        st.error(path_data["error"])
    else:
        st.success(f"Learning Path for: **{path_data['target_concept']}**")
        
        # VISUAL GRAPH
        st.subheader("Visual Prerequisites Map")
        html_data = graph_service.generate_visual_graph(target_concept)
        import streamlit.components.v1 as components
        components.html(html_data, height=550)
        
        # TEXT PATH
        st.subheader("Recommended Reading Order")
        for i, step in enumerate(path_data['path']):
            with st.expander(f"Step {i+1}: {step['concept'].title()}", expanded=True):
                if step['recommended_sources']:
                    st.write("Recommended Sources:")
                    for src in step['recommended_sources']:
                        st.write(f"- [{src['source_type'].upper()}] {src['document_name']}")
                else:
                    st.write("*(No specific source document explicitly teaches this foundational prerequisite)*")

st.divider()

st.header("TUTOR CHAT")

if "sessions" not in st.session_state:
    st.session_state.sessions = {"General": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "General"

with st.sidebar:
    st.header("Chat Sessions")
    new_session = st.text_input("New Topic Session")
    if st.button("Create Session") and new_session:
        if new_session not in st.session_state.sessions:
            st.session_state.sessions[new_session] = []
        st.session_state.current_session = new_session
        
    st.session_state.current_session = st.radio("Select Session", list(st.session_state.sessions.keys()), index=list(st.session_state.sessions.keys()).index(st.session_state.current_session))
    
    if st.button("Clear Current Session"):
        st.session_state.sessions[st.session_state.current_session] = []
        st.rerun()

current_history = st.session_state.sessions[st.session_state.current_session]

def render_sources(result):
    evidence_map = {d["evidence_id"]: d for d in result["evidence"]}
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
                    
                with st.expander(source_info):
                    st.write(doc['document_name'])
                    content_excerpt = doc.get('page_content', 'No text excerpt available')
                    if not content_excerpt and 'text' in doc:
                        content_excerpt = doc['text']
                    st.text_area("Excerpt", value=content_excerpt, height=150, disabled=True)
                    if doc.get('topics'): st.write(f"**Topics:** {', '.join(doc['topics'])}")
                    if doc.get('concepts'): st.write(f"**Concepts:** {', '.join(doc['concepts'])}")
                    if doc.get('prerequisites'): st.write(f"**Prerequisites:** {', '.join(doc['prerequisites'])}")
                    if doc.get('asset_ids'):
                        st.write("**Assets:**")
                        from config.settings import settings
                        for asset_id in doc['asset_ids']:
                            png_path = os.path.join(settings.ASSETS_DIR, f"{asset_id}.png")
                            jpg_path = os.path.join(settings.ASSETS_DIR, f"{asset_id}.jpg")
                            if os.path.exists(png_path): st.image(png_path, caption=asset_id)
                            elif os.path.exists(jpg_path): st.image(jpg_path, caption=asset_id)
                            else: st.write(f"- `{asset_id}` (File missing)")

for msg in current_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "result" in msg:
            with st.expander("View Sources"):
                render_sources(msg["result"])

if prompt := st.chat_input(f"Ask your tutor about {st.session_state.current_session}..."):
    current_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                backend_history = [{"role": m["role"], "content": m["content"]} for m in current_history[:-1]]
                result = answer_service.answer_question(prompt, backend_history)
                st.write(result["answer"])
                with st.expander("View Sources", expanded=True):
                    render_sources(result)
                current_history.append({"role": "assistant", "content": result["answer"], "result": result})
            except Exception as e:
                import traceback
                st.error(f"❌ Answer generation failed\nReason: {e}\n{traceback.format_exc()}")
