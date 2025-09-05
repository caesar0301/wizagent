Task Aim: Retrieve historical stock data for a given company for a specific period.

Steps:
1. Call LLM directly for the target stock ticker symbol.
2. Navigate to the 'Historical Data' or 'Historical Quotes' section with `https://www.nasdaq.com/market-activity/stocks/{STOCK_TICKER_SYMBOL}/historical` by repalcing {STOCK_TICKER_SYMBOL} directly for historical data.
3. Click 'Download historical data'.
4. Read the downloaded CSV file.
5. Filter the data by date range and extract the desired columns.
6. Format and save the data to a new CSV file.

Alternatives:

Method 1:
1. Navigate to Nasdaq.com.
2. Search for the company's ticker symbol.
3. Navigate to the 'Historical Data' or 'Historical Quotes' section.

Method 2:
- Google Finance: View interactive charts for historical data.

Notes:
- Nasdaq.com provides a convenient download option for historical data.
- Always verify the date range and filter the data programmatically if needed.