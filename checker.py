import os
import re
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= ACCOUNT CONFIGURATION =================
ACCOUNTS = [
     {
        "name": "jasimrahman7 S13",
        "country_code": "+880",
        "phone": "1304008726",
        "password": "Pass789",
    }, 
    {
        "name": "kh2 fb7",
        "country_code": "+880",
        "phone": "1863006261",
        "password": "Alamin143@",
    },
    {
        "name": "Mama",
        "country_code": "+880",
        "phone": "1789095816",
        "password": "Alamin143@",
    },
    {
        "name": "khalu 3 s13",
        "country_code": "+880",
        "phone": "1793965546",
        "password": "Alamin143@",
    },
    {
        "name": "Jamirul",
        "country_code": "+880",
        "phone": "1750450182",
        "password": "Alamin143#",
    },   
]

LOGIN_URL = "https://www.zenquantai.com/#/pages/login/login"
TRADE_URL = "https://www.zenquantai.com/#/pages/UITransaction/trade"

# ================= CONFIGURATION =================
MAX_RETRIES = 3
RETRY_DELAY = 5  
CYCLE_INTERVAL = 86400  # ২৪ ঘণ্টা 

# ================= HELPER & PARSING FUNCTIONS =================
def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{int(hours):02d}h {int(minutes):02d}m {int(secs):02d}s"

def parse_remaining_seconds(text):
    if not text: return 0
    text = text.lower().strip()
    if "claimable" in text: return 0
    
    total_sec = 0
    if ":" in text:
        parts = text.split(":")
        try:
            if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
        except Exception: pass
        
    h_match = re.search(r"(\d+)\s*h", text)
    m_match = re.search(r"(\d+)\s*m", text)
    s_match = re.search(r"(\d+)\s*s", text)
    if h_match: total_sec += int(h_match.group(1)) * 3600
    if m_match: total_sec += int(m_match.group(1)) * 60
    if s_match: total_sec += int(s_match.group(1))
    
    return total_sec

def check_and_get_card_timers(driver):
    time.sleep(2)
    min_time = None
    has_claimable = False
    
    try:
        timer_texts = driver.execute_script("""
            var texts = [];
            var elements = document.querySelectorAll('.trade-pos__claim, .trade-dur--on, uni-view');
            for(var i=0; i<elements.length; i++){
                var t = elements[i].textContent.trim();
                if(t.includes('Claimable') || t.match(/\\d+h\\s*\\d+m/) || t.match(/\\d+m\\s*\\d+s/) || t.match(/\\d+:\\d+/)){
                    texts.push(t);
                }
            }
            return texts;
        """)

        for text in timer_texts:
            if "Claimable" in text:
                has_claimable = True
                return 0
            sec = parse_remaining_seconds(text)
            if sec > 0:
                if min_time is None or sec < min_time:
                    min_time = sec
                    
        if has_claimable: return 0
        if min_time is not None: return min_time
    except Exception as e:
        print(f"⚠️ Timer checking error: {e}")
        
    return None

def countdown_timer(total_seconds, message="⏳ Next check in"):
    start_time = time.time()
    end_time = start_time + total_seconds
    
    print(f"\n{message}")
    print("=" * 60)
    
    while True:
        current_time = time.time()
        remaining = end_time - current_time
        
        if remaining <= 0:
            print("\n" + "=" * 60)
            print("🔄 NEXT CYCLE STARTING NOW!")
            print("=" * 60 + "\n")
            break
        
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        
        progress = 1 - (remaining / total_seconds)
        bar_length = 30
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r⏳ {hours:02d}h {minutes:02d}m {seconds:02d}s | {bar} | {progress*100:.1f}%", end="", flush=True)
        time.sleep(1)

def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        return None

def extract_country_code(text):
    match = re.search(r'\+\d+', text)
    return match.group(0) if match else None

def select_country_by_code(driver, wait, country_code):
    try:
        try:
            country_selector = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//uni-view[contains(@class, 'w-full theme_Login_Input_bg')]//uni-view[contains(@class, 'flex items-center')]"))
            )
            driver.execute_script("arguments[0].click();", country_selector)
            time.sleep(1.5)
        except:
            try:
                country_selector = wait.until(EC.element_to_be_clickable((By.XPATH, "//uni-view[contains(text(), '+')]")))
                driver.execute_script("arguments[0].click();", country_selector)
                time.sleep(1.5)
            except:
                print("❌ Could not open country selector")
                return False
        
        country_items = driver.find_elements(By.XPATH, "//uni-view[contains(@class, 'country-list-row')]")
        for item in country_items:
            try:
                if extract_country_code(item.text) == country_code:
                    driver.execute_script("arguments[0].click();", item)
                    time.sleep(1)
                    return True
            except:
                continue
        return False
    except Exception as e:
        return False

def handle_activity_notice(driver):
    try:
        activity_popup = driver.find_elements(By.XPATH, "//uni-view[contains(@class, 'face-activity-dialog')]")
        if activity_popup:
            try:
                cancel_btn = driver.find_element(By.XPATH, "//uni-view[contains(@class, 'btnCalcel')]")
                driver.execute_script("arguments[0].click();", cancel_btn)
                time.sleep(1)
            except:
                pass
    except Exception:
        pass

def login(driver, wait, phone, password, country_code):
    try:
        if not select_country_by_code(driver, wait, country_code):
            select_country_by_code(driver, wait, "+880")
        
        inputs = driver.find_elements(By.CSS_SELECTOR, "input.uni-input-input")
        if len(inputs) >= 2:
            inputs[0].clear()
            inputs[0].send_keys(phone)
            inputs[1].clear()
            inputs[1].send_keys(password)
        else:
            print("❌ Login inputs not found!")
            return False
        
        time.sleep(0.5)
        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "uni-view.zq-cta")))
        driver.execute_script("arguments[0].click();", login_btn)
        
        time.sleep(5)
        handle_activity_notice(driver)
        return True
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def extract_current_page_balance(driver, wait):
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'My Assets')]")))
        time.sleep(2)
        
        elements = driver.find_elements(By.XPATH, "//uni-view[contains(text(), 'My Assets')]/following::uni-view[contains(text(), 'USD')]")
        for elem in elements:
            text = elem.text.strip()
            match = re.search(r'([\d\.]+)\s*USD', text)
            if match:
                return f"{match.group(1)} USD"

        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'USD')]")
        for elem in all_elements:
            text = elem.text.strip()
            match = re.search(r'([\d\.]+)\s*USD', text)
            if match:
                return f"{match.group(1)} USD"
        return "N/A"
    except Exception as e:
        print(f"❌ Failed to extract balance: {e}")
        return "Error"

def process_account(account, attempt):
    print(f"\n{'='*60}")
    print(f"🔄 Checking {account['name']} - Attempt {attempt}")
    print(f"📱 Phone: {account['phone']} ({account.get('country_code', '+880')})")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    driver = None
    try:
        driver = setup_driver()
        if not driver:
            return False, "Driver Error", None
            
        wait = WebDriverWait(driver, 15)
        driver.get(LOGIN_URL)
        time.sleep(2)
        handle_activity_notice(driver)
        
        country_code = account.get('country_code', '+880')
        if login(driver, wait, account['phone'], account['password'], country_code):
            print("✅ Login successful! Reading 'My Assets' balance directly from current page...")
            balance = extract_current_page_balance(driver, wait)
            print(f"💰 Balance Found: {balance}")
            
            print("⏳ Navigating to Trade page to check remaining time...")
            driver.get(TRADE_URL)
            time.sleep(3)
            handle_activity_notice(driver)
            
            remaining_seconds = check_and_get_card_timers(driver)
            if remaining_seconds is not None:
                if remaining_seconds == 0:
                    print("⏱️ Status: Claimable NOW!")
                else:
                    print(f"⏱️ Timer Found: {format_time(remaining_seconds)}")
            else:
                print("⚠️ No active timer found on trade cards.")

            return True, balance, remaining_seconds
            
        return False, "Login Failed", None
    except Exception as e:
        print(f"❌ Unhandled error processing {account['name']}: {e}")
        return False, "Error", None
    finally:
        if driver:
            driver.quit()

def print_summary(summary_data, cycle_count, previous_balances, previous_total_sum):
    total_sum = 0.0
    
    print("\n" + "=" * 135)
    print(f" 📊 ACCOUNTS BALANCE & SCHEDULE SUMMARY (CYCLE #{cycle_count})")
    print("=" * 135)
    print(f"{'Account Name':<15} | {'Phone Number':<16} | {'Prev Balance':<14} | {'New Balance':<14} | {'Profit':<10} | {'Remaining Time':<16} | {'Exact Next Run':<20}")
    print("-" * 135)
    
    for data in summary_data:
        match = re.search(r'[\d\.]+', data['balance'])
        current_bal = float(match.group(0)) if match else 0.0
        total_sum += current_bal
        
        prev_bal_str = previous_balances.get(data['name'], "N/A")
        prev_bal_match = re.search(r'[\d\.]+', prev_bal_str) if prev_bal_str != "N/A" else None
        prev_bal_val = float(prev_bal_match.group(0)) if prev_bal_match else 0.0
        
        if cycle_count > 1 and prev_bal_str != "N/A":
            profit = current_bal - prev_bal_val
            profit_str = f"+{profit:.4f}" if profit >= 0 else f"{profit:.4f}"
        else:
            prev_bal_str = "N/A"
            profit_str = "N/A"

        print(f"{data['name']:<15} | {data['phone']:<16} | {prev_bal_str:<14} | {data['balance']:<14} | {profit_str:<10} | {data['rem_str']:<16} | {data['next_time']:<20}")
        
    print("-" * 135)
    print(f"{'TOTAL SUM OF ALL ACCOUNTS':<80} | {total_sum:.5f} USD")
    
    if cycle_count > 1 and previous_total_sum is not None:
        total_profit = total_sum - previous_total_sum
        print(f"{'PREVIOUS TOTAL SUM':<80} | {previous_total_sum:.5f} USD")
        if total_profit >= 0:
            print(f"{'TOTAL PROFIT':<80} | +{total_profit:.5f} USD")
        else:
            print(f"{'TOTAL PROFIT':<80} | {total_profit:.5f} USD")

    print("=" * 135 + "\n")
    return total_sum

def main():
    cycle_count = 1
    previous_balances = {}  
    previous_total_sum = None 
    
    while True:
        print(f"\n🚀 Starting Balance & Time Check Cycle #{cycle_count}")
        print(f"⏰ Cycle Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        summary_data = []
        
        for account in ACCOUNTS:
            success = False
            final_balance = "N/A"
            final_seconds = None
            
            for attempt in range(1, MAX_RETRIES + 1):
                success, balance, remaining_sec = process_account(account, attempt)
                if success:
                    final_balance = balance
                    final_seconds = remaining_sec
                    break
                print(f"⚠️ Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                
            if not success:
                print(f"❌ Account {account['name']} failed after {MAX_RETRIES} attempts.")
            
            if final_seconds is not None:
                if final_seconds == 0:
                    rem_str = "Claimable Now"
                    next_time_str = "Right Now"
                else:
                    rem_str = format_time(final_seconds)
                    next_time_obj = datetime.now() + timedelta(seconds=final_seconds)
                    next_time_str = next_time_obj.strftime('%Y-%m-%d %I:%M %p')
            else:
                rem_str = "N/A"
                next_time_str = "N/A"
                
            summary_data.append({
                "name": account["name"],
                "phone": f"{account.get('country_code', '')}{account['phone']}",
                "balance": final_balance,
                "rem_str": rem_str,
                "next_time": next_time_str
            })
        
        current_total_sum = print_summary(summary_data, cycle_count, previous_balances, previous_total_sum)
        
        for data in summary_data:
            previous_balances[data['name']] = data['balance']
        previous_total_sum = current_total_sum
        
        cycle_count += 1
        countdown_timer(CYCLE_INTERVAL, "⏳ Cycle finished. Waiting for next data collection:")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Execution stopped manually by user.")
