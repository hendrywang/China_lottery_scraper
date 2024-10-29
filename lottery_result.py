from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import pandas as pd
from datetime import datetime
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class LotteryResultsScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.base_url = "https://www.sporttery.cn/ctzc/kjgg/index.html"
        
        self.select_id_map = {
            '胜负游戏': 'sfc_issue',
            '任选9场': 'rj_issue',
            '6场半全场': 'bqc_issue',
            '4场进球': 'jq_issue'
        }
        
        self.game_id_map = {
            '胜负游戏': 'sfc_game',
            '任选9场': 'rj_game',
            '6场半全场': 'bqc_game',
            '4场进球': 'jq_game'
        }

    def wait_for_element(self, by, value, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timeout waiting for element: {value}")
            return None

    def clean_team_name(self, text):
        return ''.join(text.split())

    def process_match_data(self, lottery_type, rows, i):
        match_data = {}
        
        if lottery_type == '6场半全场':
            match_index = i
            
            if len(rows) > 1:
                home_cells = rows[1].find_elements(By.TAG_NAME, "td")
                if match_index < len(home_cells):
                    match_data['Home_Team'] = self.clean_team_name(home_cells[match_index].get_attribute("textContent"))
            
            if len(rows) > 3:
                away_cells = rows[3].find_elements(By.TAG_NAME, "td")
                if match_index < len(away_cells):
                    match_data['Away_Team'] = self.clean_team_name(away_cells[match_index].get_attribute("textContent"))
            
            if len(rows) > 5:
                score_cells = rows[5].find_elements(By.TAG_NAME, "td")
                if match_index * 2 + 1 < len(score_cells):
                    match_data['Half_Time_Score'] = score_cells[match_index * 2].text.strip()
                    match_data['Full_Time_Score'] = score_cells[match_index * 2 + 1].text.strip()
            
            if len(rows) > 6:
                result_cells = rows[6].find_elements(By.TAG_NAME, "td")
                if match_index * 2 + 1 < len(result_cells):
                    match_data['Half_Time_Result'] = result_cells[match_index * 2].text.strip()
                    match_data['Full_Time_Result'] = result_cells[match_index * 2 + 1].text.strip()
        
        elif lottery_type == '4场进球':
            match_index = i
            
            if len(rows) > 1:
                home_cells = rows[1].find_elements(By.TAG_NAME, "td")
                if match_index < len(home_cells):
                    match_data['Home_Team'] = self.clean_team_name(home_cells[match_index].get_attribute("textContent"))
            
            if len(rows) > 3:
                away_cells = rows[3].find_elements(By.TAG_NAME, "td")
                if match_index < len(away_cells):
                    match_data['Away_Team'] = self.clean_team_name(away_cells[match_index].get_attribute("textContent"))
            
            if len(rows) > 5:
                score_cells = rows[5].find_elements(By.TAG_NAME, "td")
                if match_index < len(score_cells):
                    match_data['Score'] = score_cells[match_index].text.strip()
            
            if len(rows) > 6:
                result_cells = rows[6].find_elements(By.TAG_NAME, "td")
                if match_index * 2 + 1 < len(result_cells):
                    match_data['Home_Goals'] = result_cells[match_index * 2].text.strip()
                    match_data['Away_Goals'] = result_cells[match_index * 2 + 1].text.strip()
        
        else:
            if len(rows) > 1:
                home_cells = rows[1].find_elements(By.TAG_NAME, "td")
                if i < len(home_cells):
                    match_data['Home_Team'] = self.clean_team_name(home_cells[i].text)
            
            if len(rows) > 3:
                away_cells = rows[3].find_elements(By.TAG_NAME, "td")
                if i < len(away_cells):
                    match_data['Away_Team'] = self.clean_team_name(away_cells[i].text)
            
            if len(rows) > 4:
                score_cells = rows[4].find_elements(By.TAG_NAME, "td")
                if i < len(score_cells):
                    match_data['Score'] = score_cells[i].text.strip()
            
            if len(rows) > 5:
                result_cells = rows[5].find_elements(By.TAG_NAME, "td")
                if i < len(result_cells):
                    match_data['Result'] = result_cells[i].text.strip()
        
        return match_data

    def scrape_lottery_results(self, issue=None):
        print("Starting results scraper...")
        self.driver.get(self.base_url)
        print("Page loaded, waiting for content...")
        time.sleep(5)
        
        current_date = datetime.now().strftime("%Y%m%d")
        
        try:
            lottery_tabs = self.driver.find_elements(By.CSS_SELECTOR, ".m-cz-tit span")
            
            for tab in lottery_tabs:
                try:
                    lottery_type = tab.text.strip()
                    print(f"Processing lottery type: {lottery_type}")
                    tab.click()
                    time.sleep(2)
                    
                    results = []
                    
                    date_id_map = {
                        '胜负游戏': 'openTime_kj_sfc',
                        '任选9场': 'openTime_kj_rj',
                        '6场半全场': 'openTime_kj_bqc',
                        '4场进球': 'openTime_kj_jq'
                    }
                    
                    date_id = date_id_map.get(lottery_type)
                    if date_id:
                        date_element = self.wait_for_element(By.ID, date_id)
                        date = date_element.text.replace('开奖日期：', '') if date_element else None
                        print(f"Got date for {lottery_type}: {date}")
                    
                    select_id = self.select_id_map.get(lottery_type)
                    if select_id:
                        select_element = self.wait_for_element(By.ID, select_id)
                        if select_element:
                            select = Select(select_element)
                            issue_number = select.first_selected_option.get_attribute("value")
                    
                    game_id = self.game_id_map.get(lottery_type)
                    if game_id:
                        table = self.wait_for_element(By.ID, game_id)
                        if table:
                            rows = table.find_elements(By.TAG_NAME, "tr")
                            
                            if lottery_type == '6场半全场':
                                match_count = 6
                            elif lottery_type == '4场进球':
                                match_count = 4
                            else:
                                match_numbers = [th.text for th in rows[0].find_elements(By.TAG_NAME, "th")]
                                match_count = len(match_numbers)
                            
                            for i in range(match_count):
                                match_data = {
                                    'Period': issue_number,
                                    'Date': date,
                                    'Match_Number': str(i + 1),
                                }
                                
                                match_data.update(self.process_match_data(lottery_type, rows, i))
                                results.append(match_data)
                    
                    if results:
                        df = pd.DataFrame(results)
                        filename = f'lottery_results_{lottery_type}_{issue_number}.csv'
                        df.to_csv(filename, index=False, encoding='utf-8-sig')
                        print(f"Saved {lottery_type} results to {filename}")
                                
                except Exception as e:
                    print(f"Error processing lottery type {lottery_type}: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            self.driver.save_screenshot("error_screenshot.png")
            print("Error screenshot saved as error_screenshot.png")
        
        finally:
            print("Closing browser...")
            self.driver.quit()

    def run(self, issue=None):
        self.scrape_lottery_results(issue)

if __name__ == "__main__":
    scraper = LotteryResultsScraper()
    scraper.run()
