import os
import time
import streamlit as st

from local_ads import create_ad, list_ads, save_asset, set_ad_active
from local_notifications import queue_notification, pending_notifications
from ui_components import inject_base_css, wordmark

st.set_page_config(
    page_title="Switch Admin",
    page_icon="🟠",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_base_css()

wordmark()
st.caption("Separate admin dashboard — ads and notification groundwork")

# This is intentionally separate from student auth. In production, replace
# the environment-variable gate with the real admin identity/role system.
admin_username = os.getenv("SWITCH_ADMIN_USERNAME", "admin")
admin_password = os.getenv("SWITCH_ADMIN_PASSWORD")
if not admin_password:
    st.warning("Set SWITCH_ADMIN_PASSWORD before using the admin dashboard.")
    st.stop()

with st.form("admin_login"):
    username = st.text_input("Admin username")
    password = st.text_input("Admin password", type="password")
    login = st.form_submit_button("Log in", use_container_width=True)

if login:
    st.session_state["admin_authenticated"] = (
        username.strip() == admin_username and password == admin_password
    )

if not st.session_state.get("admin_authenticated"):
    st.info("This dashboard is separate from student sign-in.")
    st.stop()

tab_ads, tab_notifications = st.tabs(["Ads", "Push notifications"])

with tab_ads:
    st.markdown("### Create an ad")
    with st.form("create_ad_form"):
        title = st.text_input("Ad title")
        advertiser = st.text_input("Advertiser")
        body = st.text_area("Short message")
        destination_url = st.text_input("Destination URL", placeholder="https://...")
        course_names = st.text_input(
            "Optional course targeting",
            placeholder="Pathophysiology, Pharmacology",
        )
        creative = st.file_uploader(
            "Optional creative",
            type=["png", "jpg", "jpeg", "webp"],
        )
        starts = st.date_input("Start date")
        ends = st.date_input("End date")
        submit_ad = st.form_submit_button("Publish ad", use_container_width=True)

    if submit_ad:
        if not title or not advertiser or not destination_url:
            st.error("Title, advertiser, and destination URL are required.")
        else:
            asset_path = save_asset(creative)
            starts_at = time.mktime(starts.timetuple()) if starts else None
            ends_at = time.mktime(ends.timetuple()) + 86399 if ends else None
            ad = create_ad(
                title=title,
                advertiser=advertiser,
                body=body,
                destination_url=destination_url,
                course_names=[x.strip() for x in course_names.split(",") if x.strip()],
                asset_filename=asset_path,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            st.success(f"Published {ad['title']}.")

    st.markdown("### Existing ads")
    for ad in list_ads(active_only=False):
        with st.container():
            st.markdown(
                f"""<div class="card">
                <div class="card-title">{ad.get('title', 'Untitled')}</div>
                <div class="card-meta">{ad.get('advertiser', '')} · {'active' if ad.get('active') else 'paused'}</div>
                <div>{ad.get('body', '')}</div>
                </div>""",
                unsafe_allow_html=True,
            )
            new_state = not ad.get("active", True)
            if st.button(
                "Pause" if ad.get("active", True) else "Activate",
                key=f"toggle_ad_{ad['id']}",
                use_container_width=True,
            ):
                set_ad_active(ad["id"], new_state)
                st.rerun()

with tab_notifications:
    st.markdown("### Queue a push notification")
    st.caption(
        "This creates a durable notification job. Sending through FCM/APNs/Web Push "
        "is intentionally left for the future smartphone-app delivery adapter."
    )
    with st.form("notification_form"):
        notification_title = st.text_input("Notification title")
        notification_body = st.text_area("Notification body")
        audience = st.selectbox("Audience", ["all", "users"])
        user_ids_text = st.text_input(
            "User IDs (comma separated)",
            disabled=audience != "users",
        )
        submit_notification = st.form_submit_button(
            "Queue notification",
            use_container_width=True,
        )
    if submit_notification:
        if not notification_title or not notification_body:
            st.error("Title and body are required.")
        else:
            job = queue_notification(
                notification_title,
                notification_body,
                audience=audience,
                user_ids=[x.strip() for x in user_ids_text.split(",") if x.strip()],
            )
            st.success(f"Queued notification {job['id']}.")

    pending = pending_notifications()
    st.markdown(f"### Pending jobs ({len(pending)})")
    for job in pending:
        st.write(f"**{job['title']}** — {job['body']}")
