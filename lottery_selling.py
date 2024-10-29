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

    def scrape_match_data(self):
        print("Starting scraper...")
        self.driver.get(self.base_url)
        print("Page loaded, waiting for content...")
        time.sleep(5)
        
        current_date = datetime.now().strftime("%Y%m%d")
        matches_by_type = {
            '胜负游戏': [],
            '任选9场': [],
            '6场半全场': [],
            '4场进球': []
        }
        
        try:
            game_types = self.driver.find_elements(By.CSS_SELECTOR, ".m-czTitle-l li")
            
            for index, game_type in enumerate(game_types):
                try:
                    game_type.click()
                    time.sleep(2)
                    game_type_text = game_type.text.strip()
                    print(f"Processing game type: {game_type_text}")
                    
                    # Get period number and deadline
                    period_element = self.driver.find_element(By.CSS_SELECTOR, ".m-czNums span").text.strip()
                    deadline_element = self.driver.find_element(By.CSS_SELECTOR, ".m-czTime-r").text.strip()
                    deadline_time = deadline_element.replace('投注截止时间：', '')
                    
                    # Wait for table to load after clicking tab
                    self.wait_for_element(By.CSS_SELECTOR, ".m-czTab tbody tr")
                    
                    matches = self.driver.find_elements(By.CSS_SELECTOR, ".m-czTab tbody tr:not([style*='display: none'])")
                    
                    for match in matches:
                        try:
                            tds = match.find_elements(By.TAG_NAME, "td")
                            if len(tds) >= 4:
                                match_data = {
                                    'period': period_element,
                                    'deadline': deadline_time,
                                    'match_num': tds[0].text.strip(),
                                    'league': tds[1].text.strip(),
                                    'start_time': tds[2].text.strip(),
                                }
                                
                                # Handle team names
                                teams_element = tds[3].find_element(By.CLASS_NAME, "team")
                                teams_text = teams_element.text.strip()
                                if "VS" in teams_text:
                                    home_team, away_team = teams_text.split("VS")
                                    match_data['home_team'] = home_team.strip()
                                    match_data['away_team'] = away_team.strip()
                                
                                if game_type_text == '4场进球':
                                    # Get period number and deadline for 4场进球
                                    try:
                                        period_info = self.driver.find_element(By.CSS_SELECTOR, ".m-czNums li.on span").text.strip()
                                        deadline_info = self.driver.find_element(By.CSS_SELECTOR, ".m-czTime-r.f-fr").text.strip()
                                        deadline_time = deadline_info.replace('投注截止时间：', '')
                                        
                                        match_data['period'] = period_info
                                        match_data['deadline'] = deadline_time
                                    except Exception as e:
                                        print(f"Error getting period/deadline info for 4场进球: {str(e)}")
                                        match_data['period'] = ''
                                        match_data['deadline'] = ''
                                    
                                    # Handle betting options for 4场进球
                                    betting_divs = tds[5].find_elements(By.CSS_SELECTOR, ".tdDiv")
                                    if len(betting_divs) == 2:
                                        # Home team goals
                                        home_options = betting_divs[0].find_elements(By.CSS_SELECTOR, "span em")
                                        home_values = [opt.text.strip() for opt in home_options]
                                        if len(home_values) >= 4:
                                            for i, val in enumerate(['0', '1', '2', '3+']):
                                                match_data[f'home_goals_{val}'] = home_values[i]
                                        
                                        # Away team goals
                                        away_options = betting_divs[1].find_elements(By.CSS_SELECTOR, "span em")
                                        away_values = [opt.text.strip() for opt in away_options]
                                        if len(away_values) >= 4:
                                            for i, val in enumerate(['0', '1', '2', '3+']):
                                                match_data[f'away_goals_{val}'] = away_values[i]
                                
                                elif game_type_text == '6场半全场':
                                    # Get period number and deadline for 6场半全场
                                    try:
                                        period_info = self.driver.find_element(By.CSS_SELECTOR, ".m-czNums li.on span").text.strip()
                                        deadline_info = self.driver.find_element(By.CSS_SELECTOR, ".m-czTime-r.f-fr").text.strip()
                                        deadline_time = deadline_info.replace('投注截止时间：', '')
                                        
                                        match_data['period'] = period_info
                                        match_data['deadline'] = deadline_time
                                    except Exception as e:
                                        print(f"Error getting period/deadline info for 6场半全场: {str(e)}")
                                        match_data['period'] = ''
                                        match_data['deadline'] = ''
                                    
                                    # Handle betting options for 6场半全场
                                    betting_divs = tds[5].find_elements(By.CSS_SELECTOR, ".tdDiv")
                                    if len(betting_divs) == 2:
                                        # Half-time options
                                        half_time_options = betting_divs[0].find_elements(By.CSS_SELECTOR, "span em")
                                        half_time_values = [opt.text.strip() for opt in half_time_options]
                                        if len(half_time_values) >= 3:
                                            match_data['half_win'] = half_time_values[0]
                                            match_data['half_draw'] = half_time_values[1]
                                            match_data['half_lose'] = half_time_values[2]
                                        
                                        # Full-time options
                                        full_time_options = betting_divs[1].find_elements(By.CSS_SELECTOR, "span em")
                                        full_time_values = [opt.text.strip() for opt in full_time_options]
                                        if len(full_time_values) >= 3:
                                            match_data['full_win'] = full_time_values[0]
                                            match_data['full_draw'] = full_time_values[1]
                                            match_data['full_lose'] = full_time_values[2]
                                
                                elif game_type_text == '任选9场':
                                    # Get period number and deadline
                                    try:
                                        period_info = self.driver.find_element(By.CSS_SELECTOR, ".m-czNums li.on span").text.strip()
                                        deadline_info = self.driver.find_element(By.CSS_SELECTOR, ".m-czTime-r.f-fr").text.strip()
                                        deadline_time = deadline_info.replace('投注截止时间：', '')
                                        
                                        # Add period and deadline to match data
                                        match_data['period'] = period_info
                                        match_data['deadline'] = deadline_time
                                    except Exception as e:
                                        print(f"Error getting period/deadline info: {str(e)}")
                                        match_data['period'] = ''
                                        match_data['deadline'] = ''
                                    
                                    # Handle betting options
                                    betting_options = tds[4].find_elements(By.CSS_SELECTOR, ".tdDiv span em")
                                    if len(betting_options) >= 3:
                                        match_data['bet_win'] = betting_options[0].text.strip()
                                        match_data['bet_draw'] = betting_options[1].text.strip()
                                        match_data['bet_lose'] = betting_options[2].text.strip()
                                
                                else:
                                    # For other game types (胜负游戏 and 任选9场)
                                    betting_options = tds[4].find_elements(By.CSS_SELECTOR, ".tdDiv span em")
                                    if len(betting_options) >= 3:
                                        match_data['bet_win'] = betting_options[0].text.strip()
                                        match_data['bet_draw'] = betting_options[1].text.strip()
                                        match_data['bet_lose'] = betting_options[2].text.strip()
                                
                                matches_by_type[game_type_text].append(match_data)
                                print(f"Successfully processed match: {match_data['home_team']} vs {match_data['away_team']}")
                                
                        except Exception as e:
                            print(f"Error processing individual match: {str(e)}")
                            continue
                            
                except Exception as e:
                    print(f"Error processing game type {game_type_text}: {str(e)}")
                    continue
            
            # Save matches by game type to separate CSV files
            for game_type, matches in matches_by_type.items():
                if matches:
                    print(f"Saving {len(matches)} matches for {game_type}...")
                    df = pd.DataFrame(matches)
                    filename = f'lottery_matches_{game_type}_{current_date}.csv'
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                    print(f"Data saved to {filename}")
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            self.driver.save_screenshot("error_screenshot.png")
            print("Error screenshot saved as error_screenshot.png")
        
        finally:
            print("Closing browser...")
            self.driver.quit()

    def run(self):
        self.scrape_match_data()

if __name__ == "__main__":
    scraper = LotteryScraper()
    scraper.run()
