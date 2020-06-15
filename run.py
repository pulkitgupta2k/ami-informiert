from helper import driver
import time
import schedule

if __name__ == "__main__":
    for i in ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]:
        schedule.every().monday.at(i).do(driver)
        schedule.every().tuesday.at(i).do(driver)
        schedule.every().wednesday.at(i).do(driver)
        schedule.every().thursday.at(i).do(driver)
        schedule.every().friday.at(i).do(driver)

    while True:
        try:
            schedule.run_pending()
        except:
            pass
        time.sleep(30)
        