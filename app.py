import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os
from job_scraper import EnhancedJobScraper
from onedrive_uploader import OneDriveUploader

st.set_page_config(
    page_title="Job Scraper",
    page_icon="🤖",
    layout="centered"
)

def main():
    st.title("🤖 AI/ML Job Scraper")
    st.write("Click the button below to scrape jobs and save to your OneDrive")
    
    # Initialize session state
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'completed' not in st.session_state:
        st.session_state.completed = False
    if 'job_count' not in st.session_state:
        st.session_state.job_count = 0
    
    # Big run button
    if st.button("🚀 RUN JOB SCRAPER", type="primary", disabled=st.session_state.running):
        run_scraper()
    
    # Show status
    if st.session_state.running:
        st.info("🔄 Scraper is running... Please wait")
        
    if st.session_state.completed:
        st.success(f"✅ Completed! Found {st.session_state.job_count} jobs")
        st.success("📁 File uploaded to your OneDrive!")

def run_scraper():
    """Run the job scraper and upload to OneDrive"""
    st.session_state.running = True
    st.session_state.completed = False
    
    # Create progress placeholder
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        # Initialize scraper
        with status_placeholder:
            st.info("🔧 Initializing scraper...")
        
        scraper = EnhancedJobScraper()
        
        # Progress bar
        progress_bar = progress_placeholder.progress(0)
        
        # Scrape Greenhouse
        with status_placeholder:
            st.info("🔍 Scraping Greenhouse jobs...")
        progress_bar.progress(0.2)
        greenhouse_jobs = scraper.scrape_greenhouse_jobs()
        
        # Scrape Lever
        with status_placeholder:
            st.info("🔍 Scraping Lever jobs...")
        progress_bar.progress(0.4)
        lever_jobs = scraper.scrape_lever_jobs()
        
        # Scrape other sources
        with status_placeholder:
            st.info("🔍 Scraping other job portals...")
        progress_bar.progress(0.6)
        angellist_jobs = scraper.scrape_angellist_jobs()
        yc_jobs = scraper.scrape_ycombinator_jobs()
        remote_jobs = scraper.scrape_remoteco_jobs()
        wwr_jobs = scraper.scrape_weworkremotely_jobs()
        
        # Process all jobs
        with status_placeholder:
            st.info("⚙️ Processing jobs...")
        progress_bar.progress(0.8)
        
        all_jobs = greenhouse_jobs + lever_jobs + angellist_jobs + yc_jobs + remote_jobs + wwr_jobs
        processed_jobs = scraper.process_jobs(all_jobs)
        scraper.jobs_data = processed_jobs
        
        # Create Excel file
        with status_placeholder:
            st.info("📊 Creating Excel file...")
        progress_bar.progress(0.9)
        excel_file = scraper.create_excel_file()
        
        # Upload to OneDrive
        with status_placeholder:
            st.info("☁️ Uploading to OneDrive...")
        
        # Get OneDrive credentials
        client_id = os.getenv('MICROSOFT_CLIENT_ID')
        client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        tenant_id = os.getenv('MICROSOFT_TENANT_ID')
        
        if not all([client_id, client_secret, tenant_id]):
            st.error("❌ OneDrive credentials not configured!")
            return
        
        # Upload file
        uploader = OneDriveUploader(client_id, client_secret, tenant_id)
        
        if uploader.get_access_token():
            file_id = uploader.upload_file(excel_file)
            
            if file_id:
                # Share with configured users if any
                share_users = os.getenv('SHARE_USERS', '').split(',')
                if share_users and share_users[0]:
                    uploader.share_with_users(file_id, [user.strip() for user in share_users if user.strip()])
                
                progress_bar.progress(1.0)
                
                # Update session state
                st.session_state.job_count = len(processed_jobs)
                st.session_state.completed = True
                st.session_state.running = False
                
                # Clear status
                progress_placeholder.empty()
                status_placeholder.empty()
                
                # Rerun to show completion message
                st.rerun()
            else:
                st.error("❌ Failed to upload to OneDrive")
        else:
            st.error("❌ Failed to authenticate with OneDrive")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
    finally:
        st.session_state.running = False

if __name__ == "__main__":
    main()