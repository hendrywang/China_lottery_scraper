from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class LotteryScraper:
    def __init__(self):
        # Initialize Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--enable-javascript')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.base_url = "https://www.sporttery.cn/ctzc/jsq/index.html"
        
    def wait_for_element(self, by, value, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timeout waiting for element: {value}")
            return None

    def wait_for_period_info(self, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".m-czNums li.on span"))
            )
            return True
        except TimeoutException:
            print("Timeout waiting for period information")
            return False

    def scrape_match_data(self):
        print("Starting scraper...")
        self.driver.get(self.base_url)
        print("Page loaded, waiting for content...")
        
        # Wait for JavaScript to load
        time.sleep(10)  # Increased wait time
        
        # Execute JavaScript to check if page is ready
        is_ready = self.driver.execute_script("return document.readyState") == "complete"
        print(f"Page ready state: {is_ready}")
        
        # Wait for specific element that indicates the page is fully loaded
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".m-sfcL"))
            )
        except TimeoutException:
            print("Timeout waiting for page to load completely")
            return
        
        current_date = datetime.now().strftime("%Y%m%d")
        matches_by_type = {
            '胜负游戏': [],
            '任选9场': [],
            '6场半全场': [],
            '4场进球': []
        }
        
        try:
            # Wait for game type tabs
            tabs = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".m-czTitle-l li"))
            )
            print(f"Found {len(tabs)} tabs")
            
            for tab in tabs:
                try:
                    game_type_text = tab.text.strip()
                    if not game_type_text in matches_by_type:
                        continue
                    
                    print(f"\nProcessing game type: {game_type_text}")
                    
                    # Click game type tab
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", tab)
                    time.sleep(2)
                    self.driver.execute_script("arguments[0].click();", tab)
                    time.sleep(3)
                    
                    # Find and process both sale status tabs
                    sale_status_tabs = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".m-zstab li"))
                    )
                    
                    for status_tab in sale_status_tabs:
                        try:
                            status_text = status_tab.text.strip()
                            print(f"Processing {status_text}")
                            
                            # Click sale status tab
                            self.driver.execute_script("arguments[0].click();", status_tab)
                            time.sleep(3)
                            
                            # Get all period tabs for this status
                            period_tabs = WebDriverWait(self.driver, 10).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".m-czNums li"))
                            )
                            
                            # Process each period
                            for period_tab in period_tabs:
                                try:
                                    period_span = period_tab.find_element(By.TAG_NAME, "span")
                                    period_info = period_span.text.strip() + "期"
                                    print(f"Processing period: {period_info}")
                                    
                                    # Click period tab and wait
                                    self.driver.execute_script("arguments[0].click();", period_tab)
                                    time.sleep(3)
                                    
                                    # Get deadline/sale time
                                    try:
                                        time_element = WebDriverWait(self.driver, 5).until(
                                            EC.presence_of_element_located((By.CSS_SELECTOR, ".m-czTime-r.f-fr"))
                                        )
                                        time_text = time_element.text.strip()
                                        
                                        # Update time info based on sale status
                                        if status_text == "即将开售":
                                            sale_time = time_text.replace('开售时间：', '')
                                            deadline_time = ''
                                        else:  # 在售奖期
                                            deadline_time = time_text.replace('投注截止时间：', '')
                                            sale_time = ''
                                            
                                    except Exception as e:
                                        print(f"Error getting time info: {str(e)}")
                                        deadline_time = ''
                                        sale_time = ''
                                    
                                    # Process matches table
                                    try:
                                        table = WebDriverWait(self.driver, 10).until(
                                            EC.visibility_of_element_located((By.CSS_SELECTOR, ".m-czTab"))
                                        )
                                        
                                        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr:not([style*='display: none'])")
                                        print(f"Found {len(rows)} match rows for period {period_info} ({status_text})")
                                        
                                        for row in rows:
                                            try:
                                                cells = row.find_elements(By.TAG_NAME, "td")
                                                if len(cells) < 5:
                                                    continue
                                                
                                                # Basic match data with deadline time
                                                match_data = {
                                                    'period': period_info,
                                                    'sale_status': status_text,
                                                    'deadline_time': deadline_time,
                                                    'sale_time': sale_time,
                                                    'match_num': cells[0].text.strip(),
                                                    'league': cells[1].find_element(By.TAG_NAME, "span").text.strip(),
                                                    'start_time': cells[2].text.strip()
                                                }
                                                
                                                # Get team names
                                                team_div = cells[3].find_element(By.CLASS_NAME, "team")
                                                teams_text = team_div.text.strip()
                                                if "VS" in teams_text:
                                                    home, away = teams_text.split("VS")
                                                    match_data['home_team'] = home.strip()
                                                    match_data['away_team'] = away.strip()
                                                
                                                # Handle different game types
                                                if game_type_text in ['胜负游戏', '任选9场']:
                                                    try:
                                                        odds = cells[4].find_elements(By.CSS_SELECTOR, ".tdDiv span em")
                                                        if len(odds) >= 3:
                                                            match_data.update({
                                                                'bet_win': odds[0].text.strip(),
                                                                'bet_draw': odds[1].text.strip(),
                                                                'bet_lose': odds[2].text.strip()
                                                            })
                                                    except Exception as e:
                                                        print(f"Error getting odds: {str(e)}")
                                                
                                                elif game_type_text == '6场半全场':
                                                    try:
                                                        betting_divs = cells[5].find_elements(By.CSS_SELECTOR, ".tdDiv")
                                                        if len(betting_divs) == 2:
                                                            half_time = betting_divs[0].find_elements(By.CSS_SELECTOR, "span em")
                                                            full_time = betting_divs[1].find_elements(By.CSS_SELECTOR, "span em")
                                                            
                                                            if len(half_time) >= 3:
                                                                match_data.update({
                                                                    'half_win': half_time[0].text.strip(),
                                                                    'half_draw': half_time[1].text.strip(),
                                                                    'half_lose': half_time[2].text.strip()
                                                                })
                                                            
                                                            if len(full_time) >= 3:
                                                                match_data.update({
                                                                    'full_win': full_time[0].text.strip(),
                                                                    'full_draw': full_time[1].text.strip(),
                                                                    'full_lose': full_time[2].text.strip()
                                                                })
                                                    except Exception as e:
                                                        print(f"Error getting half/full time odds: {str(e)}")
                                                
                                                elif game_type_text == '4场进球':
                                                    try:
                                                        betting_divs = cells[5].find_elements(By.CSS_SELECTOR, ".tdDiv")
                                                        if len(betting_divs) == 2:
                                                            home_goals = betting_divs[0].find_elements(By.CSS_SELECTOR, "span em")
                                                            away_goals = betting_divs[1].find_elements(By.CSS_SELECTOR, "span em")
                                                            
                                                            for i, val in enumerate(['0', '1', '2', '3+']):
                                                                if i < len(home_goals):
                                                                    match_data[f'home_goals_{val}'] = home_goals[i].text.strip()
                                                                if i < len(away_goals):
                                                                    match_data[f'away_goals_{val}'] = away_goals[i].text.strip()
                                                    except Exception as e:
                                                        print(f"Error getting goals odds: {str(e)}")
                                                
                                                matches_by_type[game_type_text].append(match_data)
                                                print(f"Processed match: Period {period_info} - {match_data.get('home_team', '')} vs {match_data.get('away_team', '')}")
                                                
                                            except Exception as e:
                                                print(f"Error processing match row: {str(e)}")
                                                continue
                                            
                                    except Exception as e:
                                        print(f"Error processing table for period {period_info}: {str(e)}")
                                        continue
                                    
                                except Exception as e:
                                    print(f"Error processing period tab: {str(e)}")
                                    continue
                                
                        except Exception as e:
                            print(f"Error processing sale status tab {status_text}: {str(e)}")
                            continue
                        
                except Exception as e:
                    print(f"Error processing game type {game_type_text}: {str(e)}")
                    continue
            
            # Save results
            for game_type, matches in matches_by_type.items():
                if matches:
                    print(f"\nSaving {len(matches)} matches for {game_type}...")
                    df = pd.DataFrame(matches)
                    filename = f'lottery_selling_{game_type}_{current_date}.csv'
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    print(f"Data saved to {filename}")
                else:
                    print(f"\nNo matches found for {game_type}")
                    
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            print(self.driver.page_source[:1000])
            
        finally:
            print("\nClosing browser...")
            self.driver.quit()

    def run(self):
        self.scrape_match_data()

if __name__ == "__main__":
    scraper = LotteryScraper()
    scraper.run()
