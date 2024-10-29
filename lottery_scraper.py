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
        
        # Define issue numbers for different lottery types
        self.default_issues = {
            '胜负游戏': '24167',
            '任选9场': '24167',
            '6场半全场': '24214',
            '4场进球': '24214'
        }
        
        self.select_id_map = {
            '胜负游戏': 'sfc_issue',
            '任选9场': 'rj_issue',
            '6场半全场': 'bqc_issue',
            '4场进球': 'jq_issue'
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

    def get_issue_results(self, issue_value, lottery_type):
        try:
            # Use the type-specific issue number if no specific issue is provided
            actual_issue = issue_value or self.default_issues.get(lottery_type)
            select_id = self.select_id_map.get(lottery_type)
            
            if select_id:
                select_element = self.wait_for_element(By.ID, select_id)
                if select_element:
                    select = Select(select_element)
                    select.select_by_value(str(actual_issue))
                    time.sleep(2)
                    return True
        except Exception as e:
            print(f"Error selecting issue {issue_value} for {lottery_type}: {str(e)}")
        return False

    def get_issue_number(self, lottery_type):
        try:
            select_id = self.select_id_map.get(lottery_type)
            if select_id:
                select_element = self.wait_for_element(By.ID, select_id)
                if select_element:
                    select = Select(select_element)
                    selected_option = select.first_selected_option
                    return selected_option.get_attribute("value")
        except Exception as e:
            print(f"Error getting issue number: {str(e)}")
        return self.default_issues.get(lottery_type)

    def scrape_lottery_results(self, issue=None):
        print("Starting results scraper...")
        self.driver.get(self.base_url)
        print("Page loaded, waiting for content...")
        time.sleep(5)
        
        current_date = datetime.now().strftime("%Y%m%d")
        all_results = []
        
        try:
            lottery_tabs = self.driver.find_elements(By.CSS_SELECTOR, ".m-cz-tit span")
            
            for tab in lottery_tabs:
                try:
                    lottery_type = tab.text.strip()
                    print(f"Processing lottery type: {lottery_type}")
                    tab.click()
                    time.sleep(2)
                    
                    # Use type-specific issue if no specific issue is provided
                    actual_issue = issue or self.default_issues.get(lottery_type)
                    if actual_issue:
                        self.get_issue_results(actual_issue, lottery_type)
                    
                    date_element = self.wait_for_element(By.CSS_SELECTOR, "[id^='openTime_kj_']")
                    date = date_element.text.replace('开奖日期：', '') if date_element else None
                    
                    issue_number = self.get_issue_number(lottery_type)
                    print(f"Got issue number for {lottery_type}: {issue_number}")
                    
                    table = self.wait_for_element(By.CSS_SELECTOR, ".m-tabCz")
                    if table:
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        match_numbers = [th.text for th in rows[0].find_elements(By.TAG_NAME, "th")]
                        
                        for i in range(len(match_numbers)):
                            match_data = {
                                'Date': date,
                                'Issue': issue_number,
                                'Lottery_Type': lottery_type,
                                'Match_Number': match_numbers[i],
                            }
                            
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
                            
                            all_results.append(match_data)
                            
                except Exception as e:
                    print(f"Error processing lottery type {lottery_type}: {str(e)}")
                    continue
            
            if all_results:
                df = pd.DataFrame(all_results)
                issue_suffix = f"_{issue}" if issue else ""
                filename = f'lottery_results_{current_date}{issue_suffix}.csv'
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"All results saved to {filename}")
                
                for lottery_type in set(df['Lottery_Type']):
                    type_df = df[df['Lottery_Type'] == lottery_type]
                    type_filename = f'lottery_results_{lottery_type}_{current_date}_{self.default_issues[lottery_type]}.csv'
                    type_df.to_csv(type_filename, index=False, encoding='utf-8-sig')
                    print(f"Saved {lottery_type} results to {type_filename}")
            
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
    # No need to specify issue, will use default issues for each type
    scraper.run()
