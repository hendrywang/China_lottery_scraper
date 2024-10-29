Sure, I'd be happy to help you write a README for your Python lottery scraper project. Here's a suggested structure:

# Lottery Scraper

This is a Python-based web scraper that extracts lottery data from the [Sporttery.cn](https://www.sporttery.cn/) website. It allows you to scrape information about different lottery games, including:

- 胜负游戏 (Win/Lose Game)
- 任选9场 (Any 9 Games)
- 6场半全场 (6 Half-Full Games)
- 4场进球 (4 Goal Games)

The scraper saves the collected data as CSV files, with one file per lottery game type.

## Prerequisites

- Python 3.x
- Google Chrome web browser
- Chrome WebDriver (automatically downloaded using `webdriver-manager`)
- Required Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/your-username/lottery-scraper.git
   ```

2. Change to the project directory:

   ```
   cd lottery-scraper
   ```

3. Create a virtual environment (optional, but recommended):

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the `lottery_scraper.py` script to scrape the lottery results:

   ```
   python lottery_scraper.py
   ```

   This will save the results for each lottery game type in separate CSV files in the project directory.

2. Run the `lottery_selling.py` script to scrape the current lottery selling information:

   ```
   python lottery_selling.py
   ```

   This will save the selling data for each lottery game type in separate CSV files in the project directory.

## Configuration

The scraper scripts are configured to use headless mode for the Chrome browser, which means the browser window will not be visible during the scraping process. If you'd like to see the browser in action, you can remove the `--headless` argument from the `options.add_argument()` calls in the `__init__()` method of the `LotteryResultsScraper` and `LotteryScraper` classes.

## Contributing

If you find any issues or have suggestions for improvements, feel free to open a new issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
