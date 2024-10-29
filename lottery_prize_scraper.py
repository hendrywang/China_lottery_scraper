from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from datetime import datetime
import time

class LotteryPrizeScraper:
    def __init__(self):
        self.prize_columns = [
            'Issue_Number', 'Date', 'Game_Type',
            'First_Prize_Count', 'First_Prize_Amount',
            'Second_Prize_Count', 'Second_Prize_Amount',
            'Prize_Pool', 'Prize_Pool_Amount',
            'Prize_Notice_URL', 'Sales_Notice_URL'
        ]
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.base_url = "https://www.sporttery.cn/ctzc/kjgg/index.html"

    def wait_for_element(self, by, value, timeout=10):
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"Timeout waiting for element: {value}")
            return None

    def extract_prize_info(self, lottery_type='胜负游戏'):
        game_id_map = {
            '胜负游戏': 'sfc',
            '任选9场': 'rj',
            '6场半全场': 'bqc',
            '4场进球': 'jq'
        }
        
        game_id = game_id_map.get(lottery_type)
        if not game_id:
            return None

        try:
            prize_data = {
                'Game_Type': lottery_type,
                'Prize_Pool_Amount': self.driver.find_element(By.ID, f'{game_id}_pool').text,
                'Prize_Notice_URL': self.driver.find_element(By.CSS_SELECTOR, f'#kj_{game_id}_news a').get_attribute('href'),
                'Sales_Notice_URL': self.driver.find_element(By.CSS_SELECTOR, f'#kj_{game_id}_xl a').get_attribute('href')
            }

            # Different parsing logic based on game type
            if lottery_type == '胜负游戏':
                # Original logic for 胜负游戏
                prize_data.update({
                    'First_Prize_Count': self.driver.find_element(By.CSS_SELECTOR, f'#level_1_{game_id} .red').text,
                    'First_Prize_Amount': self.driver.find_elements(By.CSS_SELECTOR, f'#level_1_{game_id} .red')[1].text,
                    'Second_Prize_Count': self.driver.find_element(By.CSS_SELECTOR, f'#level_2_{game_id} .red').text,
                    'Second_Prize_Amount': self.driver.find_elements(By.CSS_SELECTOR, f'#level_2_{game_id} .red')[1].text,
                })
            else:
                # Logic for other game types (任选9场, etc.)
                kj_element = self.driver.find_element(By.ID, f'{game_id}_kj')
                if kj_element:
                    numbers = kj_element.find_elements(By.CLASS_NAME, 'red')
                    if len(numbers) >= 2:
                        prize_data.update({
                            'First_Prize_Count': numbers[0].text,
                            'First_Prize_Amount': numbers[1].text,
                            'Second_Prize_Count': None,  # These games only have one prize level
                            'Second_Prize_Amount': None
                        })
        
            # Get date and issue number
            date_element = self.wait_for_element(By.ID, f'openTime_kj_{game_id}')
            prize_data['Date'] = date_element.text.replace('开奖日期：', '') if date_element else None
            
            issue_element = self.wait_for_element(By.ID, f'{game_id}_issue')
            prize_data['Issue_Number'] = issue_element.get_attribute('value') if issue_element else None
            
            return prize_data
            
        except Exception as e:
            print(f"Error extracting prize info for {lottery_type}: {str(e)}")
            return None

    def scrape_prizes(self):
        print("Starting prize scraper...")
        self.driver.get(self.base_url)
        print("Page loaded, waiting for content...")
        time.sleep(5)
        
        lottery_types = ['胜负游戏', '任选9场', '6场半全场', '4场进球']
        all_prize_data = []
        
        try:
            lottery_tabs = self.driver.find_elements(By.CSS_SELECTOR, ".m-cz-tit span")
            
            for tab in lottery_tabs:
                lottery_type = tab.text.strip()
                if lottery_type in lottery_types:
                    print(f"Processing {lottery_type}...")
                    tab.click()
                    time.sleep(2)
                    
                    prize_data = self.extract_prize_info(lottery_type)
                    if prize_data:
                        all_prize_data.append(prize_data)
            
            if all_prize_data:
                filename = f'lottery_prizes_{datetime.now().strftime("%Y%m%d")}.csv'
                df = pd.DataFrame(all_prize_data, columns=self.prize_columns)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"Prize data saved to {filename}")
                
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            self.driver.save_screenshot("prize_error_screenshot.png")
            print("Error screenshot saved as prize_error_screenshot.png")
        
        finally:
            print("Closing browser...")
            self.driver.quit()

    def run(self):
        self.scrape_prizes()

if __name__ == "__main__":
    scraper = LotteryPrizeScraper()
    scraper.run()