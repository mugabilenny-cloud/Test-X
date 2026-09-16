import streamlit as st

import local_auth
from local_client import fetch_resource, save_bookmark, record_resource_opened
from ui_components import inject_base_css, file_type_chip, youtube_embed

st.set_page_config(page_title="Viewer | Switch", page_icon="📄", layout="centered", initial_sidebar_state="collapsed")
inject_base_css()

resource_id = st.session_state.get("active_resource_id")

if not resource_id:
    st.warning("No resource selected.")
    if st.button("← Back to Home"):
        st.switch_page("pages/1_Home.py")
    st.stop()

resource = fetch_resource(resource_id)

# gap #5 fix: history recording. Guarded one-shot-per-session (rule #7 of
# the handoff doc) --- this page has its own buttons (fullscreen toggle,
# Save, Share) that rerun this exact script with the same resource_id
# still in session state, the same rerun-heavy risk already caught once
# in ui_components.video_resource_card(); an unconditional call here
# would re-log "just opened" on every one of those clicks, not just the
# actual navigation into the Viewer.
user = local_auth.current_user()
student_id = user["user_id"] if user else "demo-student"
recorded_key = f"_history_recorded_{resource_id}"
if not st.session_state.get(recorded_key):
    record_resource_opened(student_id, resource)
    st.session_state[recorded_key] = True

top = st.columns([1, 4, 1])
if top[0].button("✕ Close"):
    st.switch_page("pages/1_Home.py")
top[1].markdown(f"**{resource.get('title', 'Resource')}**")
fullscreen = top[2].button("⛶")

st.markdown(file_type_chip(resource.get("file_type", "")), unsafe_allow_html=True)
st.caption(resource.get("course_code", ""))

# gap #5 fix: embed rendering. A youtube-kind resource now plays inline
# via the same youtube_embed() iframe used in
# ui_components.video_resource_card(), instead of falling into the
# generic placeholder box below --- no new embed logic invented here,
# reusing what gap #9 (done item, prior turn) already built and tested.
if resource.get("file_type") == "video" and resource.get("youtube_video_id"):
    youtube_embed(resource["youtube_video_id"], height=280 if fullscreen else 220)
else:
    st.markdown(
        f"""
        <div style="border:1px solid #E5E7EB; border-radius:12px; padding: {"3rem" if fullscreen else "5rem"} 1rem;
                    text-align:center; background:#F5F6FA; margin-top: 0.6rem;">
            <div style="font-size:2.5rem;">{'📄' if resource.get('file_type') == 'pdf' else '📊' if resource.get('file_type') == 'ppt' else '📝'}</div>
            <div style="color:#6B7280; margin-top:0.5rem;">
                Inline preview placeholder --- this is where the real PDF/slide/text
                renderer mounts. No download forced to open this.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

cols = st.columns(3)
if cols[0].button("🔖 Save", use_container_width=True):
    # gap #5 fix: student_id threaded through, same pattern as gaps
    # #1/#2/#4.
    save_bookmark(resource, student_id=student_id)
    st.toast("Saved")
if cols[1].button("🔗 Copy Share Link", use_container_width=True):
    st.toast("Share links aren't available yet --- no deep-link scheme exists in this schema.")
cols[2].button("⬇️ Download", use_container_width=True, disabled=True, help="Intentionally de-emphasized per spec --- inline viewing is the default.")
