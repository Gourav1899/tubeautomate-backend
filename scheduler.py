"""Multi-Channel Scheduler"""
import schedule
import time
import logging
from database import supabase
from processor import process_one_video

log = logging.getLogger(__name__)


def check_and_upload():
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M")
    log.info(f"⏰ Schedule check at {current_time}")
    try:
        result = supabase.table("channels").select("*").eq("is_active", True).execute()
        channels = result.data
        if not channels:
            log.info("📭 Koi active channel nahi")
            return
        for channel in channels:
            schedule_times = channel.get("schedule_times", ["09:00", "15:00", "21:00"])
            if current_time in schedule_times:
                log.info(f"🎬 Channel: {channel['channel_name']} — upload time!")
                process_one_video(channel)
    except Exception as e:
        log.error(f"Scheduler error: {e}")


def load_all_videos_for_channel(channel: dict):
    from drive_watcher import DriveWatcher
    log.info(f"📁 Loading videos for: {channel['channel_name']}")
    try:
        drive_token_data = channel.get("drive_token_data")
        if not drive_token_data:
            log.error(f"❌ {channel['channel_name']} — Drive token missing!")
            return 0

        watcher = DriveWatcher(
            folder_id=channel["drive_folder_id"],
            token_data=drive_token_data
        )
        all_videos = watcher.get_all_videos()
        added = 0
        for video in all_videos:
            existing = supabase.table("queue").select("id").eq(
                "video_file_id", video["id"]
            ).eq("channel_id", channel["id"]).execute()
            if not existing.data:
                supabase.table("queue").insert({
                    "channel_id": channel["id"],
                    "user_id": channel["user_id"],
                    "video_file_id": video["id"],
                    "video_name": video["name"],
                    "status": "pending"
                }).execute()
                added += 1
        log.info(f"✅ {added} new videos added for {channel['channel_name']}")
        return added
    except Exception as e:
        log.error(f"Load videos error for {channel['channel_name']}: {e}")
        return 0


def daily_drive_refresh():
    log.info("🔄 Daily Drive refresh starting...")
    try:
        result = supabase.table("channels").select("*").eq("is_active", True).execute()
        for channel in result.data:
            if channel.get("drive_token_data") and channel.get("drive_folder_id") != "pending":
                load_all_videos_for_channel(channel)
    except Exception as e:
        log.error(f"Daily refresh error: {e}")


def run_scheduler():
    log.info("=" * 50)
    log.info("🤖 Multi-Channel Scheduler Starting")
    log.info("=" * 50)

    # Pehle schedule register karo
    schedule.every(1).minutes.do(check_and_upload)
    schedule.every().day.at("08:45").do(daily_drive_refresh)
    log.info("✅ Scheduler running — checking every minute")

    # 60 second baad Drive refresh (server start hone ke baad)
    time.sleep(60)
    daily_drive_refresh()

    while True:
        schedule.run_pending()
        time.sleep(30)
