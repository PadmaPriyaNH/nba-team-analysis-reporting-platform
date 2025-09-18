import schedule
import time
import os

def run_all():
    os.system("python main_analysis.py")
    os.system("python email_summary.py")

# Run every Monday at 9 AM
#schedule.every().monday.at("09:00").do(run_all)
schedule.every(1).minutes.do(run_all)


print("🔄 Auto-scheduler running...")
while True:
    schedule.run_pending()
    time.sleep(60)
